"""Measure the Zeppelin Mediterranée Z96903 (9690-3) front photo (white background, 3996 x 6144) into mm. numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z96903_trace [out.json] [overlay.png]   # default config/watches/zeppelin-z96903-trace.json

Anchor: case circle (fitted on both flanks clear of the crown and lugs) = 42 mm (listing); the strap width is reported as a
check. mm, x right, y toward 12, origin = hand pivot.
Hands, the three sub-dials (day at 9, power reserve at 12, 24 h at 6), hubs and crown come from 10 px gridded crops
(MANUAL_PX, about +-0.1 mm); centre hand angles from a scan of the white pixels along rays from the pivot. Hands are
stored posed. Sub-dial hands have a paddle tail on its own traced angle (the day hand's tail is bent off the pointer's line).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/zeppelin-z96903/front_3996x6144.png"
OUT = ROOT / "config/watches/zeppelin-z96903-trace.json"
CASE_MM = 42.0  # listing: case size 42.00 mm

MANUAL_PX = {
    "hand_pivot": [1810, 3082],
    # bezel inner edge, inner edge of the sloped pulsometer flange (= flat dial edge)
    "ring_radius_px": {"bezel_inner": 1480, "flange_inner": 1262},
    # (distance from the pivot, half width) from the hub to the tip; tips on the scanned angles
    "hour": {"tip": [1135, 2681], "profile": [[0, 16], [240, 16], [300, 22], [380, 28], [440, 50], [480, 54], [520, 46], [560, 26],
                                              [600, 20], [700, 16], [760, 12], [785, 0]]},  # needle with a teardrop bulb (300.75 deg)
    "minute": {"tip": [2392, 2050], "profile": [[0, 15], [180, 20], [300, 28], [420, 26], [600, 20], [900, 16], [1100, 11],
                                                [1185, 0]]},  # lance (29.4 deg)
    "seconds": {"tip": [1101, 2014], "profile": [[0, 11.5], [1000, 11], [1260, 5], [1282, 0]],  # needle (326.4 deg)
                "tail": [[0, 9], [320, 8], [340, 12], [355, 13], [375, 8], [389, 0]]},  # gold lozenge counterweight
    "hub_px": {"radius": 108, "pin": 12},
    "subdials": {
        "day": {"centre": [1242, 3104], "tip": [1534, 3171], "tail": [1062, 3110],
                "profile": [[0, 12], [150, 14], [260, 10], [292, 4], [300, 0]],
                "tail_profile": [[0, 8], [95, 7.5], [110, 12], [140, 13], [170, 9], [180, 0]]},
        "power": {"centre": [1792, 2120], "tip": [1438, 2341], "tail": None,
                  "profile": [[0, 9], [90, 8], [110, 22], [300, 20], [380, 12], [418, 0]]},
        "h24": {"centre": [1823, 3667], "tip": [1641, 3347], "tail": [1885, 3765],
                "profile": [[0, 8], [300, 6], [355, 4], [368, 0]], "tail_profile": [[0, 10], [60, 9], [90, 14], [116, 0]]},
    },
    "sub_hub_px": {"radius": 50, "pin": 12},
    # fluted crown at 3 with a domed end: neck start, flutes start, flutes end, dome end (x px on the centre row)
    "crown": {"centre_y": 3125, "radius": 193, "neck_radius": 215, "x_from_to": [3392, 3430, 3660, 3765]},
    # stepped lugs: the outer block and a lower inner step next to the strap, split at this distance from the centre line
    "lug_step_x_px": [860, 2735],
}
ARTEFACTS = ["applied numerals, Z logo, sub-dial scales, power-reserve scale and the date window stay in the dial map (flat)",
             "pulsometer scale on the sloped flange: in the dial map, mapped onto a cone",
             "the 24 h hand is red with a white tail (photo): red pointer, white tail"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 215
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    # case flanks near the pivot row: higher and lower rows bend out of a circle (photo taken slightly from below)
    pts = [(np.nonzero(fg[y])[0].min(), y) for y in range(2700, 3500, 5)]
    pts += [(np.nonzero(fg[y])[0].max(), y) for y in list(range(2600, 2820, 5)) + list(range(3380, 3600, 5))]  # clear of the crown
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case circle fit x2 = {CASE_MM} mm (listing)", "case_circle_px": [round(cx, 1), round(cy, 1), round(rad, 1)]}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["ring_radius_px"].items()}
    out["rings_mm"]["case"] = CASE_MM / 2

    h = fg.shape[0]
    prof = []
    for y_mm in np.arange(-37.5, 37.51, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    sil = {p[0]: p for p in prof}
    half = lambda y: sum((sil[k][1] + sil[k][2]) / 2 for k in (round(y, 2), round(-y, 2))) / 2
    # strap just past the lug tips (24-26 mm), where it is still flat to the camera
    inner = float(np.median([half(y) for y in np.arange(24, 26.01, 0.25)]))
    tips = []
    for sy in (1, -1):
        tips.append(next(float(y) for y in np.arange(18, 27, 0.25)
                         if (sil[round(sy * y, 2)][1] + sil[round(sy * y, 2)][2]) / 2 < inner + 0.3))
    from_y = next(float(y) for y in np.arange(12, 20, 0.25) if half(y) > math.sqrt(max(CASE_MM ** 2 / 4 - y * y, 0)) + 0.15)
    out["lug"] = {"inner_x_mm": round(inner, 3), "tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)},
                  "from_y_mm": from_y, "outer_x_mm": round(max(half(y) for y in np.arange(from_y, tips[0], 0.25)), 3),
                  "step_x_mm": round(sum(abs(x - px0) for x in M["lug_step_x_px"]) / 2 / S, 3)}
    out["strap_photo_end_mm"] = {"top": round((py0 - np.nonzero(fg[:, px0])[0].min()) / S - 0.2, 2),
                                 "bottom": round((np.nonzero(fg[:, px0])[0].max() - py0) / S - 0.2, 2)}
    out["checks"] = {"strap_width_mm": round(2 * inner, 2), "lug_to_lug_mm": round(sum(tips), 2)}

    def posed(angle, local):  # local (x across, y along) px -> posed mm
        t = math.radians(angle)
        return [[round((x * math.cos(t) + y * math.sin(t)) / S, 3), round((-x * math.sin(t) + y * math.cos(t)) / S, 3)] for x, y in local]

    def lance(profile, sign=1):
        right = [(w, sign * d) for d, w in profile]
        return right + [(-w, sign * d) for d, w in reversed(profile) if w > 0]

    ang = lambda p, o=(px0, py0): math.degrees(math.atan2(p[0] - o[0], o[1] - p[1])) % 360
    hands = {}
    for name in ("hour", "minute", "seconds"):
        hm = M[name]
        a = ang(hm["tip"])
        hands[name] = {"angle_deg": round(a, 2), "length_mm": round(hm["profile"][-1][0] / S, 3), "outline_mm": posed(a, lance(hm["profile"]))}
    hands["seconds"]["tail_mm"] = posed(hands["seconds"]["angle_deg"], lance(M["seconds"]["tail"], -1))
    out["hands"] = hands
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub_px"].items()}

    subs = {}
    for k, sd in M["subdials"].items():
        c = sd["centre"]
        a = ang(sd["tip"], c)
        cm = mm(c)
        shift = lambda poly: [[round(x + cm[0], 3), round(y + cm[1], 3)] for x, y in poly]
        subs[k] = {"centre_mm": cm, "hand_angle_deg": round(a, 2), "hand_length_mm": round(sd["profile"][-1][0] / S, 3),
                   "hand_mm": shift(posed(a, lance(sd["profile"])))}
        if sd["tail"]:
            subs[k]["tail_mm"] = shift(posed((ang(sd["tail"], c) + 180) % 360, lance(sd["tail_profile"], -1)))
    out["subdials"] = subs
    out["sub_hub_mm"] = {k: round(v / S, 3) for k, v in M["sub_hub_px"].items()}

    cr = M["crown"]
    out["crown"] = {"angle_deg": round(ang((cr["x_from_to"][1], cr["centre_y"])), 2), "radius_mm": round(cr["radius"] / S, 3),
                    "neck_radius_mm": round(cr["neck_radius"] / S, 3), "r_from_to_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(cx), int(cy)), int(rad), (0, 0, 255), 2)
        for r in M["ring_radius_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 128, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, Pp((-l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, Pp((r_, y_mm)), 3, (0, 255, 0), -1)
        polys = [hd["outline_mm"] for hd in hands.values()] + [hands["seconds"]["tail_mm"]]
        polys += [s[k] for s in subs.values() for k in ("hand_mm", "tail_mm") if k in s]
        for poly in polys:
            cv2.polylines(ov, [np.array([Pp(p) for p in poly])], True, (0, 255, 255), 2)
        cv2.circle(ov, (px0, py0), M["hub_px"]["radius"], (255, 0, 255), 2)
        for sd in M["subdials"].values():
            cv2.circle(ov, tuple(sd["centre"]), M["sub_hub_px"]["radius"], (255, 0, 255), 2)
        lg = out["lug"]
        for sy in (1, -1):
            cv2.line(ov, Pp((-20, sy * lg["tip_mm"]["mean"])), Pp((20, sy * lg["tip_mm"]["mean"])), (0, 128, 255), 2)
            cv2.line(ov, Pp((-20, sy * lg["from_y_mm"])), Pp((20, sy * lg["from_y_mm"])), (255, 255, 0), 1)
        for sx in (1, -1):
            cv2.line(ov, Pp((sx * inner, -36)), Pp((sx * inner, 36)), (0, 128, 255), 1)
            cv2.line(ov, Pp((sx * lg["step_x_mm"], -26)), Pp((sx * lg["step_x_mm"], 26)), (255, 0, 128), 1)
        k = out["crown"]
        for r_ in k["r_from_to_mm"]:
            cv2.line(ov, Pp((r_, -k["radius_mm"])), Pp((r_, k["radius_mm"])), (255, 0, 128), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "rings_mm", "lug", "strap_photo_end_mm", "checks", "crown")},
                     default=float), "->", dest)
