"""Measure the Orient RA-AA0818L19B (Mako III) front photo (1700 x 2715) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_ra_aa0818l19b_trace [out.json] [overlay.png]   # default config/watches/orient-ra-aa0818l19b-trace.json

Same method as pipeline/orient_ra_ac0q17y_trace.py. Anchor: case width 41.8 mm across the flanks at 3 and 9 (Orient USA listing; the scalloped bezel is a little smaller); listed lug width
22 mm and lug to lug 46.8 mm are reported as checks. mm, x right, y toward 12, origin = hand pivot. Hands, indices, numeral
boxes, day-date, logo, crown and bracelet joints come from gridded crops (MANUAL_PX, +-2 px = +-0.06 mm). The aluminium
insert's two colours are read along a ring (light blue from the triangle to 15, dark blue elsewhere); its white prints and
the applied 12 / 6 / 9 numerals are traced by threshold and become geometry.
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
FRONT = ROOT / "references/orient-ra-aa0818l19b/front_1700x2715.jpg"
OUT = ROOT / "config/watches/orient-ra-aa0818l19b-trace.json"
CASE_MM = 41.8  # listing (Orient USA): case flanks, the bezel sits inside them
LISTED = {"lug_width_mm": 22.0, "lug_to_lug_mm": 46.8}

MANUAL_PX = {
    "hand_pivot": [787, 1318],
    # hour: leaf, polished outline, black border, lume centre
    "hour_hand_tip": [548, 1153],
    "hour_widest": [206, 48],  # distance from the pivot, half width (polished outline included)
    "hour_root_half_width_px": 12,
    "hour_lume_px": [70, 240],  # from, to (distance from the pivot)
    # minute: sword, polished outline, black stem, lume blade
    "minute_hand_tip": [1212, 1267],
    "minute_widest": [347, 30],
    "minute_root_half_width_px": 10,
    "minute_lume_px": [77, 371],
    # seconds: polished needle, yellow lume triangle (wide end toward the pivot) and yellow pointer, black wedge counterweight
    "seconds_hand_tip": [313, 1173],
    "seconds_hand_tail_end": [960, 1368],
    "seconds_hand_half_width_px": [3, 5, 17],  # needle, counterweight at the hub, at its end
    "seconds_lume_px": [309, 470, 18],  # wide end, point (distance from the pivot), half width at the wide end
    "hub_radius_px": [24, 9],  # collar, cap
    "day_date": [935, 1256, 1216, 1362],  # polished frame outer edge
    "day_date_divider_x": [1088, 1097],
    "numeral_12": [672, 870, 860, 1004],
    "numeral_9": [390, 1236, 495, 1393],
    "numeral_6": [722, 1640, 850, 1765],
    "logo": [668, 1080, 925, 1250],  # crown emblem, ORIENT, Automatic
    "print_wr": [610, 1480, 950, 1565],  # Water Resistant 20 bar
    "print_6": [520, 1715, 1070, 1800],  # MOV'T JAPAN, movement print
    "index_r_px": [330, 442],  # inner, outer end of the bars
    "index_width_px": 33,
    "frame_px": 4,  # polished edge around the white bars
    "crown_box": [1460, 1215, 1625, 1435],  # collar at the case to the end of the cap
    "bezel_notch_count": 110,  # scallops, counted over 49 deg at 6 o'clock (15 intervals)
    "bezel_rings_px": {"lip_in": 523, "insert_in": 548, "dial_out": 505, "rim_out": 690},  # about the bezel centre; insert_out is fitted
    "pip_px": [764, 712, 22, 13],  # lume pip in the 12 triangle: centre, polished ring radius, lume radius
    # bracelet: three columns, tapering; centre joints nearer the case than the outer ones
    "bracelet_joints_y": {"top_outer": [530, 372, 192], "top_centre": [400, 222],
                          "bottom_outer": [2150, 2352, 2517], "bottom_centre": [2305, 2490]},
    "bracelet_centre_px": [[655, 955], [640, 955]],
    "end_link_x_px": [405, 1150],
}
ARTEFACTS = ["the photo is 1700 x 2715 at about 33 px/mm: hand and index edges are +-2 px",
             "the minute hand covers the top of the day-date window: the dial map redraws SAT 11 there"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * math.sin(math.radians(a)), c[1] - r * math.cos(math.radians(a)))

    # case outline on the flanks (the lugs leave it above 68 / below 112 deg; the crown sits at 80-100 deg)
    edge = []
    for a in list(np.arange(56, 68.1, 1.0)) + list(np.arange(112, 124.1, 1.0)) + list(np.arange(240, 300.1, 1.0)):
        rs = np.arange(600, 760, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    # bezel centre and insert outer edge: end of the saturated blue along rays (dark part; the pale lit part is skipped),
    # fitted with outliers (steel reflecting the insert) dropped
    sat = hsv[..., 1]
    pts = []
    for a in np.arange(0, 360, 1.0):
        rs = np.arange(560, 700, 0.5)
        xs, ys = (np.array(v).astype(int) for v in at(rs, a))
        blue = sat[ys, xs] > 110
        k = next((i for i in range(1, len(rs) - 16) if rs[i] > 600 and blue[i - 1] and not blue[i:i + 16].any()), None)
        if k:
            pts.append((xs[k], ys[k]))
    pts = np.array(pts, float)
    keep = np.ones(len(pts), bool)
    for _ in range(6):
        bcx, bcy, ins_r = fit_circle(pts[keep])
        d = np.abs(np.hypot(pts[:, 0] - bcx, pts[:, 1] - bcy) - ins_r)
        keep = d < max(2.5, 2 * np.percentile(d[keep], 60))
    rg = dict(M["bezel_rings_px"], insert_out=round(float(ins_r), 1))
    rings = {k: round(v / S, 3) for k, v in rg.items()}
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "bezel_offset_mm": mm((bcx, bcy)), "bezel_rings_mm": rings,
           "insert_edge_fit": {"centre_px": [round(float(bcx), 1), round(float(bcy), 1)], "points": int(keep.sum()), "of": len(pts)}}
    out["bezel_notches"] = {"count": M["bezel_notch_count"], "basis": "scallops 3.3 deg apart at 6 o'clock"}

    # insert colours: brightness of the blue (white prints left out) along the middle of the insert
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - bcx, yy - bcy)
    band = (rr > rg["insert_in"] + 6) & (rr < rg["insert_out"] - 3)
    white = (hsv[..., 1] < 50) & (hsv[..., 2] > 150)  # the lit blue at 9 o'clock reaches S 80; the 30 sits in shade
    ang = (np.degrees(np.arctan2(xx - bcx, bcy - yy)) % 360)
    bins = np.arange(0, 360.01, 1.0)
    val = np.array([np.median(hsv[..., 2][band & ~white & (ang >= a) & (ang < a + 1)]) for a in bins[:-1]])
    # the light sector's edges are the sharpest steps; the dark part only brightens slowly toward the lit side at 9 o'clock
    step = np.roll(val, -2) - np.roll(val, 2)
    near = lambda c: [(c + d) % 360 for d in range(-30, 31)]  # the triangle at 12 and the 15 mark
    a0, a1 = max(near(0), key=lambda a: step[a]), min(near(90), key=lambda a: step[a])
    out["insert_light_sector_deg"] = [float(a0), float(a1)]
    pick = lambda m: [round(float(v) / 255, 3) for v in np.median(im[m][:, ::-1], 0)]
    sector = (ang >= a0 + 3) & (ang < a1 - 3) if a0 < a1 else (ang >= a0 + 3) | (ang < a1 - 3)
    out["insert_srgb"] = {"light": pick(band & ~white & sector), "dark": pick(band & ~white & ~sector & (ang > 100) & (ang < 340))}

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
                      "layout": "applied white bars with a polished edge at 1 2 4 5 7 8 10 11; applied numerals 12 6 9; day-date at 3"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[name + "_hand_tip"])
        wa, ww = M[name + "_widest"]
        l0, l1 = M[name + "_lume_px"]
        hands[name] = {"angle_deg": a, "length_mm": r, "widest_at_mm": round(wa / S, 3), "half_width_max_mm": round(ww / S, 3),
                       "half_width_root_mm": round(M[name + "_root_half_width_px"] / S, 3), "lume_mm": [round(l0 / S, 3), round(l1 / S, 3)]}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc0, wc1 = M["seconds_hand_half_width_px"]
    l0, l1, lw = M["seconds_lume_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": [round(wc0 / S, 3), round(wc1 / S, 3)],
                        "lume_mm": [round(l0 / S, 3), round(l1 / S, 3), round(lw / S, 3)]}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    for k in ("day_date", "logo", "print_wr", "print_6", "crown_box", "numeral_12", "numeral_9", "numeral_6"):
        out[k] = box(M[k])
    out["day_date_divider_mm"] = [round((x - px0) / S, 3) for x in M["day_date_divider_x"]]
    pc = M["pip_px"]
    out["pip_mm"] = {"centre": mm(pc[:2]), "ring_r": round(pc[2] / S, 3), "lume_r": round(pc[3] / S, 3)}

    def traced(mask, x0b, y0b, min_area):
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(255 - mask)  # fill specks inside the strokes
        mask[np.isin(lab2, [i for i in range(2, n2) if st2[i, 4] < 12])] = 255
        up = cv2.GaussianBlur(cv2.resize(mask, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
        to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
        return shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, min_area)

    # insert prints: white on blue between the insert edges (the pip is built separately)
    pr = (white & band).astype(np.uint8) * 255
    pr = cv2.morphologyEx(pr, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)

    def printed(i):
        """Drop glare on the insert's outer edge: thin arcs along the ring, or long pieces touching the edge."""
        ys, xs = np.nonzero(lab == i)
        r = np.hypot(xs - bcx, ys - bcy)
        a_ = np.unwrap(np.sort(np.arctan2(ys - bcy, xs - bcx)))
        along, across = (a_.max() - a_.min()) * r.mean(), r.max() - r.min()
        edge = r.max() > rg["insert_out"] - 3 and (along > 2 * across or r.min() > rg["insert_out"] - 14)
        thin = len(xs) / max(along, across, 1) < 6  # glare lines are 2-5 px wide; dots and strokes 10 px or more
        return len(xs) >= 15 and not (along > 2.5 * across and across < 12) and not edge and not thin

    pr = np.isin(lab, [i for i in range(1, n) if printed(i)]).astype(np.uint8) * 255
    x0b, y0b = int(bcx - rg["insert_out"] - 10), int(bcy - rg["insert_out"] - 10)
    sz = int(2 * rg["insert_out"] + 20)
    out["insert_prints"] = traced(pr[y0b:y0b + sz, x0b:x0b + sz].copy(), x0b, y0b, 12)

    # applied numerals: white inside their boxes
    out["numerals"] = []
    for k in ("numeral_12", "numeral_9", "numeral_6"):
        x0, y0, x1, y1 = M[k]
        m = ((gray[y0:y1, x0:x1] > 150).astype(np.uint8)) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        out["numerals"] += traced(m, x0, y0, 30)

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
        for rk in rg.values():
            cv2.circle(ov, (int(bcx), int(bcy)), int(rk), (0, 0, 255), 1)
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for a in out["insert_light_sector_deg"]:
            cv2.line(ov, tuple(int(v) for v in at(rg["insert_in"], a, (bcx, bcy))), tuple(int(v) for v in at(rg["insert_out"], a, (bcx, bcy))), (0, 255, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 1, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 1, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            tail = hd.get("tail_mm", 0)
            cv2.line(ov, P((-tail * math.sin(t), -tail * math.cos(t))), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            for r_ in (r0, r1):
                cv2.circle(ov, (int(px0 + r_ * math.sin(t)), int(py0 - r_ * math.cos(t))), 4, (255, 0, 255), 1)
        for k in ("day_date", "logo", "print_wr", "print_6", "crown_box", "numeral_12", "numeral_9", "numeral_6"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for sh in out["insert_prints"] + out["numerals"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        cv2.circle(ov, tuple(pc[:2]), pc[2], (255, 0, 0), 1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (380, y), (1180, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_rings_mm", "insert_light_sector_deg", "insert_srgb", "lug_tip_mm",
                                           "checks", "indices", "hands", "pip_mm", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_centre_half_mm", "end_link_half_mm")}, default=float), "->", dest,
          len(data["insert_prints"]), "insert prints,", len(data["numerals"]), "numeral shapes")
