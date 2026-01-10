"""Select entities for Lyngdorf integration."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LyngdorfConfigEntry
from .const import DOMAIN
from .coordinator import LyngdorfCoordinator

LOG = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LyngdorfConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lyngdorf select entities."""
    coordinator = entry.runtime_data.coordinator
    client = coordinator.client

    entities: list[SelectEntity] = []

    # discover RoomPerfect positions
    positions = await client.roomperfect.discover_positions()
    if positions:
        entities.append(LyngdorfRoomPerfectPositionSelect(coordinator, positions))

    # discover RoomPerfect voicings
    voicings = await client.roomperfect.discover_voicings()
    if voicings:
        entities.append(LyngdorfRoomPerfectVoicingSelect(coordinator, voicings))

    # discover audio modes
    audio_modes = await client.audio_mode.discover()
    if audio_modes:
        entities.append(LyngdorfAudioModeSelect(coordinator, audio_modes))

    if entities:
        async_add_entities(entities, update_before_add=True)


class LyngdorfSelectEntity(CoordinatorEntity[LyngdorfCoordinator], SelectEntity):
    """Base class for Lyngdorf select entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LyngdorfCoordinator,
        entity_type: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f'{DOMAIN}_{coordinator.model_id}_{entity_type}'.lower()

        model_name = coordinator.client._model_config['name']
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f'{DOMAIN}_{coordinator.model_id}')},
            manufacturer='Lyngdorf',
            model=model_name,
            name=f'Lyngdorf {model_name}',
        )


class LyngdorfRoomPerfectPositionSelect(LyngdorfSelectEntity):
    """Select entity for RoomPerfect focus position."""

    _attr_translation_key = 'roomperfect_position'

    def __init__(
        self,
        coordinator: LyngdorfCoordinator,
        positions: dict[int, str],
    ) -> None:
        """Initialize RoomPerfect position select."""
        super().__init__(coordinator, 'roomperfect_position')
        self._positions = positions
        self._position_name_to_id = {name: idx for idx, name in positions.items()}
        self._attr_options = list(self._position_name_to_id.keys())

    @property
    def current_option(self) -> str | None:
        """Return current RoomPerfect position."""
        if self.coordinator.data.roomperfect:
            return self.coordinator.data.roomperfect.position_name
        return None

    async def async_select_option(self, option: str) -> None:
        """Set RoomPerfect position."""
        position_id = self._position_name_to_id.get(option)
        if position_id is not None:
            await self.coordinator.client.roomperfect.set_position(position_id)
            await self.coordinator.async_request_refresh()


class LyngdorfRoomPerfectVoicingSelect(LyngdorfSelectEntity):
    """Select entity for RoomPerfect voicing."""

    _attr_translation_key = 'roomperfect_voicing'

    def __init__(
        self,
        coordinator: LyngdorfCoordinator,
        voicings: dict[int, str],
    ) -> None:
        """Initialize RoomPerfect voicing select."""
        super().__init__(coordinator, 'roomperfect_voicing')
        self._voicings = voicings
        self._voicing_name_to_id = {name: idx for idx, name in voicings.items()}
        self._attr_options = list(self._voicing_name_to_id.keys())

    @property
    def current_option(self) -> str | None:
        """Return current RoomPerfect voicing."""
        if self.coordinator.data.roomperfect:
            return self.coordinator.data.roomperfect.voicing_name
        return None

    async def async_select_option(self, option: str) -> None:
        """Set RoomPerfect voicing."""
        voicing_id = self._voicing_name_to_id.get(option)
        if voicing_id is not None:
            await self.coordinator.client.roomperfect.set_voicing(voicing_id)
            await self.coordinator.async_request_refresh()


class LyngdorfAudioModeSelect(LyngdorfSelectEntity):
    """Select entity for audio processing mode."""

    _attr_translation_key = 'audio_mode'

    def __init__(
        self,
        coordinator: LyngdorfCoordinator,
        modes: dict[int, str],
    ) -> None:
        """Initialize audio mode select."""
        super().__init__(coordinator, 'audio_mode')
        self._modes = modes
        self._mode_name_to_id = {name: idx for idx, name in modes.items()}
        self._attr_options = list(self._mode_name_to_id.keys())

    @property
    def current_option(self) -> str | None:
        """Return current audio mode."""
        if self.coordinator.data.audio_mode:
            return self.coordinator.data.audio_mode.mode_name
        return None

    async def async_select_option(self, option: str) -> None:
        """Set audio processing mode."""
        mode_id = self._mode_name_to_id.get(option)
        if mode_id is not None:
            await self.coordinator.client.audio_mode.set(mode_id)
            await self.coordinator.async_request_refresh()
