"""Tests for Lyngdorf integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant


async def test_setup_entry(
    hass: HomeAssistant,
    mock_async_get_lyngdorf: AsyncMock,
    mock_lyngdorf_client: MagicMock,
    mock_config_entry_data: dict,
) -> None:
    """Test successful setup of config entry."""
    entry = MagicMock()
    entry.entry_id = 'test_entry'
    entry.data = mock_config_entry_data
    entry.options = {}
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.async_on_unload = MagicMock()

    # mock platform setup
    with patch.object(hass.config_entries, 'async_forward_entry_setups', new_callable=AsyncMock):
        from custom_components.lyngdorf import async_setup_entry

        result = await async_setup_entry(hass, entry)

    assert result is True
    assert entry.runtime_data is not None
    assert entry.runtime_data.client == mock_lyngdorf_client


async def test_setup_entry_connection_failed(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
) -> None:
    """Test setup failure when connection fails."""
    entry = MagicMock()
    entry.entry_id = 'test_entry'
    entry.data = mock_config_entry_data
    entry.options = {}

    with patch(
        'custom_components.lyngdorf.async_get_lyngdorf',
        side_effect=Exception('Connection failed'),
    ):
        from homeassistant.exceptions import ConfigEntryNotReady

        from custom_components.lyngdorf import async_setup_entry

        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


async def test_unload_entry(
    hass: HomeAssistant,
    mock_async_get_lyngdorf: AsyncMock,
    mock_lyngdorf_client: MagicMock,
    mock_config_entry_data: dict,
) -> None:
    """Test unloading config entry."""
    entry = MagicMock()
    entry.entry_id = 'test_entry'
    entry.data = mock_config_entry_data
    entry.options = {}
    entry.add_update_listener = MagicMock(return_value=MagicMock())
    entry.async_on_unload = MagicMock()

    with patch.object(hass.config_entries, 'async_forward_entry_setups', new_callable=AsyncMock):
        from custom_components.lyngdorf import async_setup_entry

        await async_setup_entry(hass, entry)

    with patch.object(
        hass.config_entries, 'async_unload_platforms', new_callable=AsyncMock
    ) as mock_unload:
        mock_unload.return_value = True
        from custom_components.lyngdorf import async_unload_entry

        result = await async_unload_entry(hass, entry)

    assert result is True
