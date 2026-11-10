"""Measure the Orient RA-AA0C02L19B front photo (native 2000 x 2000) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_ra_aa0c02l19b_trace [out.json] [overlay.png]   # default config/watches/orient-ra-aa0c02l19b-trace.json

Same method as pipeline/orient_ra_ac0f06l10b_trace.py. Anchor: case width 41.9 mm (Orient official), read on the 9-3 row from
the case edge to the crown root; the official lug to lug 48.0 mm and bracelet width 22 mm are reported as checks. mm, x right,
y toward 12, origin = the index ring centre. The photo is taken a little from below (hand pivot and bezel sit 0.2 mm above and
left of the index ring centre, lugs, crown and bracelet lower); the model is symmetric about one centre, hand angles are read
about their own pivot. Hands, indices, day-date, logo, crown, guards and bracelet joints come from gridded crops (MANUAL_PX).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-ra-aa0c02l19b/front_2000x2000.jpg"
OUT = ROOT / "config/watches/orient-ra-aa0c02l19b-trace.json"
CASE_MM = 41.9  # Orient official, case width without the crown
LISTED = {"lug_to_lug_mm": 48.0, "bracelet_width_mm": 22.0, "thickness_mm": 11.7}

MANUAL_PX = {
    "dial_centre": [955, 860],  # index ring centre: 3/9 outer ends; 12/6 read 862 (the lower bars sit a little low in the photo)
    "hand_pivot": [950, 855],
    "case_x": [315, 1583],  # left case edge, crown root (9-3 row); the brushed bezel is flush with the case
    "bezel_centre": [949, 855],
    "bezel_inner_r": 564,  # brushed bezel ends here (mean of 12 3 6 9)
    "rehaut_r": 535,  # grey inner slope from the crystal ring down to the dial, about the dial centre
    # hands about the hand pivot: (distance from the pivot, half width); polished frame with a lume inlay
    "hour_angle_deg": 304.41,  # axis refit from the midpoints of the hand edges
    "hour_profile_px": [[-15, 10], [30, 14], [55, 23], [240, 20], [255, 17], [285, 7], [298, 0]],
    "hour_lume_px": [[88, 15], [238, 14], [256, 0]],
    "minute_angle_deg": 52.5,  # midpoints lie 4-7 px off a line through the pivot: compromise between root and tip
    "minute_profile_px": [[-15, 9], [40, 9], [95, 18.5], [340, 16.5], [360, 14.25], [390, 7.75], [418, 0]],
    "minute_lume_px": [[110, 12], [340, 11], [372, 0]],
    "seconds_hand_tip": [697, 1198],
    "seconds_tail_px": [105, 3, 4.5],  # tail length, needle half width, tail half width
    "hub_radius_px": [37, 15],  # stepped collar, cap
    # indices about the dial centre: rounded polished bars with a lume inlay; a wider solid polished bar at 12
    "index_px": {"inner": 343, "outer": 469, "half": 15},
    "index_12_px": {"inner": 327, "outer": 462, "half": 32},
    "index_3_inner_px": 387,
    "index_frame_px": 4,
    "daydate": [1092, 820, 1335, 910],  # polished frame outer edge
    "daydate_divider_x": 1222,
    "daydate_frame_px": 9,
    "logo": [840, 575, 1075, 730],  # emblem, ORIENT, Automatic
    "print_wr": [810, 1052, 1090, 1098],  # Water Resistant
    "print_6": [750, 1325, 1190, 1372],  # MOV'T JAPAN / F692-UAD8 TH 2 either side of the 6
    "crown_x": [1583, 1660],  # root at the case, end of the cap
    "crown_cap_x": 1640,
    "crown_radius_px": 80,
    "crown_teeth": 22,
    "crown_axis_y": 880,  # the crown and its guards sit lower than the pivot in the photo
    "guard_px": {"from_axis": 90, "to_axis": 200, "outer_x": 1640},
    "lug_inner_x_mm": 11.0,  # inner edges at the tips: 665 px, the 22 mm end link
    "lug_tips_y": [190, 1612],  # silhouette steps
    # bracelet: three brushed columns, centre joints between the outer ones (bottom side, the top runs away from the camera)
    "bracelet_columns_x": [640, 785, 1145, 1290],
    "bracelet_joints_y": {"bottom_outer": [1630, 1812], "bottom_centre": [1728, 1886]},
    "bracelet_centre_x": 965,  # bracelet centre line in the photo (bottom)
}
ARTEFACTS = ["the photo is taken a little from below: lugs, crown and bracelet sit 0.5-1.5 mm lower than the dial in the photo; "
             "the model is symmetric about the index ring centre and uses the official lug to lug",
             "the top bracelet runs away from the camera: pitch and layout are read on the bottom side",
             "logo, printed lume squares, minute track and prints stay in the photo map"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    M = MANUAL_PX
    ox, oy = M["dial_centre"]
    hx, hy = M["hand_pivot"]
    S = (M["case_x"][1] - M["case_x"][0]) / CASE_MM
    mm = lambda p, c=(ox, oy): [round((p[0] - c[0]) / S, 3), round(-(p[1] - c[1]) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p, (hx, hy))), 3), round(math.degrees(math.atan2(*mm(p, (hx, hy)))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [ox, oy], "hand_pivot_px": [hx, hy],
           "hand_pivot_mm": mm((hx, hy)), "anchor": f"case width = {CASE_MM} mm (Orient official)",
           "case": {"radius_mm": round(CASE_MM / 2, 3)},
           "bezel_inner_mm": round(M["bezel_inner_r"] / S, 3), "rehaut_mm": round(M["rehaut_r"] / S, 3)}

    # lug outline: silhouette half width by depth from the tip, top and bottom averaged (the photo's lugs are not centred)
    t0, t1 = M["lug_tips_y"]
    half = lambda row: (np.nonzero(fg[row])[0].max() - np.nonzero(fg[row])[0].min()) / 2 / S
    depth = []
    for d in np.arange(0.25, 9.01, 0.25):
        k = int(round(d * S))
        depth.append([round(float(d), 2), round((half(t0 + k) + half(t1 - k)) / 2, 3)])
    tip = LISTED["lug_to_lug_mm"] / 2
    out["lug"] = {"tip_mm": round(tip, 3), "photo_lug_to_lug_mm": round((t1 - t0) / S, 2),
                  "inner_x_mm": M["lug_inner_x_mm"], "half_width_by_depth_mm": depth}

    # bracelet: half width past the tips from the left edge about the bracelet centre line (the clasp shows on the right)
    bw = []
    for y in range(t1 + 20, im.shape[0] - 10, 10):
        xs = np.nonzero(fg[y])[0]
        bw.append([round(tip + (y - t1) / S, 2), round((M["bracelet_centre_x"] - xs.min()) / S, 3)])
    out["bracelet_half_width_by_s_mm"] = bw
    c = M["bracelet_columns_x"]
    j = M["bracelet_joints_y"]
    pitch = [(b - a) / S for v in j.values() for a, b in zip(v, v[1:])]
    out["bracelet_pitch_mm"] = round(float(np.mean(pitch)), 3)
    out["bracelet_centre_half_mm"] = round((c[2] - c[1]) / 2 / S, 3)
    # centre joints sit this far nearer the case than the outer joints (outer rows start at the lug tip)
    out["bracelet_centre_joint_shift_mm"] = round(float(np.mean([(o - cc) / S % out["bracelet_pitch_mm"] for o, cc in
                                                                  ((j["bottom_outer"][1], j["bottom_centre"][0]), (j["bottom_outer"][1] + (j["bottom_centre"][1] - j["bottom_centre"][0]), j["bottom_centre"][1]))])), 3)
    out["checks"] = {"lug_to_lug_mm": out["lug"]["photo_lug_to_lug_mm"], "end_link_width_mm": round((c[3] - c[0]) / S, 2),
                     "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    out["indices"] = {"bar_mm": {k: round(v / S, 3) for k, v in M["index_px"].items()},
                      "index_12_mm": {k: round(v / S, 3) for k, v in M["index_12_px"].items()},
                      "index_3_inner_mm": round(M["index_3_inner_px"] / S, 3), "frame_mm": round(M["index_frame_px"] / S, 3),
                      "layout": "rounded polished bars with lume at 1-11 (3 shortened by the day-date), solid polished bar at 12"}
    out["daydate"] = box(M["daydate"])
    out["daydate"]["frame_mm"] = round(M["daydate_frame_px"] / S, 3)
    out["daydate"]["divider_x_mm"] = mm((M["daydate_divider_x"], 0))[0]
    for k in ("logo", "print_wr", "print_6"):
        out[k] = box(M[k])

    prof = lambda key: [[round(a / S, 3), round(b / S, 3)] for a, b in M[key]]
    hands = {n: {"angle_deg": M[n + "_angle_deg"], "length_mm": round(M[n + "_profile_px"][-1][0] / S, 3),
                 "outline_mm": prof(n + "_profile_px"), "lume_mm": prof(n + "_lume_px")} for n in ("hour", "minute")}
    tail, wn, wc = M["seconds_tail_px"]
    r, a = polar(M["seconds_hand_tip"])
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": round(tail / S, 3), "half_width_mm": round(wn / S, 3),
                        "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    bx = M["bezel_centre"][0]
    gp = M["guard_px"]
    out["crown"] = {"from_mm": round((M["crown_x"][0] - bx) / S, 3), "to_mm": round((M["crown_x"][1] - bx) / S, 3),
                    "cap_from_mm": round((M["crown_cap_x"] - bx) / S, 3), "radius_mm": round(M["crown_radius_px"] / S, 3),
                    "teeth": M["crown_teeth"],
                    "guard_mm": {"from_axis": round(gp["from_axis"] / S, 3), "to_axis": round(gp["to_axis"] / S, 3),
                                 "outer_x": round((gp["outer_x"] - bx) / S, 3)}}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy, c=(ox, oy): (int(round(c[0] + xy[0] * S)), int(round(c[1] - xy[1] * S)))
        cv2.circle(ov, tuple(M["bezel_centre"]), int((M["case_x"][1] - M["case_x"][0]) / 2), (0, 128, 255), 2)
        cv2.circle(ov, tuple(M["bezel_centre"]), M["bezel_inner_r"], (0, 0, 255), 1)
        cv2.circle(ov, (ox, oy), M["rehaut_r"], (0, 0, 255), 1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            for key in ("outline_mm", "lume_mm"):
                pts = hd.get(key)
                if pts:
                    poly = [(w * math.cos(t) + rr * math.sin(t), -w * math.sin(t) + rr * math.cos(t)) for rr, w in pts] + \
                           [(-w * math.cos(t) + rr * math.sin(t), w * math.sin(t) + rr * math.cos(t)) for rr, w in pts[::-1]]
                    cv2.polylines(ov, [np.array([P(p, (hx, hy)) for p in poly], np.int32)], True, (0, 255, 255), 1)
            if "outline_mm" not in hd:
                L, tl = hd["length_mm"], hd["tail_mm"]
                cv2.line(ov, P((-tl * math.sin(t), -tl * math.cos(t)), (hx, hy)), P((L * math.sin(t), L * math.cos(t)), (hx, hy)), (0, 255, 255), 1)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            q = out["indices"]["index_12_mm"] if hr == 12 else out["indices"]["bar_mm"]
            r0 = out["indices"]["index_3_inner_mm"] if hr == 3 else q["inner"]
            quad = [(sx * q["half"] * math.cos(t) + rr * math.sin(t), -sx * q["half"] * math.sin(t) + rr * math.cos(t))
                    for sx, rr in ((1, r0), (1, q["outer"]), (-1, q["outer"]), (-1, r0))]
            cv2.polylines(ov, [np.array([P(p) for p in quad], np.int32)], True, (255, 0, 255), 1)
        for k in ("daydate", "logo", "print_wr", "print_6"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (600, y), (1350, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "hand_pivot_mm", "bezel_inner_mm", "rehaut_mm", "checks", "indices",
                                           "hands", "hub_radius_mm", "crown", "daydate", "bracelet_pitch_mm",
                                           "bracelet_centre_half_mm", "bracelet_centre_joint_shift_mm")}, default=float), "->", dest)
