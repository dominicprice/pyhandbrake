from datetime import timedelta
from pathlib import Path

from handbrake import HandBrake
from handbrake.models.preset import Preset
from handbrake.opts import ConvertOpts, ScanOpts

SAMPLE_VIDEO = Path(__file__).parent / "sample.mp4"


def test_version():
    h = HandBrake()
    h.version()  # just checking no error gets thrown


def test_presets():
    h = HandBrake()
    preset_groups = h.list_presets()
    assert len(preset_groups) > 0
    for group in preset_groups:
        for info in group.presets:
            preset = h.get_preset(info.name)
            assert len(preset.preset_list) == 1
            return


def test_scan_all_titles():
    h = HandBrake()
    titles = h.scan_titles(ScanOpts(SAMPLE_VIDEO, "all"))
    assert len(titles.title_list) == 1
    title = titles.title_list[0]
    assert title.duration.to_timedelta() == timedelta(seconds=16)
    assert title.video_codec == "h264"
    assert title.geometry.width == 480
    assert title.geometry.height == 360


def test_convert_title(tmp_path: Path):
    h = HandBrake()
    p = Preset(
        preset_list=[
            {
                "AlignAVStart": False,
                "AudioCopyMask": [
                    "copy:aac",
                    "copy:ac3",
                    "copy:eac3",
                    "copy:dtshd",
                    "copy:dts",
                    "copy:mp3",
                    "copy:truehd",
                    "copy:flac",
                ],
                "AudioEncoderFallback": "av_aac",
                "AudioLanguageList": [],
                "AudioList": [
                    {
                        "AudioBitrate": 128,
                        "AudioCompressionLevel": -1.0,
                        "AudioDitherMethod": "auto",
                        "AudioEncoder": "av_aac",
                        "AudioMixdown": "dpl2",
                        "AudioNormalizeMixLevel": False,
                        "AudioSamplerate": "auto",
                        "AudioTrackDRCSlider": 0.0,
                        "AudioTrackGainSlider": 0.0,
                        "AudioTrackQuality": -1.0,
                        "AudioTrackQualityEnable": False,
                    }
                ],
                "AudioSecondaryEncoderMode": True,
                "AudioTrackSelectionBehavior": "first",
                "ChapterMarkers": True,
                "ChildrenArray": [],
                "Default": True,
                "FileFormat": "av_mp4",
                "Folder": False,
                "FolderOpen": False,
                "InlineParameterSets": False,
                "MetadataPassthrough": True,
                "Mp4iPodCompatible": False,
                "Optimize": False,
                "PictureAllowUpscaling": False,
                "PictureAutoCrop": True,
                "PictureBottomCrop": 0,
                "PictureChromaSmoothCustom": "",
                "PictureChromaSmoothPreset": "off",
                "PictureChromaSmoothTune": "none",
                "PictureColorspaceCustom": "",
                "PictureColorspacePreset": "off",
                "PictureCombDetectCustom": "",
                "PictureCombDetectPreset": "off",
                "PictureCropMode": 0,
                "PictureDARWidth": 0,
                "PictureDeblockCustom": "strength=strong:thresh=20:blocksize=8",
                "PictureDeblockPreset": "off",
                "PictureDeblockTune": "medium",
                "PictureDeinterlaceCustom": "",
                "PictureDeinterlaceFilter": "off",
                "PictureDeinterlacePreset": "default",
                "PictureDenoiseCustom": "",
                "PictureDenoiseFilter": "off",
                "PictureDenoisePreset": "medium",
                "PictureDenoiseTune": "none",
                "PictureDetelecine": "off",
                "PictureDetelecineCustom": "",
                "PictureForceHeight": 0,
                "PictureForceWidth": 0,
                "PictureHeight": 0,
                "PictureItuPAR": False,
                "PictureKeepRatio": True,
                "PictureLeftCrop": 0,
                "PictureModulus": 2,
                "PicturePAR": "auto",
                "PicturePARHeight": 720,
                "PicturePARWidth": 853,
                "PicturePadBottom": 0,
                "PicturePadColor": "black",
                "PicturePadLeft": 0,
                "PicturePadMode": "none",
                "PicturePadRight": 0,
                "PicturePadTop": 0,
                "PictureRightCrop": 0,
                "PictureRotate": "angle=0:hflip=0",
                "PictureSharpenCustom": "",
                "PictureSharpenFilter": "off",
                "PictureSharpenPreset": "medium",
                "PictureSharpenTune": "none",
                "PictureTopCrop": 0,
                "PictureUseMaximumSize": True,
                "PictureWidth": 0,
                "PresetDescription": "",
                "PresetDisabled": False,
                "PresetName": "pytest",
                "SubtitleAddCC": False,
                "SubtitleAddForeignAudioSearch": False,
                "SubtitleAddForeignAudioSubtitle": False,
                "SubtitleBurnBDSub": False,
                "SubtitleBurnBehavior": "none",
                "SubtitleBurnDVDSub": False,
                "SubtitleLanguageList": [],
                "SubtitleTrackSelectionBehavior": "none",
                "Type": 0,
                "UsesPictureFilters": True,
                "VideoAvgBitrate": 6000,
                "VideoColorMatrixCodeOverride": 0,
                "VideoEncoder": "x264",
                "VideoFramerate": "auto",
                "VideoFramerateMode": "vfr",
                "VideoGrayScale": False,
                "VideoHWDecode": 0,
                "VideoLevel": "auto",
                "VideoMultiPass": False,
                "VideoOptionExtra": "",
                "VideoPreset": "medium",
                "VideoProfile": "auto",
                "VideoQSVDecode": False,
                "VideoQualitySlider": 22.0,
                "VideoQualityType": 2,
                "VideoScaler": "swscale",
                "VideoTune": "",
                "VideoTurboMultiPass": False,
                "x264Option": "",
                "x264UseAdvancedOptions": False,
            }
        ],
        version_major=53,
        version_micro=0,
        version_minor=0,
    )
    h.convert_title(
        ConvertOpts(
            SAMPLE_VIDEO,
            tmp_path / "output.mkv",
            1,
            preset="pytest",
            presets=[p],
        )
    )
