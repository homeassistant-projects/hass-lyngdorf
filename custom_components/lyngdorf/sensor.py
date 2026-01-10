"""Sensor entities for Lyngdorf integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    """Set up Lyngdorf sensor entities."""
    coordinator = entry.runtime_data.coordinator

    entities: list[SensorEntity] = [
        LyngdorfAudioFormatSensor(coordinator),
        LyngdorfVideoInputSensor(coordinator),
        LyngdorfVideoOutputSensor(coordinator),
    ]

    async_add_entities(entities, update_before_add=True)


class LyngdorfSensorEntity(CoordinatorEntity[LyngdorfCoordinator], SensorEntity):
    """Base class for Lyngdorf sensor entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LyngdorfCoordinator,
        entity_type: str,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f'{DOMAIN}_{coordinator.model_id}_{entity_type}'.lower()

        model_name = coordinator.client._model_config['name']
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f'{DOMAIN}_{coordinator.model_id}')},
            manufacturer='Lyngdorf',
            model=model_name,
            name=f'Lyngdorf {model_name}',
        )


class LyngdorfAudioFormatSensor(LyngdorfSensorEntity):
    """Sensor for current audio format information."""

    _attr_translation_key = 'audio_format'
    _attr_icon = 'mdi:waveform'

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize audio format sensor."""
        super().__init__(coordinator, 'audio_format')

    @property
    def native_value(self) -> str | None:
        """Return current audio format."""
        if self.coordinator.data.audio_info:
            audio = self.coordinator.data.audio_info
            parts = []
            if audio.format:
                parts.append(audio.format)
            if audio.channels:
                parts.append(audio.channels)
            if audio.sample_rate:
                parts.append(audio.sample_rate)
            return ' '.join(parts) if parts else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional audio information."""
        if self.coordinator.data.audio_info:
            audio = self.coordinator.data.audio_info
            return {
                'format': audio.format,
                'sample_rate': audio.sample_rate,
                'channels': audio.channels,
                'bitrate': audio.bitrate,
            }
        return None


class LyngdorfVideoInputSensor(LyngdorfSensorEntity):
    """Sensor for current video input."""

    _attr_translation_key = 'video_input'
    _attr_icon = 'mdi:video-input-hdmi'

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize video input sensor."""
        super().__init__(coordinator, 'video_input')

    @property
    def native_value(self) -> str | None:
        """Return current video input name."""
        if self.coordinator.data.video_info:
            return self.coordinator.data.video_info.input_name
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional video input information."""
        if self.coordinator.data.video_info:
            video = self.coordinator.data.video_info
            return {
                'input_index': video.input,
                'resolution': video.resolution,
                'format': video.format,
            }
        return None


class LyngdorfVideoOutputSensor(LyngdorfSensorEntity):
    """Sensor for current video output."""

    _attr_translation_key = 'video_output'
    _attr_icon = 'mdi:video-output-hdmi'

    def __init__(self, coordinator: LyngdorfCoordinator) -> None:
        """Initialize video output sensor."""
        super().__init__(coordinator, 'video_output')

    @property
    def native_value(self) -> str | None:
        """Return current video output name."""
        if self.coordinator.data.video_info:
            return self.coordinator.data.video_info.output_name
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional video output information."""
        if self.coordinator.data.video_info:
            video = self.coordinator.data.video_info
            return {
                'output_index': video.output,
                'resolution': video.resolution,
                'format': video.format,
            }
        return None
