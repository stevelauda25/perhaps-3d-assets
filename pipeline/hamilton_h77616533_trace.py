"""Measure the Hamilton H77616533 (Khaki Aviation X-Wind Auto Chrono 44 mm) official front render (2000 x 2000, transparent
background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.hamilton_h77616533_trace [out.json] [overlay.png]   # default config/watches/hamilton-h77616533-trace.json

Same method as pipeline/hamilton_h76305530_trace.py. Anchor: 44 mm case (Hamilton official) from a circle fitted to the bezel
edge; the official 22 mm lug width and 54 mm lug to lug are reported as checks (the render's lugs are foreshortened: the
official lug to lug is used). mm, x right, y toward 12, origin = hand pivot. Hand outlines come from bright components in
hand-aligned crops (MANUAL_PX); the steel bezel's engraved scale is traced by threshold and becomes black inlays. The inner
rotating ring, dial, subdials, numerals, day-date and prints stay in the dial map.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_print import UP, shapes_from_mask
from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/hamilton-h77616533/front_official_2000x2000.png"
OUT = ROOT / "config/watches/hamilton-h77616533-trace.json"
CASE_MM = 44.0  # Hamilton official
LISTED = {"lug_width_mm": 22.0, "lug_to_lug_mm": 54.0, "thickness_mm": 15.55}

MANUAL_PX = {
    "hand_pivot": [999, 969],
    # outlines: [distance from the pivot, half width] from bright components in hand-aligned crops
    "hour": {"angle_deg": 305.3, "outline": [[-12, 12], [30, 12], [60, 11], [100, 13.5], [130, 15.5], [160, 17.5], [170, 13.5], [180, 8],
                                              [200, 3.5], [240, 2.5], [248, 0]], "lume": [40, 182]},
    "minute": {"angle_deg": 55.2, "outline": [[-12, 12], [50, 12], [100, 13], [200, 14], [230, 15.5], [260, 10], [290, 6], [310, 3.5],
                                               [340, 3], [347, 0]], "lume": [55, 285]},
    "chrono": {"angle_deg": 227.0, "length": 350, "half": 4, "arrow": [295, 11], "tail": 40},
    "hub_radius_px": [37, 18, 7],  # polished hub disc, ring, cap
    "outline_px": 3,
    # subdials: centre, hand angle, hand length, tail, half width at the widest, hub radius
    "subdials": {"12": [[995, 774], 0.0, 62, 12, 5, 8], "6": [[997, 1174], 0.0, 60, 12, 5, 8], "3": [[1206, 974], 162.6, 90, 15, 7, 9]},
    "rings_px": {"dial": 470, "bezel_out": 560},  # bezel inner edge (inner rotating ring outside it is printed), bezel outer edge
    "bezel_print_band_px": [476, 552],
    "crown": {"angle_deg": 267.0, "r": [556, 647], "radius": 65, "teeth": 18},
    "pushers": [{"angle_deg": 70.4, "r": [556, 632], "radius": 55}, {"angle_deg": 114.2, "r": [556, 632], "radius": 55}],
    "crown_rows_px": [925, 1075],  # the crown at 9 widens the left edge here; the right edge is used
    "lug_inner_x_px": [731, 1267],
    "lug_tips_y": [335, 1667],
    "logo": [670, 900, 890, 938],  # HAMILTON at 9
    "day_date": [675, 940, 886, 1016],
    "print_khaki": [692, 1014, 876, 1086],
}
ARTEFACTS = ["official render: the lugs are foreshortened (tips 24.9 / 27.4 mm from the pivot); the official 54 mm lug to lug is used, symmetric",
             "applied numerals, lume dots, the day-date frame and the inner rotating ring are kept in the dial map",
             "the chrono seconds tail sits under the minute hand: its length is an estimate"]


def load(path):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    a = im[..., 3:4].astype(float) / 255
    return (im[..., :3] * a + 255 * (1 - a) + 0.5).astype(np.uint8)  # transparent background -> white


def trace(path=FRONT, overlay=None):
    im = load(path)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)[..., 3] > 128  # the alpha: bright steel is close to the white background
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))
    # bezel edge at the gaps between the lugs, lobes, crown and pushers (read on rays every 6 deg)
    edge = []
    for a in [a0 + d for a0 in (24, 48, 54, 90, 96, 132, 156, 204, 228, 252, 288, 312, 330, 336) for d in (-1, 0, 1)]:
        rs = np.arange(500, 575, 0.5)  # a ray that meets a lug or a lobe instead is dropped
        xs, ys = (np.array(v) for v in at(rs, a))
        k = np.nonzero(~fg[ys.astype(int), xs.astype(int)])[0]
        if len(k):
            edge.append((xs[k[0]], ys[k[0]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Hamilton official), bezel edge",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}

    # case outline per row: the narrower side (the crown at 9 and the pushers at 2 / 4 are built separately)
    c0, c1 = M["crown_rows_px"]
    prof = []
    for y_mm in np.arange(-30, 30.01, 0.25):
        row = int(round(py0 - y_mm * S))
        xs = np.nonzero(fg[row])[0]
        left, right = (px0 - xs.min()) / S, (xs.max() - px0) / S
        prof.append([round(float(y_mm), 2), round(right if c0 <= row <= c1 else min(left, right), 3)])
    out["case_half_width_by_y_mm"] = prof
    t0, t1 = M["lug_tips_y"]
    xi0, xi1 = M["lug_inner_x_px"]
    out["lug"] = {"tip_mm": round(LISTED["lug_to_lug_mm"] / 2, 3), "photo_tips_mm": [f(py0 - t0), f(t1 - py0)], "inner_x_mm": f((xi1 - xi0) / 2)}
    widths = {}
    for row in (t0 - 100, t0 - 10, t1 + 10, t1 + 150):
        xs = np.nonzero(fg[row])[0]
        widths[str(row)] = f(xs.max() - xs.min())
    out["checks"] = {"photo_lug_to_lug_mm": f(t1 - t0), "lug_gap_mm": f(xi1 - xi0), "strap_width_mm": widths, "listed": LISTED}

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        hands[name] = {"angle_deg": hm["angle_deg"], "outline_mm": [[f(r), f(v)] for r, v in hm["outline"]],
                       "lume_mm": [f(v) for v in hm["lume"]], "length_mm": f(hm["outline"][-1][0])}
    cm = M["chrono"]
    hands["chrono"] = {"angle_deg": cm["angle_deg"], "length_mm": f(cm["length"]), "half_width_mm": f(cm["half"]),
                       "arrow_mm": [f(v) for v in cm["arrow"]], "tail_mm": f(cm["tail"])}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_outline_mm"] = f(M["outline_px"])
    out["subdials"] = {k: {"centre_mm": mm(c), "angle_deg": a, "length_mm": f(L), "tail_mm": f(tl), "half_mm": f(hw), "hub_mm": f(hb)}
                       for k, (c, a, L, tl, hw, hb) in M["subdials"].items()}
    cr = M["crown"]
    out["crown"] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"]}
    out["pushers"] = [{"angle_deg": p["angle_deg"], "r_mm": [f(v) for v in p["r"]], "radius_mm": f(p["radius"])} for p in M["pushers"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [f(b[2] - b[0]), f(b[3] - b[1])]}
    for k in ("logo", "day_date", "print_khaki"):
        out[k] = box(M[k])

    # engraved bezel scale: dark strokes on the steel ring, traced to outlines (black inlays)
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - px0, yy - py0)
    b0, b1 = M["bezel_print_band_px"]
    pr = ((gray < 95) & (rr > b0) & (rr < b1)).astype(np.uint8) * 255
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)
    pr = np.isin(lab, [i for i in range(1, n) if st[i, 4] >= 6]).astype(np.uint8) * 255
    x0b, y0b, sz = px0 - b1 - 4, py0 - b1 - 4, 2 * b1 + 8
    win = pr[y0b:y0b + sz, x0b:x0b + sz].copy()
    up = cv2.GaussianBlur(cv2.resize(win, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
    to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
    out["bezel_prints"] = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 4)
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
            pts = hd["outline_mm"]
            poly = [(v * math.cos(t) + r * math.sin(t), -v * math.sin(t) + r * math.cos(t)) for r, v in pts] + \
                   [(-v * math.cos(t) + r * math.sin(t), v * math.sin(t) + r * math.cos(t)) for r, v in pts[::-1]]
            cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (0, 255, 255), 1)
        t = math.radians(cm["angle_deg"])
        cv2.line(ov, P((-hands["chrono"]["tail_mm"] * math.sin(t), -hands["chrono"]["tail_mm"] * math.cos(t))),
                 P((hands["chrono"]["length_mm"] * math.sin(t), hands["chrono"]["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        for k, sd in out["subdials"].items():
            c = sd["centre_mm"]
            t = math.radians(sd["angle_deg"])
            cv2.line(ov, P(c), P((c[0] + sd["length_mm"] * math.sin(t), c[1] + sd["length_mm"] * math.cos(t))), (255, 0, 255), 1)
        for sh in out["bezel_prints"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        for k in ("logo", "day_date", "print_khaki"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for y in M["lug_tips_y"]:
            cv2.line(ov, (500, y), (1500, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "rings_mm", "lug", "checks", "crown", "pushers")}, default=float),
          len(data["bezel_prints"]), "bezel prints ->", dest)
