"""Measure the Seiko 5 SNK361K1 front photo (white background, 3170 x 6256) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snk361_trace [out.json] [overlay.png]     # default config/watches/seiko-snk361k1-trace.json

Same method as pipeline/seiko_trace.py (SNK607K1). Anchor: case width on the flanks = 36.0 mm (Irsyad); no verified
bracelet width to cross-check, so the measured width next to the case is reported only. mm, x right, y toward 12, origin =
hand pivot. The dial is plain black, so index and ring radii are read from radial profiles; hands, day-date, logo, crown and bracelet columns from gridded crops (MANUAL_PX, +-8 px = +-0.1 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snk361k1/front_3170x6256.png"
OUT = ROOT / "config/watches/seiko-snk361k1-trace.json"
CASE_MM = 36.0  # Irsyad, 2026-11-05
BRACELET_MM = None  # no verified listing

MANUAL_PX = {
    "hand_pivot": [1563, 3136],
    "hour_hand_tip": [1062, 2791],
    "hour_hand_tail_end": [1702, 3232],
    "hour_hand_lume": [[1143, 2839], [1320, 2975]],
    "hour_hand_width_px": [85, 102],  # blade, tail (outer edges of the polished outline)
    "minute_hand_tip": [2142, 2434],
    "minute_hand_tail_end": [1452, 3267],
    "minute_hand_lume": [[1809, 2845], [2095, 2488]],
    "minute_hand_width_px": [76, 96],
    "seconds_hand_tip": [1416, 2230],
    "seconds_hand_tail_end": [1615, 3493],
    "seconds_hand_width_px": [24, 52],  # blade, end of the tail paddle
    "hub_radius_px": [56, 26],  # polished ring, cap
    "daydate_frame": [1914, 3026, 2497, 3228],
    "logo_seiko": [1329, 2559, 1789, 2649],
    "logo_5_shield": [1440, 2702, 1585, 2815],
    "print_automatic_21_jewels": [1369, 3535, 1779, 3660],
    "crown_box": [2833, 3537, 2973, 3756],  # knurled crown at about 4 o'clock
    "index_width_px": [62, 154],  # single baton, double baton at 12
    "end_link_x_px": [890, 2245],  # between the lugs
    # bracelet, row at y = 1160: outer edges, then the three inner columns (mid, centre, mid)
    "bracelet_row_1160": {"edges": [984, 2202], "columns": [[1303, 1484], [1506, 1687], [1709, 1890]]},
    "bracelet_joints_y": {"outer_centre": [297, 652, 1087, 1508], "mid": [478, 899, 1320]},
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "the seconds hand crosses the SEIKO letters and the 5 shield, so both stay in the dial map (inpainted under the hand), not geometry"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 2)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # case outline on the flanks only: the lugs flare in above 80 / below 100 deg, the crown sits at 100-130 deg
    edge = []
    for a in list(np.arange(80, 100.1, 1.0)) + list(np.arange(260, 280.1, 1.0)):
        rs = np.arange(1200, 1550, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    edge = np.array(edge)
    # bezel inner edge: first bright pixel after the dark gasket, moving outward from the dial edge
    ring, dial_edge = [], []
    for a in np.arange(0, 360, 2.0):
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(1010, 1250, 1.0)]
        first = next(i for i, v in enumerate(prof) if v > 120)
        dark = next(i for i in range(first, len(prof)) if prof[i] < 50)
        bez = next(i for i in range(dark + 15, len(prof)) if prof[i] > 120)
        dial_edge.append(at(1010 + first, a))
        ring.append(at(1010 + bez, a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    _, _, rd = fit_circle(np.array(dial_edge))
    case_r = float(np.median(np.hypot(edge[:, 0] - rcx, edge[:, 1] - rcy)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (Irsyad); bracelet width not verified",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((rcx, rcy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)),
                            "basis": "inner edge of the polished bezel, first bright pixel outside the dark gasket"},
           "dial_edge_radius_mm": round(rd / S, 3)}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    # lug tips: where the silhouette steps in from the lugs to the bracelet (more than 1 mm between rows 0.25 mm apart)
    tips = [next(y for y in np.arange(15, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (22, 24, 28, 32, 36, 40, -22, -24, -28, -32, -36, -40) if y in width}
    near = [width[y] for y in width if 22 <= abs(y) <= 24]
    out["checks"] = {"bracelet_next_to_case_mm": round(float(np.median(near)), 2), "expected_mm": BRACELET_MM}

    # indices from radial profiles at each hour: polished baton outline, white lume block at the outer end
    idx = {}
    for hr in range(1, 13):
        p = [g[int(at(r, hr * 30)[1]), int(at(r, hr * 30)[0])] for r in range(650, 1050)]
        lit = [i for i, v in enumerate(p) if v > 120]
        lume0 = max(i for i in lit if i - 1 not in lit)
        idx[str(hr)] = {"inner": round((650 + lit[0]) / S, 3), "lume_from": round((650 + lume0) / S, 3), "outer": round((650 + lit[-1]) / S, 3)}
    med = lambda k: round(float(np.median([v[k] for hr, v in idx.items() if hr not in ("3", "12")])), 3)
    # the batons are hollow (polished outline, black centre): a ray along the centre can miss the inner end bar, so take the low quartile
    inner = round(float(np.percentile([v["inner"] for hr, v in idx.items() if hr not in ("3", "12")], 25)), 3)
    out["indices"] = {"per_hour_mm": idx, "inner_mm": inner, "lume_from_mm": med("lume_from"), "outer_mm": med("outer"),
                      "width_mm": round(M["index_width_px"][0] / S, 3), "width_12_mm": round(M["index_width_px"][1] / S, 3),
                      "layout": "applied polished batons with a black centre and a white lume block at the outer end; double at 12; lume block only at 3"}

    hands = {}
    for name in ("hour", "minute", "seconds"):
        r, a = polar(M[f"{name}_hand_tip"])
        wb, wt = (v / S for v in M[f"{name}_hand_width_px"])
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_mm": round(wb / 2, 3), "tail_half_width_mm": round(wt / 2, 3)}
    for name in ("hour", "minute"):
        a, b = M[f"{name}_hand_lume"]
        hands[name]["lume_from_to_mm"] = sorted([polar(a)[0], polar(b)[0]])
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "crown_box"):
        out[k] = box(M[k])
    out["end_link_half_width_mm"] = round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / 2 / S, 3)
    row = M["bracelet_row_1160"]
    c, hw = sum(row["edges"]) / 2, (row["edges"][1] - row["edges"][0]) / 2
    cols = [[round(abs(x - c) / hw, 3) for x in col] for col in row["columns"]]
    out["bracelet_columns"] = {"centre_half": round((cols[1][0] + cols[1][1]) / 2, 3),
                               "mid_from_to": [round((cols[0][1] + cols[2][0]) / 2, 3), round((cols[0][0] + cols[2][1]) / 2, 3)],
                               "basis": "fractions of the bracelet half width, row at y = 1160 px"}
    j = M["bracelet_joints_y"]
    pitch = [(a - b) / S for js in j.values() for a, b in zip(js[1:], js[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.median(pitch)), 3)
    out["bracelet_joints_mm"] = {k: [round(-(y - py0) / S, 3) for y in v] for k, v in j.items()}

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r_ in (case_r, rr, rd):
            cv2.circle(ov, (int(rcx), int(rcy)), int(r_), (0, 0, 255), 3)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, P((-hd["tail_mm"] * math.sin(t), -hd["tail_mm"] * math.cos(t))),
                     P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 3)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            for k in ("inner_mm", "lume_from_mm", "outer_mm"):
                r_ = out["indices"][k]
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 8, (255, 0, 255), 3)
        for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "checks",
                                           "indices", "bracelet_columns", "bracelet_pitch_mm")}), "->", dest)
