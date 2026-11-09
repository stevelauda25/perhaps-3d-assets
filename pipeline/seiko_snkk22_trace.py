"""Measure the Seiko 5 SNKK22K1 front photo (white background, 1920 x 1920) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snkk22_trace [out.json] [overlay.png]     # default config/watches/seiko-snkk22k1-trace.json

Same method as pipeline/seiko_snkl50_trace.py. Anchor: case width on the flanks = 38.0 mm (owner's spec sheet); the listed 18 mm
lug width is reported as a check against the bracelet next to the case. mm, x right, y toward 12, origin = hand pivot. Hands,
day-date, logo, crown and bracelet joints come from gridded crops (MANUAL_PX, +-3 px = +-0.12 mm); ring and index radii from
radial profiles, index widths from a cross profile at mid radius.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snkk22k1/front_1920.png"
OUT = ROOT / "config/watches/seiko-snkk22k1-trace.json"
CASE_MM = 38.0  # owner's spec sheet, 2026-11-09 (PSB Watches lists 37 mm)
LUG_WIDTH_MM = 18.0  # spec sheet
HOURS = (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12)  # the day-date replaces 3

MANUAL_PX = {
    "hand_pivot": [922, 892],
    # hour and minute: straight gold batons with a lume insert, square ends, broad short tails (the cross round the hub)
    "hour_hand_tip": [748, 761],
    "hour_hand_tail_end": [973, 929],
    "hour_hand_lume": [[860, 840], [760, 772]],
    "hour_hand_half_width_px": 12,
    "minute_hand_tip": [1170, 701],
    "minute_hand_tail_end": [873, 927],
    "minute_hand_lume": [[1000, 827], [1158, 716]],
    "minute_hand_half_width_px": 13,
    "hand_tail_half_width_px": 15,
    "seconds_hand_tip": [623, 987],
    "seconds_hand_tail_end": [1020, 862],
    "seconds_hand_half_width_px": [2, 4],  # needle, tail
    "hub_radius_px": [18, 5],  # polished cap, dark centre
    "daydate_frame": [1038, 847, 1240, 937],  # raised gold frame round both windows
    "daydate_window": [1050, 862, 1229, 925],
    "logo_seiko": [845, 705, 1005, 738],
    "logo_5_shield": [878, 745, 977, 800],
    "print_automatic_21_jewels": [830, 1055, 982, 1106],
    "print_6": [1005, 1215, 1090, 1255],  # 7S26 calibre print
    "crown_box": [1382, 1035, 1432, 1135],  # fluted crown at about 4 o'clock
    "index_width_px": {"12": 67, "6": 56, "9": 56},  # wide batons; 12 is two bars with one lume strip each
    "index_lume_px": {"12": [[900, 918], [928, 947]], "6": [910, 940], "9": [877, 910]},
    # bracelet, row at y = 230 px: top surface edges (the right flank shows to 1206), centre, narrow polished strips
    "bracelet_row_230": {"edges": [687, 1187], "centre": [845, 1025], "strips": [[810, 845], [1025, 1064]]},
    # first outer joints next to the case: foreshortened at the top, stretched at the bottom, so the pitch is their mean
    "bracelet_joints_y": {"outer_top": [152, 290], "outer_bottom": [1500, 1695]},
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "the photo is 1920 px: the dial is about 750 px across, small print soft",
             "the bracelet sits about 15 px right of the pivot (watch slightly turned): the build centres it",
             "the bracelet curves away at the top and toward the camera at the bottom: link rows are foreshortened differently"]


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
    for a in list(np.arange(62, 98.1, 1.0)) + list(np.arange(242, 298.1, 1.0)):
        rs = np.arange(380, 560, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    # crystal ring: the thin dark gasket line between the gold rehaut (from about 13.7 mm) and the gold bezel; rays between the
    # indices, skipping the day-date and crown side
    ring = []
    for a in np.arange(0, 360, 1.0):
        if 70 <= a <= 125 or abs((a + 15) % 30 - 15) < 9:
            continue
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(385, 415, 0.5)]
        ring.append(at(385 + 0.5 * int(np.argmin(prof)), a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (spec sheet); lug width {LUG_WIDTH_MM} mm (spec sheet) as a check",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "dark gasket line inside the gold bezel"}}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(15, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 3 or -tips[1] - 3 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "listed_lug_width_mm": LUG_WIDTH_MM}

    # indices: longest lit run along each hour ray (gold frame and lume are brighter than the black dial); width and lume
    # width from a cross profile at mid length (lume is the brightest part)
    idx = {}
    for hr in HOURS:
        p = [g[int(at(r, hr * 30)[1]), int(at(r, hr * 30)[0])] for r in range(150, 350)]
        lit = [i for i, v in enumerate(p) if v > 110]
        runs, s = [], lit[0]
        for a_, b_ in zip(lit, lit[1:] + [None]):
            if b_ is None or b_ > a_ + 3:  # small gaps: the dark facet of the ridge
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t: t[1] - t[0])
        rm, t_ = 150 + (r0 + r1) / 2, math.radians(hr * 30)
        cross = np.array([g[int(round(at(rm, hr * 30)[1] + k * math.sin(t_))), int(round(at(rm, hr * 30)[0] + k * math.cos(t_)))]
                          for k in np.arange(-45, 45.1, 0.5)])
        run = lambda thr: 0.5 * len(np.nonzero(cross > thr)[0])
        idx[str(hr)] = {"inner": round((150 + r0) / S, 3), "outer": round((150 + r1) / S, 3),
                        "width_mm": round(run(110) / S, 3), "lume_width_mm": round(run(185) / S, 3)}
    out["indices"] = {"per_hour_mm": idx,
                      "inner_mm": round(float(np.median([v["inner"] for k, v in idx.items() if k != "12"])), 3),
                      "outer_mm": round(float(np.median([v["outer"] for k, v in idx.items() if k != "12"])), 3),
                      "width_mm": round(float(np.median([v["width_mm"] for k, v in idx.items() if k not in M["index_width_px"]])), 3),
                      "lume_width_mm": round(float(np.median([v["lume_width_mm"] for k, v in idx.items() if k not in M["index_width_px"]])), 3),
                      "wide_mm": {k: round(v / S, 3) for k, v in M["index_width_px"].items()},
                      "wide_lume_mm": {"12": [[round((a - px0) / S, 3), round((b - px0) / S, 3)] for a, b in M["index_lume_px"]["12"]],
                                       "6": round((M["index_lume_px"]["6"][1] - M["index_lume_px"]["6"][0]) / S, 3),
                                       "9": round((M["index_lume_px"]["9"][1] - M["index_lume_px"]["9"][0]) / S, 3)},
                      "layout": "applied polished gold frames with a white lume insert; wide at 6 and 9; two bars at 12; none at 3 (day-date)"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3), "broad_tail_half_width_mm": round(M["hand_tail_half_width_px"] / S, 3),
                       "lume_from_to_mm": sorted(polar(p)[0] for p in M[f"{name}_hand_lume"])}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_half_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "daydate_window", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6", "crown_box"):
        out[k] = box(M[k])

    row = M["bracelet_row_230"]
    c, hw = sum(row["edges"]) / 2, (row["edges"][1] - row["edges"][0]) / 2
    f = lambda x: round(abs(x - c) / hw, 3)
    out["bracelet_columns"] = {"centre_half": round((f(row["centre"][0]) + f(row["centre"][1])) / 2, 3),
                               "strip_outer": round((f(row["strips"][0][0]) + f(row["strips"][1][1])) / 2, 3),
                               "basis": "fractions of the bracelet half width, row at y = 230 px"}
    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.mean([(b - a) / S for a, b in j.values()])), 3)
    out["bracelet_centre_phase"] = 0.5  # photo: centre joints about half a row off the outer joints (0.57 bottom, 0.63 top, foreshortened)
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
        for k in ("daydate_frame", "daydate_window", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6", "crown_box"):
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
