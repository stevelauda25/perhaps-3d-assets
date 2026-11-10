"""Measure the Orient FAC0000EW0 (Bambino version 3) front photo into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_fac0000ew0_trace [out.json] [overlay.png]   # default config/watches/orient-fac0000ew0-trace.json

Same method as pipeline/orient_ra_ac0f06l10b_trace.py. Source: Orient USA's front image of TAC0000EW0 (the US code of the same
watch), flattened on white, enlarged 2x and stretched 1.0416x vertically about the dial ring centre: the image is shot a little
from below and its dial ring reads 1153 x 1106 px; after the stretch it is round and the lug to lug reads 46.4 mm against the
listed 46.5 mm. MANUAL_PX are read on the unstretched 2x copy (front_2x_white_3200x2134.png) and mapped with STRETCH.
Anchor: case width 40.5 mm (listings); lug width 21 mm and lug to lug 46.5 mm are reported as checks. mm, x right, y toward 12,
origin = the dial ring centre; hand angles about their own pivot. Applied batons at 12, 3, 6 and 9 only (the other hours are
printed lines in the dial map).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-fac0000ew0/front_2x_rect_3200x2223.png"
OUT = ROOT / "config/watches/orient-fac0000ew0-trace.json"
CASE_MM = 40.5  # listings (watch.co.uk, seriouswatches.com)
STRETCH = (576 / 553, 932)  # y factor and fixed row: the dial ring reads 1153 x 1106 px on the 2x copy
LISTED = {"lug_to_lug_mm": 46.5, "strap_width_mm": 21.0, "thickness_mm": 11.8}

_RAW = {  # unstretched 2x copy
    "dial_centre": [1609, 932],  # dial ring (dark line) 1033-2185 x, 379-1485 y
    "hand_pivot": [1600, 922],
    "case_x": [970, 2269],  # case width on the 9-3 row (crown root hidden: from the rows 100 px above and below)
    "case_y": [376, 1488],
    "bezel_centre": [1619, 932],
    "bezel_inner_r": 589,  # bright polished bezel ends at the dark ring (x 1030 on the 9 side)
    "rehaut_r": 570,
    # hands about the hand pivot: (distance from the pivot, half width), flat-ended rectangular batons
    "hour_hand_tip": [1367, 773],
    "hour_profile_px": [[-25, 15], [278, 15]],
    "minute_angle_deg": None,
    "minute_hand_tip": [1935, 665],
    "minute_profile_px": [[-25, 12], [424, 12]],
    "seconds_hand_tip": [1343, 1269],
    "seconds_tail_end": [1673, 823],
    "seconds_tail_px": [125, 3, 4],
    "seconds_angle_deg": None,
    "hub_radius_px": [30, 10],
    # applied batons about the dial centre at 12 3 6 9 (rectangular, faceted); the 3 starts further out (date)
    "index_px": {"inner": 360, "outer": 525, "half_inner": 10, "half_outer": 10},
    "index_12_px": {"inner": 360, "outer": 525, "half_inner": 10, "half_outer": 10},
    "index_3_inner_px": 415,
    "date_window": [1902, 898, 1997, 958],
    "date_frame_px": 0,
    "logo": [1525, 680, 1715, 820],  # emblem, ORIENT, Automatic
    "print_wr": [1480, 1125, 1760, 1180],  # Water Resistant
    "print_6": [1450, 1440, 1770, 1470],  # no print visible at 6 in this image; small box over the minute track there
    "crown_x": [2269, 2347],
    "crown_radius_px": 80,
    "crown_teeth": 24,
    "lug_inner_x_mm": 10.6,  # 21 mm strap
    "lug_tips_y": [280, 1710],
}


POINTS = ("dial_centre", "hand_pivot", "bezel_centre", "hour_hand_tip", "minute_hand_tip", "seconds_hand_tip", "seconds_tail_end")
BOXES = ("date_window", "logo", "print_wr", "print_6")
ROWS = ("case_y", "lug_tips_y")


def _st(v, key):
    """Map unstretched 2x px to the stretched working copy (y only); lengths and x values stay."""
    k, y0 = STRETCH
    y = lambda a: round(y0 + (a - y0) * k)
    if key in POINTS:
        return [v[0], y(v[1])]
    if key in BOXES:
        return [v[0], y(v[1]), v[2], y(v[3])]
    if key in ROWS:
        return [y(a) for a in v]
    return v


MANUAL_PX = {key: _st(v, key) for key, v in _RAW.items()}
_p = MANUAL_PX
_p["minute_angle_deg"] = round(math.degrees(math.atan2(_p["minute_hand_tip"][0] - _p["hand_pivot"][0], _p["hand_pivot"][1] - _p["minute_hand_tip"][1])) % 360, 2)
_p["seconds_angle_deg"] = round(math.degrees(math.atan2(_p["seconds_hand_tip"][0] - _p["seconds_tail_end"][0],
                                                        _p["seconds_tail_end"][1] - _p["seconds_hand_tip"][1])) % 360, 2)
ARTEFACTS = ["Orient USA image of TAC0000EW0 (same watch, US code); stretched vertically 1.0416 so the dial ring is round",
             "the domed crystal bends the batons a little: one inner and outer radius for all four",
             "printed hour lines, minute track, logo and prints stay in the photo map"]


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
           "hand_pivot_mm": mm((hx, hy)), "anchor": f"case width = {CASE_MM} mm (listings)", "stretch_y": STRETCH,
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
