"""Measure the Orient FAA02004B9 (Ray II) front photo (native 1811 x 2956) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_faa02004b9_trace [out.json] [overlay.png]   # default config/watches/orient-faa02004b9-trace.json

Same method as pipeline/orient_ra_ac0q16n_trace.py. Anchor: bezel diameter 41.5 mm (listing, the bezel is the widest part);
listed lug width 22 mm and lug to lug 47 mm are reported as checks. mm, x right, y toward 12, origin = hand pivot. Hands,
indices, day-date, logo, crown, crown guards and bracelet joints come from gridded and hand-rotated crops (MANUAL_PX,
+-3 px = +-0.08 mm). Hand and lume outlines are half-width profiles: [distance from the pivot, half width] in px, mirrored.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-faa02004b9/front_1811x2956.jpg"
OUT = ROOT / "config/watches/orient-faa02004b9-trace.json"
CASE_MM = 41.5  # listing (Orient USA, Serious Watches): without the crown
LISTED = {"lug_width_mm": 22.0, "lug_to_lug_mm": 47.0}

MANUAL_PX = {
    "hand_pivot": [874, 1476],
    # hour: polished frame, black inside, arrow-head lume over a smaller lume block, needle tip
    "hour": {"angle_deg": 304.0, "outline": [[-14, 12], [35, 14], [55, 32], [112, 32], [122, 41], [222, 46], [266, 4], [308, 0]],
             "lume": [[[138, 0], [128, 37], [215, 39], [262, 0]], [[64, 26], [118, 26], [126, 0]]]},
    # minute: sword, polished frame, black inside, lume blade
    "minute": {"angle_deg": 54.4, "outline": [[-14, 22], [70, 25], [350, 31], [445, 0]], "lume": [[[88, 19], [355, 20], [425, 0]]]},
    # seconds: polished needle and tail, hollow red arrow near the tip
    "seconds": {"angle_deg": 91.0, "length_px": 448, "tail_px": 182, "half_px": [2.5, 5], "arrow_px": [305, 430, 17, 4]},
    "hub_radius_px": [30, 9],  # collar, cap
    "daydate": [1027, 1417, 1317, 1525], "daydate_divider_x": 1195,  # polished frame outer edge, bar between day and date
    "logo": [715, 1200, 985, 1385],  # crown emblem, ORIENT, Automatic
    "print_wr": [735, 1630, 960, 1700],  # Water Resist 200m
    "print_6": [720, 1915, 1040, 1965],  # JAPAN MOV'T TH AA02-000-B T
    # applied polished frames with lume: dots, a trapezoid at 12, tapered bars at 6 and 9 ([r, half] outer and inner end)
    "dot_px": [413.5, 46.5, 36.5],  # centre r, frame radius, lume radius
    "index_12_px": {"frame": [[337, 27], [457, 66]], "lume": [[347, 22], [447, 54]]},
    "index_bar_px": {"frame": [[347, 32], [462, 40]], "lume": [[352, 22], [452, 30]]},
    "crown_box": [1600, 1372, 1728, 1588],  # fluted part, between the guards
    "crown_collar_px": [1560, 1602, 70],  # x from, x to, radius
    "crown_guard_px": [[1540, 1285], [1640, 1300], [1692, 1335], [1703, 1375], [1703, 1590], [1692, 1640], [1640, 1668], [1540, 1680]],
    # rings measured along 6 radii from the pivot (colour profiles)
    "bezel_rings_px": {"dial": 474, "crystal": 550, "insert_in": 572},  # about the pivot; insert_out and rim_out: fitted,
    "bezel_notch_count": 60,  # half-moon recesses on the steel ring, about 72 px apart at 8 o'clock
    # bracelet: three columns, the centre one with polished strips at its edges; centre joints nearer the case
    "bracelet_joints_y": {"top_outer": [640, 415, 210], "top_centre": [490, 280],
                          "bottom_outer": [2340, 2560, 2772], "bottom_centre": [2490, 2690]},
    "bracelet_centre_px": [[785, 990], [790, 995]],  # brushed centre
    "bracelet_narrow_px": [[735, 1045], [735, 1050]],  # outer edge of the polished strips
    "end_link_x_px": [497, 1258],
}
ARTEFACTS = ["the bracelet sits about 18 px right of the pivot (slight tilt): the model is symmetric about the pivot",
             "the minute track, the sloped chapter ring and the insert print stay in the photo map",
             "the half-moon recesses on the steel bezel ring are modelled as notches on its edge"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # bezel centre from the black insert's outer edge (insert -> bright steel), radius from the 9 o'clock edge on that row
    #   (the crown guards and lugs cover the rest of the outline)
    edge = []
    for a in np.arange(0, 360, 3.0):
        rs = np.arange(640, 700, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        v = gray[ys.astype(int), xs.astype(int)]
        k = np.nonzero(v > 120)[0]
        if len(k) and k[0] > 4 and (v[:k[0]] < 70).mean() > 0.8:  # skip angles where white print touches the edge
            edge.append((xs[k[0]], ys[k[0]]))
    e = np.array(edge)
    ccx, ccy, ins_r = fit_circle(e)
    e = e[np.abs(np.hypot(e[:, 0] - ccx, e[:, 1] - ccy) - ins_r) < 4]
    ccx, ccy, ins_r = fit_circle(e)
    case_r = ccx - np.nonzero(fg[int(round(ccy))])[0].min()
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    rings = {k: round(v / S, 3) for k, v in M["bezel_rings_px"].items()}
    rings.update(insert_out=round(ins_r / S, 3), rim_out=round(case_r / S, 3))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"bezel diameter = {CASE_MM} mm (listing), centre from the insert edge, radius at 9 o'clock",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy)), "insert_edge_points": len(e),
                    "insert_out_mm": round(ins_r / S, 3)},
           "bezel_offset_mm": mm((ccx, ccy)),
           "bezel_rings_mm": rings,
           "bezel_notches": {"count": M["bezel_notch_count"], "basis": "about 72 px apart along the ring at 8 o'clock"}}

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
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 2 or -tips[1] - 2 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "end_link_width_mm": round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S, 2), "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    s = lambda pts: [[round(a / S, 3), round(b / S, 3)] for a, b in pts]
    cr, fr, lr = M["dot_px"]
    out["indices"] = {"dot_mm": [round(cr / S, 3), round(fr / S, 3), round(lr / S, 3)],
                      "index_12_mm": {k: s(v) for k, v in M["index_12_px"].items()},
                      "index_bar_mm": {k: s(v) for k, v in M["index_bar_px"].items()},
                      "layout": "dots at 1 2 4 5 7 8 10 11, trapezoid at 12, tapered bars at 6 and 9, day-date at 3"}

    hands = {}
    for name in ("hour", "minute"):
        hd = M[name]
        hands[name] = {"angle_deg": hd["angle_deg"], "length_mm": round(hd["outline"][-1][0] / S, 3), "outline_mm": s(hd["outline"]),
                       "lume_mm": [s(lp) for lp in hd["lume"]]}
    sd = M["seconds"]
    a0, a1, ah, aw = sd["arrow_px"]
    hands["seconds"] = {"angle_deg": sd["angle_deg"], "length_mm": round(sd["length_px"] / S, 3), "tail_mm": round(sd["tail_px"] / S, 3),
                        "half_width_mm": round(sd["half_px"][0] / S, 3), "tail_half_width_mm": round(sd["half_px"][1] / S, 3),
                        "arrow_mm": [round(a0 / S, 3), round(a1 / S, 3), round(ah / S, 3), round(aw / S, 3)]}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    for k in ("daydate", "logo", "print_wr", "print_6", "crown_box"):
        out[k] = box(M[k])
    out["daydate_divider_x_mm"] = round((M["daydate_divider_x"] - px0) / S, 3)
    cx0, cx1, crr = M["crown_collar_px"]
    out["crown_collar_mm"] = {"from": round((cx0 - px0) / S, 3), "to": round((cx1 - px0) / S, 3), "radius": round(crr / S, 3)}
    out["crown_guard_mm"] = [mm(p) for p in M["crown_guard_px"]]

    j = M["bracelet_joints_y"]
    pitch = [abs(a - b) / S for js in j.values() for a, b in zip(js[1:], js[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.mean(pitch)), 3)
    out["bracelet_joints_mm"] = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    shift = [abs(o - c) / S for o, c in ((j["top_outer"][1], j["top_centre"][0]), (j["top_outer"][2], j["top_centre"][1]),
                                         (j["bottom_outer"][1], j["bottom_centre"][0]), (j["bottom_outer"][2], j["bottom_centre"][1]))]
    out["bracelet_centre_joint_shift_mm"] = round(float(np.mean(shift)), 3)
    half = lambda k: round(float(np.mean([(c[1] - c[0]) / 2 / S for c in M[k]])), 3)
    out["bracelet_centre_half_mm"], out["bracelet_narrow_half_mm"] = half("bracelet_centre_px"), half("bracelet_narrow_px")
    out["end_link_half_mm"] = round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / 2 / S, 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in M["bezel_rings_px"].values():
            cv2.circle(ov, (px0, py0), int(rk), (0, 0, 255), 1)
        cv2.circle(ov, (int(ccx), int(ccy)), int(ins_r), (0, 0, 255), 1)
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for name in ("hour", "minute"):
            hd = hands[name]
            t = math.radians(hd["angle_deg"])
            pts = [(hh, r) for r, hh in hd["outline_mm"]] + [(-hh, r) for r, hh in hd["outline_mm"][::-1]]
            cv2.polylines(ov, [np.array([P((x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))) for x, y in pts], np.int32)],
                          True, (0, 255, 255), 2)
        t = math.radians(hands["seconds"]["angle_deg"])
        L, tl = hands["seconds"]["length_mm"], hands["seconds"]["tail_mm"]
        cv2.line(ov, P((-tl * math.sin(t), -tl * math.cos(t))), P((L * math.sin(t), L * math.cos(t))), (0, 255, 255), 2)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            cv2.circle(ov, (int(px0 + cr * math.sin(t)), int(py0 - cr * math.cos(t))), int(fr), (255, 0, 255), 2)
        for k in ("daydate", "logo", "print_wr", "print_6", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        cv2.polylines(ov, [np.array(M["crown_guard_px"], np.int32)], True, (255, 255, 0), 2)
        for v in j.values():
            for y in v:
                cv2.line(ov, (480, y), (1280, y), (255, 128, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_rings_mm", "lug_tip_mm", "checks", "bracelet_pitch_mm",
                                           "bracelet_centre_joint_shift_mm", "bracelet_centre_half_mm", "bracelet_narrow_half_mm",
                                           "end_link_half_mm", "crown_collar_mm")}, default=float), "->", dest)
