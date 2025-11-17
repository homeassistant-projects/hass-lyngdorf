"""Constants for the Lyngdorf integration"""

from __future__ import annotations

from typing import Final

# import from local pylyngdorf package
import sys
from pathlib import Path

# add pylyngdorf to path if not already there
pylyngdorf_path = Path(__file__).parent.parent.parent / 'pylyngdorf'
if str(pylyngdorf_path) not in sys.path:
    sys.path.insert(0, str(pylyngdorf_path))

from pylyngdorf.models import SUPPORTED_MODELS as LYNGDORF_MODELS, DEFAULT_IP_PORT

DOMAIN: Final[str] = 'lyngdorf'

DEFAULT_URL: Final = f'socket://lyngdorf.local:{DEFAULT_IP_PORT}'

CONF_URL: Final = 'url'
CONF_BAUD_RATE: Final = 'baudrate'
CONF_MODEL: Final = 'model_id'
CONF_SOURCES: Final = 'sources'

# supported lyngdorf models
COMPATIBLE_MODELS: list[str] = LYNGDORF_MODELS
