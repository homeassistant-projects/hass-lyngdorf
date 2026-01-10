"""Tests for Lyngdorf coordinator."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.lyngdorf.coordinator import LyngdorfCoordinator
from custom_components.lyngdorf.pylyngdorf.state import DeviceState


async def test_coordinator_init(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test coordinator initialization."""
    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
        update_interval=timedelta(seconds=30),
    )

    assert coordinator.client == mock_lyngdorf_client
    assert coordinator.model_id == 'mp60'
    assert coordinator.name == 'Lyngdorf mp60'
    assert isinstance(coordinator.data, DeviceState)


async def test_coordinator_update_success(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test successful coordinator update."""
    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
    )

    # perform update
    data = await coordinator._async_update_data()

    assert data.connected is True
    assert data.power.main is True
    assert data.volume_main.level == -30.0
    assert data.volume_main.muted is False
    assert data.source_main is not None
    assert data.source_main.index == 1
    assert data.source_main.name == 'HDMI'


async def test_coordinator_update_device_off(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test coordinator update when device is off."""
    mock_lyngdorf_client.power.get.return_value = False

    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
    )

    data = await coordinator._async_update_data()

    assert data.connected is True
    assert data.power.main is False
    # volume and source should not be queried when power is off
    mock_lyngdorf_client.volume.get.assert_not_called()
    mock_lyngdorf_client.source.get.assert_not_called()


async def test_coordinator_update_zone2(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test coordinator update for zone 2."""
    mock_lyngdorf_client.zone_2.power.get.return_value = True
    mock_lyngdorf_client.zone_2.volume.get.return_value = -35.0
    mock_lyngdorf_client.zone_2.mute.get.return_value = True
    mock_lyngdorf_client.zone_2.source.get.return_value = {
        'source': 3,
        'name': 'Optical 1',
    }

    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
    )

    data = await coordinator._async_update_data()

    assert data.power.zone2 is True
    assert data.volume_zone2.level == -35.0
    assert data.volume_zone2.muted is True
    assert data.source_zone2 is not None
    assert data.source_zone2.index == 3


async def test_coordinator_update_roomperfect(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test coordinator update for RoomPerfect state."""
    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
    )

    data = await coordinator._async_update_data()

    assert data.roomperfect is not None
    assert data.roomperfect.position == 1
    assert data.roomperfect.position_name == 'Focus 1'
    assert data.roomperfect.voicing == 0
    assert data.roomperfect.voicing_name == 'Neutral'


async def test_coordinator_update_trim(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test coordinator update for trim settings."""
    mock_lyngdorf_client.trim.get_bass.return_value = 2.0
    mock_lyngdorf_client.trim.get_treble.return_value = -1.5

    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
    )

    data = await coordinator._async_update_data()

    assert data.trim is not None
    assert data.trim.bass == 2.0
    assert data.trim.treble == -1.5


async def test_coordinator_update_failure(
    hass: HomeAssistant,
    mock_lyngdorf_client: MagicMock,
) -> None:
    """Test coordinator update failure."""
    mock_lyngdorf_client.power.get.side_effect = Exception('Connection lost')

    coordinator = LyngdorfCoordinator(
        hass,
        mock_lyngdorf_client,
        'mp60',
    )

    with pytest.raises(UpdateFailed, match='Error communicating with device'):
        await coordinator._async_update_data()
