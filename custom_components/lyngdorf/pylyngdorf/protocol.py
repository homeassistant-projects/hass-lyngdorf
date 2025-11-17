"""Lyngdorf RS232/IP protocol implementation."""

import asyncio
import functools
import logging
import re
import time
from collections.abc import Callable
from typing import Optional

from .exceptions import ConnectionError as LyngdorfConnectionError
from .exceptions import TimeoutError as LyngdorfTimeoutError

LOG = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 2.0

# regex patterns for parsing unsolicited state updates
STATE_UPDATE_PATTERNS = {
    'power': re.compile(r'!POWER\((\d+)\)'),
    'power_zone2': re.compile(r'!POWERZONE2\((\d+)\)'),
    'volume': re.compile(r'!VOL\((-?\d+)\)'),
    'volume_zone2': re.compile(r'!ZVOL\((-?\d+)\)'),
    'mute': re.compile(r'!MUTE(ON|OFF)'),
    'mute_zone2': re.compile(r'!ZMUTE(ON|OFF)'),
    'source': re.compile(r'!SRC\((\d+)\)"([^"]*)"'),
    'source_zone2': re.compile(r'!ZSRC\((\d+)\)"([^"]*)"'),
    'roomperfect_position': re.compile(r'!RPFOC\((\d+)\)"([^"]*)"'),
    'roomperfect_voicing': re.compile(r'!RPVOI\((\d+)\)"([^"]*)"'),
    'audio_mode': re.compile(r'!AUDMODE\((\d+)\)"([^"]*)"'),
    'lipsync': re.compile(r'!LIPSYNC\((\d+)\)'),
    'loudness': re.compile(r'!LOUDNESS\((\d+)\)'),
}


async def async_get_protocol(
    serial_port: str,
    min_time_between_commands: float,
    response_eol: str,
    serial_config: dict,
    loop,
):
    """Create async protocol for Lyngdorf communication."""

    def locked_method(method):
        """Decorator to ensure only one command is sent at a time."""
        @functools.wraps(method)
        async def wrapper(self, *method_args, **method_kwargs):
            async with self._lock:
                return await method(self, *method_args, **method_kwargs)

        return wrapper

    def ensure_connected(method):
        """Decorator to check connection before sending."""
        @functools.wraps(method)
        async def wrapper(self, *method_args, **method_kwargs):
            try:
                await asyncio.wait_for(self._connected.wait(), self._timeout)
            except Exception:
                LOG.debug(f'Timeout sending data to {self._serial_port}, no connection')
                return
            return await method(self, *method_args, **method_kwargs)

        return wrapper

    class LyngdorfProtocol(asyncio.Protocol):
        """Async protocol for Lyngdorf communication with callback support."""

        def __init__(
            self,
            serial_port: str,
            min_time_between_commands: float,
            response_eol: str,
            serial_config: dict,
            loop,
        ):
            super().__init__()
            self._serial_port = serial_port
            self._min_time_between_commands = min_time_between_commands
            self._response_eol = response_eol
            self._serial_config = serial_config
            self._loop = loop

            self._last_send = time.time() - 1
            self._timeout = serial_config.get('timeout', DEFAULT_TIMEOUT)

            self._transport = None
            self._connected = asyncio.Event()
            self._q = asyncio.Queue()
            self._lock = asyncio.Lock()

            # callback system for unsolicited state updates
            self._state_callbacks: dict[str, list[Callable]] = {}
            self._general_callback: Optional[Callable] = None

            LOG.info(f'Lyngdorf protocol timeout set to {self._timeout}s')

        def register_state_callback(self, state_type: str, callback: Callable) -> None:
            """Register callback for specific state updates (e.g., 'power', 'volume')."""
            if state_type not in self._state_callbacks:
                self._state_callbacks[state_type] = []
            self._state_callbacks[state_type].append(callback)
            LOG.debug(f'Registered callback for {state_type} updates')

        def register_general_callback(self, callback: Callable) -> None:
            """Register callback for all state updates."""
            self._general_callback = callback
            LOG.debug('Registered general state update callback')

        def _parse_state_update(self, message: str) -> Optional[tuple[str, dict]]:
            """Parse message to extract state update information."""
            # try each pattern to identify the state type
            for state_type, pattern in STATE_UPDATE_PATTERNS.items():
                match = pattern.search(message)
                if match:
                    data = {'raw': message, 'groups': match.groups()}
                    return (state_type, data)
            return None

        def _dispatch_state_update(self, state_type: str, data: dict) -> None:
            """Dispatch state update to registered callbacks."""
            # call state-specific callbacks
            if state_type in self._state_callbacks:
                for callback in self._state_callbacks[state_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            asyncio.create_task(callback(state_type, data))
                        else:
                            callback(state_type, data)
                    except Exception as e:
                        LOG.exception(f'Error in {state_type} callback: {e}')

            # call general callback
            if self._general_callback:
                try:
                    if asyncio.iscoroutinefunction(self._general_callback):
                        asyncio.create_task(self._general_callback(state_type, data))
                    else:
                        self._general_callback(state_type, data)
                except Exception as e:
                    LOG.exception(f'Error in general callback: {e}')

        def connection_made(self, transport):
            """Handle connection established."""
            self._transport = transport
            LOG.debug(f'Port {self._serial_port} opened')
            self._connected.set()

        def data_received(self, data):
            """
            Handle data received from device.

            This method processes both:
            1. Responses to sent commands (queued for send() method)
            2. Unsolicited state updates (dispatched to callbacks)
            """
            # always queue the data for send() method to consume
            asyncio.ensure_future(self._q.put(data))

            # try to parse as state update and dispatch callbacks
            try:
                message = data.decode('ascii', errors='ignore').strip()
                if message and not message.startswith('#'):  # skip echo messages
                    state_update = self._parse_state_update(message)
                    if state_update:
                        state_type, state_data = state_update
                        LOG.debug(f'Unsolicited state update: {state_type} = {state_data}')
                        self._dispatch_state_update(state_type, state_data)
            except Exception as e:
                LOG.debug(f'Error parsing state update: {e}')

        def connection_lost(self, exc):
            """Handle connection lost."""
            LOG.debug(f'Port {self._serial_port} closed')
            self._connected.clear()

        async def _throttle_requests(self):
            """Throttle RS232 sends to avoid causing timeouts."""
            delta = time.time() - self._last_send

            if delta < self._min_time_between_commands:
                delay = max(0, self._min_time_between_commands - delta)
                LOG.debug(f'Throttling: sleeping {delay:.3f}s before next command')
                await asyncio.sleep(delay)

        @locked_method
        @ensure_connected
        async def send(self, request: bytes, wait_for_reply: bool = True) -> Optional[str]:
            """Send command and optionally wait for response."""
            await self._throttle_requests()

            # clear buffers
            self._transport.serial.reset_output_buffer()
            self._transport.serial.reset_input_buffer()
            while not self._q.empty():
                self._q.get_nowait()

            # send command
            LOG.debug(f'Sending: {request}')
            self._last_send = time.time()
            self._transport.serial.write(request)

            if not wait_for_reply:
                return None

            # read response - handle verbosity level 2 echo (# prefix)
            data = bytearray()
            response_eol_bytes = self._response_eol.encode('ascii')

            try:
                while True:
                    data += await asyncio.wait_for(self._q.get(), self._timeout)

                    if response_eol_bytes in data:
                        LOG.debug(
                            f'Received: {data.decode("ascii", errors="ignore")} (len={len(data)})'
                        )

                        # split by EOL and filter empty lines
                        lines = data.split(response_eol_bytes)
                        lines = [line for line in lines if line]

                        if not lines:
                            return ''

                        # filter out echo messages (# prefix) from verbosity level 2
                        status_lines = [
                            line for line in lines
                            if not line.startswith(b'#')
                        ]

                        if not status_lines:
                            # only echo received, no status - wait for more data
                            data = bytearray()
                            continue

                        if len(status_lines) > 1:
                            LOG.debug(f'Multiple response lines, using first: {status_lines}')

                        return status_lines[0].decode('ascii', errors='ignore')

            except asyncio.TimeoutError as e:
                LOG.warning(
                    f'Timeout waiting for response to {request}: received={data} ({self._timeout}s)'
                )
                raise LyngdorfTimeoutError(
                    f'Timeout waiting for response: {self._timeout}s'
                ) from e

    # create protocol factory
    factory = functools.partial(
        LyngdorfProtocol,
        serial_port,
        min_time_between_commands,
        response_eol,
        serial_config,
        loop,
    )

    LOG.info(f'Creating connection to {serial_port}: {serial_config}')

    # lazy import to avoid blocking
    def _import_serial_asyncio():
        from serial_asyncio import create_serial_connection

        return create_serial_connection

    create_serial_connection = await loop.run_in_executor(None, _import_serial_asyncio)

    # create connection
    _, protocol = await create_serial_connection(loop, factory, serial_port, **serial_config)
    return protocol
