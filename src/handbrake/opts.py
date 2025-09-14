import os
from contextlib import ExitStack
from tempfile import NamedTemporaryFile
from typing import Iterable, Literal, TypedDict

from handbrake.models.common import Offset
from handbrake.models.preset import Preset

AudioSelection = Literal["all", "first", "none"]
SubtitleSelection = Literal["all", "first", "scan", "none"]


class ConvertOpts(TypedDict, total=False):
    chapters: int | tuple[int, int]
    angle: int
    previews: tuple[int, bool]
    start_at_preview: int
    start_at: Offset
    stop_at: Offset
    audio: int | Iterable[int] | AudioSelection
    subtitles: int | Iterable[int] | SubtitleSelection
    preset: str
    preset_files: Iterable[str | os.PathLike]
    presets: Iterable[Preset]
    preset_from_gui: bool
    no_dvdnav: bool


def generate_convert_args(
    stack: ExitStack,
    input: str | os.PathLike,
    output: str | os.PathLike,
    title: int | Literal["main"],
    opts: ConvertOpts | None,
) -> list[str]:
    if title == 0:
        raise ValueError("invalid title")

    # generate base args
    args: list[str] = [
        "--json",
        "-i",
        str(input),
        "-o",
        str(output),
    ]
    if title == "main":
        args += ["--main-feature"]
    else:
        args += ["-t", str(title)]

    # generate opts
    if opts is not None:
        # generate list of preset import files
        preset_import_files: list[str] = []
        if preset_files := opts.get("preset_files"):
            preset_import_files += [str(f) for f in preset_files]

        # generate a temporary file for each in-memory preset
        if opts.get("presets") is not None:
            for p in opts.get("presets", []):
                f = NamedTemporaryFile("w")
                stack.enter_context(f)
                f.write(p.model_dump_json(by_alias=True))
                f.flush()
                preset_import_files.append(f.name)

        # preset args
        if len(preset_import_files) > 0:
            args += [
                "--preset-import-file",
                " ".join(preset_import_files),
            ]
        if preset := opts.get("preset"):
            args += ["--preset", preset]
        if opts.get("preset_from_gui"):
            args += ["--preset-import-gui"]

        # dvdnav arg
        if opts.get("no_dvdnav"):
            args += ["--no-dvdnav"]

        # chapters arg
        if (chapters := opts.get("chapters")) is not None:
            if isinstance(chapters, tuple):
                args += ["-c", f"{chapters[0]}-{chapters[1]}"]
            elif isinstance(chapters, int):
                args += ["-c", str(chapters)]

        # angle arg
        if (angle := opts.get("angle")) is not None:
            args += ["--angle", str(angle)]

        # preview args
        if previews := opts.get("previews"):
            args += [
                "--previews",
                f"{previews[0]}:{int(previews[1])}",
            ]
        if opts.get("start_at_preview") is not None:
            args += ["--start-at-preview", str(opts.get("start_at_preview"))]

        # start/stop args
        if start_at := opts.get("start_at"):
            args += [
                "--start-at",
                f"{start_at.unit}:{start_at.count}",
            ]
        if stop_at := opts.get("stop_at"):
            args += [
                "--stop-at",
                f"{stop_at.unit}:{stop_at.count}",
            ]

        # audio args
        if (audio := opts.get("audio")) is not None:
            if isinstance(audio, int):
                args += ["--audio", str(audio)]
            elif audio == "all":
                args += ["--all-audio"]
            elif audio == "first":
                args += ["--first-audio"]
            elif audio == "none":
                args += ["--audio", "none"]
            else:
                args += ["--audio", ",".join(str(a) for a in audio)]

        # subtitle args
        if (subtitles := opts.get("subtitles")) is not None:
            if isinstance(subtitles, int):
                args += ["--subtitle", str(subtitles)]
            elif subtitles == "all":
                args += ["--all-subtitles"]
            elif subtitles == "first":
                args += ["--first-subtitle"]
            elif subtitles == "none":
                args += ["--subtitle", "none"]
            elif subtitles == "scan":
                args += ["--subtitle", "scan"]
            else:
                args += ["--subtitle", ",".join(str(s) for s in subtitles)]

    return args


def generate_scan_args(
    input: str | os.PathLike,
    title: int | Literal["main", "all"],
) -> list[str]:
    args: list[str] = ["--json", "-i", str(input), "--scan"]
    if title == "main":
        args += ["--main-feature"]
    elif title == "all":
        args += ["-t", "0"]
    else:
        args += ["-t", str(title)]

    return args
