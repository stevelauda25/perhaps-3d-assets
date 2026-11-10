"""Measure the Orient RA-AK0704N10B front photo into mm (same case as RA-AK0705R10B: its trace code, these constants).

    python3 -B -m pipeline.orient_ra_ak0704n10b_trace [out.json] [overlay.png]   # default config/watches/orient-ra-ak0704n10b-trace.json

2000 x 2000 retailer photo, close to straight-on but seen a little from below: the case outline is 3 % shorter than wide and
its centre sits 1.1 mm below the pivot, the lug tips at 12 nearer than at 6. Anchor: the case's horizontal width (rows away from
the crown) = 40.5 mm; the strap at the lug tips (21 mm listed) is the check. The dial rings are centred on the pivot (minute
track 1 % out of round), so the dial UVs need no offset (rings_centre = pivot). Lugs: RA-AK0705R10B's (same case, straighter
photo). Hands, sub-dial hands, rings, strap and lug tip rows: MANUAL_PX from gridded crops. Applied numerals, bars and the
ORIENT letters: bright (silver) blobs, sub-dial print and the hands left out.
"""
import json
import sys
from pathlib import Path

from pipeline.orient_ra_ak0705r10b_trace import ROOT, trace

FRONT = ROOT / "references/orient-ra-ak0704n10b/front_2000x2000.jpg"
OUT = ROOT / "config/watches/orient-ra-ak0704n10b-trace.json"
CASE_MM = 40.5  # same case as RA-AK0705R10B (listing 40.5 mm without crown)

MANUAL_PX = {
    "hand_pivot": [954, 846],
    # outer edge per row: x 340 / 1582 at y 880 (rows 500-1260 symmetric about x 961, widths symmetric about y 880)
    "case_circle": [961.0, 880.0, 621.0],
    "rings_centre": [954, 846],
    "crystal_open_r": 559, "dial_edge_r": 517,
    # silver hands: [r, half width] of the bright hand along pivot -> tip, tail [r, half] toward the tail
    "hands": {
        "hour": {"tip": [721, 704], "length": 273, "stations": [[0, 14], [40, 14.5], [80, 13.5], [110, 11], [140, 9.5], [170, 8.5],
                                                               [210, 6.5], [240, 5.5], [260, 4.5], [268, 2.5]],
                 "tail": [[30, 13], [50, 11], [65, 6], [80, 0]]},
        "minute": {"tip": [1272, 603], "length": 400, "stations": [[0, 13], [60, 12], [90, 11.5], [150, 11], [200, 8.5], [250, 7.5],
                                                                   [300, 6], [340, 5.5], [370, 4.5], [390, 3.5]],
                   "tail": [[25, 13], [45, 11], [60, 5], [68, 0]]},
        "seconds": {"tip": [699, 1192], "length": 430, "stations": [[0, 4], [60, 3], [200, 2], [400, 1.5], [425, 1]],
                    "tail": [[30, 5], [125, 5]], "tail_round": 5},
    },
    "rim_px": 0,  # the bright hand is the whole hand
    "hub": {"black_r": 24, "pin_r": 5},
    "subhands": {"day": {"hub": [798, 757], "tip": [799, 672], "head_r": 12, "half": 4},
                 "h24": {"hub": [1043, 1001], "tip": [1084, 1084], "head_r": 20, "half": 5}},
    "numeral_r": [250, 430], "numeral_bright": [41, 55, 50], "numeral_min_area": 400,
    "exclude_circles": [[798, 757, 124], [1043, 1001, 144], [592, 1065, 26]],  # sub-dials and the track's "40": printed
    "logo_box": [[968, 698], [1182, 752]], "logo_white": 175,
    "date_box": [[1222, 802], [1338, 898]],
    "lugs_from": "config/watches/orient-ra-ak0705r10b-trace.json",
    "lugs": {"tl": {"tip_y": 205}, "bl": {"tip_y": 1635}},  # tip rows: where the photo's straight strap is mapped from
    "strap": {"top": {"x": [644, 1271], "case_y": 273}, "bottom": {"x": [647, 1280], "case_y": 1478}},
    "crown": {"y_top_bottom": [785, 945], "x_from_to": [1584, 1662], "teeth": 18},
}
ARTEFACTS = ["minute track, sub-dial rings and print, date window, crest and Automatic stay in the photo map (flat)",
             "hands, numerals and bars are polished steel (silver in the photo)",
             "case, lugs and crown follow RA-AK0705R10B (same case); the buckle is not modelled"]

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(FRONT, Path(sys.argv[2]) if len(sys.argv) > 2 else None, MANUAL_PX, CASE_MM, ARTEFACTS)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_centre_mm", "crystal_open_mm", "dial_edge_mm", "strap_mm", "checks")},
                     default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, "numerals", len(data["numerals"]), "logo", len(data["logo"]))
