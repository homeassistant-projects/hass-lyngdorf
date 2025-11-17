"""Constants for the Lyngdorf integration"""

from __future__ import annotations

from typing import Final

# import from embedded pylyngdorf package
from .pylyngdorf.models import SUPPORTED_MODELS as LYNGDORF_MODELS, DEFAULT_IP_PORT

DOMAIN: Final[str] = 'lyngdorf'

DEFAULT_URL: Final = f'socket://lyngdorf.local:{DEFAULT_IP_PORT}'

CONF_URL: Final = 'url'
CONF_BAUD_RATE: Final = 'baudrate'
CONF_MODEL: Final = 'model_id'
CONF_SOURCES: Final = 'sources'

# zone 2 configuration
CONF_ZONE2_ENABLED: Final = 'zone2_enabled'
CONF_ZONE2_DEFAULT_SOURCE: Final = 'zone2_default_source'
CONF_ZONE2_MAX_VOLUME: Final = 'zone2_max_volume'

# defaults
DEFAULT_ZONE2_ENABLED: Final = False
DEFAULT_ZONE2_MAX_VOLUME: Final = -20.0  # -20.0 dB default max for safety

# supported lyngdorf models
COMPATIBLE_MODELS: list[str] = LYNGDORF_MODELS
