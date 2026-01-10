"""Lyngdorf device model definitions and configurations."""

from __future__ import annotations

from typing import Any

# connection parameters
DEFAULT_BAUD_RATE = 115200
DEFAULT_TIMEOUT = 2.0
DEFAULT_IP_PORT = 84
RESPONSE_EOL = '\r'
COMMAND_EOL = '\r'

# rate limiting
MIN_TIME_BETWEEN_COMMANDS = 0.1  # 100ms between volume updates
MIN_TIME_BETWEEN_GENERAL_COMMANDS = 0.05  # 50ms for other commands

# audio input definitions (common to MP-50 and MP-60)
AUDIO_INPUTS: dict[int, str] = {
    0: 'None',
    1: 'HDMI',
    3: 'SPDIF 1 (Optical)',
    4: 'SPDIF 2 (Optical)',
    5: 'SPDIF 3 (Optical)',
    6: 'SPDIF 4 (Optical)',
    7: 'SPDIF 5 (AES/EBU)',
    8: 'SPDIF 6 (Coaxial)',
    9: 'SPDIF 7 (Coaxial)',
    10: 'SPDIF 8 (Coaxial)',
    11: 'Internal Player',
    12: 'USB',
    20: '16-Channel (AES)',  # MP-60 optional module
    21: '16-Channel 2.0 (AES)',  # MP-60 optional module
    22: '16-Channel 5.1 (AES)',  # MP-60 optional module
    23: '16-Channel 7.1 (AES)',  # MP-60 optional module
    24: 'Audio Return Channel',
}

# video input definitions (common to both models)
VIDEO_INPUTS: dict[int, str] = {
    0: 'None',
    1: 'HDMI 1',
    2: 'HDMI 2',
    3: 'HDMI 3',
    4: 'HDMI 4',
    5: 'HDMI 5',
    6: 'HDMI 6',
    7: 'HDMI 7',
    8: 'HDMI 8',
    9: 'Internal',
}

# video output definitions
VIDEO_OUTPUTS: dict[int, str] = {
    0: 'None',
    1: 'HDMI Out 1',
    2: 'HDMI Out 2',
    3: 'HDBT Out',
}

# stream types (MP-60 network player)
STREAM_TYPES: dict[int, str] = {
    0: 'None',
    1: 'vTuner',
    2: 'Spotify',
    3: 'AirPlay',
    4: 'UPnP',
    5: 'Storage',
    6: 'Roon Ready',
}

MODEL_CONFIGS: dict[str, dict[str, Any]] = {
    'mp50': {
        'name': 'MP-50',
        'description': 'Lyngdorf MP-50 Surround Sound Processor',
        'tested': False,
        'min_volume': -999,  # -99.9dB
        'max_volume': 200,  # +20.0dB
        'volume_step': 1,  # 0.1dB steps
        'supports_dts_dialog': False,
        'supports_stream_type': False,
        'supports_16ch_aes': False,
        'min_time_between_commands': MIN_TIME_BETWEEN_GENERAL_COMMANDS,
        'min_time_between_volume_commands': MIN_TIME_BETWEEN_COMMANDS,
        'rs232': {
            'baudrate': DEFAULT_BAUD_RATE,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': DEFAULT_TIMEOUT,
        },
        'ip': {
            'port': DEFAULT_IP_PORT,
        },
    },
    'mp60': {
        'name': 'MP-60',
        'description': 'Lyngdorf MP-60 Surround Sound Processor',
        'tested': False,
        'min_volume': -999,  # -99.9dB
        'max_volume': 240,  # +24.0dB
        'volume_step': 1,  # 0.1dB steps
        'supports_dts_dialog': True,
        'supports_stream_type': True,
        'supports_16ch_aes': True,  # optional module
        'min_time_between_commands': MIN_TIME_BETWEEN_GENERAL_COMMANDS,
        'min_time_between_volume_commands': MIN_TIME_BETWEEN_COMMANDS,
        'rs232': {
            'baudrate': DEFAULT_BAUD_RATE,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': DEFAULT_TIMEOUT,
        },
        'ip': {
            'port': DEFAULT_IP_PORT,
        },
    },
}

SUPPORTED_MODELS = list(MODEL_CONFIGS.keys())


def get_model_config(model_id: str) -> dict[str, Any]:
    """Get configuration for a specific model."""
    if model_id not in MODEL_CONFIGS:
        raise ValueError(f"Unsupported model '{model_id}'. Supported: {SUPPORTED_MODELS}")
    return MODEL_CONFIGS[model_id]


def db_to_protocol(db: float) -> int:
    """Convert dB value to protocol integer.

    Lyngdorf uses 0.1dB precision, so multiply by 10.
    Example: -45.5dB -> -455
    """
    return int(db * 10)


def protocol_to_db(value: int) -> float:
    """Convert protocol integer to dB value.

    Example: -455 -> -45.5dB
    """
    return value / 10.0
