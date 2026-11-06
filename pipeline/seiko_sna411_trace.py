"""Measure the straightened SNA411P1 photo (pipeline/seiko_sna411_rectify.py) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.seiko_sna411_trace [out.json] [overlay.png]     # default config/watches/seiko-sna411p1-var-nato3-trace.json

Anchor: coin-edge bezel 42 mm across (Irsyad, 2026-11-06). mm, x right, y toward 12, origin = dial centre. The straightened
image is true only for the dial plane; parts above it are shifted left (the photo was taken from the left): the bezel insert
by 34 px, the crystal ring by 12 px, the hands by 17 px. Each ring therefore has its own centre, and the hands are measured
from their own pivot. Lugs and strap are read at 6 o'clock (the 12 o'clock end rises toward the camera). All points come
from gridded crops and fitted circles (+-3 px = +-0.07 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RECT = ROOT / "outputs/watches/seiko-sna411p1-var-nato3/front_rectified.png"
OUT = ROOT / "config/watches/seiko-sna411p1-var-nato3-trace.json"
BEZEL_MM = 42.0  # Irsyad, 2026-11-06

MANUAL_PX = {
    "dial_centre": [1150, 1640],
    "bezel_centre": [1116.3, 1634.4],  # circle fitted to the insert's outer edge
    "bezel_outer_r": 870.0,  # coin-edge silhouette against the background, 8 to 10 o'clock
    "insert_outer_r": 842.3,
    "crystal_centre": [1137.8, 1639.8],  # dark ring at the crystal edge (fitted)
    "crystal_r": 693.8,
    "teeth": 56,  # scallop period about 97 px at the 6 o'clock edge
    "lume_dot_r": [455.0, 34.0],  # ring radius (homography target), dot radius with its rim
    "subdial_r": 318.0,
    "hand_pivot": [1133, 1643],
    "hour_tip": [826, 1432],
    "minute_tip": [1523, 1310],
    "hour_half_width_px": 39,
    "minute_half_width_px": 25,
    "chrono_tip": [1132, 1112],
    "chrono_tail": {"apex_y": 1700, "base_y": 1810, "base_half_px": 44, "needle_half_px": 4, "root_half_px": 14},
    "hub_r_px": 22,
    "crown": {"angle_deg": 90.0, "r_to_px": 1064, "radius_px": 110},
    "pushers": {"angles_deg": [62.0, 118.0], "r_to_px": 1047, "radius_px": 80},
    "lug_px": {"inner_x": 1614, "outer_x": 1750, "tip_y": 2600},  # 6 o'clock right lug (left one mirrors it)
    "strap_px": {"x": [700, 1650], "rows_top": [330, 645]},  # 6 o'clock width; top-end rows for the weave atlas
}


def trace(overlay=None):
    M = MANUAL_PX
    S = M["bezel_outer_r"] / (BEZEL_MM / 2)
    cx, cy = M["dial_centre"]
    mm = lambda p, c=(cx, cy): [round((p[0] - c[0]) / S, 3), round(-(p[1] - c[1]) / S, 3)]
    px0, py0 = M["hand_pivot"]
    polar = lambda p: (round(math.hypot(p[0] - px0, p[1] - py0) / S, 3), round(math.degrees(math.atan2(p[0] - px0, py0 - p[1])) % 360, 2))
    out = {"source": str(RECT.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [cx, cy],
           "anchor": f"coin-edge bezel {BEZEL_MM} mm across (Irsyad)",
           "rings_mm": {"bezel_outer": round(M["bezel_outer_r"] / S, 3), "insert_outer": round(M["insert_outer_r"] / S, 3),
                        "crystal": round(M["crystal_r"] / S, 3)},
           "photo_centres_mm": {"bezel": mm(M["bezel_centre"]), "crystal": mm(M["crystal_centre"]), "hand_pivot": mm(M["hand_pivot"])},
           "teeth_count": M["teeth"],
           "lume_dots": {"ring_mm": round(M["lume_dot_r"][0] / S, 3), "radius_mm": round(M["lume_dot_r"][1] / S, 3),
                         "hours": [1, 2, 4, 5, 7, 8, 10, 11]},
           "subdial_ring_mm": round(M["subdial_r"] / S, 3)}
    hands = {}
    for name in ("hour", "minute"):
        L, a = polar(M[name + "_tip"])
        w = round(M[name + "_half_width_px"] / S, 3)
        neck, shoulder, point = (0.3, 1.0, 1.3) if name == "hour" else (0.25, 1.2, 1.2)
        half = [(0, -0.8), (neck, -0.8), (neck, shoulder), (w, shoulder + 1.0), (w, round(L - point, 3)), (0, L)]
        hands[name] = {"angle_deg": a, "length_mm": L, "half_width_mm": w, "half_outline_mm": half,
                       "lume": {"from_mm": round(shoulder + 1.4, 3), "to_mm": round(L - point - 0.3, 3), "half_width_mm": round(w * 0.62, 3)}}
    L, a = polar(M["chrono_tip"])
    ct = M["chrono_tail"]
    hands["chrono"] = {"angle_deg": a, "length_mm": L, "needle_half_mm": round(ct["needle_half_px"] / S, 3),
                       "root_half_mm": round(ct["root_half_px"] / S, 3), "tail_apex_mm": round((ct["apex_y"] - py0) / S, 3),
                       "tail_mm": round((ct["base_y"] - py0) / S, 3), "tail_base_half_mm": round(ct["base_half_px"] / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = round(M["hub_r_px"] / S, 3)
    out["crown"] = {"angle_deg": M["crown"]["angle_deg"], "r_to_mm": round(M["crown"]["r_to_px"] / S, 3), "radius_mm": round(M["crown"]["radius_px"] / S, 3)}
    out["pushers"] = {"angles_deg": M["pushers"]["angles_deg"], "r_to_mm": round(M["pushers"]["r_to_px"] / S, 3),
                      "radius_mm": round(M["pushers"]["radius_px"] / S, 3)}
    lp = M["lug_px"]
    out["lug_mm"] = {"inner_x": round((lp["inner_x"] - cx) / S, 3), "outer_x": round((lp["outer_x"] - cx) / S, 3), "tip_y": round((lp["tip_y"] - cy) / S, 3)}
    sx = M["strap_px"]["x"]
    out["strap_mm"] = {"half_width": round((sx[1] - sx[0]) / 2 / S, 3)}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ["straightened from a turned photo: only the dial plane is true",
                                   "subdial hands stay in the photo map (flat)", "12 o'clock lug and strap distorted by perspective: 6 o'clock values mirrored"]
    if overlay:
        im = cv2.imread(str(RECT))
        for c, r in ((M["bezel_centre"], M["bezel_outer_r"]), (M["bezel_centre"], M["insert_outer_r"]), (M["crystal_centre"], M["crystal_r"]),
                     (M["dial_centre"], M["lume_dot_r"][0])):
            cv2.circle(im, (int(c[0]), int(c[1])), int(r), (0, 0, 255), 2)
        for k in ("hour_tip", "minute_tip", "chrono_tip"):
            cv2.line(im, (px0, py0), tuple(M[k]), (0, 255, 255), 2)
        cv2.imwrite(str(overlay), im)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k not in ("manual_px", "artefacts_not_traced")}), "->", dest)
