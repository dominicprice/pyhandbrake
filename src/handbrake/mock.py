from datetime import timedelta
from os import PathLike
from time import sleep
from typing import Iterable, Literal
from handbrake import HandBrake
from handbrake.models.common import Duration, Fraction, Offset
from handbrake.models.preset import Preset
from handbrake.models.progress import (
    Progress,
    ProgressScanning,
    ProgressWorkDone,
    ProgressWorking,
)
from handbrake.models.title import Color, Geometry, Title, TitleSet
from handbrake.models.version import Version, VersionIdentifier
from handbrake.progresshandler import ProgressHandler
from dataclasses import dataclass


@dataclass
class MockTitle:
    index: int
    runtime: timedelta

    def get_title(self) -> Title:
        return Title(
            angle_count=1,
            audio_list=[],
            chapter_list=[],
            color=Color(
                bit_depth=-1,
                chroma_location=-1,
                chroma_subsampling="",
                format=1,
                matrix=1,
                primary=1,
                range=1,
                transfer=1,
            ),
            crop=(0, 0, 0, 0),
            duration=Duration.from_timedelta(self.runtime),
            frame_rate=Fraction(num=30, den=1),
            geometry=Geometry(height=360, width=480, PAR=Fraction(num=480, den=360)),
            index=self.index,
            interlace_detected=False,
            loose_crop=(-1, -1, -1, -1),
            metadata={},
            name=f"Title {self.index}",
            path=f"mock/{self.index}",
            playlist=-1,
            subtitle_list=[],
            type=-1,
            video_codec="AV1",
        )


class MockHandBrake(HandBrake):
    def __init__(self, scan_factor: float, convert_factor: float, *titles: MockTitle):
        self.scan_factor = scan_factor
        self.convert_factor = convert_factor
        self.titles = titles
        self.main_title = max(
            range(len(self.titles)),
            key=lambda i: self.titles[i].runtime,
        )

    def version(self) -> Version:
        return Version(
            arch="Python",
            name="HandBrake (mock)",
            official=False,
            repo_date="",
            repo_hash="",
            system="Python",
            type="mock",
            version=VersionIdentifier(major=0, minor=0, point=0),
            version_string="0.0.0",
        )

    def convert_title(
        self,
        input: str | PathLike,
        output: str | PathLike,
        title: int | Literal["main"],
        chapters: int | tuple[int, int] | None = None,
        angle: int | None = None,
        previews: tuple[int, bool] | None = None,
        start_at_preview: int | None = None,
        start_at: Offset | None = None,
        stop_at: Offset | None = None,
        audio: int | Iterable[int] | Literal["all", "first", "none"] | None = None,
        subtitles: (
            int | Iterable[int] | Literal["all", "first", "scan", "none"] | None
        ) = None,
        preset: str | None = None,
        preset_files: Iterable[str | PathLike] | None = None,
        presets: Iterable[Preset] | None = None,
        preset_from_gui: bool = False,
        no_dvdnav: bool = False,
        progress_handler: ProgressHandler | None = None,
    ):
        if title == "main":
            t = self.titles[self.main_title]
        else:
            t = self.titles[title - 1]
        total = round(t.runtime.total_seconds())
        for i in range(total):
            sleep(self.convert_factor)
            if progress_handler is not None:
                pw = ProgressWorking(
                    ETASeconds=int(self.convert_factor * (total - i)),
                    hours=0,
                    minutes=i,
                    Pass=1,
                    pass_count=1,
                    PassID=1,
                    paused=0,
                    progress=i / total,
                    rate=1,
                    rate_avg=1,
                    seconds=0,
                    SequenceID=0,
                )
                progress_handler(Progress(working=pw, state="WORKING"))
        if progress_handler is not None:
            pd = ProgressWorkDone(error=0, SequenceID=0)
            progress_handler(Progress(work_done=pd, state="WORKDONE"))

    def scan_title(
        self,
        input: str | PathLike,
        title: int | Literal["main"],
        progress_handler: ProgressHandler | None = None,
    ) -> TitleSet:
        if title == 0:
            raise ValueError("title == 0, use scan_all_titles to select all titles")
        elif title == "main":
            t = self.titles[self.main_title]
            i = self.main_title
        else:
            t = self.titles[title - 1]
            i = title

        total = round(t.runtime.total_seconds())
        for i in range(total):
            sleep(self.scan_factor)
            if progress_handler is not None:
                sleep(1)
                ps = ProgressScanning(
                    preview=0,
                    preview_count=0,
                    progress=i / total,
                    SequenceID=0,
                    title=1,
                    title_count=1,
                )
                progress_handler(Progress(scanning=ps, state="SCANNING"))

        return TitleSet(main_feature=i + 1, title_list=[t.get_title()])

    def scan_all_titles(
        self,
        input: str | PathLike,
        progress_handler: ProgressHandler | None = None,
    ) -> TitleSet:
        for i, t in enumerate(self.titles):
            total = round(t.runtime.total_seconds())
            for p in range(total):
                sleep(self.scan_factor)
                if progress_handler is not None:
                    ps = ProgressScanning(
                        preview=0,
                        preview_count=0,
                        progress=p / total,
                        SequenceID=0,
                        title=i + 1,
                        title_count=len(self.titles),
                    )
                    progress_handler(Progress(scanning=ps, state="SCANNING"))

        return TitleSet(
            main_feature=self.main_title + 1,
            title_list=[t.get_title() for t in self.titles],
        )

    def get_preset(self, name: str) -> Preset:
        return Preset(version_major=0, version_minor=0, version_micro=0, preset_list=[])

    def list_presets(self) -> dict[str, dict[str, str]]:
        return {}

    def load_preset_from_file(self, file: str | PathLike) -> Preset:
        return Preset(version_major=0, version_minor=0, version_micro=0, preset_list=[])
