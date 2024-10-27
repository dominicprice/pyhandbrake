from pprint import pprint

from handbrake import HandBrake

if __name__ == "__main__":
    h = HandBrake()
    p = h.get_preset("Social 25 MB 5 Minutes 360p60")
    p.preset_list[0].preset_name = "custom"
    h.add_preset(p)
    pprint(h.list_presets())
