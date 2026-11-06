"""Measure the Seiko 5 SNZG13K1 front photo (white background, 3680 x 6400) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snzg13_trace [out.json] [overlay.png]     # default config/watches/seiko-snzg13k1-trace.json

Anchor: case width on the flanks = 42 mm (Irsyad, 2026-11-06: same case as SNZG11J1; at 43 mm the lug gap would read 22.7 mm).
mm, x right, y toward 12, origin = hand pivot. All dial print (numerals, track, logo, day-date) stays in the dial map, so only
the hands, hub, rings, crown, lugs and the three-column bracelet are measured. Hands, rings, crown, lug corners and bracelet
joints come from gridded crops (MANUAL_PX, +-5 px = +-0.07 mm); hand widths from cross profiles.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snzg13k1/front_3680x6400.png"
OUT = ROOT / "config/watches/seiko-snzg13k1-trace.json"
CASE_MM = 42.0  # Irsyad, 2026-11-06
LISTED = {"case_mm": 43.0, "lug_width_mm": 22.0, "thickness_mm": 12.0}

MANUAL_PX = {
    "hand_pivot": [1736, 3127],
    "case_left_flank_x": 184,  # at the pivot row; the right flank there is the crown
    "bezel_inner_r": 1382,  # brushed bezel ends, black gasket ring begins (radial profiles at 200-320 deg)
    "dial_edge_r": 1268,  # black ring ends, dial begins
    "hour_hand_tip": [1207, 2793],
    "minute_hand_tip": [2443, 2527],
    "seconds_hand_tip": [2632, 3401],  # end of the thin red needle
    "seconds_arrow_px": [[2294, 3298], [2422, 3337]],  # red arrowhead: wide end, point (outward); red mask 7.9 -> 9.7 mm
    "seconds_tail_end_px": [1435, 3025],  # rounded end of the paddle counterweight, under the hour hand
    "seconds_tail_width_px": 58,
    "hub_radius_px": [96, 46],  # hour hand collet, minute hand collet
    "crown_box": [3300, 2946, 3496, 3375],  # fluted crown, sits against the case flank (no neck shows)
    "lug_inner_px": {"top": [[938, 1392], [2567, 1383]], "bottom": [[925, 5008], [2575, 5008]]},  # inner corner at the tip: left, right
    "bracelet_centre_x_px": [1335, 2195],  # centre column edges
    "bracelet_outer_joints_y_px": {"top": [1355, 910], "bottom": [5031, 5512]},  # dark gap band centres, case side first
    "bracelet_centre_joints_y_px": {"top": [1410, 1000]},  # centre column gaps (thin bright line)
}
ARTEFACTS = ["bright arcs inside the black gasket ring: crystal edge reflections, not parts",
             "the bottom half is about 2 mm longer to the lug tip (watch tilted slightly): top/bottom means are used",
             "the far bracelet rows are foreshortened (the bracelet rolls away from the camera): pitch from the rows next to the lugs"]


def cross_width(g, p0, tip, f, thr, reach):
    """Lit run across the hand axis at fraction f of its length, px: (from, to) relative to the axis."""
    dx, dy = tip[0] - p0[0], tip[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    cx, cy = p0[0] + ux * L * f, p0[1] + uy * L * f
    lit = [t for t in range(-reach, reach + 1) if g[int(round(cy + ux * t)), int(round(cx - uy * t))] > thr]
    return min(lit), max(lit)


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    case_r = px0 - M["case_left_flank_x"]
    S = 2 * case_r / CASE_MM
    reach = int(1.5 * S)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (Irsyad)",
           "case": {"radius_mm": round(case_r / S, 3)},
           "crystal_ring": {"radius_mm": round(M["bezel_inner_r"] / S, 3), "basis": "inner edge of the bezel"},
           "dial_edge_radius_mm": round(M["dial_edge_r"] / S, 3)}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    lp = M["lug_inner_px"]
    tips = {k: round(float(np.mean([abs(mm(p)[1]) for p in v])), 3) for k, v in lp.items()}
    gaps = [(r[0] - l[0]) / S for l, r in lp.values()]
    out["lug_tip_mm"] = {**tips, "mean": round((tips["top"] + tips["bottom"]) / 2, 3)}
    out["lug_inner_x_mm"] = round(float(np.mean(gaps)) / 2, 3)

    # bracelet: centre column half width, outer joint pitch (next to the lugs), centre joints nearer the case by `shift`
    cx0, cx1 = M["bracelet_centre_x_px"]
    oj, cj = M["bracelet_outer_joints_y_px"], M["bracelet_centre_joints_y_px"]
    pitch = float(np.mean([abs(v[1] - v[0]) for v in oj.values()])) / S
    shift = float(np.mean([abs(a - b) for a, b in zip(oj["top"], cj["top"])])) / S
    out["bracelet"] = {"centre_half_mm": round((cx1 - cx0) / 2 / S, 3), "centre_offset_mm": round(((cx0 + cx1) / 2 - px0) / S, 3),
                       "pitch_mm": round(pitch, 3), "centre_shift_mm": round(shift, 3)}
    out["checks"] = {"lug_gap_mm": round(float(np.mean(gaps)), 2), "lug_to_lug_mm": round(tips["top"] + tips["bottom"], 2),
                     "bracelet_width_1mm_past_tip_mm": round(float(np.mean([r - l for y, l, r in prof if abs(abs(y) - tips["top" if y > 0 else "bottom"] - 1.25) < 0.13])), 2),
                     "listed": LISTED}

    # hands: sword hour/minute with a lume inlay; full width = lit run across the axis (the inlay frame is in the spec)
    hands = {}
    for name in ("hour", "minute"):
        tip = M[f"{name}_hand_tip"]
        r, ang = polar(tip)
        full = [cross_width(gray, (px0, py0), tip, f, 120, reach) for f in (0.35, 0.5, 0.65, 0.8)]
        half = float(np.median([(b_ - a_ + 1) / 2 for a_, b_ in full])) / S
        hands[name] = {"angle_deg": ang, "length_mm": r, "half_width_mm": round(half, 3),
                       "axis_offset_px": float(np.median([(a_ + b_) / 2 for a_, b_ in full]))}
    r, ang = polar(M["seconds_hand_tip"])
    nw = float(np.median([(b_ - a_ + 1) / 2 for a_, b_ in (cross_width(gray, (px0, py0), M["seconds_hand_tip"], f, 120, reach // 3) for f in (0.2, 0.35, 0.5))]))
    (aw, ap) = M["seconds_arrow_px"]
    hands["seconds"] = {"angle_deg": ang, "length_mm": r, "half_width_mm": round(nw / S, 3),
                        "arrow_from_to_mm": [polar(aw)[0], polar(ap)[0]], "tail_mm": polar(M["seconds_tail_end_px"])[0],
                        "tail_half_width_mm": round(M["seconds_tail_width_px"] / 2 / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    b = M["crown_box"]
    out["crown_box"] = {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                        "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r_ in (case_r, M["bezel_inner_r"], M["dial_edge_r"]):
            cv2.circle(ov, (px0, py0), int(r_), (0, 0, 255), 3)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            ux, uy = math.sin(t), math.cos(t)
            hw = hd["half_width_mm"]
            poly = [(-hw * uy, hw * ux), (hd["length_mm"] * ux, hd["length_mm"] * uy), (hw * uy, -hw * ux)]
            cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (0, 255, 255), 3)
        for side, sy in (("top", 1), ("bottom", -1)):
            cv2.line(ov, P((-14, sy * tips[side])), P((14, sy * tips[side])), (255, 255, 0), 3)
            for y in oj[side]:
                cv2.line(ov, (cx0 - 400, y), (cx0, y), (255, 0, 255), 3)
        for y in cj["top"]:
            cv2.line(ov, (cx0, y), (cx1, y), (0, 128, 255), 3)
        for x in (cx0, cx1):
            cv2.line(ov, (x, 200), (x, 1300), (0, 128, 255), 3)
        cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "lug_inner_x_mm",
                                           "bracelet", "checks", "hands", "hub_radius_mm", "crown_box")}, default=float), "->", dest)
