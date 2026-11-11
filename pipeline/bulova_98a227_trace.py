"""Measure the Bulova 98A227 (Marine Star automatic, 44 mm, rose-gold tone case, blue outer ring, blue silicone strap) official
front render (1390 x 2048, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.bulova_98a227_trace [out.json] [overlay.png]   # default config/watches/bulova-98a227-trace.json

Anchor: 44 mm case width (Bulova official) across the blue ring's flat at 9 o'clock (the crown is on the right); the
official 24 mm lug width is a check on the strap. mm, x right, y toward 12, origin = hand pivot. The applied rose-gold
numerals and the Bulova logo are traced as outlines from a rose-gold colour mask (hands, rings and red prints excluded);
hands, rings, screws, crown and strap edges are read from gridded and hand-aligned crops (MANUAL_PX).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/bulova-98a227/front_official_1390x2048.png"
OUT = ROOT / "config/watches/bulova-98a227-trace.json"
CASE_MM = 44.0  # Bulova official case width
LISTED = {"lug_width_mm": 24.0, "thickness_mm": 12.0}

MANUAL_PX = {
    "hand_pivot": [633, 1021],
    # sword hands: [distance from the pivot, half width] of the rose-gold frame, the lume window and the open slot
    "hour": {"angle_deg": 305.4, "outline": [[0, 17], [110, 17], [175, 25], [255, 0]], "lume": [[118, 10], [175, 17], [232, 0]], "slot": [42, 100, 9]},
    "minute": {"angle_deg": 51.0, "outline": [[0, 14], [150, 14], [290, 19], [362, 0]], "lume": [[160, 8], [290, 13], [343, 0]], "slot": [45, 130, 7.5]},
    "hub_radius_px": [27, 13],
    # sub-seconds at 4: red hand with a wide tail
    "sub": {"centre": [732, 1150], "angle_deg": 50.3, "length": 108, "half": 3.2, "tail": 46, "tail_half": 7, "hub": 14,
            "ring": [119, 149]},
    "aperture": {"centre": [530, 1200], "ring": [120, 132]},
    "rings_px": {"dial": 380, "bezel_in": 447, "bezel_out": 574, "ring_out": 601},  # ring_out: circumradius of the blue 24-gon
    "ring_notch": {"count": 24, "depth": 14, "half_width": 12},  # V cuts in the bezel's outer edge, one at every vertex of the blue ring
    "screws": {"r": 506, "radius": 34, "angles": [0, 60, 120, 180, 240, 300]},
    "crown": {"angle_deg": 90.6, "r": [597, 712], "radius": 83, "teeth": 14},
    "crown_rows": [940, 1117],  # the right silhouette in these rows is the crown: the case edge is interpolated across
    "lug_tips_y": [342, 1705],
    "strap_x": {"top": [[310, 957], [343, 923]], "bottom": [[305, 950], [337, 911]]},  # at the lug tip, at the end row (it tapers)
    "strap_rows": [100, 1960],  # last full-width rows before the rounded ends
    "logo_box": [594, 626, 675, 742],
}
ARTEFACTS = ["the dial (sunray ridges, chapter ring with minutes, BULOVA, Marine Star, 200 m, Automatic 21 Jewels, the sub-seconds"
             " track and the open-heart movement) stays in the dial map", "the strap texture is a photo map"]


def hand_poly(h, scale_r=1.0):
    t = math.radians(h["angle_deg"])
    pts = h["outline"]
    loop = [(v, r) for r, v in pts] + [(-v, r) for r, v in pts[::-1][1:-1]]
    return [(x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)) for x, y in loop]


def trace(path=FRONT, overlay=None):
    im = load(path)
    raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    fg = raw[..., 3] > 128
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    left = np.median([np.nonzero(fg[y])[0].min() for y in range(950, 1090)])  # flat of the blue ring at 9 o'clock
    S = 2 * (px0 - left) / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Bulova official) across the blue ring's flat at 9 o'clock", "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}
    out["ring_notch_mm"] = {"count": M["ring_notch"]["count"], "depth": f(M["ring_notch"]["depth"]), "half_width": f(M["ring_notch"]["half_width"])}
    out["screws_mm"] = {"r": f(M["screws"]["r"]), "radius": f(M["screws"]["radius"]), "angles": M["screws"]["angles"]}

    # head outline: left and right alpha edges per row between the lug tips; the crown rows are bridged on the right
    t0, t1 = M["lug_tips_y"]
    c0, c1 = M["crown_rows"]
    xr0, xr1 = np.nonzero(fg[c0])[0].max(), np.nonzero(fg[c1])[0].max()
    rows = []
    for y in range(t0 + 2, t1 - 1, 2):
        xs = np.nonzero(fg[y])[0]
        xr = xs.max() if not c0 <= y <= c1 else xr0 + (xr1 - xr0) * (y - c0) / (c1 - c0)
        rows.append([round(-(y - py0) / S, 3), round((xs.min() - px0) / S, 3), round((xr - px0) / S, 3)])
    out["head_rows_y_left_right_mm"] = rows
    sx = M["strap_x"]
    out["lug"] = {"photo_tips_mm": [f(py0 - t0), f(t1 - py0)], "tip_mm": f((t1 - t0) / 2),
                  "inner_x_mm": f(((sx["top"][0][1] - sx["top"][0][0]) + (sx["bottom"][0][1] - sx["bottom"][0][0])) / 4)}
    xmm = lambda pair: [mm((pair[0], 0))[0], mm((pair[1], 0))[0]]
    out["strap_mm"] = {"top": {"x": xmm(sx["top"][0]), "x_end": xmm(sx["top"][1]), "tip_y": f(py0 - t0), "end_y": f(py0 - M["strap_rows"][0])},
                       "bottom": {"x": xmm(sx["bottom"][0]), "x_end": xmm(sx["bottom"][1]), "tip_y": f(t1 - py0), "end_y": f(M["strap_rows"][1] - py0)}}
    out["checks"] = {"photo_lug_to_lug_mm": f(t1 - t0), "strap_width_mm": [f(sx["top"][0][1] - sx["top"][0][0]), f(sx["bottom"][0][1] - sx["bottom"][0][0])], "listed": LISTED}

    hands = {}
    for name in ("hour", "minute"):
        h = M[name]
        hands[name] = {"angle_deg": h["angle_deg"], "outline_mm": [[f(r), f(v)] for r, v in h["outline"]],
                       "lume_mm": [[f(r), f(v)] for r, v in h["lume"]], "slot_mm": [f(v) for v in h["slot"]]}
    sb = M["sub"]
    out["sub"] = {"centre_mm": mm(sb["centre"]), "angle_deg": sb["angle_deg"], "length_mm": f(sb["length"]), "half_mm": f(sb["half"]),
                  "tail_mm": f(sb["tail"]), "tail_half_mm": f(sb["tail_half"]), "hub_mm": f(sb["hub"]), "ring_mm": [f(v) for v in sb["ring"]]}
    ap = M["aperture"]
    out["aperture"] = {"centre_mm": mm(ap["centre"]), "ring_mm": [f(v) for v in ap["ring"]]}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    cr = M["crown"]
    out["crown"] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"]}

    # applied rose-gold numerals and logo: colour mask, minus the hands, the two rings, the openings and red prints
    bgr = raw[..., :3].astype(int)
    B, G, R = bgr[..., 0], bgr[..., 1], bgr[..., 2]
    gold = ((R - B) > 40) & (R > 120) & (G > 0.55 * R)
    yy, xx = np.mgrid[:fg.shape[0], :fg.shape[1]]
    keep = np.hypot(xx - px0, yy - py0) < 425
    for c, (r0, r1) in ((sb["centre"], sb["ring"]), (ap["centre"], ap["ring"])):
        keep &= np.hypot(xx - c[0], yy - c[1]) > r1 + 4
    block = np.zeros(fg.shape, np.uint8)
    for name in ("hour", "minute"):
        cv2.fillPoly(block, [np.array([(px0 + x, py0 - y) for x, y in hand_poly(M[name])], np.int32)], 1)
    block = cv2.dilate(block, np.ones((7, 7), np.uint8))
    cv2.circle(block, (px0, py0), M["hub_radius_px"][0] + 4, 1, -1)
    m = (gold & keep & ~block.astype(bool)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    shapes = []
    for i, c in enumerate(cs):
        if hier[0][i][3] != -1 or cv2.contourArea(c) < 400:
            continue
        poly = cv2.approxPolyDP(c, 0.8, True)[:, 0]
        holes = []
        k = hier[0][i][2]
        while k != -1:
            if cv2.contourArea(cs[k]) > 25:
                holes.append([mm(p) for p in cv2.approxPolyDP(cs[k], 0.8, True)[:, 0]])
            k = hier[0][k][0]
        shapes.append({"outer": [mm(p) for p in poly], "holes": holes, "area_px": int(cv2.contourArea(c))})
    out["applied_shapes_mm"] = shapes
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = im // 2
        cv2.drawContours(ov, [np.array([(px0 + p[0] * S, py0 - p[1] * S) for p in sh["outer"]], np.int32) for sh in shapes], -1, (0, 255, 255), 1)
        for name in ("hour", "minute"):
            cv2.polylines(ov, [np.array([(px0 + x, py0 - y) for x, y in hand_poly(M[name])], np.int32)], True, (0, 255, 0), 1)
        for v in M["rings_px"].values():
            cv2.circle(ov, (px0, py0), v, (0, 0, 255), 1)
        for c, (r0, r1) in ((sb["centre"], sb["ring"]), (ap["centre"], ap["ring"])):
            cv2.circle(ov, tuple(c), r0, (255, 0, 255), 1)
            cv2.circle(ov, tuple(c), r1, (255, 0, 255), 1)
        for a in M["screws"]["angles"]:
            q = (int(px0 + M["screws"]["r"] * math.sin(math.radians(a))), int(py0 - M["screws"]["r"] * math.cos(math.radians(a))))
            cv2.circle(ov, q, M["screws"]["radius"], (255, 255, 0), 1)
        t = math.radians(sb["angle_deg"])
        cx, cy = sb["centre"]
        cv2.line(ov, (int(cx - sb["tail"] * math.sin(t)), int(cy + sb["tail"] * math.cos(t))), (int(cx + sb["length"] * math.sin(t)), int(cy - sb["length"] * math.cos(t))), (0, 255, 0), 1)
        pts = [(px0 + r[1] * S, py0 - r[0] * S) for r in rows] + [(px0 + r[2] * S, py0 - r[0] * S) for r in rows[::-1]]
        cv2.polylines(ov, [np.array(pts, np.int32)], True, (255, 128, 0), 1)
        for y in M["lug_tips_y"]:
            cv2.line(ov, (200, y), (1100, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "lug", "checks", "crown", "sub", "aperture")}, default=float),
          "shapes", len(data["applied_shapes_mm"]), "->", dest)
