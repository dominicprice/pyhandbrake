import subprocess
from contextlib import ExitStack
from os import PathLike
from tempfile import NamedTemporaryFile
from typing import Iterable, Literal

from handbrake.models.common import Offset
from handbrake.models.preset import Preset
from handbrake.models.progress import Progress
from handbrake.models.title import TitleSet
from handbrake.models.version import Version
from handbrake.progresshandler import ProgressHandler
from handbrake.runner import CommandRunner, OutputProcessor


class HandBrake:
    def __init__(self, executable: str = "HandBrakeCLI"):
        """Initialise the HandBrake wrapper

        :param executable: path to the HandBrakeCLI executable to use
        """
        self.executable = executable

    def version(self) -> Version:
        """Returns the version of HandBrakeCLI

        :returns: an object holding the handbrake version
        """
        version_processor = OutputProcessor(
            ("Version: {", "{"),
            ("}", "}"),
            Version.model_validate_json,
        )
        version: Version | None = None
        runner = CommandRunner(version_processor)
        cmd = [self.executable, "--json", "--version"]
        for obj in runner.process(cmd):
            if isinstance(obj, Version):
                version = obj

        if version is None:
            raise RuntimeError("version not found")
        return version

    def convert_title(
        self,
        input: str | PathLike,
        output: str | PathLike,
        title: int | Literal["main"],
        chapters: int | tuple[int, int] | None = None,
        angle: int | None = None,
        previews: tuple[int, bool] | None = None,
        start_at_preview: int | None = None,
        start_at: Offset | None = None,
        stop_at: Offset | None = None,
        audio: int | Iterable[int] | Literal["all", "first", "none"] | None = None,
        subtitles: (
            int | Iterable[int] | Literal["all", "first", "scan", "none"] | None
        ) = None,
        preset: str | None = None,
        preset_files: Iterable[str | PathLike] | None = None,
        presets: Iterable[Preset] | None = None,
        preset_from_gui: bool = False,
        no_dvdnav: bool = False,
        progress_handler: ProgressHandler | None = None,
    ):
        """Convert a title from the input source

        :param input: path to the input source
        :param output: path to the output file
        :param title: the index of the title to rip, or the literal string "main"
        to automatically select the main feature
        :param chapters: the chapter, or chapter range specified as (start, stop), to convert
        :param angle: the video angle to convert
        :param previews: an (int, bool) tuple indicating the number of previews to generate
        and whether the previews should be stored to disk
        :param start_at_preview: an index of the preview to start the conversion at
        :param start_at: an offset from the beginning of the media to start conversion at
        :param stop_at: an offset from the start_at parameter to stop conversion at
        :param audio: select which audio track(s) to convert
        :param subtitles: select which subtitle track(s) to convert
        :param preset: the name of the preset to use
        :param preset_files: a list of extra preset files to load when searching for the named preset
        :param presets: a list of `Preset` objects to load when searching for the named preset
        :param preset_from_gui: whether to import preset settings from the GUI
        :param no_dvdnav: switch to toggle whether to use dvdnav for reading DVDs
        :param progress_handler: a callback function to handle progress updates
        """
        if title == 0:
            raise ValueError("invalid title")

        with ExitStack() as stack:
            # generate list of preset import files
            preset_import_files: list[str] = []
            if preset_files is not None:
                preset_import_files += [str(f) for f in preset_files]
            if presets is not None:
                # generate a temporary file for each in-memory preset
                for p in presets:
                    f = NamedTemporaryFile("w")
                    stack.enter_context(f)
                    f.write(p.model_dump_json(by_alias=True))
                    f.flush()
                    preset_import_files.append(f.name)

            # generate command
            cmd: list[str] = [
                self.executable,
                "--json",
                "-i",
                str(input),
                "-o",
                str(output),
            ]
            if len(preset_import_files) > 0:
                cmd += [
                    "--preset-import-file",
                    " ".join(preset_import_files),
                ]
            if preset is not None:
                cmd += ["--preset", preset]
            if preset_from_gui:
                cmd += ["--preset-import-gui"]
            if title == "main":
                cmd += ["--main-feature"]
            else:
                cmd += ["-t", str(title)]
            if no_dvdnav:
                cmd += ["--no-dvdnav"]
            if isinstance(chapters, tuple):
                cmd += ["-c", f"{chapters[0]}-{chapters[1]}"]
            elif isinstance(chapters, int):
                cmd += ["-c", str(chapters)]
            if angle is not None:
                cmd += ["--angle", str(angle)]
            if previews is not None:
                cmd += ["--previews", f"{previews[0]}:{int(previews[1])}"]
            if start_at_preview is not None:
                cmd += ["--start-at-preview", str(start_at_preview)]
            if start_at is not None:
                cmd += ["--start-at", f"{start_at.unit}:{start_at.count}"]
            if stop_at is not None:
                cmd += ["--stop-at", f"{stop_at.unit}:{stop_at.count}"]
            if isinstance(audio, int):
                cmd += ["--audio", str(audio)]
            elif audio == "all":
                cmd += ["--all-audio"]
            elif audio == "first":
                cmd += ["--first-audio"]
            elif audio == "none":
                cmd += ["--audio", "none"]
            elif audio is not None:
                cmd += ["--audio", ",".join(str(a) for a in audio)]
            if isinstance(subtitles, int):
                cmd += ["--subtitle", str(subtitles)]
            elif subtitles == "all":
                cmd += ["--all-subtitles"]
            elif subtitles == "first":
                cmd += ["--first-subtitle"]
            elif subtitles == "none":
                cmd += ["--subtitle", "none"]
            elif subtitles == "scan":
                cmd += ["--subtitle", "scan"]
            elif subtitles is not None:
                cmd += ["--subtitle", ",".join(str(s) for s in subtitles)]

            # run command
            progress_processor = OutputProcessor(
                ("Progress: {", "{"),
                ("}", "}"),
                Progress.model_validate_json,
            )
            runner = CommandRunner(progress_processor)
            for obj in runner.process(cmd):
                if isinstance(obj, Progress):
                    if progress_handler is not None:
                        progress_handler(obj)

    def scan_title(
        self,
        input: str | PathLike,
        title: int | Literal["main"],
        progress_handler: ProgressHandler | None = None,
    ) -> TitleSet:
        """Scans the selected title and returns information about it

        :param input: path to the input source
        :param title: the index of the title to scan, or the literal string "main"
        to automatically select the main feature
        :param progress_handler: a callback function to handle progress updates
        :return: a `TitleSet` containing the selected title
        """
        if title == 0:
            raise ValueError("title == 0, use scan_all_titles to select all titles")

        # generate command
        cmd: list[str] = [self.executable, "--json", "-i", str(input), "--scan"]
        if title == "main":
            cmd += ["--main-feature"]
        else:
            cmd += ["-t", str(title)]

        # run command
        progress_processor = OutputProcessor(
            ("Progress: {", "{"),
            ("}", "}"),
            Progress.model_validate_json,
        )
        titleset_processor = OutputProcessor(
            ("JSON Title Set: {", "{"),
            ("}", "}"),
            TitleSet.model_validate_json,
        )
        title_set: TitleSet | None = None
        runner = CommandRunner(progress_processor, titleset_processor)
        for obj in runner.process(cmd):
            if isinstance(obj, Progress):
                if progress_handler is not None:
                    progress_handler(obj)
            elif isinstance(obj, TitleSet):
                title_set = obj

        # check output
        if title_set is None:
            raise RuntimeError("no titles found")
        if len(title_set.title_list) == 0:
            raise RuntimeError("title not found")
        return title_set

    def scan_all_titles(
        self,
        input: str | PathLike,
        progress_handler: ProgressHandler | None = None,
    ) -> TitleSet:
        """Scan all titles and return information about them

        :param input: path to the input source
        :param progress_handler: a callback function to handle progress updates
        :return: a `TitleSet` containing the all titles in the input source
        """
        # generate command
        cmd: list[str] = [
            self.executable,
            "--json",
            "-i",
            str(input),
            "--scan",
            "-t",
            "0",
        ]

        # run command
        progress_output_handler = OutputProcessor(
            ("Progress: {", "{"),
            ("}", "}"),
            Progress.model_validate_json,
        )
        titleset_output_handler = OutputProcessor(
            ("JSON Title Set: {", "{"),
            ("}", "}"),
            TitleSet.model_validate_json,
        )
        title_set: TitleSet | None = None
        runner = CommandRunner(progress_output_handler, titleset_output_handler)
        for obj in runner.process(cmd):
            if isinstance(obj, Progress):
                if progress_handler is not None:
                    progress_handler(obj)
            elif isinstance(obj, TitleSet):
                title_set = obj

        # check output
        if title_set is None:
            raise RuntimeError("no titles found")
        return title_set

    def get_preset(self, name: str) -> Preset:
        """Get the builtin preset with the given name

        :param name: the name of the preset to select
        :returns: a `Preset` object containing the selected preset
        """
        preset_list_processor = OutputProcessor(
            ("{", "{"), ("}", "}"), lambda d: Preset.model_validate_json(d)
        )
        preset_list: Preset | None = None
        runner = CommandRunner(preset_list_processor)
        cmd = [
            self.executable,
            "--json",
            "-Z",
            name,
            "--preset-export",
            name,
        ]
        for obj in runner.process(cmd):
            if isinstance(obj, Preset):
                preset_list = obj

        if preset_list is None:
            raise RuntimeError("no preset list found")
        return preset_list

    def list_presets(self) -> dict[str, dict[str, str]]:
        """List all builtin presets

        :returns: a dict[group, dict[name, description]] containing all builtin presets
        """
        res: dict[str, dict[str, str]] = {}
        group: dict[str, str] = {}
        preset: str = ""
        cmd = [self.executable, "-z"]
        proc = subprocess.run(cmd, capture_output=True, check=True)
        for line in proc.stderr.decode().splitlines():
            if line.endswith("/"):
                group = {}
                res[line[:-1]] = group
            elif line.startswith("        "):
                if group[preset] == "":
                    group[preset] = line.strip()
                else:
                    group[preset] += " " + line.strip()
            elif line.startswith("    "):
                preset = line.strip()
                group[preset] = ""
        return res

    def load_preset_from_file(self, file: str | PathLike) -> Preset:
        """Load a handbrake preset export into a `Preset` object

        :returns: a `Preset` object from the data in the given file
        """
        with open(file) as f:
            return Preset.model_validate_json(f.read())
