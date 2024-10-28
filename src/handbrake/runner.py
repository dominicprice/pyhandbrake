import subprocess
from typing import Any, Callable, Generator, Generic, TypeVar

from handbrake.errors import HandBrakeError

T = TypeVar("T")


class OutputProcessor(Generic[T]):
    """
    Match the beginning and end of an object in command output and
    convert it to a model
    """

    def __init__(
        self,
        start_line: tuple[str, str],
        end_line: tuple[str, str],
        converter: Callable[[str], T],
    ):
        self.start_line = start_line
        self.end_line = end_line
        self.converter = converter

    def match_start(self, line: str) -> str | None:
        if line == self.start_line[0]:
            return self.start_line[1]
        return None

    def match_end(self, line: str) -> str | None:
        if line == self.end_line[0]:
            return self.end_line[1]
        return None

    def convert(self, data: str) -> T:
        return self.converter(data)


class CommandRunner:
    def __init__(self, *processors: OutputProcessor):
        self.processors = processors
        self.current_processor: OutputProcessor | None = None
        self.collect: list[str] = []

    def process_line(self, line: str) -> Any:
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
                res = self.current_processor.convert("\n".join(self.collect))
                self.current_processor = None
                self.collect = []
                return res
            # append line to current collect
            self.collect.append(line)

    def process(self, cmd: list[str]) -> Generator[Any, None, None]:
        # create process with pipes to output
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # slurp stdout line-by-line as the process is running
        while proc.poll() is None:
            if proc.stdout is not None:
                line = proc.stdout.readline().decode().rstrip()
                o = self.process_line(line)
                if o is not None:
                    yield o

        # slurp the rest of stdout
        if proc.stdout is not None:
            lines = [l.rstrip() for l in proc.stdout.read().decode().splitlines()]
            for line in lines:
                o = self.process_line(line)
                if o is not None:
                    yield o

        # raise error on nonzero return code
        if proc.returncode != 0:
            stderr = ""
            if proc.stderr is not None:
                stderr = proc.stderr.read().decode()
            raise HandBrakeError(proc.returncode, stderr)
