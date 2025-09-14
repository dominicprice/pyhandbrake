import pytest

from handbrake import HandBrake


def test_version():
    h = HandBrake()
    v = h.version()
    assert v.arch != ""
    assert v.name != ""
    assert v.repo_date != ""
    assert v.repo_hash != ""
    assert v.system != ""
    assert v.type != ""
    assert v.version_string != ""


@pytest.mark.asyncio
async def test_version_async():
    h = HandBrake()
    v = await h.version_async()
    assert v.arch != ""
    assert v.name != ""
    assert v.repo_date != ""
    assert v.repo_hash != ""
    assert v.system != ""
    assert v.type != ""
    assert v.version_string != ""
