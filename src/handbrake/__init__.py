import os
import shutil
import subprocess
from contextlib import ExitStack

from handbrake.canceller import Canceller
from handbrake.models.preset import Preset, PresetGroup, PresetInfo
from handbrake.models.progress import Progress
from handbrake.models.title import TitleSet
from handbrake.models.version import Version
from handbrake.opts import ConvertOpts, ScanOpts
from handbrake.progresshandler import ProgressHandler
from handbrake.runner import (
    ConvertCommandRunner,
    PresetCommandRunner,
    ScanCommandRunner,
    VersionCommandRunner,
)


class HandBrake:
    def __init__(self, executable: str | None = None):
        """Initialise the HandBrake wrapper

        :param executable: path to the HandBrakeCLI executable to use
        """
        if executable is not None:
            self.executable = executable
        elif e := os.getenv("HANDBRAKECLI"):
            self.executable = e
        elif w := shutil.which("HandBrakeCLI"):
            self.executable = w
        elif w := shutil.which("handbrakecli"):
            self.executable = w
        else:
            raise FileNotFoundError("could not find HandBrakeCLI")

    def version(self) -> Version:
        """Returns the version of HandBrakeCLI

        :returns: an object holding the handbrake version
        """
        version: Version | None = None
        runner = VersionCommandRunner()
        args = ["--json", "--version"]
        for obj in runner.process(self.executable, *args):
            if isinstance(obj, Version):
                version = obj

        if version is None:
            raise RuntimeError("version not found")
        return version

    async def version_async(self, cancel: Canceller | None = None) -> Version:
        """Returns the version of HandBrakeCLI

        :returns: an object holding the handbrake version
        """
        version: Version | None = None
        runner = VersionCommandRunner()
        args = ["--json", "--version"]
        async for obj in runner.aprocess(self.executable, *args, cancel=cancel):
            if isinstance(obj, Version):
                version = obj

        if version is None:
            raise RuntimeError("version not found")
        return version

    def convert_title(
        self,
        opts: ConvertOpts,
        progress_handler: ProgressHandler | None = None,
    ):
        """Convert a title from the input source

        :param opts: conversion options
        :param progress_handler: a callback function to handle progress updates
        """
        with ExitStack() as stack:
            args = opts.generate_cmd_args(stack)
            runner = ConvertCommandRunner()
            for obj in runner.process(self.executable, *args):
                if isinstance(obj, Progress):
                    if progress_handler is not None:
                        progress_handler(obj)

    async def convert_title_async(
        self,
        opts: ConvertOpts,
        progress_handler: ProgressHandler | None = None,
        cancel: Canceller | None = None,
    ):
        """Convert a title from the input source

        :param opts: conversion options
        :param progress_handler: a callback function to handle progress updates
        """
        with ExitStack() as stack:
            args = opts.generate_cmd_args(stack)
            runner = ConvertCommandRunner()
            async for obj in runner.aprocess(self.executable, *args, cancel=cancel):
                if isinstance(obj, Progress):
                    if progress_handler is not None:
                        progress_handler(obj)

    def scan_titles(
        self,
        opts: ScanOpts,
        progress_handler: ProgressHandler | None = None,
    ) -> TitleSet:
        """Scans the selected title and returns information about it

        :param opts: scanning options
        :param progress_handler: a callback function to handle progress updates
        :return: a `TitleSet` containing the selected title
        """

        args = opts.generate_cmd_args()
        title_set: TitleSet | None = None
        runner = ScanCommandRunner()
        for obj in runner.process(self.executable, *args):
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

    async def scan_title_async(
        self,
        opts: ScanOpts,
        progress_handler: ProgressHandler | None = None,
        cancel: Canceller | None = None,
    ) -> TitleSet:
        """Scans the selected title and returns information about it

        :param opts: scanning options
        :param progress_handler: a callback function to handle progress updates
        :return: a `TitleSet` containing the selected title
        """

        args = opts.generate_cmd_args()
        title_set: TitleSet | None = None
        runner = ScanCommandRunner()
        async for obj in runner.aprocess(self.executable, *args, cancel=cancel):
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

    def get_preset(self, name: str) -> Preset:
        """Get the builtin preset with the given name

        :param name: the name of the preset to select
        :returns: a `Preset` object containing the selected preset
        """
        preset_list: Preset | None = None
        runner = PresetCommandRunner()
        args = [
            "--json",
            "-Z",
            name,
            "--preset-export",
            name,
        ]
        for obj in runner.process(self.executable, *args):
            if isinstance(obj, Preset):
                preset_list = obj

        if preset_list is None:
            raise RuntimeError("no preset list found")
        return preset_list

    def list_presets(self) -> list[PresetGroup]:
        """List all builtin presets

        :returns: a list of preset groups
        """
        res: list[PresetGroup] = []
        curgroup = PresetGroup(name="", presets=[])
        curpreset = PresetInfo(name="", description="")
        cmd = [self.executable, "-z"]
        proc = subprocess.run(cmd, capture_output=True, check=True)

        # the output is of the format
        # groupA/
        #     preset 1 name
        #         the description of the preset
        #     preset 2 name
        #         the second description, it can span
        #         multiple lines
        # groupB/
        #     ...
        for line in proc.stderr.decode().splitlines():
            if line.endswith("/"):
                curgroup = PresetGroup(name=line[:-1], presets=[])
                res.append(curgroup)
            elif line.startswith("        "):
                if curpreset.description == "":
                    curpreset.description = line.strip()
                else:
                    curpreset.description += " " + line.strip()
            elif line.startswith("    "):
                curpreset = PresetInfo(name=line.strip(), description="")
                curgroup.presets.append(curpreset)
        return res

    def load_preset_from_file(self, file: str | os.PathLike) -> Preset:
        """Load a handbrake preset export into a `Preset` object

        :returns: a `Preset` object from the data in the given file
        """
        with open(file) as f:
            return Preset.model_validate_json(f.read())
