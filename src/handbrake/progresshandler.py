from typing import Callable

from handbrake.models import Progress

ProgressHandler = Callable[[Progress], None]
