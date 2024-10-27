from datetime import timedelta
from typing import Any

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_pascal


class HandBrakeModel(BaseModel):
    class Config:
        alias_generator = to_pascal
        populate_by_name = True


class VersionIdentifier(HandBrakeModel):
    major: int
    minor: int
    point: int


class Version(HandBrakeModel):
    arch: str
    name: str
    official: bool
    repo_date: str
    repo_hash: str
    system: str
    type: str
    version: VersionIdentifier
    version_string: str


class ProgressScanning(HandBrakeModel):
    preview: int
    preview_count: int
    progress: float
    sequence_id: int = Field(alias="SequenceID")
    title: int
    title_count: int


class ProgressWorking(HandBrakeModel):
    eta_seconds: int = Field(alias="ETASeconds")
    hours: int
    minutes: int
    pass_: int = Field(alias="Pass")
    pass_count: int
    pass_id: int = Field(alias="PassID")
    paused: int
    progress: float
    rate: float
    rate_avg: float
    seconds: int
    sequence_id: int = Field(alias="SequenceID")


class ProgressWorkDone(HandBrakeModel):
    error: int
    sequence_id: int = Field(alias="SequenceID")


class Progress(HandBrakeModel):
    scanning: ProgressScanning | None = None
    working: ProgressWorking | None = None
    work_done: ProgressWorkDone | None = None
    state: str

    @property
    def percent(self) -> float:
        if self.scanning is not None:
            return self.scanning.progress
        elif self.working is not None:
            return self.working.progress
        elif self.work_done is not None:
            return 100
        return 0

    @property
    def task_description(self) -> str:
        if self.state == "SCANNING":
            return "scanning title sets"
        elif self.state == "WORKING":
            return "processing title"
        elif self.state == "WORKDONE":
            return "done"
        return ""


class AudioPreset(HandBrakeModel):
    audio_bitrate: int
    audio_compression_level: float
    audio_dither_method: str
    audio_encoder: str
    audio_mixdown: str
    audio_normalize_mix_level: bool
    audio_samplerate: str
    audio_track_drc_slider: float = Field(alias="AudioTrackDRCSlider")
    audio_track_gain_slider: float
    audio_track_quality: float
    audio_track_quality_enable: bool


class Preset(HandBrakeModel):
    align_av_start: bool = Field(alias="AlignAVStart")
    audio_copy_mask: list[str]
    audio_encoder_fallback: str
    audio_language_list: list[str]
    audio_list: list[AudioPreset]
    audio_secondary_encoder_mode: bool
    audio_track_selection_behavior: str
    chapter_markers: bool
    children_array: list[str]
    default: bool
    file_format: str
    folder: bool
    folder_open: bool
    inline_parameter_sets: bool
    metadata_passthrough: bool
    mp4_ipod_compatible: bool = Field(alias="Mp4iPodCompatible")
    optimize: bool
    picture_allow_upscaling: bool
    picture_auto_crop: bool
    picture_bottom_crop: int
    picture_chroma_smooth_custom: str
    picture_chroma_smooth_preset: str
    picture_chroma_smooth_tune: str
    picture_colorspace_custom: str
    picture_colorspace_preset: str
    picture_comb_detect_custom: str
    picture_comb_detect_preset: str
    picture_crop_mode: int
    picture_dar_width: int = Field(alias="PictureDARWidth")
    picture_deblock_custom: str
    picture_deblock_preset: str
    picture_deblock_tune: str
    picture_deinterlace_custom: str
    picture_deinterlace_filter: str
    picture_deinterlace_preset: str
    picture_denoise_custom: str
    picture_denoise_filter: str
    picture_denoise_preset: str
    picture_denoise_tune: str
    picture_detelecine: str
    picture_detelecine_custom: str
    picture_force_height: int
    picture_force_width: int
    picture_height: int
    picture_itu_par: bool = Field(alias="PictureItuPAR")
    picture_keep_ratio: bool
    picture_left_crop: int
    picture_modulus: int
    picture_par: str = Field(alias="PicturePAR")
    picture_par_height: int = Field(alias="PicturePARHeight")
    picture_par_width: int = Field(alias="PicturePARWidth")
    picture_pad_bottom: int
    picture_pad_color: str
    picture_pad_left: int
    picture_pad_mode: str
    picture_pad_right: int
    picture_pad_top: int
    picture_right_crop: int
    picture_rotate: str
    picture_sharpen_custom: str
    picture_sharpen_filter: str
    picture_sharpen_preset: str
    picture_sharpen_tune: str
    picture_top_crop: int
    picture_use_maximum_size: bool
    picture_width: int
    preset_description: str
    preset_disabled: bool
    preset_name: str
    subtitle_add_cc: bool = Field(alias="SubtitleAddCC")
    subtitle_add_foreign_audio_search: bool
    subtitle_add_foreign_audio_subtitle: bool
    subtitle_burn_bd_sub: bool = Field(alias="SubtitleBurnBDSub")
    subtitle_burn_behavior: str
    subtitle_burn_dvd_sub: bool = Field(alias="SubtitleBurnDVDSub")
    subtitle_language_list: list[str]
    subtitle_track_selection_behavior: str
    type: int
    uses_picture_filters: bool
    video_avg_bitrate: int
    video_color_matrix_code_override: int
    video_encoder: str
    video_framerate: str
    video_framerate_mode: str
    video_gray_scale: bool
    video_hw_decode: int | str = Field(alias="VideoHWDecode")
    video_level: str
    video_multi_pass: bool
    video_option_extra: str
    video_preset: str
    video_profile: str
    video_qsv_decode: bool | str = Field(alias="VideoQSVDecode")
    video_quality_slider: float
    video_quality_type: int
    video_scaler: str
    video_tune: str
    video_turbo_multi_pass: bool
    x264_option: str = Field(alias="x264Option")
    x264_use_advanced_options: bool | str = Field(alias="x264UseAdvancedOptions")


class PresetList(HandBrakeModel):
    preset_list: list[Preset]
    version_major: int
    version_micro: int
    version_minor: int

    @property
    def main(self) -> Preset:
        return self.preset_list[0]


class Duration(HandBrakeModel):
    hours: int
    minutes: int
    seconds: int
    ticks: int

    def to_timedelta(self) -> timedelta:
        return timedelta(hours=self.hours, minutes=self.minutes, seconds=self.seconds)


class Fraction(HandBrakeModel):
    den: int
    num: int

    def to_float(self) -> float:
        return self.num / self.den


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
    bit_depth: int
    chroma_location: int
    chroma_subsampling: str
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
    loose_crop: tuple[int, int, int, int]
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
