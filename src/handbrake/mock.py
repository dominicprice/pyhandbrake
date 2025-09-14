import asyncio
import json
import os
from dataclasses import dataclass
from datetime import timedelta
from io import TextIOBase
from os import PathLike
from time import sleep
from typing import Iterable, Literal

from handbrake import HandBrake
from handbrake.canceller import Canceller
from handbrake.models.common import Duration, Fraction
from handbrake.models.preset import Preset, PresetGroup
from handbrake.models.progress import (
    Progress,
    ProgressScanning,
    ProgressWorkDone,
    ProgressWorking,
)
from handbrake.models.title import Color, Geometry, Title, TitleSet
from handbrake.models.version import Version, VersionIdentifier
from handbrake.opts import ConvertOpts
from handbrake.progresshandler import ProgressHandler


class DictJSONEncoder(json.JSONEncoder):
    def default(self, o: object):
        return o.__dict__


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
    def __init__(
        self,
        title_runtime_minutes: Iterable[int],
        touch: bool = False,
        scan_factor: float = 0.0003,
        convert_factor: float = 0.001,
    ):
        self.scan_factor = scan_factor
        self.convert_factor = convert_factor
        self.titles = [
            MockTitle(i, timedelta(minutes=m))
            for i, m in enumerate(title_runtime_minutes, 1)
        ]
        self.touch = touch
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

    async def version_async(self, cancel: Canceller | None = None) -> Version:
        _ = cancel
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
        input: str | os.PathLike,
        output: str | os.PathLike,
        title: int | Literal["main"],
        opts: ConvertOpts | None = None,
        progress_handler: ProgressHandler | None = None,
    ):
        if title == "main":
            t = self.titles[self.main_title]
        else:
            t = self.titles[title - 1]
        total = int(t.runtime.total_seconds())
        if self.touch:
            with open(output, "w") as f:
                d = {
                    "input": input,
                    "title": title,
                    **(opts or {}),
                }
                json.dump(d, f)
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

    async def convert_title_async(
        self,
        input: str | os.PathLike,
        output: str | os.PathLike,
        title: int | Literal["main"],
        opts: ConvertOpts | None = None,
        progress_handler: ProgressHandler | None = None,
        cancel: Canceller | None = None,
    ):
        if title == "main":
            t = self.titles[self.main_title]
        else:
            t = self.titles[title - 1]
        total = int(t.runtime.total_seconds())
        if self.touch:
            with open(output, "w") as f:
                d = {
                    "input": input,
                    "title": title,
                    **(opts or {}),
                }
                json.dump(d, f)
        for i in range(total):
            await asyncio.sleep(self.convert_factor)
            if cancel and cancel.is_cancelled():
                return
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

    def scan_titles(
        self,
        input: str | PathLike,
        title: int | Literal["main", "all"],
        progress_handler: ProgressHandler | None = None,
    ) -> TitleSet:
        _ = input
        if title == 0 or title == "all":
            main_feature = self.main_title + 1
            titles = [t for t in self.titles]
        elif title == "main":
            main_feature = self.main_title + 1
            titles = [self.titles[self.main_title]]
        else:
            main_feature = title + 1
            titles = [self.titles[title - 1]]

        partial = 0
        overall_total = sum(int(t.runtime.total_seconds()) for t in titles)
        for i, t in enumerate(titles):
            total = int(t.runtime.total_seconds())
            for p in range(total):
                sleep(self.scan_factor)
                if progress_handler is not None:
                    ps = ProgressScanning(
                        preview=0,
                        preview_count=0,
                        progress=(partial + p) / overall_total,
                        SequenceID=0,
                        title=i + 1,
                        title_count=len(self.titles),
                    )
                    progress_handler(Progress(scanning=ps, state="SCANNING"))
            partial += total

        return TitleSet(
            main_feature=main_feature,
            title_list=[t.get_title() for t in titles],
        )

    async def scan_titles_async(
        self,
        input: str | PathLike,
        title: int | Literal["main", "all"],
        progress_handler: ProgressHandler | None = None,
        cancel: Canceller | None = None,
    ) -> TitleSet:
        _ = input
        if title == 0 or title == "all":
            main_feature = self.main_title + 1
            titles = [t for t in self.titles]
        elif title == "main":
            main_feature = self.main_title + 1
            titles = [self.titles[self.main_title]]
        else:
            main_feature = title + 1
            titles = [self.titles[title - 1]]

        partial = 0
        overall_total = sum(int(t.runtime.total_seconds()) for t in titles)
        for i, t in enumerate(titles):
            total = int(t.runtime.total_seconds())
            for p in range(total):
                await asyncio.sleep(self.scan_factor)
                if cancel and cancel.is_cancelled():
                    return TitleSet(main_feature=0, title_list=[])
                if progress_handler is not None:
                    ps = ProgressScanning(
                        preview=0,
                        preview_count=0,
                        progress=(partial + p) / overall_total,
                        SequenceID=0,
                        title=i + 1,
                        title_count=len(self.titles),
                    )
                    progress_handler(Progress(scanning=ps, state="SCANNING"))
            partial += total

        return TitleSet(
            main_feature=main_feature,
            title_list=[t.get_title() for t in titles],
        )

    def get_preset(self, name: str) -> Preset:
        _ = name
        return Preset(version_major=0, version_minor=0, version_micro=0, preset_list=[])

    def list_presets(self) -> list[PresetGroup]:
        return []

    def load_preset_from_file(self, file: str | PathLike | TextIOBase) -> Preset:
        _ = file
        return Preset(version_major=0, version_minor=0, version_micro=0, preset_list=[])

    def save_preset_to_file(self, file: str | PathLike | TextIOBase, preset: Preset):
        _ = file
        _ = preset
