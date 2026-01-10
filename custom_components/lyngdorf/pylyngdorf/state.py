"""Dataclasses for Lyngdorf device state representation."""

from __future__ import annotations

from dataclasses import dataclass


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
    max_volume: float | None = None  # dB
    default_volume: float | None = None  # dB


@dataclass
class SourceInfo:
    """Source information."""

    index: int
    name: str
    offset: float = 0.0  # volume offset in dB


@dataclass
class RoomPerfectState:
    """RoomPerfect calibration state."""

    position: int | None = None
    position_name: str | None = None
    voicing: int | None = None
    voicing_name: str | None = None


@dataclass
class AudioModeState:
    """Audio processing mode state."""

    mode: int | None = None
    mode_name: str | None = None


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

    format: str | None = None
    sample_rate: str | None = None
    channels: str | None = None
    bitrate: str | None = None


@dataclass
class VideoInfo:
    """Current video stream information."""

    input: int | None = None
    input_name: str | None = None
    output: int | None = None
    output_name: str | None = None
    resolution: str | None = None
    format: str | None = None


@dataclass
class DeviceState:
    """Complete device state."""

    # basic controls
    power: PowerState
    volume_main: VolumeState
    volume_zone2: VolumeState
    source_main: SourceInfo | None = None
    source_zone2: SourceInfo | None = None

    # audio processing
    roomperfect: RoomPerfectState | None = None
    audio_mode: AudioModeState | None = None
    trim: TrimSettings | None = None
    lipsync: int = 0  # milliseconds
    loudness: bool = False
    dts_dialog: float | None = None  # dB, MP-60 only

    # stream info
    audio_info: AudioInfo | None = None
    video_info: VideoInfo | None = None

    # device info
    connected: bool = False
    model: str | None = None
    name: str | None = None
