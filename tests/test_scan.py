from datetime import timedelta

import pytest

from handbrake import HandBrake

from .helpers import sample_video_path


def test_scan_all_titles():
    h = HandBrake()
    titles = h.scan_titles(sample_video_path, "all")
    assert len(titles.title_list) == 1
    title = titles.title_list[0]
    assert title.duration.to_timedelta() == timedelta(seconds=16)
    assert title.video_codec == "h264"
    assert title.geometry.width == 480
    assert title.geometry.height == 360


@pytest.mark.asyncio
async def test_scan_all_titles_async():
    h = HandBrake()
    titles = await h.scan_titles_async(sample_video_path, "all")
    assert len(titles.title_list) == 1
    title = titles.title_list[0]
    assert title.duration.to_timedelta() == timedelta(seconds=16)
    assert title.video_codec == "h264"
    assert title.geometry.width == 480
    assert title.geometry.height == 360
