"""DataUpdateCoordinator for Lyngdorf integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .pylyngdorf.state import (
    AudioModeState,
    DeviceState,
    PowerState,
    RoomPerfectState,
    SourceInfo,
    TrimSettings,
    VolumeState,
)

LOG = logging.getLogger(__name__)


class LyngdorfCoordinator(DataUpdateCoordinator[DeviceState]):
    """Coordinator to manage fetching Lyngdorf device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: Any,
        model_id: str,
        update_interval: timedelta = timedelta(seconds=30),
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOG,
            name=f'Lyngdorf {model_id}',
            update_interval=update_interval,
        )
        self.client = client
        self.model_id = model_id

        # initialize device state
        self.data = DeviceState(
            power=PowerState(),
            volume_main=VolumeState(),
            volume_zone2=VolumeState(),
        )

        # register protocol callbacks for push notifications
        if hasattr(client, '_protocol'):
            self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        """Set up protocol callbacks for real-time state updates."""
        protocol = self.client._protocol

        async def on_state_update(state_type: str, data: dict[str, Any]) -> None:
            """Handle state update from device."""
            LOG.debug(f'State update callback: {state_type}')
            # trigger immediate refresh to update all entities
            await self.async_request_refresh()

        protocol.register_general_callback(on_state_update)

    async def _async_update_data(self) -> DeviceState:
        """Fetch data from Lyngdorf device."""
        try:
            # create new state object
            state = DeviceState(
                power=PowerState(),
                volume_main=VolumeState(),
                volume_zone2=VolumeState(),
            )

            # fetch main zone state
            power = await self.client.power.get()
            if power is not None:
                state.power.main = power
                state.connected = True

                if power:
                    # only query other state if device is on
                    volume = await self.client.volume.get()
                    if volume is not None:
                        state.volume_main.level = volume

                    mute = await self.client.mute.get()
                    if mute is not None:
                        state.volume_main.muted = mute

                    source_info = await self.client.source.get()
                    if source_info:
                        state.source_main = SourceInfo(
                            index=source_info['source'],
                            name=source_info.get('name', ''),
                        )

                    # fetch RoomPerfect state
                    rp_pos = await self.client.roomperfect.get_position()
                    rp_voi = await self.client.roomperfect.get_voicing()
                    if rp_pos or rp_voi:
                        state.roomperfect = RoomPerfectState()
                        if rp_pos:
                            state.roomperfect.position = rp_pos.get('position')
                            state.roomperfect.position_name = rp_pos.get('name')
                        if rp_voi:
                            state.roomperfect.voicing = rp_voi.get('voicing')
                            state.roomperfect.voicing_name = rp_voi.get('name')

                    # fetch audio mode
                    audio_mode = await self.client.audio_mode.get()
                    if audio_mode:
                        state.audio_mode = AudioModeState(
                            mode=audio_mode.get('mode'),
                            mode_name=audio_mode.get('name'),
                        )

                    # fetch trim settings
                    trim = TrimSettings(
                        bass=await self.client.trim.get_bass() or 0.0,
                        treble=await self.client.trim.get_treble() or 0.0,
                        center=await self.client.trim.get_center() or 0.0,
                        lfe=await self.client.trim.get_lfe() or 0.0,
                        surrounds=await self.client.trim.get_surrounds() or 0.0,
                        height=await self.client.trim.get_height() or 0.0,
                    )
                    state.trim = trim

                    # fetch lipsync
                    lipsync = await self.client.lipsync.get()
                    if lipsync is not None:
                        state.lipsync = lipsync

                    # fetch loudness
                    loudness = await self.client.loudness.get()
                    if loudness is not None:
                        state.loudness = loudness

            # fetch zone 2 state
            zone2_power = await self.client.zone_2.power.get()
            if zone2_power is not None:
                state.power.zone2 = zone2_power

                if zone2_power:
                    zone2_volume = await self.client.zone_2.volume.get()
                    if zone2_volume is not None:
                        state.volume_zone2.level = zone2_volume

                    zone2_mute = await self.client.zone_2.mute.get()
                    if zone2_mute is not None:
                        state.volume_zone2.muted = zone2_mute

                    zone2_source = await self.client.zone_2.source.get()
                    if zone2_source:
                        state.source_zone2 = SourceInfo(
                            index=zone2_source['source'],
                            name=zone2_source.get('name', ''),
                        )

            return state

        except Exception as e:
            LOG.exception(f'Error fetching Lyngdorf data: {e}')
            raise UpdateFailed(f'Error communicating with device: {e}') from e
