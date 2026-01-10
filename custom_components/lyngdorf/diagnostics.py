"""Diagnostics support for Lyngdorf integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import LyngdorfConfigEntry
from .const import CONF_SOURCES

# keys to redact from diagnostics
TO_REDACT = {
    'url',
    'ip_address',
    'serial_port',
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: LyngdorfConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    client = entry.runtime_data.client

    # get device state as dict
    state_dict = {}
    if coordinator.data:
        state_dict = asdict(coordinator.data)

    # get model configuration (safe to include)
    model_config = {}
    if hasattr(client, '_model_config'):
        model_config = {
            k: v
            for k, v in client._model_config.items()
            if k not in ('rs232', 'ip')  # don't include connection details
        }

    # build diagnostics data
    diagnostics_data = {
        'config_entry': {
            'entry_id': entry.entry_id,
            'version': entry.version,
            'domain': entry.domain,
            'title': entry.title,
            'data': async_redact_data(dict(entry.data), TO_REDACT),
            'options': async_redact_data(dict(entry.options), TO_REDACT),
        },
        'device': {
            'model_id': coordinator.model_id,
            'model_config': model_config,
            'connected': coordinator.data.connected if coordinator.data else False,
        },
        'state': {
            'power': state_dict.get('power', {}),
            'volume_main': state_dict.get('volume_main', {}),
            'volume_zone2': state_dict.get('volume_zone2', {}),
            'source_main': state_dict.get('source_main'),
            'source_zone2': state_dict.get('source_zone2'),
            'roomperfect': state_dict.get('roomperfect'),
            'audio_mode': state_dict.get('audio_mode'),
            'trim': state_dict.get('trim'),
            'lipsync': state_dict.get('lipsync'),
            'loudness': state_dict.get('loudness'),
        },
        'coordinator': {
            'last_update_success': coordinator.last_update_success,
            'update_interval': str(coordinator.update_interval),
        },
    }

    # include custom source configuration if present (anonymize source names)
    if CONF_SOURCES in entry.options:
        sources = entry.options[CONF_SOURCES]
        diagnostics_data['config_entry']['sources_configured'] = len(sources)
    elif CONF_SOURCES in entry.data:
        sources = entry.data[CONF_SOURCES]
        diagnostics_data['config_entry']['sources_configured'] = len(sources)

    return diagnostics_data
