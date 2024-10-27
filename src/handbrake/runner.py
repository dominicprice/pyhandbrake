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
            for processor in self.processors:
                c = processor.match_start(line)
                if c is not None:
                    self.current_processor = processor
                    self.collect = [c]
                    return
        else:
            c = self.current_processor.match_end(line)
            if c is not None:
                self.collect.append(c)
                res = self.current_processor.convert("\n".join(self.collect))
                self.current_processor = None
                self.collect = []
                return res
            self.collect.append(line)

    def process(self, cmd: list[str]) -> Generator[Any, None, None]:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stderr: list[str] = []
        return_code: int | None = None
        while return_code is None:
            if proc.stdout is not None:
                line = proc.stdout.readline().decode().rstrip()
                if line:
                    print(line)
                o = self.process_line(line)
                if o is not None:
                    yield o
            if proc.stderr is not None:
                line = proc.stderr.readline().decode().rstrip()
                if line:
                    print(line)
                    stderr.append(line)
            return_code = proc.poll()

        if return_code != 0:
            raise HandBrakeError(return_code, "\n".join(stderr))
