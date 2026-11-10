"""Measure the Hamilton H76419931 (Khaki Aviation Pilot Pioneer Mechanical 36 x 33 mm, black dial, grey NATO strap) official
front render (1200 x 1200, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.hamilton_h76419931_trace [out.json] [overlay.png]   # default config/watches/hamilton-h76419931-trace.json

Same method as pipeline/hamilton_h70515137_trace.py. Anchor: 33 mm case width (Hamilton official "36 x 33 mm") across the
cushion case at its widest row, crown excluded; the official 36 mm length and 18 mm lug width are reported as checks. mm, x
right, y toward 12, origin = hand pivot. The cushion outline is the alpha silhouette per row; hand outlines come from bright
components in hand-aligned crops (MANUAL_PX). The dial with its printed numerals, markers, chapter ring and prints stays in
the dial map.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load
from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/hamilton-h76419931/front_official_1200x1200.png"
OUT = ROOT / "config/watches/hamilton-h76419931-trace.json"
CASE_MM = 33.0  # Hamilton official: 36 x 33 mm (length x width)
LISTED = {"case_length_mm": 36.0, "lug_width_mm": 18.0, "thickness_mm": 9.95}

MANUAL_PX = {
    "hand_pivot": [600, 557],
    # outlines: [distance from the pivot, half width]; lance hour, needle minute (polished outline, beige lume)
    "hour": {"angle_deg": 303.4, "outline": [[-12, 8], [25, 5], [60, 6.5], [120, 10.5], [128, 6.5], [139, 0]], "lume": [30, 124]},
    "minute": {"angle_deg": 55.2, "outline": [[-12, 8], [25, 5], [60, 6.5], [150, 6.5], [180, 5], [195, 2.5], [203, 0]], "lume": [30, 155]},
    "seconds": {"angle_deg": 222.6, "length": 205, "half": 3, "red_from": 205, "tail": 30, "disc": 0},
    "hub_radius_px": [20, 5],
    "outline_px": 2,
    "rings_px": {"dial": 212, "bezel_in": 227},  # chapter ring outer edge; polished inner bezel ring to the crystal edge
    "crown": {"angle_deg": 90.0, "r": [262, 292], "radius": 38, "teeth": 16},
    "case_rows_px": [264, 866],  # top and bottom of the cushion case (the strap runs on past both)
    "strap_x_px": [464, 734],
    "logo": [533, 457, 667, 481],
    "print_mech": [545, 650, 655, 670],
    "print_swiss_made": [555, 730, 645, 745],
}
ARTEFACTS = ["the cushion case measures 37.4 mm long at the 33 mm anchor (36 mm listed); the render's proportions are kept",
             "the numerals, markers and chapter ring are printed: they stay in the dial map"]


def trace(path=FRONT, overlay=None):
    im = load(path)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)[..., 3] > 128
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))
    rows = range(*M["case_rows_px"])
    lefts = {y: np.nonzero(fg[y])[0].min() for y in rows}
    wide = min(lefts, key=lambda y: lefts[y])
    S = 2 * (px0 - lefts[wide]) / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    y0c, y1c = M["case_rows_px"]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Hamilton official), cushion at its widest row ({wide})",
           "case": {"half_width_mm": round(CASE_MM / 2, 3), "top_mm": f(py0 - y0c), "bottom_mm": f(y1c - py0)},
           "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}
    # cushion outline: left edge per row (the crown is on the right), top and bottom kept as they are (not centred on the pivot)
    out["case_left_by_y_mm"] = [[round(-(y - py0) / S, 3), f(px0 - lefts[y])] for y in rows[::2]]
    sx0, sx1 = M["strap_x_px"]
    out["strap"] = {"half_width_mm": f((sx1 - sx0) / 2), "centre_x_mm": f((sx0 + sx1) / 2 - px0)}
    out["checks"] = {"case_length_mm": f(y1c - y0c), "strap_width_mm": f(sx1 - sx0), "listed": LISTED}

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        hands[name] = {"angle_deg": hm["angle_deg"], "outline_mm": [[f(r), f(v)] for r, v in hm["outline"]],
                       "lume_mm": [f(v) for v in hm["lume"]], "length_mm": f(hm["outline"][-1][0])}
    sm = M["seconds"]
    hands["seconds"] = {"angle_deg": sm["angle_deg"], "length_mm": f(sm["length"]), "half_width_mm": f(sm["half"]), "red_from_mm": f(sm["red_from"]),
                        "tail_mm": f(sm["tail"]), "disc_mm": f(sm["disc"])}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_outline_mm"] = f(M["outline_px"])
    cr = M["crown"]
    out["crown"] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"]}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [f(b[2] - b[0]), f(b[3] - b[1])]}
    for k in ("logo", "print_mech", "print_swiss_made"):
        out[k] = box(M[k])

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for y_mm, x_mm in out["case_left_by_y_mm"]:
            cv2.circle(ov, P((-x_mm, y_mm)), 1, (0, 128, 255), -1)
            cv2.circle(ov, P((x_mm, y_mm)), 1, (0, 128, 255), -1)
        for v in M["rings_px"].values():
            cv2.circle(ov, (px0, py0), v, (0, 0, 255), 1)
        for name in ("hour", "minute"):
            hd = hands[name]
            t = math.radians(hd["angle_deg"])
            pts = hd["outline_mm"]
            poly = [(v * math.cos(t) + r * math.sin(t), -v * math.sin(t) + r * math.cos(t)) for r, v in pts] + \
                   [(-v * math.cos(t) + r * math.sin(t), v * math.sin(t) + r * math.cos(t)) for r, v in pts[::-1]]
            cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (0, 255, 255), 1)
        sd = hands["seconds"]
        t = math.radians(sd["angle_deg"])
        cv2.line(ov, P((-sd["tail_mm"] * math.sin(t), -sd["tail_mm"] * math.cos(t))), P((sd["length_mm"] * math.sin(t), sd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        for k in ("logo", "print_mech", "print_swiss_made"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "rings_mm", "strap", "checks", "crown")}, default=float), "->", dest)
