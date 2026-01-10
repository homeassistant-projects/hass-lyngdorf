"""Tests for Lyngdorf config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.lyngdorf.const import CONF_MODEL, DOMAIN


async def test_user_form(hass: HomeAssistant) -> None:
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )
    assert result['type'] == FlowResultType.FORM
    assert result['step_id'] == 'user'
    assert result['errors'] == {}


async def test_user_form_success(
    hass: HomeAssistant,
    mock_config_flow_lyngdorf: AsyncMock,
    mock_lyngdorf_client: AsyncMock,
) -> None:
    """Test successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result['flow_id'],
        {
            CONF_MODEL: 'mp60',
            'url': 'socket://192.168.1.100:84',
        },
    )

    assert result['type'] == FlowResultType.CREATE_ENTRY
    assert result['title'] == 'Lyngdorf'
    assert result['data'] == {
        CONF_MODEL: 'mp60',
        'url': 'socket://192.168.1.100:84',
    }


async def test_user_form_cannot_connect(
    hass: HomeAssistant,
    mock_lyngdorf_client: AsyncMock,
) -> None:
    """Test handling connection failure."""
    mock_lyngdorf_client.device.ping.return_value = False

    with patch(
        'custom_components.lyngdorf.config_flow.async_get_lyngdorf',
        return_value=mock_lyngdorf_client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={'source': config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_MODEL: 'mp60',
                'url': 'socket://192.168.1.100:84',
            },
        )

    assert result['type'] == FlowResultType.FORM
    assert result['errors'] == {'base': 'cannot_connect'}


async def test_user_form_connection_error(
    hass: HomeAssistant,
) -> None:
    """Test handling connection error exception."""
    with patch(
        'custom_components.lyngdorf.config_flow.async_get_lyngdorf',
        side_effect=ConnectionError('Connection refused'),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={'source': config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_MODEL: 'mp60',
                'url': 'socket://192.168.1.100:84',
            },
        )

    assert result['type'] == FlowResultType.FORM
    assert result['errors'] == {'base': 'cannot_connect'}


async def test_user_form_already_configured(
    hass: HomeAssistant,
    mock_config_flow_lyngdorf: AsyncMock,
    mock_lyngdorf_client: AsyncMock,
) -> None:
    """Test we handle already configured."""
    # create first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result['flow_id'],
        {
            CONF_MODEL: 'mp60',
            'url': 'socket://192.168.1.100:84',
        },
    )

    assert result['type'] == FlowResultType.CREATE_ENTRY

    # try to create duplicate entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={'source': config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result['flow_id'],
        {
            CONF_MODEL: 'mp60',
            'url': 'socket://192.168.1.100:84',
        },
    )

    assert result['type'] == FlowResultType.ABORT
    assert result['reason'] == 'already_configured'
