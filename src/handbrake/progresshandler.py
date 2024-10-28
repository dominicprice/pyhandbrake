from typing import Callable

from handbrake.models.progress import Progress

ProgressHandler = Callable[[Progress], None]
