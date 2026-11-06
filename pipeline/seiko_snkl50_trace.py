"""Measure the Seiko 5 SNKL50K1 front photo (white background, 4520 x 4520) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snkl50_trace [out.json] [overlay.png]     # default config/watches/seiko-snkl50k1-trace.json

Same method as pipeline/seiko_sur419_trace.py. Anchor: case width on the flanks = 35.0 mm (Irsyad); the listed 18 mm lug width
is reported as a check against the bracelet next to the case. mm, x right, y toward 12, origin = hand pivot. Hands, day-date,
logo, crown and bracelet joints come from gridded crops (MANUAL_PX, +-5 px = +-0.08 mm); ring and index radii from radial profiles.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snkl50k1/front_4520.png"
OUT = ROOT / "config/watches/seiko-snkl50k1-trace.json"
CASE_MM = 35.0  # Irsyad, 2026-11-06 (listings: 37 and 36.5 mm)
LUG_WIDTH_MM = 18.0  # listing

MANUAL_PX = {
    "hand_pivot": [2258, 2120],
    # hour and minute: dauphine blades with a lume insert and a short pointed tail (the "star" round the hub)
    "hour_hand_tip": [1890, 1862],
    "hour_hand_tail_end": [2365, 2200],
    "hour_hand_lume": [[2178, 2066], [2060, 1985]],
    "hour_hand_half_width_px": 36,  # widest point of the blade
    "minute_hand_tip": [2785, 1700],
    "minute_hand_tail_end": [2145, 2205],
    "minute_hand_lume": [[2365, 2010], [2530, 1900]],
    "minute_hand_half_width_px": 27,
    "seconds_hand_tip": [1829, 2727],
    "seconds_hand_tail_end": [2407, 1902],
    "seconds_hand_half_width_px": [5, 14],  # needle, counterweight
    "hub_radius_px": [35, 12],  # polished ring, dark centre
    "daydate_frame": [2514, 2044, 2950, 2206],  # dark raised border round both windows
    "marker_3": [2955, 2103, 3000, 2148],  # applied gold square outside the day-date
    "logo_seiko": [2075, 1765, 2425, 1842],
    "logo_5_shield": [2150, 1855, 2360, 1978],
    "print_automatic_21_jewels": [2105, 2385, 2420, 2490],
    "print_6": [2130, 2850, 2390, 2890],
    "crown_box": [3195, 2410, 3305, 2665],  # fluted crown at about 4 o'clock
    "index_width_px": [45, 75],  # single baton, double at 12
    # bracelet, row at y = 500 px: outer edges, then centre and the narrow polished strips
    "bracelet_row_500": {"edges": [1693, 2764], "centre": [2043, 2421], "strips": [[1964, 2036], [2429, 2507]]},
    "bracelet_joints_y": {"outer": [614, 993], "centre": [443, 800]},
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "the photo looks upscaled: small print is soft",
             "the bracelet sits about 30 px left of the pivot at the top (watch slightly turned): the build centres it"]


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
        rs = np.arange(850, 1300, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    # crystal ring: last dark pixel (gasket) moving outward from the dial, skipping the day-date and crown side
    ring = []
    for a in np.arange(0, 360, 2.0):
        if 70 <= a <= 125:
            continue
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in range(700, 900)]
        gold = next((i for i, v in enumerate(prof) if v > 120 and i > 20 and min(prof[i - 20:i]) < 45), None)
        if gold is not None:
            ring.append(at(700 + gold, a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (Irsyad); lug width {LUG_WIDTH_MM} mm (listing) as a check",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "inner edge of the gold bezel after the dark gasket"}}

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

    # indices: longest lit run along each hour ray (gold batons are brighter than the black dial)
    idx = {}
    for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        p = [g[int(at(r, hr * 30)[1]), int(at(r, hr * 30)[0])] for r in range(380, 800)]
        lit = [i for i, v in enumerate(p) if v > 110]
        runs, s = [], lit[0]
        for a_, b_ in zip(lit, lit[1:] + [None]):
            if b_ is None or b_ > a_ + 3:  # small gaps: the dark facet of the ridge
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t: t[1] - t[0])
        idx[str(hr)] = {"inner": round((380 + r0) / S, 3), "outer": round((380 + r1) / S, 3)}
    out["indices"] = {"per_hour_mm": idx,
                      "inner_mm": round(float(np.median([v["inner"] for k, v in idx.items() if k != "12"])), 3),
                      "outer_mm": round(float(np.median([v["outer"] for k, v in idx.items() if k != "12"])), 3),
                      "width_mm": round(M["index_width_px"][0] / S, 3), "width_12_mm": round(M["index_width_px"][1] / S, 3),
                      "layout": "applied gold batons with a lengthwise ridge (the light ends are reflections, not lume; Irsyad); double at 12; a gold square at 3 beside the day-date"}

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

    row = M["bracelet_row_500"]
    c, hw = sum(row["edges"]) / 2, (row["edges"][1] - row["edges"][0]) / 2
    f = lambda x: round(abs(x - c) / hw, 3)
    out["bracelet_columns"] = {"centre_half": round((f(row["centre"][0]) + f(row["centre"][1])) / 2, 3),
                               "strip_outer": round((f(row["strips"][0][0]) + f(row["strips"][1][1])) / 2, 3),
                               "basis": "fractions of the bracelet half width, row at y = 500 px"}
    j = M["bracelet_joints_y"]
    pitch = [(a - b) / S for js in j.values() for a, b in zip(js[1:], js[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.median(pitch)), 3)
    out["bracelet_centre_phase"] = round(float(np.mean([((o - cj) / S / out["bracelet_pitch_mm"]) % 1
                                                        for o, cj in zip(j["outer"], j["centre"])])), 3)
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
