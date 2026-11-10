"""Measure the Orient RA-AC0F06L10B front photo (native 2000 x 2000) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_ra_ac0f06l10b_trace [out.json] [overlay.png]   # default config/watches/orient-ra-ac0f06l10b-trace.json

Same method as pipeline/orient_ra_wj0002l_trace.py. Anchor: case width 41.6 mm (Orient official), read on the 9-3 row from the
case edge to the crown root; the official lug to lug 48.3 mm and strap width 22 mm are reported as checks. mm, x right, y toward
12, origin = the index ring centre. The photo is taken a little from below: the hand pivot sits 0.23 mm above the index ring
centre, the bezel ring about the same, and the low parts (lugs, crown, strap) lower. The model is symmetric about one centre;
hand angles are read about their own pivot. Hands, indices, date, logo and crown come from gridded crops (MANUAL_PX).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-ra-ac0f06l10b/front_2000x2000.jpg"
OUT = ROOT / "config/watches/orient-ra-ac0f06l10b-trace.json"
CASE_MM = 41.6  # Orient official, case width without the crown
LISTED = {"lug_to_lug_mm": 48.3, "strap_width_mm": 22.0, "thickness_mm": 11.7}

MANUAL_PX = {
    "dial_centre": [947, 865],  # index ring centre: mean of the 3/9 and 12/6 index outer ends
    "hand_pivot": [945, 858],
    "case_x": [327, 1567],  # left case edge, crown root (9-3 row)
    "case_y": [242, 1472],  # bezel band top and bottom on the 12-6 column
    "bezel_centre": [947, 857],
    "bezel_inner_r": 565,  # bright polished bezel ends here (mean of 12 3 6 9), about the bezel centre
    "rehaut_r": 530,  # grey inner slope from the crystal ring down to the dial, about the dial centre
    # hands about the hand pivot: (distance from the pivot, half width) along the hand, faceted
    "hour_hand_tip": [700, 703],
    "hour_profile_px": [[-12, 9], [38, 8.5], [72, 19.5], [200, 11], [280, 5], [293, 0]],
    "minute_angle_deg": 52.9,  # tip read 4 px off the centre line; angle from the symmetric part of the profile
    "minute_profile_px": [[-12, 8], [45, 7], [100, 17.5], [210, 13], [330, 8], [390, 6], [437, 0]],
    "seconds_hand_tip": [676, 1205],
    "seconds_tail_px": [110, 3, 6],  # tail length, needle half width, tail half width
    "seconds_angle_deg": 217.0,  # line through the tip and the tail (the tip alone reads 217.8 about the pivot)
    "hub_radius_px": [32, 13],  # collar, cap
    # indices about the dial centre: tapered faceted batons, the 12 a wide trapezoid with two ridges, the 3 shortened by the date
    "index_px": {"inner": 333, "outer": 470, "half_inner": 9, "half_outer": 19},
    "index_12_px": {"inner": 328, "outer": 463, "half_inner": 26, "half_outer": 49},
    "index_3_inner_px": 394,
    "date_window": [1210, 820, 1328, 912],  # polished frame outer edge
    "date_frame_px": 11,
    "logo": [835, 600, 1065, 750],  # emblem, ORIENT, Automatic
    "print_wr": [815, 1065, 1075, 1112],  # Water Resistant
    "print_6": [745, 1282, 1165, 1335],  # MOV'T JAPAN / F672-UAF8 TH 2 either side of the 6
    "crown_x": [1567, 1660],  # root at the case, end of the cap
    "crown_radius_px": 80,
    "crown_teeth": 24,
    "lug_inner_x_mm": 11.2,  # inner edges at the tips (photo 22.7 mm between them, strap 22 mm listed)
    "lug_tips_y": [185, 1625],  # silhouette steps
}
ARTEFACTS = ["the photo is taken a little from below: lugs, crown and strap sit 0.5-1.5 mm lower than the dial in the photo; "
             "the model is symmetric about the index ring centre and uses the official lug to lug",
             "the strap runs a little to the right in the photo; its leather is resampled row by row between its own edges",
             "logo, minute track and prints stay in the photo map"]


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
           "case": {"radius_mm": round(CASE_MM / 2, 3), "height_mm_in_photo": round((M["case_y"][1] - M["case_y"][0]) / S, 3)},
           "bezel_inner_mm": round(M["bezel_inner_r"] / S, 3), "rehaut_mm": round(M["rehaut_r"] / S, 3)}

    # lug outline: silhouette half width by depth from the tip, top and bottom averaged (the photo's lugs are not centred)
    t0, t1 = M["lug_tips_y"]
    half = lambda row: (np.nonzero(fg[row])[0].max() - np.nonzero(fg[row])[0].min()) / 2 / S
    depth = []
    for d in np.arange(0.25, 9.01, 0.25):
        k = int(round(d * S))
        depth.append([round(float(d), 2), round((half(t0 + k) + half(t1 - k)) / 2, 3)])
    out["lug"] = {"tip_mm": round(LISTED["lug_to_lug_mm"] / 2, 3), "photo_lug_to_lug_mm": round((t1 - t0) / S, 2),
                  "inner_x_mm": M["lug_inner_x_mm"], "half_width_by_depth_mm": depth}
    widths = {}
    for row in (t0 - 100, t0 - 60, t1 + 60, t1 + 150, t1 + 300):
        xs = np.nonzero(fg[row])[0]
        widths[str(row)] = round((xs.max() - xs.min()) / S, 2)
    out["checks"] = {"lug_to_lug_mm": out["lug"]["photo_lug_to_lug_mm"], "strap_width_past_tips_mm": widths, "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    ix = {k: round(v / S, 3) for k, v in M["index_px"].items()}
    out["indices"] = {"baton_mm": ix, "index_12_mm": {k: round(v / S, 3) for k, v in M["index_12_px"].items()},
                      "index_3_inner_mm": round(M["index_3_inner_px"] / S, 3),
                      "layout": "faceted tapered batons at 1-11 (3 shortened by the date), wide double-ridge trapezoid at 12"}
    out["date_window"] = box(M["date_window"])
    out["date_window"]["frame_mm"] = round(M["date_frame_px"] / S, 3)
    for k in ("logo", "print_wr", "print_6"):
        out[k] = box(M[k])

    prof = lambda key: [[round(a / S, 3), round(b / S, 3)] for a, b in M[key]]
    r, a = polar(M["hour_hand_tip"])
    hands = {"hour": {"angle_deg": a, "length_mm": r, "outline_mm": prof("hour_profile_px")},
             "minute": {"angle_deg": M["minute_angle_deg"], "length_mm": round(M["minute_profile_px"][-1][0] / S, 3),
                        "outline_mm": prof("minute_profile_px")}}
    tail, wn, wc = M["seconds_tail_px"]
    hands["seconds"] = {"angle_deg": M["seconds_angle_deg"], "length_mm": polar(M["seconds_hand_tip"])[0], "tail_mm": round(tail / S, 3),
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    cx0, cx1 = M["crown_x"]
    out["crown"] = {"from_mm": round((cx0 - M["bezel_centre"][0]) / S, 3), "to_mm": round((cx1 - M["bezel_centre"][0]) / S, 3),
                    "radius_mm": round(M["crown_radius_px"] / S, 3), "teeth": M["crown_teeth"]}
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
            pts = hd.get("outline_mm")
            if pts:
                poly = [(w * math.cos(t) + rr * math.sin(t), -w * math.sin(t) + rr * math.cos(t)) for rr, w in pts] + \
                       [(-w * math.cos(t) + rr * math.sin(t), w * math.sin(t) + rr * math.cos(t)) for rr, w in pts[::-1]]
                cv2.polylines(ov, [np.array([P(p, (hx, hy)) for p in poly], np.int32)], True, (0, 255, 255), 1)
            else:
                L, tl = hd["length_mm"], hd["tail_mm"]
                cv2.line(ov, P((-tl * math.sin(t), -tl * math.cos(t)), (hx, hy)), P((L * math.sin(t), L * math.cos(t)), (hx, hy)), (0, 255, 255), 1)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            q = out["indices"]["index_12_mm"] if hr == 12 else ix
            r0 = out["indices"]["index_3_inner_mm"] if hr == 3 else q["inner"]
            quad = [(sx * q[hk] * math.cos(t) + rr * math.sin(t), -sx * q[hk] * math.sin(t) + rr * math.cos(t))
                    for sx, hk, rr in ((1, "half_inner", r0), (1, "half_outer", q["outer"]), (-1, "half_outer", q["outer"]), (-1, "half_inner", r0))]
            cv2.polylines(ov, [np.array([P(p) for p in quad], np.int32)], True, (255, 0, 255), 1)
        for k in ("date_window", "logo", "print_wr", "print_6"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for y in M["lug_tips_y"]:
            cv2.line(ov, (500, y), (1400, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "hand_pivot_mm", "case", "bezel_inner_mm", "rehaut_mm", "checks",
                                           "indices", "hands", "hub_radius_mm", "crown", "date_window")}, default=float), "->", dest)
