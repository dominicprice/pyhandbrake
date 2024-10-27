from handbrake import HandBrake


def test_version():
    h = HandBrake()
    h.version()  # just checking no error gets thrown


def test_list_presets():
    h = HandBrake()
    presets = h.list_presets()
    assert len(presets) > 0


def test_get_preset():
    h = HandBrake()
    cli_default = h.get_preset("CLI Default")
    assert len(cli_default.preset_list) == 1
