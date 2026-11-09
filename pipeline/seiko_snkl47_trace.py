"""Measure the Seiko 5 SNKL47K1 front photo, straightened by pipeline/seiko_snkl47_rectify.py, into mm. Host-side, numpy +
OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snkl47_rectify          # first: outputs/watches/seiko-snkl47k1/front_rectified.png
    python3 -B -m pipeline.seiko_snkl47_trace [out.json] [overlay.png]     # default config/watches/seiko-snkl47k1-trace.json

Same method as pipeline/seiko_snkl50_trace.py. Anchor: case width on the left flank = 36.9 mm (spec sheet); the case is taken
as concentric with the crystal ring (the right flank shows the case side and crown). The listed 19 mm lug width is reported as
a check. mm, x right, y toward 12, origin = hand pivot. Hands, day-date, logo, crown and bracelet come from gridded crops
(MANUAL_PX, +-3 px = +-0.1 mm); ring and index radii from radial profiles.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "outputs/watches/seiko-snkl47k1/front_rectified.png"
OUT = ROOT / "config/watches/seiko-snkl47k1-trace.json"
CASE_MM = 36.9  # owner's spec sheet, 2026-11-09 (listings: 37 mm)
LUG_WIDTH_MM = 19.0  # spec sheet

MANUAL_PX = {
    "hand_pivot": [1379, 1387],
    # hour and minute: gold dauphine blades with a cream lume strip down the middle, short pointed tails round the hub
    "hour_hand_tip": [1165, 1237],
    "hour_hand_tail_end": [1445, 1430],
    "hour_hand_lume": [[1340, 1360], [1195, 1258]],
    "hour_hand_half_width_px": 20,  # widest point of the blade
    "minute_hand_tip": [1700, 1156],
    "minute_hand_tail_end": [1318, 1437],
    "minute_hand_lume": [[1430, 1350], [1660, 1185]],
    "minute_hand_half_width_px": 17,
    "seconds_hand_tip": [1378, 958],
    "seconds_hand_tail_end": [1379, 1541],
    "seconds_hand_half_width_px": [2, 9],  # needle, wide gold counterweight bar
    "hub_radius_px": [15, 4],  # polished cap, dark centre
    "daydate_frame": [1552, 1355, 1782, 1422],  # thin silver frame round both windows
    "marker_3": [1793, 1373, 1819, 1403],  # printed black square outside the day-date (stays in the dial map)
    "logo_seiko": [1290, 1180, 1492, 1225],
    "logo_5_shield": [1330, 1232, 1442, 1302],
    "print_automatic_21_jewels": [1300, 1532, 1478, 1592],
    "print_6": [1318, 1824, 1462, 1848],
    "crown_box": [1900, 1590, 1990, 1700],  # gold fluted crown at about 4 o'clock
    "index_width_px": [26, 26],  # single baton, the same at 12
    "index_ring_px": 12,  # small grey ring at the inner end of each baton (lume pip), radius
    # bracelet, rows next to the case: top surface edges, centre column, gold strips (centre shifted by parallax)
    "bracelet_row_560": {"edges": [1118, 1750], "centre": [1322, 1547], "strips": [[1280, 1322], [1547, 1586]]},
    "bracelet_joints_y": {"top": [415, 572], "bottom": [2061, 2236]},
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "straightened from a photo turned toward the crown: bezel, case and bracelet stand off the dial plane and keep some parallax; the bracelet centre sits about 55 px right of the pivot at the top",
             "the photo looks upscaled from about 1000 px: small print soft"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 2)
    fg = (765 - im.astype(int).sum(2)) > 45
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # case outline on the flanks: lugs leave the case above 60 / below 120 deg, the crown sits at 100-125 deg
    edge = []
    for a in list(np.arange(242, 298.1, 1.0)):  # left flank only: the right one shows the case side
        rs = np.arange(500, 700, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    # crystal ring: the dark gasket line between the dial rehaut and the polished bezel, skipping the day-date and crown side
    ring = []
    for a in np.arange(0, 360, 2.0):
        if 70 <= a <= 135:
            continue
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(468, 492, 0.5)]
        ring.append(at(468 + 0.5 * int(np.argmin(prof)), a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    ccx, ccy = rcx, rcy  # a 56 deg arc cannot fix a centre: the case is concentric with the crystal ring
    case_r = float(np.median(np.hypot(*(np.array(edge) - (ccx, ccy)).T)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the left flank = {CASE_MM} mm (spec sheet); lug width {LUG_WIDTH_MM} mm (spec sheet) as a check",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "dark gasket line inside the polished bezel"}}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                l_ = round((xs.min() - ccx) / S, 3)  # left side mirrored: the right side shows the case flank and clasp
                prof.append([round(float(y_mm), 2), l_, -l_])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(15, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 3 or -tips[1] - 3 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "listed_lug_width_mm": LUG_WIDTH_MM}

    # indices: longest gold run along each hour ray (saturated against the white dial), +-2 deg for parallax
    sat = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[..., 1].astype(float), (0, 0), 1.5)
    idx = {}
    for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        p = [max(sat[int(at(r, hr * 30 + d)[1]), int(at(r, hr * 30 + d)[0])] for d in np.arange(-2, 2.1, 0.5)) for r in range(270, 460)]
        lit = [i for i, v in enumerate(p) if v > 90]
        runs, s = [], lit[0]
        for a_, b_ in zip(lit, lit[1:] + [None]):
            if b_ is None or b_ > a_ + 3:  # small gaps: the dark facet of the ridge
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t: t[1] - t[0])
        idx[str(hr)] = {"inner": round((270 + r0) / S, 3), "outer": round((270 + r1) / S, 3)}
    out["indices"] = {"per_hour_mm": idx,
                      "inner_mm": round(float(np.median([v["inner"] for k, v in idx.items() if k != "12"])), 3),
                      "outer_mm": round(float(np.median([v["outer"] for k, v in idx.items() if k != "12"])), 3),
                      "width_mm": round(M["index_width_px"][0] / S, 3), "width_12_mm": round(M["index_width_px"][1] / S, 3),
                      "ring_radius_mm": round(M["index_ring_px"] / S, 3),
                      "layout": "applied gold batons with a lengthwise ridge and a small grey ring at the inner end; single at 12; none at 3 (day-date and a printed black square)"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3),
                       "lume_from_to_mm": sorted(polar(p)[0] for p in M[f"{name}_hand_lume"])}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_half_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "marker_3", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6", "crown_box"):
        out[k] = box(M[k])

    row = M["bracelet_row_560"]
    c, hw = sum(row["edges"]) / 2, (row["edges"][1] - row["edges"][0]) / 2
    f = lambda x: round(abs(x - c) / hw, 3)
    out["bracelet_columns"] = {"centre_half": round((f(row["centre"][0]) + f(row["centre"][1])) / 2, 3),
                               "strip_outer": round((f(row["strips"][0][0]) + f(row["strips"][1][1])) / 2, 3),
                               "basis": "fractions of the bracelet half width, row at y = 560 px"}
    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.mean([(b - a) / S for a, b in j.values()])), 3)
    out["bracelet_centre_phase"] = 0.5  # photo: centre joints about half a row off the outer joints
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 0, 255), 4)
        cv2.circle(ov, (int(rcx), int(rcy)), int(rr), (255, 128, 0), 4)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, P((-hd["tail_mm"] * math.sin(t), -hd["tail_mm"] * math.cos(t))),
                     P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 3)
        for hr, v in idx.items():
            t = math.radians(int(hr) * 30)
            for r_ in (v["inner"], v["outer"]):
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 8, (255, 0, 255), 3)
        for k in ("daydate_frame", "marker_3", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "lug_tip_mm", "checks", "indices", "hands",
                                           "bracelet_columns", "bracelet_pitch_mm", "bracelet_centre_phase")}, default=float), "->", dest)
