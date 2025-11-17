"""Python library for controlling Lyngdorf MP-50/MP-60 processors."""

import asyncio
import logging
import serial
from functools import wraps
from threading import RLock
from typing import Optional, Dict, Any, List

from .models import (
    get_model_config,
    SUPPORTED_MODELS,
    COMMAND_EOL,
    RESPONSE_EOL,
    db_to_protocol,
    protocol_to_db,
)
from .protocol import async_get_protocol

__version__ = '0.1.0'

LOG = logging.getLogger(__name__)


class PowerControl:
    """Power control interface."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Turn system power on."""
        return self._client._send_command('!POWERONMAIN')

    def off(self):
        """Turn system power off."""
        return self._client._send_command('!POWEROFFMAIN')

    def get(self) -> Optional[bool]:
        """Get power status (True=on, False=off)."""
        response = self._client._send_command('!POWER?')
        if response and '!POWER(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class VolumeControl:
    """Volume control interface."""

    def __init__(self, client):
        self._client = client

    def set(self, db: float):
        """
        Set volume level in dB.

        Args:
            db: Volume in dB (-99.9 to +20.0 for MP-50, -99.9 to +24.0 for MP-60)
        """
        value = db_to_protocol(db)
        min_vol = self._client._model_config['min_volume']
        max_vol = self._client._model_config['max_volume']
        value = max(min_vol, min(max_vol, value))
        return self._client._send_command(f'!VOL({value})')

    def up(self, amount: Optional[float] = None):
        """
        Increase volume.

        Args:
            amount: Optional amount in dB to increase (0.1 to 99.9)
        """
        if amount:
            value = db_to_protocol(amount)
            return self._client._send_command(f'!VOL+({value})')
        return self._client._send_command('!VOL+')

    def down(self, amount: Optional[float] = None):
        """
        Decrease volume.

        Args:
            amount: Optional amount in dB to decrease (0.1 to 99.9)
        """
        if amount:
            value = db_to_protocol(amount)
            return self._client._send_command(f'!VOL-({value})')
        return self._client._send_command('!VOL-')

    def get(self) -> Optional[float]:
        """Get current volume level in dB."""
        response = self._client._send_command('!VOL?')
        if response and '!VOL(' in response:
            vol = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(vol))
        return None

    def get_max(self) -> Optional[float]:
        """Get maximum volume setting in dB."""
        response = self._client._send_command('!MAXVOL?')
        if response and '!MAXVOL(' in response:
            max_vol = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(max_vol))
        return None

    def set_max(self, db: float):
        """Set maximum volume in dB (-55.0 to +20.0 for MP-50, -55.0 to +24.0 for MP-60)."""
        value = db_to_protocol(db)
        return self._client._send_command(f'!MAXVOL({value})')

    def get_default(self) -> Optional[float]:
        """Get default volume setting in dB."""
        response = self._client._send_command('!DEFVOL?')
        if response and '!DEFVOL(' in response:
            defvol = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(defvol))
        return None

    def set_default(self, db: Optional[float] = None):
        """Set default volume in dB, or None to use last volume on boot."""
        if db is None:
            return self._client._send_command('!DEFVOL(OFF)')
        value = db_to_protocol(db)
        return self._client._send_command(f'!DEFVOL({value})')


class MuteControl:
    """Mute control interface."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Mute on."""
        return self._client._send_command('!MUTEON')

    def off(self):
        """Mute off."""
        return self._client._send_command('!MUTEOFF')

    def toggle(self):
        """Toggle mute."""
        return self._client._send_command('!MUTE')

    def get(self) -> Optional[bool]:
        """Get mute status (True=muted, False=unmuted)."""
        response = self._client._send_command('!MUTE?')
        if response:
            return '!MUTEON' in response
        return None


class SourceControl:
    """Source/input control interface."""

    def __init__(self, client):
        self._client = client
        self._sources = {}  # will be populated by discover()

    def discover(self) -> Dict[int, str]:
        """
        Discover available sources.

        Returns:
            Dictionary mapping source index to source name
        """
        response = self._client._send_command('!SRCS?')
        if not response:
            return {}

        sources = {}
        lines = response.split('\r')
        for line in lines:
            if '!SRC(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    sources[idx] = name
                except (ValueError, IndexError):
                    continue

        self._sources = sources
        return sources

    def set(self, source: int):
        """Set source input by index."""
        return self._client._send_command(f'!SRC({source})')

    def get(self) -> Optional[Dict[str, Any]]:
        """Get current source info."""
        response = self._client._send_command('!SRC?')
        if response and '!SRC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                source_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'source': source_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    def next(self):
        """Select next source."""
        return self._client._send_command('!SRC+')

    def previous(self):
        """Select previous source."""
        return self._client._send_command('!SRC-')

    def info(self, source: int) -> Optional[Dict[str, Any]]:
        """Get info for specific source."""
        response = self._client._send_command(f'!SRC({source})?')
        if response and '!SRC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                source_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'source': source_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    def get_offset(self) -> Optional[float]:
        """Get source volume offset for current source in dB."""
        response = self._client._send_command('!SRCOFF?')
        if response and '!SRCOFF(' in response:
            offset = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(offset))
        return None

    def set_offset(self, db: float):
        """Set source volume offset for current source in dB (-10.0 to +10.0)."""
        value = db_to_protocol(db)
        value = max(-100, min(100, value))
        return self._client._send_command(f'!SRCOFF({value})')


class RoomPerfectControl:
    """RoomPerfect focus position and voicing control."""

    def __init__(self, client):
        self._client = client
        self._positions = {}
        self._voicings = {}

    def discover_positions(self) -> Dict[int, str]:
        """Discover available RoomPerfect focus positions."""
        response = self._client._send_command('!RPFOCS?')
        if not response:
            return {}

        positions = {}
        lines = response.split('\r')
        for line in lines:
            if '!RPFOC(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    positions[idx] = name
                except (ValueError, IndexError):
                    continue

        self._positions = positions
        return positions

    def get_position(self) -> Optional[Dict[str, Any]]:
        """Get current RoomPerfect position."""
        response = self._client._send_command('!RPFOC?')
        if response and '!RPFOC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                pos_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'position': pos_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    def set_position(self, position: int):
        """Set RoomPerfect position (0=bypass, 1-8=focus1-8, 9=global)."""
        return self._client._send_command(f'!RPFOC({position})')

    def next_position(self):
        """Select next RoomPerfect position."""
        return self._client._send_command('!RPFOC+')

    def previous_position(self):
        """Select previous RoomPerfect position."""
        return self._client._send_command('!RPFOC-')

    def discover_voicings(self) -> Dict[int, str]:
        """Discover available voicings."""
        response = self._client._send_command('!RPVOIS?')
        if not response:
            return {}

        voicings = {}
        lines = response.split('\r')
        for line in lines:
            if '!RPVOI(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    voicings[idx] = name
                except (ValueError, IndexError):
                    continue

        self._voicings = voicings
        return voicings

    def get_voicing(self) -> Optional[Dict[str, Any]]:
        """Get current voicing."""
        response = self._client._send_command('!RPVOI?')
        if response and '!RPVOI(' in response:
            try:
                parts = response.split('(')[1].split(')')
                voi_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'voicing': voi_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    def set_voicing(self, voicing: int):
        """Set voicing by index."""
        return self._client._send_command(f'!RPVOI({voicing})')

    def next_voicing(self):
        """Select next voicing."""
        return self._client._send_command('!RPVOI+')

    def previous_voicing(self):
        """Select previous voicing."""
        return self._client._send_command('!RPVOI-')


class AudioModeControl:
    """Audio processing mode control."""

    def __init__(self, client):
        self._client = client
        self._modes = {}

    def discover(self) -> Dict[int, str]:
        """Discover available audio processing modes."""
        response = self._client._send_command('!AUDMODEL?')
        if not response:
            return {}

        modes = {}
        lines = response.split('\r')
        for line in lines:
            if '!AUDMODE(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    modes[idx] = name
                except (ValueError, IndexError):
                    continue

        self._modes = modes
        return modes

    def get(self) -> Optional[Dict[str, Any]]:
        """Get current audio mode."""
        response = self._client._send_command('!AUDMODE?')
        if response and '!AUDMODE(' in response:
            try:
                parts = response.split('(')[1].split(')')
                mode_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'mode': mode_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    def set(self, mode: int):
        """Set audio processing mode by index."""
        return self._client._send_command(f'!AUDMODE({mode})')

    def next(self):
        """Select next audio mode."""
        return self._client._send_command('!AUDMODE+')

    def previous(self):
        """Select previous audio mode."""
        return self._client._send_command('!AUDMODE-')


class TrimControl:
    """Channel trim level controls."""

    def __init__(self, client):
        self._client = client

    def _get_trim(self, channel: str) -> Optional[float]:
        """Get trim level for a channel in dB."""
        response = self._client._send_command(f'!TRIM{channel}?')
        if response and f'!TRIM{channel}(' in response:
            trim = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(trim))
        return None

    def _set_trim(self, channel: str, db: float, min_db: float, max_db: float):
        """Set trim level for a channel in dB."""
        value = db_to_protocol(db)
        value = max(int(min_db * 10), min(int(max_db * 10), value))
        return self._client._send_command(f'!TRIM{channel}({value})')

    def get_bass(self) -> Optional[float]:
        """Get bass trim in dB."""
        return self._get_trim('BASS')

    def set_bass(self, db: float):
        """Set bass trim in dB (-12.0 to +12.0)."""
        return self._set_trim('BASS', db, -12.0, 12.0)

    def get_treble(self) -> Optional[float]:
        """Get treble trim in dB."""
        return self._get_trim('TREB')

    def set_treble(self, db: float):
        """Set treble trim in dB (-12.0 to +12.0)."""
        return self._set_trim('TREB', db, -12.0, 12.0)

    def get_center(self) -> Optional[float]:
        """Get center channel trim in dB."""
        return self._get_trim('CENTER')

    def set_center(self, db: float):
        """Set center channel trim in dB (-10.0 to +10.0)."""
        return self._set_trim('CENTER', db, -10.0, 10.0)

    def get_lfe(self) -> Optional[float]:
        """Get LFE channel trim in dB."""
        return self._get_trim('LFE')

    def set_lfe(self, db: float):
        """Set LFE channel trim in dB (-10.0 to +10.0)."""
        return self._set_trim('LFE', db, -10.0, 10.0)

    def get_surrounds(self) -> Optional[float]:
        """Get surround channels trim in dB."""
        return self._get_trim('SURRS')

    def set_surrounds(self, db: float):
        """Set surround channels trim in dB (-10.0 to +10.0)."""
        return self._set_trim('SURRS', db, -10.0, 10.0)

    def get_height(self) -> Optional[float]:
        """Get height channels trim in dB."""
        return self._get_trim('HEIGHT')

    def set_height(self, db: float):
        """Set height channels trim in dB (-10.0 to +10.0)."""
        return self._set_trim('HEIGHT', db, -10.0, 10.0)


class LipsyncControl:
    """Lipsync delay control."""

    def __init__(self, client):
        self._client = client

    def get(self) -> Optional[int]:
        """Get lipsync delay in milliseconds."""
        response = self._client._send_command('!LIPSYNC?')
        if response and '!LIPSYNC(' in response:
            delay = response.split('(')[1].split(')')[0]
            return int(delay)
        return None

    def set(self, ms: int):
        """Set lipsync delay in milliseconds."""
        return self._client._send_command(f'!LIPSYNC({ms})')

    def up(self):
        """Increase lipsync delay by 5ms."""
        return self._client._send_command('!LIPSYNC+')

    def down(self):
        """Decrease lipsync delay by 5ms."""
        return self._client._send_command('!LIPSYNC-')

    def get_range(self) -> Optional[Dict[str, int]]:
        """Get valid lipsync range."""
        response = self._client._send_command('!LIPSYNCRANGE?')
        if response and '!LIPSYNCRANGE(' in response:
            try:
                values = response.split('(')[1].split(')')[0].split(',')
                return {'min': int(values[0]), 'max': int(values[1])}
            except (ValueError, IndexError):
                return None
        return None


class LoudnessControl:
    """Loudness control."""

    def __init__(self, client):
        self._client = client

    def get(self) -> Optional[bool]:
        """Get loudness status."""
        response = self._client._send_command('!LOUDNESS?')
        if response and '!LOUDNESS(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None

    def set(self, enabled: bool):
        """Set loudness on/off."""
        value = '1' if enabled else '0'
        return self._client._send_command(f'!LOUDNESS({value})')


class DTSDialogControl:
    """DTS Dialog Control (MP-60 only)."""

    def __init__(self, client):
        self._client = client

    def is_available(self) -> bool:
        """Check if DTS Dialog Control is available."""
        response = self._client._send_command('!DTSDIALOGAVAILABLE?')
        if response and '!DTSDIALOGAVAILABLE(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return False

    def get(self) -> Optional[float]:
        """Get DTS Dialog Control setting in dB."""
        response = self._client._send_command('!DTSDIALOG?')
        if response and '!DTSDIALOG(' in response:
            value = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(value))
        return None

    def up(self):
        """Increase DTS Dialog Control level."""
        return self._client._send_command('!DTSDIALOGUP')

    def down(self):
        """Decrease DTS Dialog Control level."""
        return self._client._send_command('!DTSDIALOGDN')


class Zone2Control:
    """Zone 2 control interface."""

    def __init__(self, client):
        self._client = client
        self.power = Zone2PowerControl(client)
        self.volume = Zone2VolumeControl(client)
        self.mute = Zone2MuteControl(client)
        self.source = Zone2SourceControl(client)


class Zone2PowerControl:
    """Zone 2 power control."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Turn Zone 2 power on."""
        return self._client._send_command('!POWERONZONE2')

    def off(self):
        """Turn Zone 2 power off."""
        return self._client._send_command('!POWEROFFZONE2')

    def get(self) -> Optional[bool]:
        """Get Zone 2 power status."""
        response = self._client._send_command('!POWERZONE2?')
        if response and '!POWERZONE2(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class Zone2VolumeControl:
    """Zone 2 volume control."""

    def __init__(self, client):
        self._client = client

    def set(self, db: float):
        """Set Zone 2 volume in dB."""
        value = db_to_protocol(db)
        min_vol = self._client._model_config['min_volume']
        max_vol = self._client._model_config['max_volume']
        value = max(min_vol, min(max_vol, value))
        return self._client._send_command(f'!ZVOL({value})')

    def up(self, amount: Optional[float] = None):
        """Increase Zone 2 volume."""
        if amount:
            value = db_to_protocol(amount)
            return self._client._send_command(f'!ZVOL+({value})')
        return self._client._send_command('!ZVOL+')

    def down(self, amount: Optional[float] = None):
        """Decrease Zone 2 volume."""
        if amount:
            value = db_to_protocol(amount)
            return self._client._send_command(f'!ZVOL-({value})')
        return self._client._send_command('!ZVOL-')

    def get(self) -> Optional[float]:
        """Get Zone 2 volume level in dB."""
        response = self._client._send_command('!ZVOL?')
        if response and '!ZVOL(' in response:
            vol = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(vol))
        return None


class Zone2MuteControl:
    """Zone 2 mute control."""

    def __init__(self, client):
        self._client = client

    def on(self):
        """Zone 2 mute on."""
        return self._client._send_command('!ZMUTEON')

    def off(self):
        """Zone 2 mute off."""
        return self._client._send_command('!ZMUTEOFF')

    def toggle(self):
        """Toggle Zone 2 mute."""
        return self._client._send_command('!ZMUTE')

    def get(self) -> Optional[bool]:
        """Get Zone 2 mute status."""
        response = self._client._send_command('!ZMUTE?')
        if response:
            return '!ZMUTEON' in response
        return None


class Zone2SourceControl:
    """Zone 2 source control."""

    def __init__(self, client):
        self._client = client
        self._sources = {}

    def discover(self) -> Dict[int, str]:
        """Discover available Zone 2 sources."""
        response = self._client._send_command('!ZSRCS?')
        if not response:
            return {}

        sources = {}
        lines = response.split('\r')
        for line in lines:
            if '!ZSRC(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    sources[idx] = name
                except (ValueError, IndexError):
                    continue

        self._sources = sources
        return sources

    def set(self, source: int):
        """Set Zone 2 source."""
        return self._client._send_command(f'!ZSRC({source})')

    def get(self) -> Optional[Dict[str, Any]]:
        """Get Zone 2 current source."""
        response = self._client._send_command('!ZSRC?')
        if response and '!ZSRC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                source_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'source': source_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    def next(self):
        """Select next Zone 2 source."""
        return self._client._send_command('!ZSRC+')

    def previous(self):
        """Select previous Zone 2 source."""
        return self._client._send_command('!ZSRC-')

    def info(self, source: int) -> Optional[Dict[str, Any]]:
        """Get info for specific Zone 2 source."""
        response = self._client._send_command(f'!ZSRC({source})?')
        if response and '!ZSRC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                source_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'source': source_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None


class DeviceControl:
    """Device info and utility commands."""

    def __init__(self, client):
        self._client = client

    def name(self) -> Optional[str]:
        """Get device name."""
        response = self._client._send_command('!DEVICE?')
        if response and '!DEVICE(' in response:
            return response.split('(')[1].split(')')[0]
        return None

    def ping(self) -> bool:
        """Ping device."""
        response = self._client._send_command('!PING?')
        return response == '!PONG'

    def get_interface(self) -> Optional[str]:
        """Get active interface (IP or SERIAL)."""
        response = self._client._send_command('!INTERFACE?')
        if response and '!INTERFACE(' in response:
            return response.split('(')[1].split(')')[0]
        return None

    def set_verbosity(self, level: int):
        """Set verbosity level (0, 1, or 2)."""
        level = max(0, min(2, level))
        return self._client._send_command(f'!VERB({level})')

    def get_verbosity(self) -> Optional[int]:
        """Get current verbosity level."""
        response = self._client._send_command('!VERB?')
        if response and '!VERB(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None


def get_lyngdorf(model_id: str, port_url: str, **serial_config_overrides) -> 'LyngdorfSync':
    """
    Get synchronous Lyngdorf controller.

    Args:
        model_id: Model identifier (mp50, mp60)
        port_url: Serial port or socket URL (e.g. '/dev/ttyUSB0', 'socket://192.168.1.100:84')
        **serial_config_overrides: Override serial config (e.g. baudrate=9600)

    Returns:
        Synchronous Lyngdorf controller instance
    """
    if model_id not in SUPPORTED_MODELS:
        LOG.error(f"Unsupported model '{model_id}'. Supported: {SUPPORTED_MODELS}")
        return None

    return LyngdorfSync(model_id, port_url, serial_config_overrides)


async def async_get_lyngdorf(
    model_id: str, port_url: str, loop, **serial_config_overrides
) -> 'LyngdorfAsync':
    """
    Get asynchronous Lyngdorf controller.

    Args:
        model_id: Model identifier (mp50, mp60)
        port_url: Serial port or socket URL
        loop: asyncio event loop
        **serial_config_overrides: Override serial config

    Returns:
        Asynchronous Lyngdorf controller instance
    """
    if model_id not in SUPPORTED_MODELS:
        LOG.error(f"Unsupported model '{model_id}'. Supported: {SUPPORTED_MODELS}")
        return None

    model_config = get_model_config(model_id)
    serial_config = model_config['rs232'].copy()
    if serial_config_overrides:
        LOG.debug(f'Overriding serial config: {serial_config_overrides}')
        serial_config.update(serial_config_overrides)

    min_time_between_commands = model_config['min_time_between_commands']

    protocol = await async_get_protocol(
        port_url, min_time_between_commands, RESPONSE_EOL, serial_config, loop
    )

    client = LyngdorfAsync(model_id, model_config, protocol)

    # set verbosity level to 1 (automatic status updates)
    await client.device.set_verbosity(1)

    return client


class LyngdorfSync:
    """Synchronous Lyngdorf controller."""

    def __init__(self, model_id: str, port_url: str, serial_config_overrides: dict):
        self._model_id = model_id
        self._model_config = get_model_config(model_id)

        # setup serial config
        serial_config = self._model_config['rs232'].copy()
        if serial_config_overrides:
            LOG.debug(f'Overriding serial config: {serial_config_overrides}')
            serial_config.update(serial_config_overrides)

        self._port = serial.serial_for_url(port_url, **serial_config)
        self._lock = RLock()

        # create control interfaces
        self.power = PowerControl(self)
        self.volume = VolumeControl(self)
        self.mute = MuteControl(self)
        self.source = SourceControl(self)
        self.roomperfect = RoomPerfectControl(self)
        self.audio_mode = AudioModeControl(self)
        self.trim = TrimControl(self)
        self.lipsync = LipsyncControl(self)
        self.loudness = LoudnessControl(self)
        self.zone_2 = Zone2Control(self)
        self.device = DeviceControl(self)

        # MP-60 specific
        if self._model_config.get('supports_dts_dialog'):
            self.dts_dialog = DTSDialogControl(self)

        # set verbosity level to 1
        self.device.set_verbosity(1)

    def _send_command(self, command: str) -> Optional[str]:
        """Send command and return response."""
        with self._lock:
            # clear buffers
            self._port.reset_output_buffer()
            self._port.reset_input_buffer()

            # build request
            request = (command + COMMAND_EOL).encode('ascii')
            LOG.debug(f'Sending: {request}')

            # send
            self._port.write(request)
            self._port.flush()

            # read response
            result = bytearray()
            eol_bytes = RESPONSE_EOL.encode('ascii')

            while True:
                c = self._port.read(1)
                if not c:
                    LOG.warning(f'Timeout waiting for response to {command}')
                    raise serial.SerialTimeoutException(
                        f'Connection timed out! Last received: {bytes(result)}'
                    )

                result += c
                if result.endswith(eol_bytes):
                    break

            response = bytes(result).decode('ascii').strip()

            # filter out echo messages (# prefix) from verbosity level 2
            if response.startswith('#'):
                # read next line for actual status
                result = bytearray()
                while True:
                    c = self._port.read(1)
                    if not c:
                        break
                    result += c
                    if result.endswith(eol_bytes):
                        break
                response = bytes(result).decode('ascii').strip()

            LOG.debug(f'Received: {response}')
            return response


class LyngdorfAsync:
    """Asynchronous Lyngdorf controller."""

    def __init__(self, model_id: str, model_config: dict, protocol):
        self._model_id = model_id
        self._model_config = model_config
        self._protocol = protocol

        # create control interfaces
        self.power = AsyncPowerControl(self)
        self.volume = AsyncVolumeControl(self)
        self.mute = AsyncMuteControl(self)
        self.source = AsyncSourceControl(self)
        self.roomperfect = AsyncRoomPerfectControl(self)
        self.audio_mode = AsyncAudioModeControl(self)
        self.trim = AsyncTrimControl(self)
        self.lipsync = AsyncLipsyncControl(self)
        self.loudness = AsyncLoudnessControl(self)
        self.zone_2 = AsyncZone2Control(self)
        self.device = AsyncDeviceControl(self)

        # MP-60 specific
        if self._model_config.get('supports_dts_dialog'):
            self.dts_dialog = AsyncDTSDialogControl(self)

    async def _send_command(self, command: str) -> Optional[str]:
        """Send command and return response."""
        request = (command + COMMAND_EOL).encode('ascii')
        return await self._protocol.send(request)


# Async versions of control classes
class AsyncPowerControl(PowerControl):
    async def on(self):
        return await self._client._send_command('!POWERONMAIN')

    async def off(self):
        return await self._client._send_command('!POWEROFFMAIN')

    async def get(self) -> Optional[bool]:
        response = await self._client._send_command('!POWER?')
        if response and '!POWER(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class AsyncVolumeControl(VolumeControl):
    async def set(self, db: float):
        value = db_to_protocol(db)
        min_vol = self._client._model_config['min_volume']
        max_vol = self._client._model_config['max_volume']
        value = max(min_vol, min(max_vol, value))
        return await self._client._send_command(f'!VOL({value})')

    async def up(self, amount: Optional[float] = None):
        if amount:
            value = db_to_protocol(amount)
            return await self._client._send_command(f'!VOL+({value})')
        return await self._client._send_command('!VOL+')

    async def down(self, amount: Optional[float] = None):
        if amount:
            value = db_to_protocol(amount)
            return await self._client._send_command(f'!VOL-({value})')
        return await self._client._send_command('!VOL-')

    async def get(self) -> Optional[float]:
        response = await self._client._send_command('!VOL?')
        if response and '!VOL(' in response:
            vol = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(vol))
        return None

    async def get_max(self) -> Optional[float]:
        response = await self._client._send_command('!MAXVOL?')
        if response and '!MAXVOL(' in response:
            max_vol = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(max_vol))
        return None

    async def set_max(self, db: float):
        value = db_to_protocol(db)
        return await self._client._send_command(f'!MAXVOL({value})')

    async def get_default(self) -> Optional[float]:
        response = await self._client._send_command('!DEFVOL?')
        if response and '!DEFVOL(' in response:
            defvol = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(defvol))
        return None

    async def set_default(self, db: Optional[float] = None):
        if db is None:
            return await self._client._send_command('!DEFVOL(OFF)')
        value = db_to_protocol(db)
        return await self._client._send_command(f'!DEFVOL({value})')


class AsyncMuteControl(MuteControl):
    async def on(self):
        return await self._client._send_command('!MUTEON')

    async def off(self):
        return await self._client._send_command('!MUTEOFF')

    async def toggle(self):
        return await self._client._send_command('!MUTE')

    async def get(self) -> Optional[bool]:
        response = await self._client._send_command('!MUTE?')
        if response:
            return '!MUTEON' in response
        return None


class AsyncSourceControl(SourceControl):
    async def discover(self) -> Dict[int, str]:
        response = await self._client._send_command('!SRCS?')
        if not response:
            return {}

        sources = {}
        lines = response.split('\r')
        for line in lines:
            if '!SRC(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    sources[idx] = name
                except (ValueError, IndexError):
                    continue

        self._sources = sources
        return sources

    async def set(self, source: int):
        return await self._client._send_command(f'!SRC({source})')

    async def get(self) -> Optional[Dict[str, Any]]:
        response = await self._client._send_command('!SRC?')
        if response and '!SRC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                source_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'source': source_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    async def next(self):
        return await self._client._send_command('!SRC+')

    async def previous(self):
        return await self._client._send_command('!SRC-')

    async def info(self, source: int) -> Optional[Dict[str, Any]]:
        response = await self._client._send_command(f'!SRC({source})?')
        if response and '!SRC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                source_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'source': source_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    async def get_offset(self) -> Optional[float]:
        response = await self._client._send_command('!SRCOFF?')
        if response and '!SRCOFF(' in response:
            offset = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(offset))
        return None

    async def set_offset(self, db: float):
        value = db_to_protocol(db)
        value = max(-100, min(100, value))
        return await self._client._send_command(f'!SRCOFF({value})')


class AsyncRoomPerfectControl(RoomPerfectControl):
    async def discover_positions(self) -> Dict[int, str]:
        response = await self._client._send_command('!RPFOCS?')
        if not response:
            return {}

        positions = {}
        lines = response.split('\r')
        for line in lines:
            if '!RPFOC(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    positions[idx] = name
                except (ValueError, IndexError):
                    continue

        self._positions = positions
        return positions

    async def get_position(self) -> Optional[Dict[str, Any]]:
        response = await self._client._send_command('!RPFOC?')
        if response and '!RPFOC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                pos_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'position': pos_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    async def set_position(self, position: int):
        return await self._client._send_command(f'!RPFOC({position})')

    async def next_position(self):
        return await self._client._send_command('!RPFOC+')

    async def previous_position(self):
        return await self._client._send_command('!RPFOC-')

    async def discover_voicings(self) -> Dict[int, str]:
        response = await self._client._send_command('!RPVOIS?')
        if not response:
            return {}

        voicings = {}
        lines = response.split('\r')
        for line in lines:
            if '!RPVOI(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    voicings[idx] = name
                except (ValueError, IndexError):
                    continue

        self._voicings = voicings
        return voicings

    async def get_voicing(self) -> Optional[Dict[str, Any]]:
        response = await self._client._send_command('!RPVOI?')
        if response and '!RPVOI(' in response:
            try:
                parts = response.split('(')[1].split(')')
                voi_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'voicing': voi_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    async def set_voicing(self, voicing: int):
        return await self._client._send_command(f'!RPVOI({voicing})')

    async def next_voicing(self):
        return await self._client._send_command('!RPVOI+')

    async def previous_voicing(self):
        return await self._client._send_command('!RPVOI-')


class AsyncAudioModeControl(AudioModeControl):
    async def discover(self) -> Dict[int, str]:
        response = await self._client._send_command('!AUDMODEL?')
        if not response:
            return {}

        modes = {}
        lines = response.split('\r')
        for line in lines:
            if '!AUDMODE(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    modes[idx] = name
                except (ValueError, IndexError):
                    continue

        self._modes = modes
        return modes

    async def get(self) -> Optional[Dict[str, Any]]:
        response = await self._client._send_command('!AUDMODE?')
        if response and '!AUDMODE(' in response:
            try:
                parts = response.split('(')[1].split(')')
                mode_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'mode': mode_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    async def set(self, mode: int):
        return await self._client._send_command(f'!AUDMODE({mode})')

    async def next(self):
        return await self._client._send_command('!AUDMODE+')

    async def previous(self):
        return await self._client._send_command('!AUDMODE-')


class AsyncTrimControl(TrimControl):
    async def _get_trim(self, channel: str) -> Optional[float]:
        response = await self._client._send_command(f'!TRIM{channel}?')
        if response and f'!TRIM{channel}(' in response:
            trim = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(trim))
        return None

    async def _set_trim(self, channel: str, db: float, min_db: float, max_db: float):
        value = db_to_protocol(db)
        value = max(int(min_db * 10), min(int(max_db * 10), value))
        return await self._client._send_command(f'!TRIM{channel}({value})')

    async def get_bass(self) -> Optional[float]:
        return await self._get_trim('BASS')

    async def set_bass(self, db: float):
        return await self._set_trim('BASS', db, -12.0, 12.0)

    async def get_treble(self) -> Optional[float]:
        return await self._get_trim('TREB')

    async def set_treble(self, db: float):
        return await self._set_trim('TREB', db, -12.0, 12.0)

    async def get_center(self) -> Optional[float]:
        return await self._get_trim('CENTER')

    async def set_center(self, db: float):
        return await self._set_trim('CENTER', db, -10.0, 10.0)

    async def get_lfe(self) -> Optional[float]:
        return await self._get_trim('LFE')

    async def set_lfe(self, db: float):
        return await self._set_trim('LFE', db, -10.0, 10.0)

    async def get_surrounds(self) -> Optional[float]:
        return await self._get_trim('SURRS')

    async def set_surrounds(self, db: float):
        return await self._set_trim('SURRS', db, -10.0, 10.0)

    async def get_height(self) -> Optional[float]:
        return await self._get_trim('HEIGHT')

    async def set_height(self, db: float):
        return await self._set_trim('HEIGHT', db, -10.0, 10.0)


class AsyncLipsyncControl(LipsyncControl):
    async def get(self) -> Optional[int]:
        response = await self._client._send_command('!LIPSYNC?')
        if response and '!LIPSYNC(' in response:
            delay = response.split('(')[1].split(')')[0]
            return int(delay)
        return None

    async def set(self, ms: int):
        return await self._client._send_command(f'!LIPSYNC({ms})')

    async def up(self):
        return await self._client._send_command('!LIPSYNC+')

    async def down(self):
        return await self._client._send_command('!LIPSYNC-')

    async def get_range(self) -> Optional[Dict[str, int]]:
        response = await self._client._send_command('!LIPSYNCRANGE?')
        if response and '!LIPSYNCRANGE(' in response:
            try:
                values = response.split('(')[1].split(')')[0].split(',')
                return {'min': int(values[0]), 'max': int(values[1])}
            except (ValueError, IndexError):
                return None
        return None


class AsyncLoudnessControl(LoudnessControl):
    async def get(self) -> Optional[bool]:
        response = await self._client._send_command('!LOUDNESS?')
        if response and '!LOUDNESS(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None

    async def set(self, enabled: bool):
        value = '1' if enabled else '0'
        return await self._client._send_command(f'!LOUDNESS({value})')


class AsyncDTSDialogControl(DTSDialogControl):
    async def is_available(self) -> bool:
        response = await self._client._send_command('!DTSDIALOGAVAILABLE?')
        if response and '!DTSDIALOGAVAILABLE(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return False

    async def get(self) -> Optional[float]:
        response = await self._client._send_command('!DTSDIALOG?')
        if response and '!DTSDIALOG(' in response:
            value = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(value))
        return None

    async def up(self):
        return await self._client._send_command('!DTSDIALOGUP')

    async def down(self):
        return await self._client._send_command('!DTSDIALOGDN')


class AsyncZone2Control:
    """Async Zone 2 control interface."""

    def __init__(self, client):
        self._client = client
        self.power = AsyncZone2PowerControl(client)
        self.volume = AsyncZone2VolumeControl(client)
        self.mute = AsyncZone2MuteControl(client)
        self.source = AsyncZone2SourceControl(client)


class AsyncZone2PowerControl(Zone2PowerControl):
    async def on(self):
        return await self._client._send_command('!POWERONZONE2')

    async def off(self):
        return await self._client._send_command('!POWEROFFZONE2')

    async def get(self) -> Optional[bool]:
        response = await self._client._send_command('!POWERZONE2?')
        if response and '!POWERZONE2(' in response:
            state = response.split('(')[1].split(')')[0]
            return state == '1'
        return None


class AsyncZone2VolumeControl(Zone2VolumeControl):
    async def set(self, db: float):
        value = db_to_protocol(db)
        min_vol = self._client._model_config['min_volume']
        max_vol = self._client._model_config['max_volume']
        value = max(min_vol, min(max_vol, value))
        return await self._client._send_command(f'!ZVOL({value})')

    async def up(self, amount: Optional[float] = None):
        if amount:
            value = db_to_protocol(amount)
            return await self._client._send_command(f'!ZVOL+({value})')
        return await self._client._send_command('!ZVOL+')

    async def down(self, amount: Optional[float] = None):
        if amount:
            value = db_to_protocol(amount)
            return await self._client._send_command(f'!ZVOL-({value})')
        return await self._client._send_command('!ZVOL-')

    async def get(self) -> Optional[float]:
        response = await self._client._send_command('!ZVOL?')
        if response and '!ZVOL(' in response:
            vol = response.split('(')[1].split(')')[0]
            return protocol_to_db(int(vol))
        return None


class AsyncZone2MuteControl(Zone2MuteControl):
    async def on(self):
        return await self._client._send_command('!ZMUTEON')

    async def off(self):
        return await self._client._send_command('!ZMUTEOFF')

    async def toggle(self):
        return await self._client._send_command('!ZMUTE')

    async def get(self) -> Optional[bool]:
        response = await self._client._send_command('!ZMUTE?')
        if response:
            return '!ZMUTEON' in response
        return None


class AsyncZone2SourceControl(Zone2SourceControl):
    async def discover(self) -> Dict[int, str]:
        response = await self._client._send_command('!ZSRCS?')
        if not response:
            return {}

        sources = {}
        lines = response.split('\r')
        for line in lines:
            if '!ZSRC(' in line and ')' in line and '"' in line:
                try:
                    idx = int(line.split('(')[1].split(')')[0])
                    name = line.split('"')[1]
                    sources[idx] = name
                except (ValueError, IndexError):
                    continue

        self._sources = sources
        return sources

    async def set(self, source: int):
        return await self._client._send_command(f'!ZSRC({source})')

    async def get(self) -> Optional[Dict[str, Any]]:
        response = await self._client._send_command('!ZSRC?')
        if response and '!ZSRC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                source_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'source': source_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None

    async def next(self):
        return await self._client._send_command('!ZSRC+')

    async def previous(self):
        return await self._client._send_command('!ZSRC-')

    async def info(self, source: int) -> Optional[Dict[str, Any]]:
        response = await self._client._send_command(f'!ZSRC({source})?')
        if response and '!ZSRC(' in response:
            try:
                parts = response.split('(')[1].split(')')
                source_num = int(parts[0])
                name = response.split('"')[1] if '"' in response else ''
                return {'source': source_num, 'name': name}
            except (ValueError, IndexError):
                return None
        return None


class AsyncDeviceControl(DeviceControl):
    async def name(self) -> Optional[str]:
        response = await self._client._send_command('!DEVICE?')
        if response and '!DEVICE(' in response:
            return response.split('(')[1].split(')')[0]
        return None

    async def ping(self) -> bool:
        response = await self._client._send_command('!PING?')
        return response == '!PONG'

    async def get_interface(self) -> Optional[str]:
        response = await self._client._send_command('!INTERFACE?')
        if response and '!INTERFACE(' in response:
            return response.split('(')[1].split(')')[0]
        return None

    async def set_verbosity(self, level: int):
        level = max(0, min(2, level))
        return await self._client._send_command(f'!VERB({level})')

    async def get_verbosity(self) -> Optional[int]:
        response = await self._client._send_command('!VERB?')
        if response and '!VERB(' in response:
            level = response.split('(')[1].split(')')[0]
            return int(level)
        return None
