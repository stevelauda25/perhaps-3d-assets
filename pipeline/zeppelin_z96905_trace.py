"""Measure the Zeppelin Mediterranée Z96905 (9690-5) front photo (white background, 2730 x 3940) into mm. numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z96905_trace [out.json] [overlay.png]   # default config/watches/zeppelin-z96905-trace.json

Anchor: case circle (fitted on both flanks clear of the crown and lugs) = 42 mm (listing); the strap width is reported as a
check. mm, x right, y toward 12, origin = hand pivot (the case circle centre sits within 1 px of it).
Hands, the three sub-dials (day at 9, power reserve at 12, 24 h at 6), hubs and crown come from 10 px gridded crops
(MANUAL_PX, about +-0.1 mm); hands are stored posed. Sub-dial hands have a paddle tail opposite the pointer.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/zeppelin-z96905/front_2730x3940.png"
OUT = ROOT / "config/watches/zeppelin-z96905-trace.json"
CASE_MM = 42.0  # listing: case size 42.00 mm

MANUAL_PX = {
    "hand_pivot": [1249, 1911],
    # bezel inner edge, inner edge of the sloped pulsometer flange (= flat dial edge)
    "ring_radius_px": {"bezel_inner": 1038, "flange_inner": 881},
    # (distance from the pivot, half width) from the hub to the tip
    "hour": {"tip": [781, 1617], "profile": [[0, 10], [60, 8], [200, 6], [250, 9], [285, 20], [330, 28], [365, 24], [395, 12],
                                              [415, 6], [540, 6], [553, 0]]},  # needle with a teardrop bulb
    "minute": {"tip": [1735, 1262], "profile": [[0, 10], [150, 10], [260, 13], [400, 17], [520, 19], [620, 16], [760, 11],
                                                [800, 8], [811, 0]]},
    "seconds": {"tip": [1806, 1272], "profile": [[0, 7], [600, 5.5], [840, 5], [848, 0]],
                "tail": [[0, 7], [190, 6], [215, 14], [240, 12], [262, 0]]},  # black diamond counterweight
    "hub_px": {"radius": 68, "pin": 10},
    "subdials": {
        "day": {"centre": [849, 1915], "tip": [1010, 1785], "tail": [752, 1995],
                "profile": [[0, 7], [150, 5], [200, 4], [207, 0]], "tail_profile": [[0, 6], [70, 4], [88, 9], [108, 11], [122, 7], [127, 0]]},
        "power": {"centre": [1247, 1238], "tip": [973, 1402], "tail": None,
                  "profile": [[0, 4], [80, 3], [92, 10], [112, 13], [140, 10], [200, 5], [310, 2.5], [320, 0]]},
        "h24": {"centre": [1251, 2312], "tip": [1131, 2098], "tail": [1306, 2402],
                "profile": [[0, 6], [200, 4.5], [235, 4], [245, 0]], "tail_profile": [[0, 6], [50, 5], [75, 9], [98, 7], [104, 0]]},
    },
    "sub_hub_px": {"radius": 33, "pin": 10},
    # fluted crown at 3 with a domed end: neck start, flutes start, flutes end, dome end (x px on the centre row)
    "crown": {"centre_y": 1910, "radius": 165, "neck_radius": 95, "x_from_to": [2330, 2350, 2525, 2600]},
    # stepped lugs: the outer block and a lower inner step next to the strap, split at this distance from the centre line
    "lug_step_x_px": [592, 1906],
}
ARTEFACTS = ["applied gold Arabic numerals and the Z logo stay in the dial map (flat)",
             "pulsometer scale on the sloped flange: in the dial map, mapped onto a cone",
             "top strap shown curling away (foreshortened above 26 mm): the curled strap end reuses the photo rows"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 215
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    pts = []  # case flanks clear of the lugs (above 1450 / below 2400) and the crown (1720-2100)
    for y in list(range(1450, 1700, 5)) + list(range(2120, 2400, 5)):
        xs = np.nonzero(fg[y])[0]
        pts += [(xs.min(), y), (xs.max(), y)]
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
            subs[k]["tail_mm"] = shift(posed(a, lance(sd["tail_profile"], -1)))
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
