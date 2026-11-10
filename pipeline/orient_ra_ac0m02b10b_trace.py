"""Measure the Orient RA-AC0M02B10B (Bambino 38) front photo into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_ra_ac0m02b10b_trace [out.json] [overlay.png]   # default config/watches/orient-ra-ac0m02b10b-trace.json

Same method as pipeline/orient_fac0000ew0_trace.py. Source: Orient USA's front image of RA-AC0M02B30B (same dial, case and strap
as B10B), flattened on white and enlarged 2x; the case reads 1270 x 1270 px, so no stretch. Anchor: case width 38.4 mm
(listings); lug width 20 mm and lug to lug 44 mm are reported as checks. mm, x right, y toward 12, origin = the dial centre;
hand angles about their own pivot. Applied faceted lancet markers with a pointed outer end; a pair at 12; the 3 a short one
beside the date.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-ra-ac0m02b10b/front_2x_white_3200x2134.png"
OUT = ROOT / "config/watches/orient-ra-ac0m02b10b-trace.json"
CASE_MM = 38.4  # listings (seriouswatches.com, orientwatch.co.uk)
STRETCH = (1.0, 920)  # no stretch: the case reads round
LISTED = {"lug_to_lug_mm": 44.0, "strap_width_mm": 20.0, "thickness_mm": 12.5}

_RAW = {  # 2x copy
    "dial_centre": [1590, 920],  # case 953-2223 x, 285-1555 y
    "hand_pivot": [1594, 913],
    "case_x": [953, 2223],
    "case_y": [285, 1555],
    "bezel_centre": [1590, 920],
    "bezel_inner_r": 550,  # bright polished bezel ends here
    "rehaut_r": 515,  # dial edge
    # hands about the hand pivot: (distance from the pivot, half width), faceted dauphine with a pointed counter-tail
    "hour_hand_tip": [1302, 717],
    "hour_profile_px": [[-62, 0], [-35, 15], [-5, 11], [55, 21], [200, 12], [348, 0]],
    "minute_angle_deg": None,
    "minute_hand_tip": [1965, 618],
    "minute_profile_px": [[-62, 0], [-35, 16], [-5, 13], [60, 22], [320, 11], [474, 0]],
    "seconds_hand_tip": [1305, 1335],
    "seconds_tail_end": [1663, 803],
    "seconds_tail_px": [130, 3, 6],
    "seconds_angle_deg": None,
    "hub_radius_px": [28, 10],
    # lancet markers about the dial centre: body half width, pointed outer end (tip length in px)
    "index_px": {"inner": 342, "outer": 490, "half_inner": 13, "half_outer": 14, "tip": 18},
    "index_12_px": {"inner": 333, "outer": 476, "half_inner": 26, "half_outer": 28, "tip": 16},
    "index_3_inner_px": 440,
    "date_window": [1906, 881, 2003, 950],
    "date_frame_px": 0,
    "logo": [1500, 690, 1690, 820],  # emblem, ORIENT, Automatic
    "print_wr": [1452, 1105, 1750, 1150],  # Water Resistant
    "print_6": [1420, 1390, 1760, 1425],  # MOV'T JAPAN, F672 print either side of the 6
    "crown_x": [2223, 2305],
    "crown_radius_px": 85,
    "crown_teeth": 22,
    "lug_inner_x_mm": 10.2,  # lug inner edges 20.3 mm apart in the photo; strap 20 mm (0.2 mm edge inset)
    "lug_tips_y": [250, 1695],
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
ARTEFACTS = ["Orient USA image of RA-AC0M02B30B (same watch, packaging variant); a little from below: the pivot sits 0.2 mm above the case centre",
             "printed minute track, logo and prints stay in the photo map"]


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
