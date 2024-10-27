import subprocess
from contextlib import ExitStack
from os import PathLike
from tempfile import NamedTemporaryFile
from typing import Iterable, Literal

from handbrake.models import PresetList, Progress, TitleSet, Version
from handbrake.progresshandler import ProgressHandler
from handbrake.runner import CommandRunner, OutputProcessor


class HandBrake:
    def __init__(self, executable: str = "HandBrakeCLI"):
        self.executable = executable

    def version(self) -> Version:
        "Returns the version of HandBrakeCLI"
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

    def rip_title(
        self,
        input: str | PathLike,
        output: str | PathLike,
        title: int | Literal["main"],
        preset: str | None = None,
        preset_files: Iterable[str | PathLike] | None = None,
        presets: Iterable[PresetList] | None = None,
        preset_from_gui: bool = False,
        no_dvdnav: bool = False,
        progress_handler: ProgressHandler | None = None,
    ):
        if title == 0:
            raise ValueError("invalid title")

        with ExitStack() as stack:
            preset_import_files = []
            if preset_files is not None:
                preset_import_files += [str(f) for f in preset_files]
            if presets is not None:
                # generate a temporary file for each in-memory preset
                for p in presets:
                    f = NamedTemporaryFile("w")
                    stack.enter_context(f)
                    f.write(p.model_dump_json(by_alias=True))
                    f.flush()
            cmd = [
                self.executable,
                "-i",
                input,
                "-o",
                output,
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
        "Returns the selected title"
        if title == 0:
            raise ValueError(
                "title must be greater than 0, use scan_all_titles to select all titles"
            )
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
        cmd = [self.executable, "--json", "-i", input, "--scan"]
        if title == "main":
            cmd += ["--main-feature"]
        else:
            cmd += ["-t", str(title)]
        for obj in runner.process(cmd):
            if isinstance(obj, Progress):
                if progress_handler is not None:
                    progress_handler(obj)
            elif isinstance(obj, TitleSet):
                title_set = obj

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
        "Returns all titles"
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
        cmd = [self.executable, "--json", "-i", input, "--scan", "-t", "0"]
        for obj in runner.process(cmd):
            if isinstance(obj, Progress):
                if progress_handler is not None:
                    progress_handler(obj)
            elif isinstance(obj, TitleSet):
                title_set = obj

        if title_set is None:
            raise RuntimeError("no titles found")
        return title_set

    def get_preset(self, name: str, strict: bool = False) -> PresetList:
        "Returns the named preset"
        preset_list_processor = OutputProcessor(
            ("{", "{"),
            ("}", "}"),
            lambda d: PresetList.model_validate_json(d, strict=strict),
        )
        preset_list: PresetList | None = None
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
            if isinstance(obj, PresetList):
                preset_list = obj

        if preset_list is None:
            raise RuntimeError("no preset list found")
        return preset_list

    def get_default_preset(self) -> PresetList:
        return self.get_preset("CLI Default")

    def list_presets(self) -> dict[str, dict[str, str]]:
        """
        Returns a dictionary of preset groups, each group is a dictionary mapping
        the preset name to its description
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

    def load_preset_from_file(self, file: str | PathLike) -> PresetList:
        with open(file) as f:
            return PresetList.model_validate_json(f.read())
