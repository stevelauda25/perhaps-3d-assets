"""Measure the Orient RA-AC0E04L10B front photo into mm (RA-AK0705R10B trace code, these constants).

    python3 -B -m pipeline.orient_ra_ac0e04l10b_trace [out.json] [overlay.png]   # default config/watches/orient-ra-ac0e04l10b-trace.json

1600 x 1067 Orient USA photo (transparent background flattened onto white), straight-on but seen a little from below: the case's
lower flank shows and the lug tips at 12 are nearer the pivot than at 6. Anchor: the case's horizontal width (648 px, rows away
from the crown) = 40.0 mm (listing); the strap between the lugs (20 mm listed) is the check. The navy dial is round (ellipse fit
1.4 % out) about a point 0.3 mm below the pivot: rings_centre. Hands, rings, lugs, strap and crown: MANUAL_PX from gridded
crops. Applied batons and the ORIENT letters: bright (silver) blobs, the hands left out; the minute track is printed on the rehaut.
"""
import json
import sys
from pathlib import Path

from pipeline.orient_ra_ak0705r10b_trace import ROOT, trace

FRONT = ROOT / "references/orient-ra-ac0e04l10b/front_1600x1067.png"
OUT = ROOT / "config/watches/orient-ra-ac0e04l10b-trace.json"
CASE_MM = 40.0  # orient-watch.com: 40.0 mm wide

MANUAL_PX = {
    "hand_pivot": [776, 459],
    "case_circle": [778.0, 474.0, 324.0],  # x 454 / 1102 at y 450-490; centre y from the top (152) and bottom (795) edges on the centre line
    "rings_centre": [776.4, 464.0],  # navy dial ellipse fit
    "crystal_open_r": 291, "dial_edge_r": 274,
    "hands": {
        "hour": {"tip": [643, 368], "length": 158, "stations": [[0, 9], [18, 8.5], [40, 8], [60, 7.5], [90, 6.5], [120, 5.5], [138, 4.5],
                                                               [148, 3], [154, 1.5]],
                 "tail": [[10, 6], [18, 0]]},
        "minute": {"tip": [967, 306], "length": 241, "stations": [[0, 7.5], [30, 6.5], [60, 6], [100, 5.5], [150, 4.5], [200, 3.5],
                                                                  [225, 3], [235, 1.5]],
                   "tail": [[10, 6], [20, 0]]},
        "seconds": {"tip": [628.6, 654.7], "length": 245, "stations": [[0, 3], [40, 2], [150, 1.5], [240, 1]],
                    "tail": [[15, 4.5], [50, 4.5]], "tail_round": 4.5},
    },
    "rim_px": 0,
    "hub": {"black_r": 16, "pin_r": 4},
    "subhands": {},
    "numeral_r": [150, 262], "numeral_bright": [25, 45, 60], "numeral_min_area": 120,
    "logo_box": [[724, 336], [830, 360]], "logo_white": 175,
    "date_box": [[918, 430], [984, 490]],
    # lug tip row and inner (strap side) x; outer edge from the silhouette
    "lugs": {"tl": {"tip_y": 118, "inner_x": 617}, "tr": {"tip_y": 118, "inner_x": 945},
             "bl": {"tip_y": 852, "inner_x": 617}, "br": {"tip_y": 852, "inner_x": 948}},
    "strap": {"top": {"x": [617, 945], "case_y": 152}, "bottom": {"x": [617, 948], "case_y": 795}},
    "crown": {"y_top_bottom": [432, 520], "x_from_to": [1092, 1145], "teeth": 20},
}
ARTEFACTS = ["minute track (on the rehaut), crest, Automatic, date window and MOV'T JAPAN print stay in the photo map (flat)",
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
