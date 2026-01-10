"""Common fixtures for Lyngdorf tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.lyngdorf.const import CONF_MODEL


@pytest.fixture
def mock_config_entry_data() -> dict[str, Any]:
    """Return mock config entry data."""
    return {
        CONF_MODEL: 'mp60',
        'url': 'socket://192.168.1.100:84',
    }


@pytest.fixture
def mock_config_entry_options() -> dict[str, Any]:
    """Return mock config entry options."""
    return {}


@pytest.fixture
def mock_lyngdorf_client() -> MagicMock:
    """Create a mock Lyngdorf client."""
    client = MagicMock()

    # mock power controls
    client.power = MagicMock()
    client.power.get = AsyncMock(return_value=True)
    client.power.on = AsyncMock()
    client.power.off = AsyncMock()

    # mock volume controls
    client.volume = MagicMock()
    client.volume.get = AsyncMock(return_value=-30.0)
    client.volume.set = AsyncMock()
    client.volume.up = AsyncMock()
    client.volume.down = AsyncMock()

    # mock mute controls
    client.mute = MagicMock()
    client.mute.get = AsyncMock(return_value=False)
    client.mute.on = AsyncMock()
    client.mute.off = AsyncMock()

    # mock source controls
    client.source = MagicMock()
    client.source.get = AsyncMock(return_value={'source': 1, 'name': 'HDMI'})
    client.source.set = AsyncMock()

    # mock zone 2 controls
    client.zone_2 = MagicMock()
    client.zone_2.power = MagicMock()
    client.zone_2.power.get = AsyncMock(return_value=False)
    client.zone_2.volume = MagicMock()
    client.zone_2.volume.get = AsyncMock(return_value=-40.0)
    client.zone_2.mute = MagicMock()
    client.zone_2.mute.get = AsyncMock(return_value=False)
    client.zone_2.source = MagicMock()
    client.zone_2.source.get = AsyncMock(return_value=None)

    # mock zone2 (alternate attribute name)
    client.zone2 = client.zone_2

    # mock roomperfect controls
    client.roomperfect = MagicMock()
    client.roomperfect.get_position = AsyncMock(return_value={'position': 1, 'name': 'Focus 1'})
    client.roomperfect.get_voicing = AsyncMock(return_value={'voicing': 0, 'name': 'Neutral'})
    client.roomperfect.discover_positions = AsyncMock(return_value={1: 'Focus 1', 2: 'Focus 2'})
    client.roomperfect.discover_voicings = AsyncMock(
        return_value={0: 'Neutral', 1: 'Music', 2: 'Movie'}
    )
    client.roomperfect.set_position = AsyncMock()
    client.roomperfect.set_voicing = AsyncMock()

    # mock audio mode controls
    client.audio_mode = MagicMock()
    client.audio_mode.get = AsyncMock(return_value={'mode': 0, 'name': 'Stereo'})
    client.audio_mode.discover = AsyncMock(return_value={0: 'Stereo', 1: 'Surround', 2: 'Party'})
    client.audio_mode.set = AsyncMock()

    # mock trim controls
    client.trim = MagicMock()
    client.trim.get_bass = AsyncMock(return_value=0.0)
    client.trim.get_treble = AsyncMock(return_value=0.0)
    client.trim.get_center = AsyncMock(return_value=0.0)
    client.trim.get_lfe = AsyncMock(return_value=0.0)
    client.trim.get_surrounds = AsyncMock(return_value=0.0)
    client.trim.get_height = AsyncMock(return_value=0.0)
    client.trim.set_bass = AsyncMock()
    client.trim.set_treble = AsyncMock()
    client.trim.set_center = AsyncMock()
    client.trim.set_lfe = AsyncMock()
    client.trim.set_surrounds = AsyncMock()
    client.trim.set_height = AsyncMock()

    # mock lipsync controls
    client.lipsync = MagicMock()
    client.lipsync.get = AsyncMock(return_value=0)
    client.lipsync.get_range = AsyncMock(return_value={'min': 0, 'max': 500})
    client.lipsync.set = AsyncMock()

    # mock loudness controls
    client.loudness = MagicMock()
    client.loudness.get = AsyncMock(return_value=False)

    # mock device info
    client.device = MagicMock()
    client.device.ping = AsyncMock(return_value=True)

    # mock model config
    client._model_config = {
        'name': 'MP-60',
        'min_volume': -999,
        'max_volume': 240,
    }

    return client


@pytest.fixture
def mock_async_get_lyngdorf(
    mock_lyngdorf_client: MagicMock,
) -> Generator[AsyncMock]:
    """Mock the async_get_lyngdorf function."""
    with patch(
        'custom_components.lyngdorf.pylyngdorf.async_get_lyngdorf',
        return_value=mock_lyngdorf_client,
    ) as mock:
        yield mock


@pytest.fixture
def mock_config_flow_lyngdorf(
    mock_lyngdorf_client: MagicMock,
) -> Generator[AsyncMock]:
    """Mock async_get_lyngdorf for config flow."""
    with patch(
        'custom_components.lyngdorf.config_flow.async_get_lyngdorf',
        return_value=mock_lyngdorf_client,
    ) as mock:
        yield mock
