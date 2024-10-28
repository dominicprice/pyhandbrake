from typing import Any

from pydantic import Field

from handbrake.models.common import Duration, Fraction, HandBrakeModel


class AudioAttributes(HandBrakeModel):
    alt_commentary: bool
    commentary: bool
    default: bool
    normal: bool
    secondary: bool
    visually_impaired: bool


class Audio(HandBrakeModel):
    attributes: AudioAttributes
    bit_rate: int
    channel_count: int
    channel_layout: int
    channel_layout_name: str
    codec: int
    codec_name: str
    codec_param: int
    description: str
    lfe_count: int = Field(alias="LFECount")
    language: str
    language_code: str
    sample_rate: int
    track_number: int


class Chapter(HandBrakeModel):
    duration: Duration
    name: str


class Color(HandBrakeModel):
    bit_depth: int = -1
    chroma_location: int
    chroma_subsampling: str = ""
    format: int
    matrix: int
    primary: int
    range: int
    transfer: int


class Geometry(HandBrakeModel):
    height: int
    par: Fraction = Field(alias="PAR")
    width: int


class SubtitleAttributes(HandBrakeModel):
    four_by_three: bool = Field(alias="4By3")
    children: bool
    closed_caption: bool
    commentary: bool
    default: bool
    forced: bool
    large: bool
    letterbox: bool
    normal: bool
    pan_scan: bool
    wide: bool


class Subtitle(HandBrakeModel):
    attributes: SubtitleAttributes
    format: str
    language: str
    language_code: str
    source: int
    source_name: str
    track_number: int


class Title(HandBrakeModel):
    angle_count: int
    audio_list: list[Audio]
    chapter_list: list[Chapter]
    color: Color
    crop: tuple[int, int, int, int]
    duration: Duration
    frame_rate: Fraction
    geometry: Geometry
    index: int
    interlace_detected: bool
    loose_crop: tuple[int, int, int, int] = (-1, -1, -1, -1)
    metadata: dict[str, Any]
    name: str
    path: str
    playlist: int
    subtitle_list: list[Subtitle]
    type: int
    video_codec: str


class TitleSet(HandBrakeModel):
    main_feature: int
    title_list: list[Title]
