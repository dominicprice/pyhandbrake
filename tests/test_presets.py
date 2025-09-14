from handbrake import HandBrake


def test_presets():
    h = HandBrake()
    preset_groups = h.list_presets()
    assert len(preset_groups) > 0
    for group in preset_groups:
        for info in group.presets:
            preset = h.get_preset(info.name)
            assert len(preset.preset_list) == 1
            return
