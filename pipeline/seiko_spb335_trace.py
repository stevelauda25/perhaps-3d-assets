"""Measure the Seiko Prospex SPB335J1 front photo (white background, 2397 x 4120) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.seiko_spb335_trace [out.json] [overlay.png]     # default config/watches/seiko-spb335j1-trace.json

Anchor: full case width at the widest row = 41 mm (listing). The case is asymmetric (it bulges on the crown side), so the left
and right edges are kept separately; top and bottom are averaged. Lug to lug (46.9 mm) and lug width (20 mm) are reported as
checks. mm, x right, y toward 12, origin = hand pivot. Rings, indices, hands and crown come from gridded and hand-aligned
crops (MANUAL_PX, about +-0.1 mm); hands are stored as posed outlines so the dial map and the build use the same shapes.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-spb335j1/front_2397x4120.jpg"
OUT = ROOT / "config/watches/seiko-spb335j1-trace.json"
CASE_MM = 41.0  # listing: diameter 41, thickness 12.3, lug width 20, lug to lug 46.9
LUG_WIDTH_MM, LUG_TO_LUG_MM = 20.0, 46.9
BG = 235  # white background: brighter than this on all channels is not the watch

MANUAL_PX = {
    "hand_pivot": [1169, 2060],
    "ring_radius_px": {"teeth_tip": 1015, "teeth_root": 985, "insert_outer": 965, "insert_inner": 835,
                       "crystal_edge": 805, "flange_outer": 800, "dial_edge": 690},
    "notch_y_px": [1050, 3080],  # case edge between the horns, under the bezel teeth (top, bottom)
    "horn_inner_x_px": [655, 1731],
    "strap_face_x_px": [682, 1715],  # top face of the strap at row 760; right of it the strap's side wall shows (photo from the crown side)
    "teeth_count": 130,  # coin edge: about 48 px pitch at r 1000 px
    "crown_rows_px": [2540, 2860],  # right edge rows covered by the crown: case edge interpolated across
    # hands: angle (clock deg) and hand-local outlines (x across, y along, px), read from crops turned upright on the hand
    "hour_angle": 303.4,
    "hour_outline": [[-40, 435], [40, 425], [45, 400], [45, 60], [30, 30], [22, -150], [-22, -150], [-30, 30], [-45, 60], [-45, 425]],
    "hour_lume": [[[-25, 390], [32, 390], [32, 200], [-25, 200]]],
    "minute_angle": 69.8,
    "minute_outline": [[-8, 660], [26, 645], [33, 620], [42, 100], [30, 40], [20, -160], [-20, -160], [-30, 40], [-42, 100], [-33, 620], [-26, 645]],
    "minute_lume": [[[-6, 630], [22, 625], [27, 140], [-27, 140], [-22, 625]]],
    "seconds_angle": 262.5,
    "seconds_length_px": 674,
    "seconds_half_width_px": 6,
    "seconds_tail_px": 190,
    "seconds_lume_px": [500, 568, 30],  # lume plate along the hand: inner, outer distance, half width
    "seconds_dot_px": [470, 21],  # red dot: distance from the pivot, radius
    "hub_radius_px": [28, 14],
    "extra_hand_mask_px": [[[1150, 2090], [1195, 2035], [1335, 2148], [1292, 2200]]],  # hour tail: bent off the hand axis in the photo
    # applied indices: inner r, outer r, half width (px); 12 is a double plate with a point toward the centre
    "index_px": {"bar": [492, 665, 44], "cardinal": [478, 665, 54], "12": [495, 665, 94]},
    "index_12_point_px": 455,
    "index_frame_px": 10,
    "index_12_bar_half_px": 5,
    # printed parts kept clear of the hand fill (x0, y0, x1, y1)
    "logo_seiko": [985, 1712, 1365, 1802],
    "logo_x": [1115, 2215, 1235, 2302],
    "print_automatic_divers": [950, 2320, 1395, 2442],
    "date_window": [1528, 2402, 1622, 2504],
    "print_6": [890, 2655, 1410, 2728],
    "crown_angle": 122.4,
    "crown_radius_px": 140,
    "crown_r_px": [1000, 1230],  # along its axis from the pivot: inner end (inside the case) to the outer face
}
ARTEFACTS = ["the photo is taken slightly from the crown side: the bezel insert looks wider on the right and the strap centre "
             "sits right of the pivot (strap_offset_mm, used by the strap UV)",
             "hand shadows fall to the right of the hands: masked with the hands"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = (im < BG).any(2)
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    h = fg.shape[0]
    rows = range(py0 - 120, py0 + 120)
    width = [np.nonzero(fg[r])[0].max() - np.nonzero(fg[r])[0].min() for r in rows]
    S = max(width) / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"full case width at the widest row = {CASE_MM} mm (listing); lug to lug {LUG_TO_LUG_MM} and lug width {LUG_WIDTH_MM} as checks"}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["ring_radius_px"].items()}
    out["notch_mm"] = round(((py0 - M["notch_y_px"][0]) + (M["notch_y_px"][1] - py0)) / 2 / S, 3)
    out["horn_inner_x_mm"] = round((M["horn_inner_x_px"][1] - M["horn_inner_x_px"][0]) / 2 / S, 3)
    out["teeth_count"] = M["teeth_count"]

    c0, c1 = M["crown_rows_px"]
    edge = {}
    for row in range(h):
        xs = np.nonzero(fg[row])[0]
        if len(xs):
            edge[row] = (xs.min(), xs.max())
    right = lambda row: edge[row][1] if not c0 < row < c1 else edge[c0][1] + (edge[c1][1] - edge[c0][1]) * (row - c0) / (c1 - c0)
    prof = []
    for y_mm in np.arange(-41.75, 41.76, 0.25):
        row = int(round(py0 - y_mm * S))
        if row in edge:
            prof.append([round(float(y_mm), 2), round((px0 - edge[row][0]) / S, 3), round((right(row) - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    # horns and strap from the left edge only: on the right the strap's side wall shows
    left = {p[0]: p[1] for p in prof}
    sf0, sf1 = M["strap_face_x_px"]
    off = (sf0 + sf1) / 2 - px0
    inner_left = (px0 - M["horn_inner_x_px"][0]) / S
    tips = [next(y for y in np.arange(18, 30, 0.25) if left[round(sy * y, 2)] < inner_left + 0.35) for sy in (1, -1)]
    out["horn_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["strap_offset_mm"] = round(off / S, 3)
    out["strap_half_y_mm"] = [[p[0], round(p[1] + off / S, 3)] for p in prof if abs(p[0]) > min(tips)]
    near = [2 * h for y, h in out["strap_half_y_mm"] if tips[0] + 0.5 <= y <= tips[0] + 3 or -tips[1] - 3 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "listed_lug_to_lug_mm": LUG_TO_LUG_MM,
                     "strap_past_horns_mm": round(float(np.median(near)), 2), "strap_face_mm": round((sf1 - sf0) / S, 2),
                     "listed_lug_width_mm": LUG_WIDTH_MM}

    def posed(angle, local):
        t = math.radians(angle)
        return [[round((x * math.cos(t) + y * math.sin(t)) / S, 3), round((-x * math.sin(t) + y * math.cos(t)) / S, 3)] for x, y in local]

    hands = {}
    for name in ("hour", "minute"):
        a = M[name + "_angle"]
        hands[name] = {"angle_deg": a, "length_mm": round(max(p[1] for p in M[name + "_outline"]) / S, 3),
                       "outline_mm": posed(a, M[name + "_outline"]), "lume_mm": [posed(a, lp) for lp in M[name + "_lume"]]}
    a, L, w, tl = M["seconds_angle"], M["seconds_length_px"], M["seconds_half_width_px"], M["seconds_tail_px"]
    l0, l1, lw = M["seconds_lume_px"]
    dd, dr = M["seconds_dot_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": round(L / S, 3),
                        "outline_mm": posed(a, [[0, L], [w, L - 6], [w, -tl], [-w, -tl], [-w, L - 6]]),
                        "lume_mm": [posed(a, [[0, l1 + 12], [lw, l1], [lw, l0], [-lw, l0], [-lw, l1]])],
                        "dot_centre_mm": posed(a, [[0, dd]])[0], "dot_radius_mm": round(dr / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    out["extra_hand_mask_mm"] = [[mm(q) for q in poly] for poly in M["extra_hand_mask_px"]]

    ix, fr = {}, M["index_frame_px"]
    for kind, (r0, r1, hw) in M["index_px"].items():
        if kind == "12":
            p = M["index_12_point_px"]
            o = ((0, p), (hw, r0), (hw, r1), (-hw, r1), (-hw, r0))
            lm = ((0, p + fr * 1.4), (hw - fr, r0 + fr * 0.4), (hw - fr, r1 - fr), (-hw + fr, r1 - fr), (-hw + fr, r0 + fr * 0.4))
        else:
            o = ((-hw, r0), (hw, r0), (hw, r1), (-hw, r1))
            lm = ((-hw + fr, r0 + fr), (hw - fr, r0 + fr), (hw - fr, r1 - fr), (-hw + fr, r1 - fr))
        ix[kind] = {"outline": [[round(v / S, 3) for v in q] for q in o], "lume": [[round(v / S, 3) for v in q] for q in lm]}
    out["indices"] = {"shapes_mm": ix, "bar_12_half_width_mm": round(M["index_12_bar_half_px"] / S, 3),
                      "layout": "applied black frames with lume: bars, wider bars at 3, 6, 9, a double plate pointed toward the centre at 12"}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("logo_seiko", "logo_x", "print_automatic_divers", "date_window", "print_6"):
        out[k] = box(M[k])
    out["crown"] = {"angle_deg": M["crown_angle"], "radius_mm": round(M["crown_radius_px"] / S, 3),
                    "r_from_to_mm": [round(v / S, 3) for v in M["crown_r_px"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r in M["ring_radius_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 128, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((-l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for hd in hands.values():
            cv2.polylines(ov, [np.array([P(p) for p in hd["outline_mm"]])], True, (0, 255, 255), 2)
            for lp in hd.get("lume_mm", []):
                cv2.polylines(ov, [np.array([P(p) for p in lp])], True, (0, 128, 255), 1)
        cv2.circle(ov, P(hands["seconds"]["dot_centre_mm"]), M["seconds_dot_px"][1], (0, 0, 255), 2)
        for hr in range(1, 13):
            sh = ix["12" if hr == 12 else "cardinal" if hr % 3 == 0 else "bar"]
            t = math.radians(hr * 30)
            rotp = lambda p: P((p[0] * math.cos(t) + p[1] * math.sin(t), -p[0] * math.sin(t) + p[1] * math.cos(t)))
            cv2.polylines(ov, [np.array([rotp(p) for p in sh["outline"]])], True, (255, 0, 255), 2)
        for k in ("logo_seiko", "logo_x", "print_automatic_divers", "date_window", "print_6"):
            cv2.rectangle(ov, tuple(M[k][:2]), tuple(M[k][2:]), (0, 200, 255), 2)
        ca = math.radians(M["crown_angle"])
        for r in M["crown_r_px"]:
            cv2.circle(ov, (int(px0 + r * math.sin(ca)), int(py0 - r * math.cos(ca))), M["crown_radius_px"], (0, 0, 255), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "notch_mm", "horn_inner_x_mm", "horn_tip_mm", "strap_offset_mm", "checks", "crown")},
                     default=float), "->", dest)
