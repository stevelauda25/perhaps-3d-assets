"""Measure the Orient RA-AC0Q17Y front photo (2x working copy, 2482 x 4096) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_ra_ac0q17y_trace [out.json] [overlay.png]   # default config/watches/orient-ra-ac0q17y-trace.json

Same method as pipeline/seiko_sur419_trace.py. Anchor: case (bezel) diameter 39.9 mm (listing); listed lug width 20 mm and
lug to lug 46.5 mm are reported as checks. mm, x right, y toward 12, origin = hand pivot. Hands, indices, date, logo, crown
and bracelet joints come from gridded crops (MANUAL_PX, +-3 px of the 2x copy = +-0.06 mm). The bezel's black-filled
engravings (numerals, minute dots and bars, the triangle at 12) are traced by threshold on the brushed steel and become
geometry; the coin-edge notches are read from a gridded crop of the rim.
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
FRONT = ROOT / "references/orient-ra-ac0q17y/front_2x_2482x4096.png"
OUT = ROOT / "config/watches/orient-ra-ac0q17y-trace.json"
CASE_MM = 39.9  # listing (Orient USA, most retailers)
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 46.5}

MANUAL_PX = {
    "hand_pivot": [1146, 1948],
    # hour: arrow, polished outline, lume head, black stem
    "hour_hand_tip": [790, 1717],
    "hour_head_base": [190, 78],  # distance from the pivot, half width (px)
    "hour_stem_half_width_px": 46,
    # minute: sword, polished outline, black stem, lume blade
    "minute_hand_tip": [1593, 1478],
    "minute_hand_half_width_px": [16, 36],  # stem at the collar, widest at 55 % of the length
    "minute_lume_from_px": 130,
    # seconds: needle, orange-framed lume triangle (wide end toward the pivot), black counterweight bar with a polished rim
    "seconds_hand_tip": [480, 1980],
    "seconds_hand_tail_end": [1405, 1936],
    "seconds_hand_half_width_px": [6, 26],  # needle, counterweight
    "seconds_lume_px": [466, 596, 24],  # wide end, point (distance from the pivot), half width at the wide end
    "hub_radius_px": [50, 18],  # collar, cap
    "date_window": [1575, 1878, 1786, 2048],  # polished frame outer edge
    "logo": [985, 1515, 1345, 1760],  # crown emblem, ORIENT, Automatic
    "print_wr": [870, 2195, 1390, 2335],  # Water Resistant 20 bar
    "print_6": [975, 2600, 1390, 2655],  # movement print either side of the 6
    "index_r_px": [480, 672],  # inner, outer end of the batons
    "index_width_px": [48, 76],  # trapezoids: inner, outer end
    "index_bar_width_px": 80,  # 6 and 9
    "index_12": [1050, 1284, 1264, 1478],  # triangle: top edge, point
    "frame_px": 10,  # polished frame around the lume
    "crown_box": [2105, 1845, 2300, 2105],  # collar at the case to the end of the fluted part
    "bezel_notch_count": 72,  # coin-edge slots, same bezel as RA-AC0Q16N
    "bezel_rings_px": {"lip_in": 738, "top_in": 758, "top_out": 922, "rim_out": 950},
    # bracelet: three columns; centre joints nearer the case than the outer ones
    "bracelet_joints_y": {"top_outer": [845, 558, 292], "top_centre": [620, 360],
                          "bottom_outer": [3155, 3497, 3765], "bottom_centre": [3400, 3698]},
    "bracelet_centre_px": [[956, 1395], [905, 1350]],
    "end_link_x_px": [662, 1656],
}
ARTEFACTS = ["the photo is 1241 x 2048 (25 px/mm); the 2x copy adds no detail",
             "the bracelet pitch looks shorter toward 12 (the strap leans away): the mean of both ends is used",
             "the top of the bracelet is cut by the photo frame at y 100 px"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * math.sin(math.radians(a)), c[1] - r * math.cos(math.radians(a)))

    # bezel outline on the flanks (the lugs leave it above 55 / below 125 deg; the crown sits at 80-100 deg)
    edge = []
    for a in list(np.arange(60, 78.1, 1.0)) + list(np.arange(102, 120.1, 1.0)) + list(np.arange(240, 300.1, 1.0)):
        rs = np.arange(850, 1080, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    rings = {k: round(v / S, 3) for k, v in M["bezel_rings_px"].items()}
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"bezel diameter = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "bezel_offset_mm": mm((ccx, ccy)), "bezel_rings_mm": rings}

    out["bezel_notches"] = {"count": M["bezel_notch_count"], "basis": "about 80 px apart along the rim at 9 o'clock (4.8 deg)"}

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
    x0, y0, x1, y1 = M["index_12"]
    out["indices"] = {"inner_mm": round(r0 / S, 3), "outer_mm": round(r1 / S, 3),
                      "width_inner_mm": round(M["index_width_px"][0] / S, 3), "width_outer_mm": round(M["index_width_px"][1] / S, 3),
                      "bar_width_mm": round(M["index_bar_width_px"] / S, 3), "frame_mm": round(M["frame_px"] / S, 3),
                      "triangle_12": {"top_r_mm": round((py0 - y0) / S, 3), "point_r_mm": round((py0 - y1) / S, 3),
                                      "half_width_mm": round((x1 - x0) / 2 / S, 3)},
                      "layout": "applied polished frames with lume: triangle at 12, bars at 6 and 9, trapezoids at 1 2 4 5 7 8 10 11, date at 3"}

    hands = {}
    r, a = polar(M["hour_hand_tip"])
    hb, hw = M["hour_head_base"]
    hands["hour"] = {"angle_deg": a, "length_mm": r, "head_from_mm": round(hb / S, 3), "head_half_width_mm": round(hw / S, 3),
                     "stem_half_width_mm": round(M["hour_stem_half_width_px"] / S, 3)}
    r, a = polar(M["minute_hand_tip"])
    w0, w1 = M["minute_hand_half_width_px"]
    hands["minute"] = {"angle_deg": a, "length_mm": r, "half_width_root_mm": round(w0 / S, 3), "half_width_max_mm": round(w1 / S, 3),
                       "lume_from_mm": round(M["minute_lume_from_px"] / S, 3)}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_half_width_px"]
    l0, l1, lw = M["seconds_lume_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3),
                        "lume_mm": [round(l0 / S, 3), round(l1 / S, 3), round(lw / S, 3)]}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    for k in ("date_window", "logo", "print_wr", "print_6", "crown_box"):
        out[k] = box(M[k])

    # bezel engravings: black fill on the brushed top, between the polished lip and the notched rim
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - ccx, yy - ccy)
    band = (rr > M["bezel_rings_px"]["top_in"] + 6) & (rr < M["bezel_rings_px"]["top_out"] + 8)
    dark = ((gray < 110) & band).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))  # glare breaks the outline numerals
    n, lab, st, cen = cv2.connectedComponentsWithStats(dark)
    keep = [i for i in range(1, n) if st[i, 4] > 40 and math.hypot(cen[i][0] - ccx, cen[i][1] - ccy) < M["bezel_rings_px"]["top_out"] - 8]

    def engraving(i):
        """Drop shadows: thin arcs along the inner step (long along the ring, flat across it) dark spots on the rim edge, specks."""
        ys, xs = np.nonzero(lab == i)
        r = np.hypot(xs - ccx, ys - ccy)
        ang = np.unwrap(np.sort(np.arctan2(ys - ccy, xs - ccx)))
        along, across = (ang.max() - ang.min()) * r.mean(), r.max() - r.min()
        thin_arc = along > 2.5 * across and across < 30
        rim_shadow = r.max() > M["bezel_rings_px"]["top_out"] + 2 and along > 3 * across  # gap at the crown
        return len(xs) >= 200 and not thin_arc and not rim_shadow

    keep = [i for i in keep if engraving(i)]
    dark = np.isin(lab, keep).astype(np.uint8) * 255
    x0b, y0b = int(ccx - 960), int(ccy - 960)
    crop = dark[y0b:y0b + 1920, x0b:x0b + 1920]
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(255 - crop)  # fill specks and thin glare lines inside the strokes
    thick = cv2.distanceTransform(255 - crop, cv2.DIST_L2, 3)
    crop[np.isin(lab2, [i for i in range(2, n2) if st2[i, 4] < 150 or thick[lab2 == i].max() < 4])] = 255
    up = cv2.GaussianBlur(cv2.resize(crop, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
    to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
    out["bezel_engravings"] = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 40)

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
            cv2.circle(ov, (int(ccx), int(ccy)), int(rk), (0, 0, 255), 1)
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
        for k in ("date_window", "logo", "print_wr", "print_6", "index_12", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        for sh in out["bezel_engravings"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 2)
        for v in j.values():
            for y in v:
                cv2.line(ov, (600, y), (1700, y), (255, 128, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_rings_mm", "bezel_notches", "lug_tip_mm", "checks",
                                           "indices", "hands", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_centre_half_mm", "end_link_half_mm")}, default=float), "->", dest,
          len(data["bezel_engravings"]), "engravings")
