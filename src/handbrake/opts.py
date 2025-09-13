import os
from contextlib import ExitStack
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from typing import Iterable, Literal

from handbrake.models.common import Offset
from handbrake.models.preset import Preset

AudioSelection = Literal["all", "first", "none"]
SubtitleSelection = Literal["all", "first", "scan", "none"]


@dataclass
class ConvertOpts:
    "path to the input source"
    input: str | os.PathLike
    "path to the output file"
    output: str | os.PathLike
    "the index of the title to rip, or the literal string 'main'"
    title: int | Literal["main"]
    "the chapter, or chapter range specified as (start, stop) to convert"
    chapters: int | tuple[int, int] | None = None
    "the video angle to convert"
    angle: int | None = None
    "an (int, bool) tuple indicating the number of preview to generate and whether the previews should be stored to disk"
    previews: tuple[int, bool] | None = None
    "an index of the preview to start the conversion at"
    start_at_preview: int | None = None
    "an offset from the beginning of the media to start conversion at"
    start_at: Offset | None = None
    "an offset from the start_at parameter to stop conversion at"
    stop_at: Offset | None = None
    "select which audio track(s) to convert"
    audio: int | Iterable[int] | AudioSelection | None = None
    "select which subtitle track(s) to convert"
    subtitles: int | Iterable[int] | SubtitleSelection | None = None
    "the name of a preset to use"
    preset: str | None = None
    "a list of extra preset files to load when searching for the named preset"
    preset_files: Iterable[str | os.PathLike] | None = None
    "a list of `Preset` objects to load when searching for the named preset"
    presets: Iterable[Preset] | None = None
    "whether to import preset settings from the GUI"
    preset_from_gui: bool = False
    "switch to toggle whether to use dvdnav for reading DVDs"
    no_dvdnav: bool = False

    def generate_cmd_args(self, stack: ExitStack) -> list[str]:
        args = []

        if self.title == 0:
            raise ValueError("invalid title")

        # generate list of preset import files
        preset_import_files: list[str] = []
        if self.preset_files is not None:
            preset_import_files += [str(f) for f in self.preset_files]
        if self.presets is not None:
            # generate a temporary file for each in-memory preset
            for p in self.presets:
                f = NamedTemporaryFile("w")
                stack.enter_context(f)
                f.write(p.model_dump_json(by_alias=True))
                f.flush()
                preset_import_files.append(f.name)

        # generate args
        args: list[str] = [
            "--json",
            "-i",
            str(self.input),
            "-o",
            str(self.output),
        ]
        if len(preset_import_files) > 0:
            args += [
                "--preset-import-file",
                " ".join(preset_import_files),
            ]
        if self.preset is not None:
            args += ["--preset", self.preset]
        if self.preset_from_gui:
            args += ["--preset-import-gui"]
        if self.title == "main":
            args += ["--main-feature"]
        else:
            args += ["-t", str(self.title)]
        if self.no_dvdnav:
            args += ["--no-dvdnav"]
        if isinstance(self.chapters, tuple):
            args += ["-c", f"{self.chapters[0]}-{self.chapters[1]}"]
        elif isinstance(self.chapters, int):
            args += ["-c", str(self.chapters)]
        if self.angle is not None:
            args += ["--angle", str(self.angle)]
        if self.previews is not None:
            args += ["--previews", f"{self.previews[0]}:{int(self.previews[1])}"]
        if self.start_at_preview is not None:
            args += ["--start-at-preview", str(self.start_at_preview)]
        if self.start_at is not None:
            args += ["--start-at", f"{self.start_at.unit}:{self.start_at.count}"]
        if self.stop_at is not None:
            args += ["--stop-at", f"{self.stop_at.unit}:{self.stop_at.count}"]
        if isinstance(self.audio, int):
            args += ["--audio", str(self.audio)]
        elif self.audio == "all":
            args += ["--all-audio"]
        elif self.audio == "first":
            args += ["--first-audio"]
        elif self.audio == "none":
            args += ["--audio", "none"]
        elif self.audio is not None:
            args += ["--audio", ",".join(str(a) for a in self.audio)]
        if isinstance(self.subtitles, int):
            args += ["--subtitle", str(self.subtitles)]
        elif self.subtitles == "all":
            args += ["--all-subtitles"]
        elif self.subtitles == "first":
            args += ["--first-subtitle"]
        elif self.subtitles == "none":
            args += ["--subtitle", "none"]
        elif self.subtitles == "scan":
            args += ["--subtitle", "scan"]
        elif self.subtitles is not None:
            args += ["--subtitle", ",".join(str(s) for s in self.subtitles)]

        return args


@dataclass
class ScanOpts:
    input: str | os.PathLike
    title: int | Literal["main", "all"]

    def generate_cmd_args(self) -> list[str]:
        args: list[str] = ["--json", "-i", str(input), "--scan"]
        if self.title == "main":
            args += ["--main-feature"]
        elif self.title == "all":
            args += ["-t", "0"]
        else:
            args += ["-t", str(self.title)]

        return args
