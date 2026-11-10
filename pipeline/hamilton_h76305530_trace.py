"""Measure the Hamilton H76305530 (Khaki Aviation Pilot Auto 39 mm) front photo (1714 x 2610) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.hamilton_h76305530_trace [out.json] [overlay.png]   # default config/watches/hamilton-h76305530-trace.json

Same method as pipeline/orient_ra_ac0p03l10b_trace.py. Anchor: case width 39 mm (Hamilton official) from a circle fitted to
the case flanks; the official 20 mm lug width is reported as a check. mm, x right, y toward 12, origin = hand pivot. Hand
outlines come from bright components in hand-aligned crops (MANUAL_PX, about +-2 px = +-0.06 mm); the skeleton windows of
the hour tip and the minute root show the dial through them. Numerals, markers, the chapter ring and the prints stay in the
dial map.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/hamilton-h76305530/front_1714x2610.jpg"
OUT = ROOT / "config/watches/hamilton-h76305530-trace.json"
CASE_MM = 39.0  # Hamilton official
LISTED = {"lug_width_mm": 20.0, "thickness_mm": 11.6}

MANUAL_PX = {
    "hand_pivot": [807, 1226],
    # outlines: [distance from the pivot, half width]; windows: open skeleton parts (dial visible), same form
    "hour": {"angle_deg": 304.0,
             "outline": [[0, 16], [45, 20], [60, 22.5], [90, 26.5], [120, 30.5], [150, 35.5], [195, 41.5], [225, 46.5], [255, 51],
                         [272, 53.5], [285, 52.5], [300, 43.5], [315, 35], [330, 26.5], [345, 18], [360, 9], [370, 0]],
             "window": [[232, 33], [240, 34.5], [255, 37.5], [270, 34.5], [285, 28], [300, 24], [315, 17], [330, 9], [339, 0]],
             "lume": [50, 222], "tail": [108, 16]},
    "minute": {"angle_deg": 55.7,
               "outline": [[0, 18], [60, 24], [100, 28], [140, 33], [200, 40], [240, 45], [280, 49], [320, 52], [360, 56], [410, 59],
                           [440, 57.5], [460, 46], [480, 34.5], [500, 23], [520, 11], [535, 0]],
               "window": [[45, 14], [60, 16], [100, 15.5], [140, 19], [200, 25], [240, 29], [248, 29]],
               "lume": [258, 505], "tail": [105, 16.5]},
    # seconds: polished needle, lume arrow tip, a polished ring on the tail
    "seconds": {"angle_deg": 194.8, "length": 575, "half": 6.5, "rod_half": 4, "arrow": [470, 12.7], "tail": 182, "ring": [23, 16]},
    "hub_radius_px": [30, 22, 10],  # hour-hand ring, dark collar, cap
    "outline_px": 5,  # polished hand edge around the lume
    "rings_px": {"dial": 519, "chapter": 602, "bevel": 630},  # dial edge, chapter ring outer edge, polished bevel to the brushed bezel
    "crown_x": [1505, 1640],  # root at the case, rounded end
    "crown_radius_px": 117,
    "crown_teeth": 16,
    "lug_inner_x_px": [452, 1160],
    "lug_tips_y": [435, 2070],
    "logo": [545, 1005, 1000, 1110],  # star emblem and HAMILTON (partly under the hands)
    "print_auto": [630, 1355, 940, 1400],
    "print_swiss_made": [700, 1785, 915, 1818],
}
ARTEFACTS = ["the right facets of the minute hand's skeleton rails reflect black: rails mirrored from the lit side",
             "the hour tip and the minute root are open skeletons: the dial (the 0 of 50, the N of HAMILTON) shows through and stays in the map",
             "numerals, the 12 triangle, the 3 6 9 bars, the chapter ring and its marks are printed: they stay in the dial map"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))
    # case outline on the flanks: the lugs leave it near 35 / 145 deg, the crown sits at 70-110 deg
    edge = []
    for a in list(np.arange(45, 66.1, 1.0)) + list(np.arange(114, 136.1, 1.0)) + list(np.arange(224, 316.1, 1.0)):
        rs = np.arange(640, 760, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Hamilton official)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}

    # lugs: silhouette half width by depth from the tip, top and bottom averaged
    t0, t1 = M["lug_tips_y"]
    half = lambda row: (np.nonzero(fg[row])[0].max() - np.nonzero(fg[row])[0].min()) / 2 / S
    depth = [[round(float(d), 2), round((half(t0 + int(round(d * S))) + half(t1 - int(round(d * S)))) / 2, 3)] for d in np.arange(0.25, 12.01, 0.25)]
    xi0, xi1 = M["lug_inner_x_px"]
    out["lug"] = {"tip_mm": round((t1 - t0) / 2 / S, 3), "inner_x_mm": f((xi1 - xi0) / 2), "half_width_by_depth_mm": depth,
                  "tips_mm": [f(py0 - t0), f(t1 - py0)]}
    widths = {}
    for row in (t0 - 150, t0 - 60, t1 + 60, t1 + 200, t1 + 350):
        xs = np.nonzero(fg[row])[0]
        widths[str(row)] = f(xs.max() - xs.min())
    out["checks"] = {"lug_to_lug_mm": f(t1 - t0), "lug_gap_mm": f(xi1 - xi0), "strap_width_mm": widths, "listed": LISTED}

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        hands[name] = {"angle_deg": hm["angle_deg"], "outline_mm": [[f(r), f(v)] for r, v in hm["outline"]],
                       "window_mm": [[f(r), f(v)] for r, v in hm["window"]], "lume_mm": [f(v) for v in hm["lume"]],
                       "tail_mm": [f(v) for v in hm["tail"]], "length_mm": f(hm["outline"][-1][0])}
    sm = M["seconds"]
    hands["seconds"] = {"angle_deg": sm["angle_deg"], "length_mm": f(sm["length"]), "half_width_mm": f(sm["half"]), "rod_half_mm": f(sm["rod_half"]),
                        "arrow_mm": [f(v) for v in sm["arrow"]], "tail_mm": f(sm["tail"]), "ring_mm": [f(v) for v in sm["ring"]]}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_outline_mm"] = f(M["outline_px"])
    cx0, cx1 = M["crown_x"]
    out["crown"] = {"from_mm": f(cx0 - px0), "to_mm": f(cx1 - px0), "radius_mm": f(M["crown_radius_px"]), "teeth": M["crown_teeth"]}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [f(b[2] - b[0]), f(b[3] - b[1])]}
    for k in ("logo", "print_auto", "print_swiss_made"):
        out[k] = box(M[k])
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for v in M["rings_px"].values():
            cv2.circle(ov, (px0, py0), v, (0, 0, 255), 1)
        for name in ("hour", "minute"):
            hd = hands[name]
            t = math.radians(hd["angle_deg"])
            for key, col in (("outline_mm", (0, 255, 255)), ("window_mm", (255, 0, 255))):
                pts = hd[key]
                poly = [(v * math.cos(t) + r * math.sin(t), -v * math.sin(t) + r * math.cos(t)) for r, v in pts] + \
                       [(-v * math.cos(t) + r * math.sin(t), v * math.sin(t) + r * math.cos(t)) for r, v in pts[::-1]]
                cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, col, 1)
        sd = hands["seconds"]
        t = math.radians(sd["angle_deg"])
        cv2.line(ov, P((-sd["tail_mm"] * math.sin(t), -sd["tail_mm"] * math.cos(t))), P((sd["length_mm"] * math.sin(t), sd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        cv2.circle(ov, P((-sd["tail_mm"] * math.sin(t), -sd["tail_mm"] * math.cos(t))), int(sm["ring"][0]), (0, 255, 255), 1)
        for k in ("logo", "print_auto", "print_swiss_made"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for y in M["lug_tips_y"]:
            cv2.line(ov, (300, y), (1400, y), (255, 128, 0), 1)
        for x in M["lug_inner_x_px"]:
            cv2.line(ov, (x, 200), (x, 2400), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "rings_mm", "checks", "hub_radius_mm", "crown")}, default=float),
          json.dumps(data["lug"]["tips_mm"]), "->", dest)
