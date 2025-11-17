"""Dataclasses for Lyngdorf device state representation."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PowerState:
    """Power state for a zone."""

    main: bool = False
    zone2: bool = False


@dataclass
class VolumeState:
    """Volume state for a zone."""

    level: float = -99.9  # dB
    muted: bool = False
    max_volume: Optional[float] = None  # dB
    default_volume: Optional[float] = None  # dB


@dataclass
class SourceInfo:
    """Source information."""

    index: int
    name: str
    offset: float = 0.0  # volume offset in dB


@dataclass
class RoomPerfectState:
    """RoomPerfect calibration state."""

    position: Optional[int] = None
    position_name: Optional[str] = None
    voicing: Optional[int] = None
    voicing_name: Optional[str] = None


@dataclass
class AudioModeState:
    """Audio processing mode state."""

    mode: Optional[int] = None
    mode_name: Optional[str] = None


@dataclass
class TrimSettings:
    """Channel trim settings in dB."""

    bass: float = 0.0
    treble: float = 0.0
    center: float = 0.0
    lfe: float = 0.0
    surrounds: float = 0.0
    height: float = 0.0


@dataclass
class AudioInfo:
    """Current audio stream information."""

    format: Optional[str] = None
    sample_rate: Optional[str] = None
    channels: Optional[str] = None
    bitrate: Optional[str] = None


@dataclass
class VideoInfo:
    """Current video stream information."""

    input: Optional[int] = None
    input_name: Optional[str] = None
    output: Optional[int] = None
    output_name: Optional[str] = None
    resolution: Optional[str] = None
    format: Optional[str] = None


@dataclass
class DeviceState:
    """Complete device state."""

    # basic controls
    power: PowerState
    volume_main: VolumeState
    volume_zone2: VolumeState
    source_main: Optional[SourceInfo] = None
    source_zone2: Optional[SourceInfo] = None

    # audio processing
    roomperfect: Optional[RoomPerfectState] = None
    audio_mode: Optional[AudioModeState] = None
    trim: Optional[TrimSettings] = None
    lipsync: int = 0  # milliseconds
    loudness: bool = False
    dts_dialog: Optional[float] = None  # dB, MP-60 only

    # stream info
    audio_info: Optional[AudioInfo] = None
    video_info: Optional[VideoInfo] = None

    # device info
    connected: bool = False
    model: Optional[str] = None
    name: Optional[str] = None
