"""The Lyngdorf A/V integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_MODEL, DOMAIN as DOMAIN
from .coordinator import LyngdorfCoordinator
from .utils import get_connection_overrides

LOG = logging.getLogger(__name__)

PLATFORMS = [
    Platform.MEDIA_PLAYER,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SENSOR,
]


@dataclass
class LyngdorfData:
    """Runtime data for Lyngdorf integration."""

    client: Any  # LyngdorfAsync client
    config: dict[str, Any]
    coordinator: LyngdorfCoordinator


type LyngdorfConfigEntry = ConfigEntry[LyngdorfData]


async def async_setup_entry(hass: HomeAssistant, entry: LyngdorfConfigEntry) -> bool:
    """Set up Lyngdorf from a config entry."""
    config = entry.data
    url = config.get('url', '')
    model_id = config[CONF_MODEL]

    try:
        from .pylyngdorf import async_get_lyngdorf

        client = await async_get_lyngdorf(
            model_id, url, hass.loop, **get_connection_overrides(config)
        )
    except Exception as e:
        raise ConfigEntryNotReady(f'Connection failed to {model_id} @ {url}') from e

    # create coordinator for state management
    coordinator = LyngdorfCoordinator(hass, client, model_id)

    # perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # store runtime data
    entry.runtime_data = LyngdorfData(
        client=client,
        config=config,
        coordinator=coordinator,
    )

    # register listener to handle config options changes
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: LyngdorfConfigEntry) -> None:
    """Handle options update."""
    LOG.info(f'Reloading integration after reconfiguration: {entry.entry_id}')
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: LyngdorfConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
