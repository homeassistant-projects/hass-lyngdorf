"""Tests for Lyngdorf diagnostics."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.lyngdorf import LyngdorfConfigEntry, LyngdorfData
from custom_components.lyngdorf.const import CONF_MODEL, DOMAIN
from custom_components.lyngdorf.coordinator import LyngdorfCoordinator
from custom_components.lyngdorf.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test diagnostics output."""
    # create coordinator
    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
        update_interval=timedelta(seconds=30),
    )
    await coordinator._async_update_data()

    # create mock config entry
    entry = MagicMock(spec=LyngdorfConfigEntry)
    entry.entry_id = 'test_entry_id'
    entry.version = 1
    entry.domain = DOMAIN
    entry.title = 'Lyngdorf MP-60'
    entry.data = {
        CONF_MODEL: 'mp60',
        'url': 'socket://192.168.1.100:84',
    }
    entry.options = {}

    # create runtime data
    entry.runtime_data = LyngdorfData(
        client=mock_lyngdorf_client,
        config=entry.data,
        coordinator=coordinator,
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # verify structure
    assert 'config_entry' in diagnostics
    assert 'device' in diagnostics
    assert 'state' in diagnostics
    assert 'coordinator' in diagnostics

    # verify URL is redacted
    assert diagnostics['config_entry']['data']['url'] == '**REDACTED**'

    # verify device info
    assert diagnostics['device']['model_id'] == 'mp60'
    assert diagnostics['device']['connected'] is True

    # verify state info
    assert 'power' in diagnostics['state']
    assert 'volume_main' in diagnostics['state']


async def test_diagnostics_with_sources(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test diagnostics with custom sources configured."""
    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
        update_interval=timedelta(seconds=30),
    )
    await coordinator._async_update_data()

    entry = MagicMock(spec=LyngdorfConfigEntry)
    entry.entry_id = 'test_entry_id'
    entry.version = 1
    entry.domain = DOMAIN
    entry.title = 'Lyngdorf MP-60'
    entry.data = {
        CONF_MODEL: 'mp60',
        'url': 'socket://192.168.1.100:84',
    }
    entry.options = {
        'sources': {1: 'My TV', 3: 'Turntable'},
    }

    entry.runtime_data = LyngdorfData(
        client=mock_lyngdorf_client,
        config=entry.data,
        coordinator=coordinator,
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # verify sources count is included but not the names
    assert diagnostics['config_entry']['sources_configured'] == 2
