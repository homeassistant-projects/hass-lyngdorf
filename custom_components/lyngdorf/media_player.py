"""Home Assistant Media Player for Lyngdorf processors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LyngdorfConfigEntry, LyngdorfData
from .const import (
    CONF_MODEL,
    CONF_SOURCES,
    CONF_ZONE2_DEFAULT_SOURCE,
    CONF_ZONE2_ENABLED,
    CONF_ZONE2_MAX_VOLUME,
    DEFAULT_ZONE2_ENABLED,
    DEFAULT_ZONE2_MAX_VOLUME,
    DOMAIN,
)

LOG = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LyngdorfConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lyngdorf media player entities."""
    data = entry.runtime_data

    entities: list[LyngdorfMediaPlayer] = [LyngdorfMediaPlayer(entry, data, zone='main')]

    # check if zone 2 is enabled in options or data
    zone2_enabled = entry.options.get(
        CONF_ZONE2_ENABLED,
        entry.data.get(CONF_ZONE2_ENABLED, DEFAULT_ZONE2_ENABLED),
    )

    if zone2_enabled:
        entities.append(LyngdorfMediaPlayer(entry, data, zone='zone2'))

    async_add_entities(entities, update_before_add=True)


@callback
def _get_sources_from_dict(
    data: dict[str, Any],
) -> tuple[dict[int, str], dict[str, int], list[str]]:
    """Extract source mappings from config data."""
    sources_config = data[CONF_SOURCES]
    source_id_name = {int(index): name for index, name in sources_config.items()}
    source_name_id = {v: k for k, v in source_id_name.items()}
    source_names = sorted(source_name_id.keys(), key=lambda v: source_name_id[v])
    return source_id_name, source_name_id, source_names


@callback
def _get_sources(
    entry: LyngdorfConfigEntry,
) -> tuple[dict[int, str], dict[str, int], list[str]]:
    """Get source configuration from config entry."""
    data = entry.options if CONF_SOURCES in entry.options else entry.data
    return _get_sources_from_dict(data)


class LyngdorfMediaPlayer(MediaPlayerEntity):
    """Lyngdorf media player entity."""

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: LyngdorfConfigEntry,
        data: LyngdorfData,
        zone: str = 'main',
    ) -> None:
        """Initialize the media player."""
        self._entry = entry
        self._data = data
        self._client = data.client
        self._model_id = entry.data[CONF_MODEL]
        self._zone = zone
        self._is_zone2 = zone == 'zone2'

        # get zone 2 configuration if applicable
        if self._is_zone2:
            self._zone2_max_volume = entry.options.get(
                CONF_ZONE2_MAX_VOLUME,
                entry.data.get(CONF_ZONE2_MAX_VOLUME, DEFAULT_ZONE2_MAX_VOLUME),
            )
            self._zone2_default_source = entry.options.get(
                CONF_ZONE2_DEFAULT_SOURCE,
                entry.data.get(CONF_ZONE2_DEFAULT_SOURCE),
            )
        else:
            self._zone2_max_volume = None
            self._zone2_default_source = None

        # get model configuration and sources
        from .pylyngdorf.models import AUDIO_INPUTS as SOURCES, get_model_config

        self._manufacturer = 'Lyngdorf'
        self._default_sources = SOURCES
        self._model_config = get_model_config(self._model_id)

        zone_suffix = '_zone2' if self._is_zone2 else ''
        self._attr_unique_id = f'{DOMAIN}_{self._model_id}{zone_suffix}'.lower().replace(' ', '_')

        # device information
        model_name = self._model_config['name']
        zone_name = ' Zone 2' if self._is_zone2 else ''

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            manufacturer=self._manufacturer,
            model=model_name,
            name=f'{self._manufacturer} {model_name}{zone_name}',
            sw_version='Unknown',
        )

        # setup source list from config or use defaults
        if CONF_SOURCES in entry.data:
            source_id_name, source_name_id, source_names = _get_sources(entry)
            self._source_id_to_name = source_id_name
            self._source_name_to_id = source_name_id
            self._attr_source_list = source_names
        else:
            # use default sources
            self._source_id_to_name = self._default_sources
            self._source_name_to_id = {v: k for k, v in self._default_sources.items()}
            self._attr_source_list = sorted(
                self._source_name_to_id.keys(),
                key=lambda v: self._source_name_to_id[v],
            )

    async def async_added_to_hass(self) -> None:
        """Handle entity being added to hass."""
        await self._initialize()

    async def _initialize(self) -> None:
        """Initialize connection dependent variables."""
        LOG.debug(f'Connected to {self._model_id} / {self._unique_id}')
        await self.async_update()

    async def async_update(self) -> None:
        """Retrieve the latest state."""
        LOG.debug(f'Updating {self.unique_id}')

        try:
            # use zone2 controls if this is a zone 2 entity
            if self._is_zone2:
                power_control = self._client.zone2.power
                volume_control = self._client.zone2.volume
                mute_control = self._client.zone2.mute
                source_control = self._client.zone2.source
            else:
                power_control = self._client.power
                volume_control = self._client.volume
                mute_control = self._client.mute
                source_control = self._client.source

            # get power state
            power = await power_control.get()
            if power is None:
                LOG.warning(f'Could not get power state for {self.unique_id}')
                return

            self._attr_state = MediaPlayerState.ON if power else MediaPlayerState.OFF

            # only query other state if device is on
            if power:
                # get volume
                volume = await volume_control.get()
                if volume is not None:
                    # Lyngdorf uses dB scale, convert to 0.0-1.0
                    # map -99.9dB to 0.0 and max_volume to 1.0
                    min_vol = self._model_config['min_volume'] / 10.0  # convert to dB
                    max_vol = self._model_config['max_volume'] / 10.0  # convert to dB

                    # apply zone 2 max volume limit if configured
                    if self._is_zone2 and self._zone2_max_volume is not None:
                        max_vol = min(max_vol, self._zone2_max_volume)

                    volume_range = max_vol - min_vol
                    self._attr_volume_level = (volume - min_vol) / volume_range

                # get mute state
                mute = await mute_control.get()
                if mute is not None:
                    self._attr_is_volume_muted = mute

                # get current source
                source_info = await source_control.get()
                if source_info:
                    source_id = source_info.get('source')
                    self._attr_source = self._source_id_to_name.get(source_id)

        except Exception as e:
            LOG.exception(f'Could not update {self.unique_id}: {e}')

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if source not in self._source_name_to_id:
            LOG.warning(
                f"Selected source '{source}' not valid for {self.unique_id}, ignoring! "
                f'Sources: {self._source_name_to_id}'
            )
            return

        source_id = self._source_name_to_id[source]
        source_control = self._client.zone2.source if self._is_zone2 else self._client.source
        await source_control.set(source_id)
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        power_control = self._client.zone2.power if self._is_zone2 else self._client.power
        await power_control.on()

        # set default source for zone 2 if configured
        if self._is_zone2 and self._zone2_default_source is not None:
            try:
                await self._client.zone2.source.set(int(self._zone2_default_source))
            except Exception as e:
                LOG.warning(f'Could not set Zone 2 default source: {e}')

        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        power_control = self._client.zone2.power if self._is_zone2 else self._client.power
        await power_control.off()
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) media player."""
        mute_control = self._client.zone2.mute if self._is_zone2 else self._client.mute
        if mute:
            await mute_control.on()
        else:
            await mute_control.off()
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0-1.0."""
        # Lyngdorf uses dB scale
        min_vol = self._model_config['min_volume'] / 10.0  # convert to dB
        max_vol = self._model_config['max_volume'] / 10.0  # convert to dB

        # apply zone 2 max volume limit if configured
        if self._is_zone2 and self._zone2_max_volume is not None:
            max_vol = min(max_vol, self._zone2_max_volume)

        volume_range = max_vol - min_vol
        db_volume = min_vol + (volume * volume_range)
        LOG.debug(f'Setting volume to {db_volume:.1f} dB (HA volume {volume})')

        volume_control = self._client.zone2.volume if self._is_zone2 else self._client.volume
        await volume_control.set(db_volume)
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_volume_up(self) -> None:
        """Volume up the media player."""
        volume_control = self._client.zone2.volume if self._is_zone2 else self._client.volume
        await volume_control.up()
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_volume_down(self) -> None:
        """Volume down the media player."""
        volume_control = self._client.zone2.volume if self._is_zone2 else self._client.volume
        await volume_control.down()
        self.async_schedule_update_ha_state(force_refresh=True)

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        if self.state is MediaPlayerState.OFF or self.is_volume_muted:
            return 'mdi:speaker-off'
        return 'mdi:speaker'
