from pathlib import Path

import pytest

from handbrake import HandBrake
from handbrake.models.progress import Progress

from .helpers import sample_preset, sample_video_path


def test_convert_title(tmp_path: Path):
    h = HandBrake()
    h.save_preset_to_file(tmp_path / "pytest.json", sample_preset)

    progress: list[Progress] = []
    h.convert_title(
        sample_video_path,
        tmp_path / "output.mkv",
        1,
        {
            "preset": "pytest",
            "preset_files": [tmp_path / "pytest.json"],
        },
        progress_handler=lambda p: progress.append(p),
    )
    assert len(progress) > 0
    assert progress[-1].state == "WORKDONE"


@pytest.mark.asyncio
async def test_convert_title_async(tmp_path: Path):
    h = HandBrake()
    h.save_preset_to_file(tmp_path / "pytest.json", sample_preset)

    progress: list[Progress] = []
    await h.convert_title_async(
        sample_video_path,
        tmp_path / "output.mkv",
        1,
        {
            "preset": "pytest",
            "preset_files": [tmp_path / "pytest.json"],
        },
        progress_handler=lambda p: progress.append(p),
    )
    assert len(progress) > 0
    assert progress[-1].state == "WORKDONE"
