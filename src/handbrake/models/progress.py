from pydantic import Field

from handbrake.models.common import HandBrakeModel


class ProgressScanning(HandBrakeModel):
    preview: int
    preview_count: int
    progress: float
    sequence_id: int = Field(alias="SequenceID")
    title: int
    title_count: int


class ProgressWorking(HandBrakeModel):
    eta_seconds: int = Field(alias="ETASeconds")
    hours: int
    minutes: int
    pass_: int = Field(alias="Pass")
    pass_count: int
    pass_id: int = Field(alias="PassID")
    paused: int
    progress: float
    rate: float
    rate_avg: float
    seconds: int
    sequence_id: int = Field(alias="SequenceID")


class ProgressWorkDone(HandBrakeModel):
    error: int
    sequence_id: int = Field(alias="SequenceID")


class Progress(HandBrakeModel):
    scanning: ProgressScanning | None = None
    working: ProgressWorking | None = None
    work_done: ProgressWorkDone | None = None
    state: str

    @property
    def percent(self) -> float:
        if self.scanning is not None:
            return self.scanning.progress * 100
        elif self.working is not None:
            return self.working.progress * 100
        elif self.work_done is not None:
            return 100
        return 0

    @property
    def task_description(self) -> str:
        if self.state == "SCANNING":
            return "scanning title sets"
        elif self.state == "WORKING":
            return "processing title"
        elif self.state == "WORKDONE":
            return "done"
        return ""
