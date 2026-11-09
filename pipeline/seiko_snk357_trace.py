"""Measure the Seiko 5 SNK357K1 front photo (white background, 3236 x 6276) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snk357_trace [out.json] [overlay.png]     # default config/watches/seiko-snk357k1-trace.json

Blue-dial version of the SNK361K1 (same case, indices, hands and bracelet): runs pipeline/seiko_snk361_trace.py on this photo.
Anchor: case width on the flanks = 38.0 mm (spec sheet). Hands, bracelet columns and joints are read from gridded crops of
this photo; day-date, logo, print, crown and end link are the SNK361K1 points moved to this photo (same shoot size within 1 %)
and checked on the overlay.
"""
import json
import sys
from pathlib import Path

from pipeline import seiko_snk361_trace as base

ROOT = base.ROOT
FRONT = ROOT / "references/seiko-snk357k1/front_3236x6276.png"
OUT = ROOT / "config/watches/seiko-snk357k1-trace.json"
base.CASE_MM = 38.0  # spec sheet (Irsyad, 2026-11-09); listed lug width 16 mm does not fit the photo (19.6 mm next to the case)
base.GASKET_DARK = 60  # the gasket reads lighter against the blue dial
base.MANUAL_PX = {
    "hand_pivot": [1591, 3134],
    "hour_hand_tip": [1108, 2818],
    "hour_hand_tail_end": [1735, 3228],
    "hour_hand_lume": [[1180, 2862], [1369, 2988]],
    "hour_hand_width_px": [85, 102],  # same hands as SNK361K1, same photo scale
    "minute_hand_tip": [2397, 2755],
    "minute_hand_tail_end": [1438, 3210],
    "minute_hand_lume": [[1925, 2975], [2340, 2778]],
    "minute_hand_width_px": [76, 96],
    "seconds_hand_tip": [740, 2840],
    "seconds_hand_tail_end": [1938, 3231],
    "seconds_hand_width_px": [24, 52],
    "hub_radius_px": [56, 22],
    "daydate_frame": [1939, 3025, 2516, 3225],
    "logo_seiko": [1359, 2562, 1815, 2652],
    "logo_5_shield": [1469, 2704, 1613, 2816],
    "print_automatic_21_jewels": [1399, 3529, 1805, 3653],
    "crown_box": [2800, 3600, 2940, 3796],  # re-read: knurled part x 2800-2983, y 3525-3871
    "index_width_px": [62, 154],
    "end_link_x_px": [924, 2267],
    "bracelet_row_1160": {"edges": [964, 2306], "columns": [[1345, 1517], [1528, 1727], [1739, 1911]]},  # read at y = 1300
    "bracelet_joints_y": {"outer_centre": [347, 713, 1162, 1620], "mid": [508, 953, 1417]},
}
base.ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
                  "the seconds needle reads about 3 deg bent between tip and tail (photo); the tip angle is used"]

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = base.trace(FRONT, overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    data["anchor"] = "case width on the flanks = 38.0 mm (spec sheet)"
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "checks",
                                           "bracelet_columns", "bracelet_pitch_mm", "hands")}), "->", dest)
