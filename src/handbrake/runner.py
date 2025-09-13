import asyncio
import asyncio.subprocess as asubprocess
import subprocess
from typing import Any, AsyncGenerator, Callable, Generator, Generic, TypeVar

from handbrake.errors import HandBrakeError
from handbrake.models.preset import Preset
from handbrake.models.progress import Progress
from handbrake.models.title import TitleSet
from handbrake.models.version import Version
from handbrake.canceller import Canceller

T = TypeVar("T")


class OutputProcessor(Generic[T]):
    """
    Match the beginning and end of an object in command output and
    convert it to a model
    """

    def __init__(
        self,
        start_line: tuple[bytes, bytes],
        end_line: tuple[bytes, bytes],
        converter: Callable[[bytes], T],
    ):
        self.start_line = start_line
        self.end_line = end_line
        self.converter = converter

    def match_start(self, line: bytes) -> bytes | None:
        if line == self.start_line[0]:
            return self.start_line[1]
        return None

    def match_end(self, line: bytes) -> bytes | None:
        if line == self.end_line[0]:
            return self.end_line[1]
        return None

    def convert(self, data: bytes) -> T:
        return self.converter(data)


class CommandRunner:
    def __init__(self, *processors: OutputProcessor):
        self.processors = processors
        self.current_processor: OutputProcessor | None = None
        self.collect: list[bytes] = []

    def process_line(self, line: bytes) -> Any:
        if self.current_processor is None:
            # attempt to start a processor
            for processor in self.processors:
                c = processor.match_start(line)
                if c is not None:
                    self.current_processor = processor
                    self.collect = [c]
                    return
        else:
            # attempt to end the current processor
            c = self.current_processor.match_end(line)
            if c is not None:
                self.collect.append(c)
                res = self.current_processor.convert(b"\n".join(self.collect))
                self.current_processor = None
                self.collect = []
                return res
            # append line to current collect
            self.collect.append(line)

    async def aprocess(
        self,
        cmd: str,
        *args: str,
        cancel: Canceller | None = None,
    ) -> AsyncGenerator[Any, None]:
        aproc = await asubprocess.create_subprocess_exec(
            cmd,
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        try:
            if aproc.stdout is None:
                raise ValueError

            # slurp output while running
            while True:
                if aproc.returncode is not None:
                    break
                elif cancel is not None and cancel.is_cancelled():
                    return
                try:
                    line = await asyncio.wait_for(aproc.stdout.readline(), 1)
                except asyncio.TimeoutError:
                    pass
                else:
                    o = self.process_line(line.rstrip())
                    if o is not None:
                        yield o

            # slurp the remaining output
            lines = await aproc.stdout.read()
            for line in lines.splitlines():
                o = self.process_line(line.rstrip())
                if o is not None:
                    yield o

        finally:
            aproc.kill()

    def process(self, cmd: str, *args: str) -> Generator[Any, None, None]:
        # create process with pipes to output
        proc = subprocess.Popen(
            [cmd, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if proc.stdout is None:
            raise ValueError

        # slurp stdout line-by-line
        while True:
            stdout = proc.stdout.readline().rstrip()
            if len(stdout) == 0 and proc.poll() is not None:
                break
            o = self.process_line(stdout)
            if o is not None:
                yield o

        # raise error on nonzero return code
        if proc.returncode != 0:
            raise HandBrakeError(proc.returncode)


class VersionCommandRunner(CommandRunner):
    def __init__(self):
        processor = OutputProcessor(
            (b"Version: {", b"{"),
            (b"}", b"}"),
            Version.model_validate_json,
        )
        super().__init__(processor)


class ConvertCommandRunner(CommandRunner):
    def __init__(self):
        processor = OutputProcessor(
            (b"Progress: {", b"{"),
            (b"}", b"}"),
            Progress.model_validate_json,
        )
        super().__init__(processor)


class ScanCommandRunner(CommandRunner):
    def __init__(self):
        progress_processor = OutputProcessor(
            (b"Progress: {", b"}"),
            (b"}", b"}"),
            Progress.model_validate_json,
        )
        titleset_processor = OutputProcessor(
            (b"JSON Title Set: {", b"{"),
            (b"}", b"}"),
            TitleSet.model_validate_json,
        )
        super().__init__(progress_processor, titleset_processor)


class PresetCommandRunner(CommandRunner):
    def __init__(self):
        processor = OutputProcessor(
            (b"{", b"{"),
            (b"}", b"}"),
            Preset.model_validate_json,
        )
        super().__init__(processor)
