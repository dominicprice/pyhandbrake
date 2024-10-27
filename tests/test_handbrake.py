from handbrake import HandBrake


def test_version():
    h = HandBrake()
    h.version()  # just checking no error gets thrown


def test_presets():
    h = HandBrake()
    presets = h.list_presets()
    assert len(presets) > 0
    for group in presets.values():
        for preset_name in group:
            preset = h.get_preset(preset_name)
            assert len(preset.preset_list) == 1
            return
