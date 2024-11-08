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

    def process(self, cmd: list[str]) -> Generator[Any, None, None]:
        # create process with pipes to output
        proc = subprocess.Popen(
            cmd,
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
