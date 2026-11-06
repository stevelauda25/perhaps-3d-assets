"""Measure the Seiko Prospex SFK001J1 front photo (white background, 2551 x 4135) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.seiko_sfk001_trace [out.json] [overlay.png]     # default config/watches/seiko-sfk001j1-trace.json

Anchor: full case width at the widest row = 45 mm (listing). Checks: lug to lug (51.8 mm) and lug width (20 mm). The photo
is taken slightly from the crown side (the right edge shows more of the case wall), so the case outline is the mean of the
left and right edges about the bezel centre (symmetric, 45 mm wide), top and bottom averaged in the build. The photo is a little off-axis, so the parts sit on three centres: dial and indices on the
dial centre, hands on their pivot, bezel and case on the bezel centre. All three become the model origin.
mm, x right, y toward 12. Rings, indices, hands, crown and prints come from gridded crops (MANUAL_PX, about +-0.1 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-sfk001j1/front_2551x4135.jpg"
OUT = ROOT / "config/watches/seiko-sfk001j1-trace.json"
CASE_MM = 45.0  # listing: diameter 45, thickness 13.2, lug width 20, lug to lug 51.8
LUG_WIDTH_MM, LUG_TO_LUG_MM = 20.0, 51.8
BG = 235  # white background: brighter than this on all channels is not the watch

MANUAL_PX = {
    "dial_centre": [1173, 2096],  # circle through the eight lume dots
    "hand_pivot": [1163, 2110],
    "bezel_centre": [1160, 2122],  # insert edges left/right/top/bottom
    # bezel and case radii about the bezel centre; flange and dial about the dial centre
    "bezel_radius_px": {"teeth_tip": 1110, "insert_outer": 1043, "insert_inner": 812, "crystal_edge": 800},
    "dial_radius_px": {"flange_outer": 795, "dial_edge": 700},
    "teeth_count": 60,  # scallops: about 6 deg pitch on the crown side
    "notch_y_px": [1040, 3170],  # case edge between the lugs: hidden under the bezel rim (top, bottom)
    "lug_inner_x_px": [690, 1725],  # bracelet gap between the lugs (top rows)
    "bracelet_x_px": [690, 1725],  # bracelet next to the lugs; its centre sits right of the bezel centre (crown-side view)
    "bracelet_columns_x_px": [958, 1467],  # centre column at row 700
    "bracelet_outer_joints_y_px": [800, 510, 230],  # top: outer links start at the lug tips
    "bracelet_centre_joints_y_px": [905, 610, 300],  # top: centre links start 2.1 mm nearer the case
    "crown_rows_px": [2360, 2740],  # right edge rows covered by the crown
    # hands: angle (clock deg about the pivot) and hand-local outlines (x across, y along, px), read from crops turned upright
    "hour_angle": 305.9,  # tip direction; the hand looks shifted 20 px toward 12 at 303.3 deg
    "hour_outline": [[0, 432], [62, 332], [62, 92], [44, 40], [40, -40], [34, -150], [0, -172], [-34, -150], [-40, -40], [-44, 40], [-62, 92], [-62, 332]],
    "hour_lume": [[[0, 410], [50, 325], [50, 104], [22, 104], [9, 222], [-9, 222], [-22, 104], [-50, 104], [-50, 325]]],
    "minute_angle": 64.7,
    "minute_outline": [[0, 722], [27, 572], [24, 110], [16, 50], [28, -40], [30, -185], [-30, -185], [-28, -40], [-16, 50], [-24, 110], [-27, 568]],  # wide tail toward 7
    "minute_lume": [[[0, 692], [16, 568], [15, 135], [-15, 135], [-16, 565]]],
    "gmt_angle": 333.1,
    "gmt_outline": [[0, 612], [33, 410], [9, 428], [9, 60], [14, 40], [-14, 40], [-9, 60], [-9, 428], [-33, 410]],
    "gmt_lume": [[[0, 565], [17, 452], [-17, 452]]],
    "seconds_angle": 242.0,
    "seconds_outline": [[0, 675], [4, 662], [4, -228], [-4, -228], [-4, 662]],
    "seconds_disc_px": [-265, 45, 33],  # counterweight ring on the tail: distance along the hand, outer radius, lume radius
    "hub_radius_px": [45, 22],
    "extra_hand_mask_px": [[[1185, 2080], [1240, 2075], [1340, 2135], [1335, 2215], [1285, 2220], [1175, 2160]]],  # hour tail + shadow
    # applied indices about the dial centre: r and half width (px); dots: centre r, frame r, lume r
    "dots_px": [592, 66, 56],
    "index_px": {"12": [[458, 40], [675, 92]], "6": [[470, 30], [680, 54]], "9": [[470, 30], [680, 54]], "3": [[628, 44], [684, 50]]},
    "index_frame_px": 11,
    # printed parts kept clear of the hand fill (x0, y0, x1, y1)
    "logo_seiko": [995, 1745, 1365, 1840],
    "logo_x": [1095, 2235, 1230, 2362],
    "print_gmt": [1085, 2395, 1265, 2465],
    "print_divers": [960, 2470, 1405, 2535],
    "print_6": [880, 2725, 1465, 2800],
    "date_window": [1630, 2052, 1776, 2155],
    "numerals_24h_px": [605, 692, 7.5],  # odd 24-hour numerals at 15 + 30k deg about the dial centre: r from, r to, half angle
    "crown_angle": 110.0,  # about the bezel centre
    "crown_radius_px": 160,
    "crown_r_px": [1190, 1395],
}
ARTEFACTS = ["the photo is taken slightly from the crown side and off-axis: dial centre, hand pivot and bezel centre differ by up to 0.6 mm; "
             "the right case edge shows more of the side wall: the case outline is the mean of both edges",
             "the hour hand looks 0.4 mm off its axis in the photo; built on the axis through its tip",
             "hand shadows fall to the lower right: masked with the hands"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = (im < BG).any(2)
    M = MANUAL_PX
    bx, by = M["bezel_centre"]
    dx0, dy0 = M["dial_centre"]
    px0, py0 = M["hand_pivot"]
    h = fg.shape[0]
    edge = {}
    for row in range(h):
        xs = np.nonzero(fg[row])[0]
        if len(xs):
            edge[row] = (xs.min(), xs.max())
    S = max(edge[r][1] - edge[r][0] for r in range(by - 150, by + 150)) / CASE_MM
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4),
           "origin_px": [dx0, dy0], "pivot_px": [px0, py0], "bezel_centre_px": [bx, by],
           "pivot_offset_mm": [round((px0 - dx0) / S, 3), round(-(py0 - dy0) / S, 3)],
           "bezel_offset_mm": [round((bx - dx0) / S, 3), round(-(by - dy0) / S, 3)],
           "anchor": f"full case width at the widest row = {CASE_MM} mm (listing); lug to lug and lug width as checks"}
    mm = lambda p: [round((p[0] - dx0) / S, 3), round(-(p[1] - dy0) / S, 3)]  # image px -> mm about the dial centre
    out["rings_mm"] = {**{k: round(v / S, 3) for k, v in M["bezel_radius_px"].items()}, **{k: round(v / S, 3) for k, v in M["dial_radius_px"].items()}}
    out["teeth_count"] = M["teeth_count"]
    out["notch_mm"] = round(((by - M["notch_y_px"][0]) + (M["notch_y_px"][1] - by)) / 2 / S, 3)
    out["lug_inner_x_mm"] = round((M["lug_inner_x_px"][1] - M["lug_inner_x_px"][0]) / 2 / S, 3)

    # case silhouette about the bezel centre; the right edge is interpolated across the crown
    c0_, c1_ = M["crown_rows_px"]
    right = lambda row: edge[row][1] if not c0_ < row < c1_ else edge[c0_][1] + (edge[c1_][1] - edge[c0_][1]) * (row - c0_) / (c1_ - c0_)
    prof = []
    for y_mm in np.arange(-41.0, 41.01, 0.25):
        row = int(round(by - y_mm * S))
        if row in edge:
            prof.append([round(float(y_mm), 2), round((bx - edge[row][0]) / S, 3), round((right(row) - bx) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    left = {p[0]: p[1] for p in prof}  # lug tips from the left edge: above the right lugs the bracelet's side wall shows
    inner = (bx - M["lug_inner_x_px"][0]) / S
    tips = [next(y for y in np.arange(18, 34, 0.25) if left[round(sy * y, 2)] < inner + 0.35) for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    b0, b1 = M["bracelet_x_px"]
    off = (b0 + b1) / 2 - bx
    out["bracelet_offset_mm"] = round(off / S, 3)
    # bracelet taper: silhouette width (side wall included) relative to the first row past each tip, times the gap between
    # the lugs; the bracelet centre drifts right toward the bottom, so the left edge alone is not used
    width = {p[0]: p[1] + p[2] for p in prof}
    ref = {sy: width[round(sy * (tips[0 if sy > 0 else 1] + 1.0), 2)] for sy in (1, -1)}
    half_gap = (b1 - b0) / 2 / S
    out["bracelet_half_y_mm"] = [[y, round(half_gap * w / ref[1 if y > 0 else -1], 3)] for y, w in width.items()
                                 if (y > tips[0] + 1.0 or y < -tips[1] - 1.0)]
    c0, c1 = M["bracelet_columns_x_px"]
    out["bracelet_centre_fraction"] = round((c1 - c0) / (b1 - b0), 3)
    oj, cj = M["bracelet_outer_joints_y_px"], M["bracelet_centre_joints_y_px"]
    out["bracelet_pitch_mm"] = round((oj[0] - oj[1] + cj[0] - cj[1]) / 2 / S, 3)  # first rows only: further out the curl shortens them
    out["bracelet_centre_joint_shift_mm"] = round(-(cj[0] - oj[0]) / S, 3)  # negative: the centre column starts nearer the case
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "listed_lug_to_lug_mm": LUG_TO_LUG_MM,
                     "bracelet_between_lugs_mm": round((b1 - b0) / S, 2), "listed_lug_width_mm": LUG_WIDTH_MM,
                     "left_half_x2_mm": round(2 * max(bx - edge[r][0] for r in range(by - 150, by + 150)) / S, 2)}

    def posed(angle, local):  # hand-local px -> mm about the pivot (the build puts the pivot at the origin)
        t = math.radians(angle)
        return [[round((x * math.cos(t) + y * math.sin(t)) / S, 3), round((-x * math.sin(t) + y * math.cos(t)) / S, 3)] for x, y in local]

    hands = {}
    for name in ("hour", "minute", "gmt", "seconds"):
        a = M[name + "_angle"]
        hands[name] = {"angle_deg": a, "length_mm": round(max(p[1] for p in M[name + "_outline"]) / S, 3),
                       "outline_mm": posed(a, M[name + "_outline"]), "lume_mm": [posed(a, lp) for lp in M.get(name + "_lume", [])]}
    d, ro, rl = M["seconds_disc_px"]
    hands["seconds"].update({"disc_centre_mm": posed(M["seconds_angle"], [[0, d]])[0], "disc_radius_mm": round(ro / S, 3), "disc_lume_radius_mm": round(rl / S, 3)})
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    out["extra_hand_mask_mm"] = [[[round((q[0] - px0) / S, 3), round(-(q[1] - py0) / S, 3)] for q in poly] for poly in M["extra_hand_mask_px"]]

    fr = M["index_frame_px"]
    ix = {}
    for k, ((r0, w0), (r1, w1)) in M["index_px"].items():
        o = ((-w0, r0), (w0, r0), (w1, r1), (-w1, r1))
        lm = ((-w0 + fr, r0 + fr), (w0 - fr, r0 + fr), (w1 - fr, r1 - fr), (-w1 + fr, r1 - fr))
        ix[k] = {"outline": [[round(v / S, 3) for v in q] for q in o], "lume": [[round(v / S, 3) for v in q] for q in lm]}
    dr, dfr, dl = M["dots_px"]
    out["indices"] = {"shapes_mm": ix, "dot_r_mm": round(dr / S, 3), "dot_radius_mm": round(dfr / S, 3), "dot_lume_radius_mm": round(dl / S, 3),
                      "layout": "applied polished frames with lume: trapezoids at 12 (wide), 6 and 9, a short bar right of the date at 3, round dots elsewhere"}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("logo_seiko", "logo_x", "print_gmt", "print_divers", "print_6", "date_window"):
        out[k] = box(M[k])
    n0, n1, na = M["numerals_24h_px"]
    out["numerals_24h"] = {"r_mm": [round(n0 / S, 3), round(n1 / S, 3)], "half_angle_deg": na, "angles_deg": [15 + 30 * k for k in range(12)]}
    out["crown"] = {"angle_deg": M["crown_angle"], "radius_mm": round(M["crown_radius_px"] / S, 3),
                    "r_from_to_mm": [round(v / S, 3) for v in M["crown_r_px"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        D = lambda xy: (int(round(dx0 + xy[0] * S)), int(round(dy0 - xy[1] * S)))
        Pv = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r in M["bezel_radius_px"].values():
            cv2.circle(ov, (bx, by), r, (255, 128, 0), 2)
        for r in M["dial_radius_px"].values():
            cv2.circle(ov, (dx0, dy0), r, (255, 200, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, (int(bx - l * S), int(by - y_mm * S)), 3, (0, 255, 0), -1)
            cv2.circle(ov, (int(bx + r_ * S), int(by - y_mm * S)), 2, (0, 160, 0), -1)
        for hd in hands.values():
            cv2.polylines(ov, [np.array([Pv(p) for p in hd["outline_mm"]])], True, (0, 255, 255), 2)
            for lp in hd["lume_mm"]:
                cv2.polylines(ov, [np.array([Pv(p) for p in lp])], True, (0, 128, 255), 1)
        cv2.circle(ov, Pv(hands["seconds"]["disc_centre_mm"]), ro, (0, 255, 255), 2)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            if str(hr) in ix:
                rotp = lambda p: D((p[0] * math.cos(t) + p[1] * math.sin(t), -p[0] * math.sin(t) + p[1] * math.cos(t)))
                cv2.polylines(ov, [np.array([rotp(p) for p in ix[str(hr)]["outline"]])], True, (255, 0, 255), 2)
            else:
                cv2.circle(ov, (int(dx0 + dr * math.sin(t)), int(dy0 - dr * math.cos(t))), dfr, (255, 0, 255), 2)
        for k in ("logo_seiko", "logo_x", "print_gmt", "print_divers", "print_6", "date_window"):
            cv2.rectangle(ov, tuple(M[k][:2]), tuple(M[k][2:]), (0, 200, 255), 2)
        ca = math.radians(M["crown_angle"])
        for r in M["crown_r_px"]:
            cv2.circle(ov, (int(bx + r * math.sin(ca)), int(by - r * math.cos(ca))), M["crown_radius_px"], (0, 0, 255), 2)
        for y in M["bracelet_outer_joints_y_px"]:
            cv2.line(ov, (b0, y), (c0, y), (0, 0, 255), 2)
        for y in M["bracelet_centre_joints_y_px"]:
            cv2.line(ov, (c0, y), (c1, y), (0, 0, 255), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "pivot_offset_mm", "bezel_offset_mm", "rings_mm", "notch_mm", "lug_inner_x_mm",
                                           "lug_tip_mm", "bracelet_offset_mm", "bracelet_centre_fraction", "bracelet_pitch_mm",
                                           "bracelet_centre_joint_shift_mm", "checks", "crown")}, default=float), "->", dest)
