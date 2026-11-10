"""Measure the Orient Star RE-AU0601B (Diver 1964 2nd edition) front photo (2x working copy, 2528 x 4000) into mm.
Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_re_au0601b_trace [out.json] [overlay.png]   # default config/watches/orient-re-au0601b-trace.json

Same method as pipeline/orient_ra_aa0818l19b_trace.py. Anchor: bezel diameter 41.0 mm across the coin edge (listing); listed
lug width 20 mm and lug to lug 49.6 mm are reported as checks. mm, x right, y toward 12, origin = hand pivot. Hands, applied
markers, power reserve, date, logo, crown and bracelet joints come from gridded crops (MANUAL_PX, +-3 px of the 2x copy =
+-0.06 mm). The black insert's outer edge is fitted along rays (dark to bright steel); its white prints are traced by
threshold and become geometry.
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
FRONT = ROOT / "references/orient-re-au0601b/front_2x_2528x4000.png"
OUT = ROOT / "config/watches/orient-re-au0601b-trace.json"
CASE_MM = 41.0  # listing (ocarat, watchia): bezel coin edge
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 49.6}

MANUAL_PX = {
    "hand_pivot": [1155, 1990],
    # hour: polished stem with lume, lume disc in a polished ring, short pointed tip beyond the disc
    "hour_hand_tip": [865, 1775],
    "hour_disc_centre": [955, 1855],
    "hour_disc_r_px": [67, 56],  # polished ring, lume
    "hour_stem_half_width_px": 22,
    # minute: sword, polished outline, lume blade
    "minute_hand_tip": [1715, 1600],
    "minute_widest": [545, 40],  # distance from the pivot, half width (polished outline included)
    "minute_root_half_width_px": 20,
    "minute_lume_px": [110, 560],
    # seconds: polished needle, lume disc near the tip, small disc on the counterweight
    "seconds_hand_tip": [680, 2430],
    "seconds_disc_centre": [900, 2230],
    "seconds_disc_r_px": 45,
    "seconds_tail_disc": [1330, 1820, 28],
    "seconds_hand_half_width_px": 5,
    "hub_radius_px": [46, 18],  # collar, cap
    # power reserve at 12: hub, tapered hand
    "pr_hub": [1150, 1530, 32],
    "pr_hand_tip": [1085, 1670],
    "pr_hand_half_width_px": 16,
    "pr_print": [1000, 1560, 1310, 1770],  # 50 / 25 / 0 and ticks
    "date_window": [1575, 1925, 1738, 2065],  # polished frame outer edge
    "date_inner": [1600, 1950, 1712, 2040],
    "logo": [928, 2140, 1390, 2410],  # OS emblem, ORIENT STAR, AUTOMATIC, DIVER'S 200m
    "print_6": [700, 2600, 1620, 2720],  # movement print either side of the 6
    "dot_r_px": [602, 50, 40],  # centre radius, polished ring, lume
    "bar_r_px": [470, 680],  # 6 and 9: inner, outer end
    "bar_width_px": 73,
    "square_3": [1762, 1950, 1838, 2040],
    "index_12": [1060, 1315, 1255, 1478, 35],  # trapezoid: top edge x0, y, x1, bottom y, bottom half width
    "frame_px": 10,  # polished frame around the lume
    "crown_box": [2100, 1835, 2300, 2160],  # case to the end of the crown
    "bezel_notch_count": 228,  # coin edge, about 27 px apart at 3 o'clock
    "bezel_rings_px": {"rehaut": 690, "lip_in": 732, "insert_in": 758},  # about the bezel centre; insert_out and rim_out are fitted
    "pip_px": [1161, 1113, 22, 15],  # lume pip in the 12 triangle: centre, polished ring radius, lume radius
    # bracelet: five columns; brushed 1 3 5 start at the lug tips, polished 2 4 joints further out
    "bracelet_joints_y": {"top_brushed": [805, 555, 325], "top_polished": [690, 465, 245],
                          "bottom_brushed": [3180, 3470, 3700], "bottom_polished": [3325, 3560, 3780]},
    "bracelet_columns_x": [700, 922, 1078, 1243, 1405, 1628],  # outer edges and the four joints, near the lug tips
    "end_link_x_px": [700, 1628],
}
ARTEFACTS = ["the photo is 1264 x 2000 (23.7 px/mm); the 2x copy adds no detail",
             "the case looks a little off-centre to the pivot (photo perspective): lugs are built symmetric about the pivot"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * math.sin(math.radians(a)), c[1] - r * math.cos(math.radians(a)))

    # coin-edge outline on the flanks (lugs above 62 / below 118 deg; the crown sits at 78-102 deg)
    edge = []
    for a in list(np.arange(62, 76.1, 1.0)) + list(np.arange(104, 118.1, 1.0)) + list(np.arange(242, 298.1, 1.0)):
        rs = np.arange(900, 1060, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))

    # insert outer edge: last dark pixel before the bright coin edge, along rays about the pivot
    pts = []
    for a in np.arange(0, 360, 1.0):
        rs = np.arange(860, 1000, 0.5)
        xs, ys = (np.array(v).astype(int) for v in at(rs, a))
        dark = gray[ys, xs] < 60
        k = next((i for i in range(len(rs) - 12, 12, -1) if dark[i - 12:i].all() and not dark[i:i + 8].any()), None)
        if k:
            pts.append((xs[k], ys[k]))
    pts = np.array(pts, float)
    keep = np.ones(len(pts), bool)
    for _ in range(6):
        bcx, bcy, ins_r = fit_circle(pts[keep])
        d = np.abs(np.hypot(pts[:, 0] - bcx, pts[:, 1] - bcy) - ins_r)
        keep = d < max(2.5, 2 * np.percentile(d[keep], 60))
    rg = dict(M["bezel_rings_px"], insert_out=round(float(ins_r), 1), rim_out=round(float(case_r), 1))  # coin edge = the anchor circle
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"bezel diameter = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "bezel_offset_mm": mm((bcx, bcy)), "bezel_rings_mm": {k: round(v / S, 3) for k, v in rg.items()},
           "insert_edge_fit": {"centre_px": [round(float(bcx), 1), round(float(bcy), 1)], "points": int(keep.sum()), "of": len(pts)}}
    out["bezel_notches"] = {"count": M["bezel_notch_count"], "basis": "teeth about 27 px apart on the 2x copy at 3 o'clock"}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(20, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (28, 32, 36, 40, -28, -32, -36, -40) if y in width}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 2 or -tips[1] - 2 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "end_link_width_mm": round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S, 2), "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:4]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    dr, dro, drl = M["dot_r_px"]
    x0, ty, x1, by_, bh = M["index_12"]
    out["indices"] = {"dot_r_mm": round(dr / S, 3), "dot_ring_mm": round(dro / S, 3), "dot_lume_mm": round(drl / S, 3),
                      "bar_inner_mm": round(M["bar_r_px"][0] / S, 3), "bar_outer_mm": round(M["bar_r_px"][1] / S, 3),
                      "bar_width_mm": round(M["bar_width_px"] / S, 3), "frame_mm": round(M["frame_px"] / S, 3),
                      "square_3": box(M["square_3"]),
                      "trapezoid_12": {"top_r_mm": round((py0 - ty) / S, 3), "bottom_r_mm": round((py0 - by_) / S, 3),
                                       "top_half_mm": round((x1 - x0) / 2 / S, 3), "bottom_half_mm": round(bh / S, 3),
                                       "x_mm": round(((x0 + x1) / 2 - px0) / S, 3)},
                      "layout": "applied polished-rim lume dots at 1 2 4 5 7 8 10 11, bars at 6 and 9, trapezoid at 12, square at 3 beside the date"}

    hands = {}
    r, a = polar(M["hour_hand_tip"])
    hands["hour"] = {"angle_deg": a, "length_mm": r, "disc_at_mm": polar(M["hour_disc_centre"])[0],
                     "disc_r_mm": [round(v / S, 3) for v in M["hour_disc_r_px"]], "stem_half_width_mm": round(M["hour_stem_half_width_px"] / S, 3)}
    r, a = polar(M["minute_hand_tip"])
    wa, ww = M["minute_widest"]
    l0, l1 = M["minute_lume_px"]
    hands["minute"] = {"angle_deg": a, "length_mm": r, "widest_at_mm": round(wa / S, 3), "half_width_max_mm": round(ww / S, 3),
                       "half_width_root_mm": round(M["minute_root_half_width_px"] / S, 3), "lume_mm": [round(l0 / S, 3), round(l1 / S, 3)]}
    r, a = polar(M["seconds_hand_tip"])
    tx, ty_, tr_ = M["seconds_tail_disc"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "disc_at_mm": polar(M["seconds_disc_centre"])[0],
                        "disc_r_mm": round(M["seconds_disc_r_px"] / S, 3), "tail_mm": polar((tx, ty_))[0], "tail_disc_r_mm": round(tr_ / S, 3),
                        "half_width_mm": round(M["seconds_hand_half_width_px"] / S, 3)}
    hx, hy, hr = M["pr_hub"]
    pr_c = mm((hx, hy))
    dx, dy = (M["pr_hand_tip"][0] - hx) / S, -(M["pr_hand_tip"][1] - hy) / S
    hands["power_reserve"] = {"centre_mm": pr_c, "hub_r_mm": round(hr / S, 3), "angle_deg": round(math.degrees(math.atan2(dx, dy)) % 360, 2),
                              "length_mm": round(math.hypot(dx, dy), 3), "half_width_mm": round(M["pr_hand_half_width_px"] / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    for k in ("date_window", "date_inner", "logo", "print_6", "pr_print", "crown_box"):
        out[k] = box(M[k])
    pc = M["pip_px"]
    out["pip_mm"] = {"centre": mm(pc[:2]), "ring_r": round(pc[2] / S, 3), "lume_r": round(pc[3] / S, 3)}

    # insert prints: white on black between the insert edges (the pip is built separately)
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - bcx, yy - bcy)
    band = (rr > rg["insert_in"] + 4) & (rr < rg["insert_out"] - 3)
    pr = ((gray > 185 - 35 * (yy > bcy + 600) - 25 * (yy > bcy + 740)) & band).astype(np.uint8) * 255  # prints are near white, the bottom of the insert sits in shade; glare stays below
    pr = cv2.morphologyEx(pr, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)

    def printed(i):
        """Drop glare on the insert edges: thin arcs along the ring."""
        ys, xs = np.nonzero(lab == i)
        r = np.hypot(xs - bcx, ys - bcy)
        a_ = np.unwrap(np.sort(np.arctan2(ys - bcy, xs - bcx)))
        along, across = (a_.max() - a_.min()) * r.mean(), r.max() - r.min()
        return len(xs) >= 40 and not (along > 2.5 * across and across < 20)

    pr = np.isin(lab, [i for i in range(1, n) if printed(i)]).astype(np.uint8) * 255
    x0b, y0b = int(bcx - rg["insert_out"] - 10), int(bcy - rg["insert_out"] - 10)
    sz = int(2 * rg["insert_out"] + 20)
    crop = pr[y0b:y0b + sz, x0b:x0b + sz].copy()
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(255 - crop)  # fill specks inside the strokes
    crop[np.isin(lab2, [i for i in range(2, n2) if st2[i, 4] < 40])] = 255
    up = cv2.GaussianBlur(cv2.resize(crop, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
    to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
    out["insert_prints"] = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 40)

    j = M["bracelet_joints_y"]
    pitch = [abs(a - b) / S for js in j.values() for a, b in zip(js[1:], js[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.mean(pitch)), 3)
    out["bracelet_joints_mm"] = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    out["bracelet_polished_joint_shift_mm"] = round(float(np.mean([abs(j["top_brushed"][0] - j["top_polished"][0]),
                                                                   abs(j["bottom_brushed"][0] - j["bottom_polished"][0])]) / S), 3)
    cx = M["bracelet_columns_x"]
    half = (cx[-1] - cx[0]) / 2
    out["bracelet_column_fractions"] = [round(abs(x - (cx[0] + cx[-1]) / 2) / half, 3) for x in cx[1:3]]  # joint |x| / half width
    out["end_link_half_mm"] = round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / 2 / S, 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in rg.values():
            cv2.circle(ov, (int(bcx), int(bcy)), int(rk), (0, 0, 255), 1)
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for name, hd in hands.items():
            if name == "power_reserve":
                continue
            t = math.radians(hd["angle_deg"])
            tail = hd.get("tail_mm", 0)
            cv2.line(ov, P((-tail * math.sin(t), -tail * math.cos(t))), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr_ in (1, 2, 4, 5, 7, 8, 10, 11):
            t = math.radians(hr_ * 30)
            cv2.circle(ov, (int(px0 + dr * math.sin(t)), int(py0 - dr * math.cos(t))), dro, (255, 0, 255), 2)
        for k in ("date_window", "date_inner", "logo", "print_6", "pr_print", "crown_box", "square_3"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:4]), (0, 200, 255), 2)
        for sh in out["insert_prints"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 2)
        cv2.circle(ov, tuple(pc[:2]), pc[2], (255, 0, 0), 2)
        for v in j.values():
            for y in v:
                cv2.line(ov, (650, y), (1680, y), (255, 128, 0), 2)
        for x in cx:
            cv2.line(ov, (x, 0), (x, 1000), (255, 128, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_offset_mm", "bezel_rings_mm", "insert_edge_fit", "lug_tip_mm",
                                           "checks", "indices", "hands", "pip_mm", "bracelet_pitch_mm", "bracelet_polished_joint_shift_mm",
                                           "bracelet_column_fractions", "end_link_half_mm")}, default=float), "->", dest,
          len(data["insert_prints"]), "insert prints")
