"""Measure the Hamilton H70515137 (Khaki Field Auto 42 mm, black dial, steel bracelet) official front render (2000 x 2000,
transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.hamilton_h70515137_trace [out.json] [overlay.png]   # default config/watches/hamilton-h70515137-trace.json

Same method as pipeline/hamilton_h77616533_trace.py. Anchor: 42 mm case (Hamilton official) from a circle fitted to the case
edge on the alpha; the official 22 mm lug width and 53 mm lug to lug are reported as checks. mm, x right, y toward 12,
origin = hand pivot. Hand outlines come from bright components in hand-aligned crops, the bracelet joints from dark rows
per column (MANUAL_PX). The dial with its chapter ring, numerals, date window and prints stays in the dial map.
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
FRONT = ROOT / "references/hamilton-h70515137/front_official_2000x2000.png"
OUT = ROOT / "config/watches/hamilton-h70515137-trace.json"
CASE_MM = 42.0  # Hamilton official
LISTED = {"lug_width_mm": 22.0, "lug_to_lug_mm": 53.0, "thickness_mm": 11.0}

MANUAL_PX = {
    "hand_pivot": [941, 929],
    # outlines: [distance from the pivot, half width]; sword hands with a needle tip, polished outline, lume
    "hour": {"angle_deg": 307.9, "outline": [[-15, 14], [30, 11], [100, 15.5], [150, 20], [165, 15], [180, 6], [190, 3], [232, 2], [238, 0]],
             "lume": [40, 165]},
    "minute": {"angle_deg": 55.0, "outline": [[-15, 14], [45, 13], [150, 14.5], [240, 17.5], [258, 14], [270, 9], [285, 6], [300, 3],
                                               [360, 2], [368, 0]], "lume": [50, 255]},
    # seconds: white needle, red tip, tail ending in a disc
    "seconds": {"angle_deg": 221.0, "length": 425, "half": 4.5, "red_from": 335, "tail": 120, "disc": 10},
    "hub_radius_px": [26, 9],
    "outline_px": 3,
    "rings_px": {"dial": 420, "bezel_in": 432},  # black dial with the chapter ring; polished sloped bezel from bezel_in to the case edge
    "crown": {"angle_deg": 90.5, "r": [487, 602], "radius": 75, "teeth": 22},
    "lug_inner_x_px": [700, 1190],
    "lug_tips_y": [340, 1545],
    "logo": [829, 803, 1057, 831],
    "print_khaki": [850, 1029, 1036, 1071],
    "date_window": [1133, 897, 1226, 969],
    # bracelet: three columns; joints (photo rows) nearest the case on each side; the render's bracelet curves away, so the
    # pitch is read on the first link past each lug tip
    "bracelet_joints_y": {"top_outer": [328, 144], "top_centre": [220, 90], "bottom_outer": [1550, 1764], "bottom_centre": [1690, 1853]},
    "bracelet_centre_x_px": [825, 1060],
}
ARTEFACTS = ["official render: the bracelet curves away from the camera, the link pitch is read on the first link past each lug tip",
             "the chapter ring, numerals, date window and prints stay in the dial map"]


def trace(path=FRONT, overlay=None):
    im = load(path)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)[..., 3] > 128
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))
    edge = []
    for a in list(np.arange(60, 81, 1.0)) + list(np.arange(100, 121, 1.0)) + list(np.arange(240, 301, 1.0)):
        rs = np.arange(420, 560, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        k = np.nonzero(~fg[ys.astype(int), xs.astype(int)])[0]
        if len(k):
            edge.append((xs[k[0]], ys[k[0]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Hamilton official), case edge",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}

    prof = []
    for y_mm in np.arange(-30, 30.01, 0.25):
        row = int(round(py0 - y_mm * S))
        xs = np.nonzero(fg[row])[0]
        prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3)])  # left edge: the crown is on the right
    out["silhouette_left_mm"] = prof
    t0, t1 = M["lug_tips_y"]
    xi0, xi1 = M["lug_inner_x_px"]
    out["lug"] = {"photo_tips_mm": [f(py0 - t0), f(t1 - py0)], "tip_mm": round(LISTED["lug_to_lug_mm"] / 2, 3), "inner_x_mm": f((xi1 - xi0) / 2)}
    out["checks"] = {"photo_lug_to_lug_mm": f(t1 - t0), "lug_gap_mm": f(xi1 - xi0), "listed": LISTED}

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
    for k in ("logo", "print_khaki", "date_window"):
        out[k] = box(M[k])

    j = M["bracelet_joints_y"]
    d = lambda v: abs(v[1] - v[0])
    out["bracelet_pitch_mm"] = {"outer": f((d(j["top_outer"]) + d(j["bottom_outer"])) / 2), "centre": f((d(j["top_centre"]) + d(j["bottom_centre"])) / 2)}
    out["bracelet_centre_joint_shift_mm"] = f(((j["top_outer"][0] - j["top_centre"][0]) + (j["bottom_centre"][0] - j["bottom_outer"][0])) / 2)
    c0, c1 = M["bracelet_centre_x_px"]
    out["bracelet_centre_half_mm"] = f((c1 - c0) / 2)
    out["end_link_half_mm"] = f((xi1 - xi0) / 2)
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
        sd = hands["seconds"]
        t = math.radians(sd["angle_deg"])
        cv2.line(ov, P((-sd["tail_mm"] * math.sin(t), -sd["tail_mm"] * math.cos(t))), P((sd["length_mm"] * math.sin(t), sd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        for k in ("logo", "print_khaki", "date_window"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (680, y), (1210, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "rings_mm", "lug", "checks", "crown", "bracelet_pitch_mm",
                                           "bracelet_centre_joint_shift_mm", "bracelet_centre_half_mm")}, default=float), "->", dest)
