"""Measure the Seiko 5 SNZG11J1 front photo (white background, 2000 x 2966) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snzg11_trace [out.json] [overlay.png]     # default config/watches/seiko-snzg11j1-trace.json

Anchor: case width on the flanks = 42 mm (Irsyad); lug gap and strap width reported as checks (22 mm listed). mm, x right,
y toward 12, origin = hand pivot. All dial print (numerals, track, logo, day-date) stays in the dial map, so only the hands,
hub, rings, crown, lugs and the NATO strap are measured. Hands, rings, crown and lug corners come from gridded crops
(MANUAL_PX, +-3 px = +-0.08 mm); hand widths from cross profiles.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snzg11j1/front_2000x2966.png"
OUT = ROOT / "config/watches/seiko-snzg11j1-trace.json"
CASE_MM = 42.0  # Irsyad, 2026-11-06
LISTED = {"lug_width_mm": 22.0}

MANUAL_PX = {
    "hand_pivot": [941, 1399],
    "case_left_flank_x": 165,  # at the pivot row; the right flank there is the crown
    "bezel_inner_r": 681,  # matte bezel ends, black gasket ring begins
    "dial_edge_r": 641,  # black ring ends, chapter ring begins
    "hour_hand_tip": [682, 1221],
    "minute_hand_tip": [1350, 1151],
    "seconds_hand_tip": [545, 1661],  # end of the thin red needle
    "seconds_arrow_px": [[700, 1545], [640, 1597]],  # red arrowhead: wide end, point (outward)
    "hub_radius_px": [48, 23],  # hour hand collet, minute hand collet
    "crown_box": [1760, 1280, 1847, 1470],  # fluted part, the neck sits inside it
    "lug_inner_px": {"top": [[525, 522], [1350, 490]], "bottom": [[555, 2345], [1397, 2320]]},  # inner corner: left, right
    "strap_rows_mm": [1.0, 8.0],  # rows past the lug tips used for the strap edges
}
ARTEFACTS = ["bright lines inside the black gasket ring: crystal edge reflections, not parts",
             "the bottom half is about 4 % larger and 0.5 mm further right (watch slightly turned): left/right and top/bottom means are used",
             "the top strap fans out to the right toward its keeper: the strap edges are read in the first 8 mm past the lug tips"]


def cross_width(g, p0, tip, f, thr):
    """Lit run across the hand axis at fraction f of its length, px: (from, to) relative to the axis."""
    dx, dy = tip[0] - p0[0], tip[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    cx, cy = p0[0] + ux * L * f, p0[1] + uy * L * f
    lit = [t for t in range(-40, 41) if g[int(round(cy + ux * t)), int(round(cx - uy * t))] > thr]
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
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (Irsyad)",
           "case": {"radius_mm": round(case_r / S, 3)},
           "crystal_ring": {"radius_mm": round(M["bezel_inner_r"] / S, 3), "basis": "inner edge of the matte bezel"},
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

    # strap: edges per side in px, rows strap_rows_mm past each side's lug tips (for the texture atlas)
    a, b = M["strap_rows_mm"]
    strap = {}
    for side, sy in (("top", 1), ("bottom", -1)):
        rows = [int(round(py0 - sy * (tips[side] + d) * S)) for d in np.arange(a, b, 0.25)]
        edges = np.array([[np.nonzero(fg[r])[0].min(), np.nonzero(fg[r])[0].max()] for r in rows])
        xl, xr = np.median(edges, 0)
        strap[side] = {"x_px": [float(xl), float(xr)], "width_mm": round((xr - xl) / S, 2), "centre_mm": round(((xl + xr) / 2 - px0) / S, 2)}
    out["strap"] = strap
    out["checks"] = {"lug_gap_mm": round(float(np.mean(gaps)), 2), "lug_to_lug_mm": round(tips["top"] + tips["bottom"], 2),
                     "strap_width_mm": round(float(np.mean([s["width_mm"] for s in strap.values()])), 2), "listed": LISTED}

    # hands: sword hour/minute with a lume inlay; full width = lit run across the axis (the inlay frame is in the spec)
    hands = {}
    for name in ("hour", "minute"):
        tip = M[f"{name}_hand_tip"]
        r, ang = polar(tip)
        full = [cross_width(gray, (px0, py0), tip, f, 120) for f in (0.35, 0.5, 0.65, 0.8)]
        half = float(np.median([(b_ - a_ + 1) / 2 for a_, b_ in full])) / S
        hands[name] = {"angle_deg": ang, "length_mm": r, "half_width_mm": round(half, 3),
                       "axis_offset_px": float(np.median([(a_ + b_) / 2 for a_, b_ in full]))}
    r, ang = polar(M["seconds_hand_tip"])
    nw = float(np.median([(b_ - a_ + 1) / 2 for a_, b_ in (cross_width(gray, (px0, py0), M["seconds_hand_tip"], f, 120) for f in (0.2, 0.35, 0.5))]))
    (aw, ap) = M["seconds_arrow_px"]
    hands["seconds"] = {"angle_deg": ang, "length_mm": r, "half_width_mm": round(nw / S, 3),
                        "arrow_from_to_mm": [polar(aw)[0], polar(ap)[0]]}
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
            cv2.circle(ov, (px0, py0), int(r_), (0, 0, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            ux, uy = math.sin(t), math.cos(t)
            hw = hd["half_width_mm"]
            poly = [(-hw * uy, hw * ux), (hd["length_mm"] * ux, hd["length_mm"] * uy), (hw * uy, -hw * ux)]
            cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (0, 255, 255), 2)
        for side, s in strap.items():
            for x in s["x_px"]:
                y = int(py0 - (1 if side == "top" else -1) * (tips[side] + 4) * S)
                cv2.line(ov, (int(x), y - 150), (int(x), y + 150), (255, 0, 255), 2)
        for side, sy in (("top", 1), ("bottom", -1)):
            cv2.line(ov, P((-14, sy * tips[side])), P((14, sy * tips[side])), (255, 255, 0), 2)
        cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "lug_inner_x_mm",
                                           "strap", "checks", "hands", "hub_radius_mm", "crown_box")}, default=float), "->", dest)
