import asyncio
from typing import AsyncIterator, Iterator, TypeVar

T = TypeVar("T")


def async_iterable_to_sync_iterable(iterator: AsyncIterator[T]) -> Iterator[T]:
    with asyncio.Runner() as runner:
        try:
            while True:
                result = runner.run(anext(iterator))  # type: ignore
                yield result
        except StopAsyncIteration:
            pass
