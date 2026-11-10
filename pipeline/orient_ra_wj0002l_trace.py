"""Measure the Orient RA-WJ0002L front photo (native 1884 x 3235) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_ra_wj0002l_trace [out.json] [overlay.png]   # default config/watches/orient-ra-wj0002l-trace.json

Same method as pipeline/orient_ra_ac0q16n_trace.py. Anchor: case diameter 39.9 mm (listing, the case flank outside the bezel);
listed lug width 20 mm and lug to lug 46.5 mm are reported as checks. mm, x right, y toward 12, origin = hand pivot. Hands,
indices, date, logo, crown and bracelet joints come from gridded crops (MANUAL_PX, +-3 px = +-0.08 mm). The applied 12, 9 and 6
are traced by threshold inside their boxes and become raised polished plates; the bezel insert print stays in the photo map.
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
FRONT = ROOT / "references/orient-ra-wj0002l/front_1884x3235.jpg"
OUT = ROOT / "config/watches/orient-ra-wj0002l-trace.json"
CASE_MM = 39.9  # listing (Orient USA, most retailers): the case, the bezel sits inside it
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 46.5}

MANUAL_PX = {
    "hand_pivot": [887, 1571],
    # hour and minute: polished frame, black inside, lume; (distance from the pivot, half width) along the hand
    "hour_hand_tip": [619, 1403],
    "hour_outline_px": [[-14, 12], [220, 39]],  # root, widest; then straight to the tip
    "hour_lume_px": [[95, 12], [210, 30], [268, 0]],
    "minute_hand_tip": [1265, 1293],
    "minute_outline_px": [[-14, 10], [377, 34]],
    "minute_lume_px": [[88, 7], [370, 26], [422, 0]],
    # seconds: thin dark needle, orange from the bulb to the tip, dark counterweight with a polished rim
    "seconds_hand_tip": [1373, 1667],
    "seconds_hand_tail_end": [696, 1533],
    "seconds_hand_half_width_px": [3, 16],  # needle, counterweight
    "seconds_orange_px": [287, 14],  # bulb: distance from the pivot, radius
    "hub_radius_px": [36, 9],  # collar, cap
    "date_window": [1204, 1515, 1345, 1625],  # polished frame outer edge
    "logo": [752, 1280, 1032, 1466],  # crown emblem, ORIENT, solar-powered
    "print_wr": [735, 1740, 1045, 1850],  # Water Resistant 20 bar
    "print_6": [680, 2012, 1118, 2075],  # MOV'T JAPAN / VS42-UAB8 R 2 either side of the 6
    "numeral_12": [771, 1079, 971, 1211],
    "numeral_9": [420, 1508, 530, 1645],
    "numeral_6": [836, 1929, 952, 2067],
    "numeral_white": 150,
    "index_r_px": [388, 520],  # inner, outer end of the batons (frame outer edge)
    "index_width_px": 46,
    "frame_px": 7,  # polished rim + black edge around the lume
    "crown_box": [1592, 1465, 1762, 1684],  # collar at the case to the end of the fluted part
    "crown_collar_px": [1592, 1640, 54],  # x from, x to, radius
    # rings measured along 6 radii from the pivot (colour profiles)
    "bezel_rings_px": {"dial": 548, "crystal": 580, "insert_in": 586, "insert_out": 710, "rim_out": 726},
    "bezel_notch_count": 60,  # round dimples on the coin edge, about 75 px apart at 12
    # bracelet: three columns; centre joints nearer the case than the outer ones
    "bracelet_joints_y": {"top_outer": [690, 465, 222], "top_centre": [515, 270],
                          "bottom_outer": [2482, 2735, 2968], "bottom_centre": [2660, 2910]},
    "bracelet_centre_px": [[745, 1110], [720, 1085]],
    "end_link_x_px": [531, 1271],
}
ARTEFACTS = ["the bracelet sits about 20 px right of the case centre in the photo (slight tilt): the model is symmetric about the pivot",
             "the case notch at 9 (and the matching one under the crown) is not modelled",
             "bezel insert print (triangle, dots, numerals, bars) and the khaki colour stay in the photo map"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * math.sin(math.radians(a)), c[1] - r * math.cos(math.radians(a)))

    # case outline on the flanks (the lugs leave it above 55 / below 125 deg; the crown sits at 75-105 deg)
    edge = []
    for a in list(np.arange(58, 74.1, 1.0)) + list(np.arange(106, 122.1, 1.0)) + list(np.arange(238, 302.1, 1.0)):
        rs = np.arange(650, 850, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    rings = {k: round(v / S, 3) for k, v in M["bezel_rings_px"].items()}
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case diameter = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "bezel_offset_mm": mm((ccx, ccy)), "bezel_rings_mm": rings,
           "bezel_notches": {"count": M["bezel_notch_count"], "basis": "round dimples about 75 px apart along the coin edge at 12"}}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(18, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (24, 28, 32, 36, 40, -24, -28, -32, -36, -40) if y in width}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 2 or -tips[1] - 2 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "end_link_width_mm": round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S, 2), "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    r0, r1 = M["index_r_px"]
    out["indices"] = {"inner_mm": round(r0 / S, 3), "outer_mm": round(r1 / S, 3), "width_mm": round(M["index_width_px"] / S, 3),
                      "frame_mm": round(M["frame_px"] / S, 3),
                      "layout": "applied polished frames with lume at 1 2 4 5 7 8 10 11; applied numerals 12 9 6; date at 3"}

    pts = lambda key: [[round(a / S, 3), round(b / S, 3)] for a, b in M[key]]
    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[name + "_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r, "outline_mm": pts(name + "_outline_px"), "lume_mm": pts(name + "_lume_px")}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_half_width_px"]
    ob, orad = M["seconds_orange_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3),
                        "orange_from_mm": round(ob / S, 3), "bulb_radius_mm": round(orad / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    for k in ("date_window", "logo", "print_wr", "print_6", "crown_box", "numeral_12", "numeral_9", "numeral_6"):
        out[k] = box(M[k])
    cx0, cx1, crr = M["crown_collar_px"]
    out["crown_collar_mm"] = {"from": round((cx0 - px0) / S, 3), "to": round((cx1 - px0) / S, 3), "radius": round(crr / S, 3)}

    # applied numerals: bright polished faces inside their boxes, holes kept (9, 6)
    numerals = []
    for k in ("numeral_12", "numeral_9", "numeral_6"):
        x0, y0, x1, y1 = M[k]
        x0, y0, x1, y1 = x0 - 6, y0 - 6, x1 + 6, y1 + 6
        m = (gray[y0:y1, x0:x1] > M["numeral_white"]).astype(np.uint8) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        up = cv2.GaussianBlur(cv2.resize(m, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.6)
        to_mm = lambda p, x0=x0, y0=y0: [round((p[0] / UP + x0 - px0) / S, 3), round(-(p[1] / UP + y0 - py0) / S, 3)]
        numerals += shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 150)
    out["numerals"] = numerals

    j = M["bracelet_joints_y"]
    pitch = [abs(a - b) / S for js in j.values() for a, b in zip(js[1:], js[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.mean(pitch)), 3)
    out["bracelet_joints_mm"] = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    shift = [abs(o - c) / S for o, c in ((j["top_outer"][1], j["top_centre"][0]), (j["top_outer"][2], j["top_centre"][1]),
                                         (j["bottom_outer"][1], j["bottom_centre"][0]), (j["bottom_outer"][2], j["bottom_centre"][1]))]
    out["bracelet_centre_joint_shift_mm"] = round(float(np.mean(shift)), 3)
    out["bracelet_centre_half_mm"] = round(float(np.mean([(c[1] - c[0]) / 2 / S for c in M["bracelet_centre_px"]])), 3)
    out["end_link_half_mm"] = round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / 2 / S, 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in M["bezel_rings_px"].values():
            cv2.circle(ov, (px0, py0), int(rk), (0, 0, 255), 1)
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            tail = hd.get("tail_mm", 0)
            cv2.line(ov, P((-tail * math.sin(t), -tail * math.cos(t))), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            for r_ in (r0, r1):
                cv2.circle(ov, (int(px0 + r_ * math.sin(t)), int(py0 - r_ * math.cos(t))), 6, (255, 0, 255), 2)
        for k in ("date_window", "logo", "print_wr", "print_6", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        for sh in numerals:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 2)
        for v in j.values():
            for y in v:
                cv2.line(ov, (500, y), (1300, y), (255, 128, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_rings_mm", "lug_tip_mm", "checks", "indices", "hands",
                                           "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm", "bracelet_centre_half_mm",
                                           "end_link_half_mm", "crown_collar_mm")}, default=float), "->", dest,
          len(data["numerals"]), "numeral shapes")
