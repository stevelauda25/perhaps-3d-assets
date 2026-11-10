"""Measure the Orient FAC0000CA0 (Bambino Version 3) front photo into mm (RA-AK0705R10B trace code, these constants).

    python3 -B -m pipeline.orient_fac0000ca0_trace [out.json] [overlay.png]   # default config/watches/orient-fac0000ca0-trace.json

2000 x 2000 WatchNation photo (TAC0000CA0: same watch), straight-on; the domed crystal throws a glare arc over the top of the dial.
Anchor: the case's horizontal width (1121 px, rows away from the crown) = 40.5 mm (Orient USA); the strap between the lugs
(21 mm listed) is the check. Hands, rings, lugs, strap and crown: MANUAL_PX from gridded crops. Applied batons and the ORIENT
letters: bright (silver) blobs, the hands left out; the minute track is printed at the dial's rim.
"""
import json
import sys
from pathlib import Path

from pipeline.orient_ra_ak0705r10b_trace import ROOT, trace

FRONT = ROOT / "references/orient-fac0000ca0/front_2000x2000.jpg"
OUT = ROOT / "config/watches/orient-fac0000ca0-trace.json"
CASE_MM = 40.5  # Orient USA: 40.5 mm without crown

MANUAL_PX = {
    "hand_pivot": [966, 1005],
    "case_circle": [967.5, 999.0, 560.5],  # x 407 / 1528 at y 1000; widths symmetric about y 999
    "rings_centre": [966, 1003],
    "crystal_open_r": 504, "dial_edge_r": 474,
    # rectangular (Bauhaus) hour and minute with square ends, seconds needle with a straight tail
    "hands": {
        "hour": {"tip": [757, 862], "length": 253, "stations": [[0, 12.5], [240, 12.5], [250, 12]], "tail": [[8, 10], [14, 0]]},
        "minute": {"tip": [1256, 786], "length": 370, "stations": [[0, 12], [355, 12.5], [366, 12]], "tail": [[8, 10], [14, 0]]},
        "seconds": {"tip": [713.5, 1299.6], "length": 388, "stations": [[0, 3.5], [40, 2.5], [200, 2.2], [360, 2], [385, 1.5]],
                    "tail": [[20, 4], [95, 4]]},
    },
    "rim_px": 0,
    "hub": {"black_r": 26, "pin_r": 5},
    "subhands": {},
    "numeral_r": [290, 468], "numeral_bright": [31, 60, 255], "numeral_min_area": 250, "numeral_rect": True,
    "exclude_circles": [[730, 637, 22]],  # glare speck by the 11 o'clock baton
    "logo_box": [[878, 818], [1056, 858]], "logo_white": 175,
    "date_box": [[1170, 950], [1300, 1060]],
    "lugs": {"tl": {"tip_y": 370, "inner_x": 668}, "tr": {"tip_y": 370, "inner_x": 1262},
             "bl": {"tip_y": 1625, "inner_x": 672}, "br": {"tip_y": 1625, "inner_x": 1262}},
    "strap": {"top": {"x": [680, 1248], "case_y": 439}, "bottom": {"x": [688, 1252], "case_y": 1559}},
    "crown": {"y_top_bottom": [938, 1068], "x_from_to": [1516, 1588], "teeth": 20},
}
ARTEFACTS = ["minute track, crest, Automatic, Water Resistant, date window and the crystal's glare stay in the photo map (flat)",
             "hands and batons are polished steel (silver in the photo)",
             "the buckle is not modelled"]

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(FRONT, Path(sys.argv[2]) if len(sys.argv) > 2 else None, MANUAL_PX, CASE_MM, ARTEFACTS)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_centre_mm", "crystal_open_mm", "dial_edge_mm", "strap_mm", "checks", "crown")},
                     default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, "numerals", len(data["numerals"]), "logo", len(data["logo"]))
    print("lug", {k: v for k, v in data["lug_mean"].items() if k != "outer_offset_by_depth"}, data["lug_mean"]["outer_offset_by_depth"][::6])
