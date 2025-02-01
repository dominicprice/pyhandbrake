from datetime import timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_pascal


class HandBrakeModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_pascal,
        populate_by_name=True,
    )


class Duration(HandBrakeModel):
    hours: int
    minutes: int
    seconds: int
    ticks: int

    def to_timedelta(self) -> timedelta:
        return timedelta(hours=self.hours, minutes=self.minutes, seconds=self.seconds)

    @staticmethod
    def from_timedelta(t: timedelta) -> "Duration":
        s = round(t.total_seconds())
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return Duration(hours=h, minutes=m, seconds=s, ticks=0)


class Fraction(HandBrakeModel):
    den: int
    num: int

    def to_float(self) -> float:
        return self.num / self.den


class Offset(HandBrakeModel):
    count: int
    unit: Literal["seconds"] | Literal["frames"] | Literal["pts"]
