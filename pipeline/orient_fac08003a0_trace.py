"""Measure the Orient FAC08003A0 (Bambino Version 4, 42 mm) front photo into mm (RA-AK0705R10B trace code, these constants).

    python3 -B -m pipeline.orient_fac08003a0_trace [out.json] [overlay.png]   # default config/watches/orient-fac08003a0-trace.json

1077 x 1557 Orient UK photo (AC08003A, transparent background flattened onto white), straight-on, a little from below (the lug
tips at 12 nearer the pivot than at 6). The case touches the photo's left edge. Anchor: case circle from rows symmetric about
y 680 (504 px radius) = 42.0 mm (Orient UK); the strap between the lugs (22 mm listed) is the check. Hands, rings, lugs, strap
and crown: MANUAL_PX from gridded crops. Applied rose gold batons: saturated blobs (the grey dial has none), hands left out.
"""
import json
import sys
from pathlib import Path

from pipeline.orient_ra_ak0705r10b_trace import ROOT, trace

FRONT = ROOT / "references/orient-fac08003a0/front_1077x1557.png"
OUT = ROOT / "config/watches/orient-fac08003a0-trace.json"
CASE_MM = 42.0  # Orient UK: 42.0 mm

MANUAL_PX = {
    "hand_pivot": [495, 665],
    "case_circle": [505.0, 680.0, 504.0],
    "rings_centre": [497, 668],
    "crystal_open_r": 440, "dial_edge_r": 407,
    # rose gold dauphine hour and minute with pointed tails, rose gold seconds with a red end (spec: hands.tip_material)
    "hands": {
        "hour": {"tip": [325, 547], "length": 207, "stations": [[0, 12], [30, 12.5], [60, 11.5], [100, 8.5], [140, 7], [170, 5], [195, 3],
                                                               [203, 1.5]],
                 "tail": [[25, 13], [38, 11], [50, 7], [58, 0]]},
        "minute": {"tip": [743, 473], "length": 318, "stations": [[0, 12], [30, 13], [60, 11.5], [100, 10], [150, 9], [200, 6.5], [250, 5],
                                                                  [290, 3.5], [310, 2]],
                   "tail": [[25, 10], [40, 9], [50, 7], [60, 0]]},
        "seconds": {"tip": [296, 937], "length": 337, "stations": [[0, 4], [40, 3], [150, 2.5], [300, 2.5], [330, 2]],
                    "tail": [[20, 3.5], [80, 3.5]]},
    },
    "rim_px": 0,
    "hub": {"black_r": 22, "pin_r": 5},
    "subhands": {},
    "numeral_r": [250, 412], "numeral_colour": [20, 30], "numeral_close": 9, "numeral_hull": True, "numeral_min_area": 300,
    "logo_box": [[425, 485], [580, 520]], "logo_white": 175,
    "date_box": [[696, 622], [816, 722]],
    "lugs": {"tl": {"tip_y": 118, "inner_x": 256}, "tr": {"tip_y": 118, "inner_x": 786},
             "bl": {"tip_y": 1270, "inner_x": 243}, "br": {"tip_y": 1270, "inner_x": 773}},
    "strap": {"top": {"x": [256, 786], "case_y": 176}, "bottom": {"x": [243, 773], "case_y": 1184}},
    "crown": {"y_top_bottom": [615, 745], "x_from_to": [997, 1065], "teeth": 20},
}
ARTEFACTS = ["minute track, crest, Automatic, Water Resistant, the framed date window and the movement print stay in the photo map (flat)",
             "hands and batons are polished rose gold tone; the seconds hand ends in red",
             "the buckle is not modelled"]

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(FRONT, Path(sys.argv[2]) if len(sys.argv) > 2 else None, MANUAL_PX, CASE_MM, ARTEFACTS)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_centre_mm", "crystal_open_mm", "dial_edge_mm", "strap_mm", "checks", "crown")},
                     default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, "numerals", len(data["numerals"]), "logo", len(data["logo"]))
    print("lug", {k: v for k, v in data["lug_mean"].items() if k != "outer_offset_by_depth"}, data["lug_mean"]["outer_offset_by_depth"][::6])
