"""Number entities for Lyngdorf integration."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfSoundPressure, UnitOfTime
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
    """Set up Lyngdorf number entities."""
    coordinator = entry.runtime_data.coordinator

    entities: list[NumberEntity] = [
        LyngdorfTrimBassNumber(coordinator),
        LyngdorfTrimTrebleNumber(coordinator),
        LyngdorfTrimCenterNumber(coordinator),
        LyngdorfTrimLFENumber(coordinator),
        LyngdorfTrimSurroundsNumber(coordinator),
        LyngdorfTrimHeightNumber(coordinator),
        LyngdorfLipsyncNumber(coordinator),
    ]

    async_add_entities(entities, update_before_add=True)


class LyngdorfNumberEntity(CoordinatorEntity[LyngdorfCoordinator], NumberEntity):
    """Base class for Lyngdorf number entities."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: LyngdorfCoordinator,
        entity_type: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f'{DOMAIN}_{coordinator.model_id}_{entity_type}'.lower()

        model_name = coordinator.client._model_config['name']
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f'{DOMAIN}_{coordinator.model_id}')},
            manufacturer='Lyngdorf',
            model=model_name,
            name=f'Lyngdorf {model_name}',
        )


class LyngdorfTrimBassNumber(LyngdorfNumberEntity):
    """Number entity for bass trim control."""

    _attr_translation_key = 'trim_bass'
    _attr_native_min_value = -12.0
    _attr_native_max_value = 12.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfSoundPressure.DECIBEL

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize bass trim number."""
        super().__init__(coordinator, 'trim_bass')

    @property
    def native_value(self) -> float | None:
        """Return current bass trim."""
        if self.coordinator.data.trim:
            return self.coordinator.data.trim.bass
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set bass trim."""
        await self.coordinator.client.trim.set_bass(value)
        await self.coordinator.async_request_refresh()


class LyngdorfTrimTrebleNumber(LyngdorfNumberEntity):
    """Number entity for treble trim control."""

    _attr_translation_key = 'trim_treble'
    _attr_native_min_value = -12.0
    _attr_native_max_value = 12.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfSoundPressure.DECIBEL

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize treble trim number."""
        super().__init__(coordinator, 'trim_treble')

    @property
    def native_value(self) -> float | None:
        """Return current treble trim."""
        if self.coordinator.data.trim:
            return self.coordinator.data.trim.treble
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set treble trim."""
        await self.coordinator.client.trim.set_treble(value)
        await self.coordinator.async_request_refresh()


class LyngdorfTrimCenterNumber(LyngdorfNumberEntity):
    """Number entity for center channel trim control."""

    _attr_translation_key = 'trim_center'
    _attr_native_min_value = -10.0
    _attr_native_max_value = 10.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfSoundPressure.DECIBEL

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize center trim number."""
        super().__init__(coordinator, 'trim_center')

    @property
    def native_value(self) -> float | None:
        """Return current center trim."""
        if self.coordinator.data.trim:
            return self.coordinator.data.trim.center
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set center trim."""
        await self.coordinator.client.trim.set_center(value)
        await self.coordinator.async_request_refresh()


class LyngdorfTrimLFENumber(LyngdorfNumberEntity):
    """Number entity for LFE channel trim control."""

    _attr_translation_key = 'trim_lfe'
    _attr_native_min_value = -10.0
    _attr_native_max_value = 10.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfSoundPressure.DECIBEL

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize LFE trim number."""
        super().__init__(coordinator, 'trim_lfe')

    @property
    def native_value(self) -> float | None:
        """Return current LFE trim."""
        if self.coordinator.data.trim:
            return self.coordinator.data.trim.lfe
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set LFE trim."""
        await self.coordinator.client.trim.set_lfe(value)
        await self.coordinator.async_request_refresh()


class LyngdorfTrimSurroundsNumber(LyngdorfNumberEntity):
    """Number entity for surround channels trim control."""

    _attr_translation_key = 'trim_surrounds'
    _attr_native_min_value = -10.0
    _attr_native_max_value = 10.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfSoundPressure.DECIBEL

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize surrounds trim number."""
        super().__init__(coordinator, 'trim_surrounds')

    @property
    def native_value(self) -> float | None:
        """Return current surrounds trim."""
        if self.coordinator.data.trim:
            return self.coordinator.data.trim.surrounds
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set surrounds trim."""
        await self.coordinator.client.trim.set_surrounds(value)
        await self.coordinator.async_request_refresh()


class LyngdorfTrimHeightNumber(LyngdorfNumberEntity):
    """Number entity for height channels trim control."""

    _attr_translation_key = 'trim_height'
    _attr_native_min_value = -10.0
    _attr_native_max_value = 10.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfSoundPressure.DECIBEL

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize height trim number."""
        super().__init__(coordinator, 'trim_height')

    @property
    def native_value(self) -> float | None:
        """Return current height trim."""
        if self.coordinator.data.trim:
            return self.coordinator.data.trim.height
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set height trim."""
        await self.coordinator.client.trim.set_height(value)
        await self.coordinator.async_request_refresh()


class LyngdorfLipsyncNumber(LyngdorfNumberEntity):
    """Number entity for lip sync delay control."""

    _attr_translation_key = 'lipsync'
    _attr_native_min_value = 0
    _attr_native_max_value = 500  # typical range, will be updated from device
    _attr_native_step = 5
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize lipsync number."""
        super().__init__(coordinator, 'lipsync')

    async def async_added_to_hass(self) -> None:
        """Query device for lipsync range."""
        await super().async_added_to_hass()
        try:
            range_info = await self.coordinator.client.lipsync.get_range()
            if range_info:
                self._attr_native_min_value = range_info['min']
                self._attr_native_max_value = range_info['max']
        except Exception as e:
            LOG.warning(f'Could not get lipsync range: {e}')

    @property
    def native_value(self) -> float | None:
        """Return current lipsync delay."""
        return self.coordinator.data.lipsync

    async def async_set_native_value(self, value: float) -> None:
        """Set lipsync delay."""
        await self.coordinator.client.lipsync.set(int(value))
        await self.coordinator.async_request_refresh()
