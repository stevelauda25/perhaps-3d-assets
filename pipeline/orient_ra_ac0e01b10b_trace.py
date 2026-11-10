"""Measure the Orient RA-AC0E01B10B front photo (Orient USA product image, 2x working copy on white, 3200 x 2134) into mm.
Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_ra_ac0e01b10b_trace [out.json] [overlay.png]   # default config/watches/orient-ra-ac0e01b10b-trace.json

Same method as pipeline/orient_ra_ac0q17y_trace.py. Anchor: case diameter 40 mm across the flanks (dealer listings); the
lug to lug 46.1 mm of the AC0E family is reported as a check. mm, x right, y toward 12, origin = hand pivot. Hands, batons,
rings, date, logo, crown and bracelet joints come from gridded crops (MANUAL_PX, +-3 px of the 2x copy = +-0.1 mm).
The photo is shot a little from below (the case flank shows under 6 o'clock): lug tips are averaged top and bottom, and the
bracelet pitch is read on the 6 o'clock side only (the 12 o'clock side leans away).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-ra-ac0e01b10b/front_2x_white_3200x2134.png"
OUT = ROOT / "config/watches/orient-ra-ac0e01b10b-trace.json"
CASE_MM = 40.0  # listing (watch.co.uk, mastersintime)
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 46.1}

MANUAL_PX = {
    "hand_pivot": [1595, 950],
    # hour and minute: polished sticks with a centre ridge, pointed tips, short tails
    "hour_hand_tip": [1310, 762],
    "hour_half_width_px": [14, 11],  # at the collar, near the tip
    "minute_hand_tip": [1958, 655],
    "minute_half_width_px": [12, 9],
    "hand_tail_px": 40,
    # seconds: polished needle, short counterweight
    "seconds_hand_tip": [1288, 1358],
    "seconds_hand_tail_end": [1662, 850],
    "seconds_half_width_px": [3, 10],  # needle, counterweight (widest at its end)
    "hub_radius_px": [30, 12],  # collar, cap
    "date_window": [1878, 918, 1992, 1002],
    "logo": [1490, 640, 1705, 795],  # emblem, ORIENT, Automatic
    "print_6": [1330, 1425, 1860, 1495],  # MOV'T JAPAN, movement print
    "index_r_px": [360, 520],  # inner, outer end of the batons
    "index_3_r_px": [412, 529],  # starts further out, beside the date
    "index_width_px": 26,
    "crown_box": [2222, 880, 2300, 1055],  # case to the end of the crown
    "rings_px": {"dial": 568, "crystal": 595},  # dial flat edge, inner edge of the polished bezel
    # bracelet: three columns; centre joints nearer the case than the outer ones (6 o'clock side, which faces the camera)
    "bracelet_joints_y": {"bottom_outer": [1745, 1958], "bottom_centre": [1690, 1900]},
    "bracelet_centre_x": [1432, 1757],
    "end_link_x_px": [1282, 1915],
}
ARTEFACTS = ["the photo is 1600 x 1067 (about 16 px/mm); the 2x copy adds no detail",
             "transparent PNG flattened onto white; the bracelet runs out of the frame at both ends",
             "shot a little from below: the 12 o'clock bracelet and lugs look shorter than the 6 o'clock ones"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * math.sin(math.radians(a)), c[1] - r * math.cos(math.radians(a)))

    # case outline on the flanks (lugs leave it above 60 / below 120 deg; the crown sits at 80-100 deg)
    edge = []
    for a in list(np.arange(62, 76.1, 1.0)) + list(np.arange(104, 118.1, 1.0)) + list(np.arange(242, 298.1, 1.0)):
        rs = np.arange(560, 720, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case diameter = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "rings_mm": {k: round(v / S, 3) for k, v in M["rings_px"].items()}}

    prof = []
    for y_mm in np.arange(-34, 30.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(19, 27, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    near = [width[y] for y in width if -tips[1] - 2 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "end_link_width_mm": round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S, 2), "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    r0, r1 = M["index_r_px"]
    out["indices"] = {"inner_mm": round(r0 / S, 3), "outer_mm": round(r1 / S, 3), "width_mm": round(M["index_width_px"] / S, 3),
                      "at_3": [round(v / S, 3) for v in M["index_3_r_px"]],
                      "layout": "applied polished batons with a centre ridge at every hour; the 3 starts further out beside the date"}
    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[name + "_hand_tip"])
        w0, w1 = M[name + "_half_width_px"]
        hands[name] = {"angle_deg": a, "length_mm": r, "half_width_mm": [round(w0 / S, 3), round(w1 / S, 3)], "tail_mm": round(M["hand_tail_px"] / S, 3)}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_half_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    for k in ("date_window", "logo", "print_6", "crown_box"):
        out[k] = box(M[k])

    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.mean([abs(v[1] - v[0]) for v in j.values()])) / S, 3)
    out["bracelet_joints_mm"] = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    out["bracelet_centre_joint_shift_mm"] = round(float(np.mean([a_ - b_ for a_, b_ in zip(j["bottom_outer"], j["bottom_centre"])])) / S, 3)
    cx = M["bracelet_centre_x"]
    out["bracelet_centre_half_mm"] = round((cx[1] - cx[0]) / 2 / S, 3)
    out["end_link_half_mm"] = round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / 2 / S, 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for rk in M["rings_px"].values():
            cv2.circle(ov, (px0, py0), int(rk), (0, 0, 255), 1)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            tail = hd.get("tail_mm", 0)
            cv2.line(ov, P((-tail * math.sin(t), -tail * math.cos(t))), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            a0, a1 = M["index_3_r_px"] if hr == 3 else (r0, r1)
            cv2.line(ov, (int(px0 + a0 * math.sin(t)), int(py0 - a0 * math.cos(t))), (int(px0 + a1 * math.sin(t)), int(py0 - a1 * math.cos(t))), (255, 0, 255), 2)
        for k in ("date_window", "logo", "print_6", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        for v in j.values():
            for y in v:
                cv2.line(ov, (1250, y), (1950, y), (255, 128, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "rings_mm", "lug_tip_mm", "checks", "indices", "hands",
                                           "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm", "bracelet_centre_half_mm",
                                           "end_link_half_mm")}, default=float), "->", dest)
