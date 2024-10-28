from typing import Any

from handbrake.models.common import HandBrakeModel


class Preset(HandBrakeModel):
    version_major: int
    version_micro: int
    version_minor: int

    preset_list: list[dict[str, Any]]

    @property
    def version_string(self) -> str:
        return f"{self.version_major}.{self.version_minor}.{self.version_micro}"
