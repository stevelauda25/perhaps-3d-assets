"""Measure the Seiko 5 SNK371K1 front photo (white background, 3096 x 6154) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snk371_trace [out.json] [overlay.png]     # default config/watches/seiko-snk371k1-trace.json

Blue-dial version of the SNK369K1 (same 37 mm case, track, hand shapes and seven-part bracelet): runs
pipeline/seiko_snk369_trace.py on this photo. Anchor: case diameter 37 mm (spec sheet) from the left flank; cross-check: the
end link between the lugs against the listed 18 mm lug width. Hands, indices, day-date, crown and bracelet columns are read
from gridded crops of this photo (MANUAL_PX, +-5 px = +-0.07 mm).
"""
import json
import sys
from pathlib import Path

import numpy as np

from pipeline import seiko_snk369_trace as base

ROOT = base.ROOT
FRONT = ROOT / "references/seiko-snk371k1/front_3096x6154.png"
OUT = ROOT / "config/watches/seiko-snk371k1-trace.json"
base.CASE_MM, base.LUG_GAP_MM = 37.0, 18.0  # spec sheet (Irsyad, 2026-11-09)
base.CASE_RS_PX = (1150, 1450)


def ring_radii(g, at):
    """Blue dial: dial edge = first bright px of the rehaut past the dial; crystal ring = outer edge of the dark gasket band."""
    ring, inner = [], []
    for a in np.arange(190, 350, 2.0):
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(990, 1110, 1.0)]
        inner.append(990 + next(i for i, v in enumerate(prof) if v > 120))
        ring.append(990 + max(i for i in range(50, 110) if prof[i] < 60))
    return float(np.median(ring)), float(np.median(inner))


base.ring_radii = ring_radii
base.MANUAL_PX = {
    "hand_pivot": [1556, 3036],
    # hour: open arrow, polished outline with lume in the head; shaft = two polished rails around a dark slot
    "hour_hand_tip": [1101, 2721],
    "hour_head_base_r_px": 337,
    "hour_head_corners": [[1328, 2772], [1230, 2915]],
    "hour_shaft_width_px": 66,
    "hour_outline_px": 20,
    # minute: polished stick, pointed tip (0.4 mm taper, spec), lume from 285 px to the tip
    "minute_hand_tip": [2262, 2473],
    "minute_hand_width_px": 62,
    "minute_lume_r_px": [285, 893],
    "minute_outline_px": 8,
    # seconds: thin yellow needle (orange toward the tip), wider yellow tail ending at the day-date frame
    "seconds_hand_tip": [664, 2914],
    "seconds_hand_tail_end": [1894, 3102],
    "seconds_hand_width_px": [10, 26],
    "hub_radius_px": [70, 50, 10],  # black ring, yellow cap, pin (the white rim outside is the hour hand collar)
    "daydate_frame": [1872, 2912, 2486, 3156],
    "crown_box": [2740, 3390, 2905, 3715],
    "index_r_px": [682, 950],
    "index_width_px": [70, 140],  # single baton, wide baton at 12
    "end_link_x_px": [914, 2221],
    # key name kept from SNK369 (read by the shared trace); this row is read at y = 5300, edges mirrored from the left about the columns' centre
    "bracelet_row_2800": {"edges": [1057, 2207], "splits": [1268, 1353, 1533, 1732, 1913, 1996]},
    "bracelet_joints_y": {"outer_centre_top": [740, 1140, 1560], "outer_centre_bottom": [5003, 5405], "mid_bottom": [4796, 5200]},
}
base.ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
                  "photo taken slightly from the crown side: right flank and right bracelet edge include the side faces, so scale and silhouette use the left side",
                  "the outer|narrow bracelet splits are faint (polished strip beside brushed link); read at +-364 px from the columns' centre"]

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = base.trace(FRONT, overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    data["anchor"] = "case diameter 37.0 mm (spec sheet) from the left flank; lug gap checked against the listed 18 mm"
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "checks",
                                           "indices", "hands", "bracelet_columns", "bracelet_pitch_mm")}), "->", dest)
