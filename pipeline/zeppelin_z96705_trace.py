"""Measure the Zeppelin Mediterranee 1921 chronograph Z96705 (9670-5) front photo (white background, 3200 x 4832) into mm.
numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z96705_trace [out.json] [overlay.png]   # default config/watches/zeppelin-z96705-trace.json

Anchor: case circle (fitted on both flanks away from the crown, pushers and lugs) = 42 mm (listing); the strap width (22 mm,
listing) is reported as a check. mm, x right, y toward 12, origin = hand pivot; the model keeps the case on the pivot.
Hands, sub-dials, crown and pushers come from 10-20 px gridded crops (MANUAL_PX, about +-0.15 mm); hands are stored posed.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/zeppelin-z96705/front_3200x4832.png"
OUT = ROOT / "config/watches/zeppelin-z96705-trace.json"
CASE_MM = 42.0  # listing: case 42 mm, 12 mm thick
STRAP_MM = 22.0  # listing: 22 mm brown leather strap

MANUAL_PX = {
    "hand_pivot": [1528, 2347],
    "ring_radius_px": {"bezel_inner": 1170, "dial_edge": 1072},
    # tip, then (distance from the pivot, half width) from the hub to the tip
    "hour": {"tip": [1008, 2000], "profile": [[0, 10], [290, 8], [310, 16], [340, 27], [380, 31], [420, 26], [455, 14], [475, 6],
                                              [600, 4.5], [625, 0]]},  # shaft with an oval bulb
    "minute": {"tip": [2172, 1695], "profile": [[0, 10], [300, 12], [600, 11], [800, 7], [916, 0]]},
    "seconds": {"tip": [1530, 1402], "profile": [[0, 10], [920, 9], [932, 12], [945, 0]],  # centre chronograph seconds
                "tail": [[0, 8], [225, 7], [240, 13], [255, 16.5], [275, 9], [293, 0]]},  # lozenge counterweight toward 6
    "hub_radius_px": [80, 45],
    # sub-dial needles: hub centre, tip, tail (distance, half width) with a lozenge end, hub radius
    "subdials": {"left": {"centre": [1023, 2356], "tip": [1021, 2065], "half": [5, 3.5],
                          "tail": [[0, 5], [92, 4], [100, 10], [115, 14], [130, 8], [143, 0]]},
                 "right": {"centre": [2029, 2341], "tip": [2225, 2134], "half": [6, 3.5],
                           "tail": [[0, 6], [60, 4], [70, 8], [85, 10], [100, 6], [134, 0]]}},
    "sub_hub_radius_px": 35,
    "crown": {"centre_y": 2357, "radius": 168, "collar_radius": 120, "x_from_to": [2745, 2775, 2955, 3050]},
    # rectangular pushers: clock angle, tangential half width, outer radius (px from the pivot)
    "pushers": {"upper": [59.5, 170, 1349], "lower": [119.5, 170, 1354]},
}
ARTEFACTS = ["date window, tachymeter, telemeter and sub-dial scales, printed numerals and the airship logo stay in the photo map (flat)",
             "glare on the crystal over the tachymeter at 2-3 o'clock stays in the photo map",
             "pusher faces read dark (reflection of the surroundings); modelled as polished steel blocks"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 215
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    # case circle on the flanks between the lugs, right side clear of the crown and pushers
    pts = []
    for y in range(1600, 3100, 10):
        pts.append((np.nonzero(fg[y])[0].min(), y))
    for y in list(range(1950, 2130, 10)) + list(range(2580, 2750, 10)):
        pts.append((np.nonzero(fg[y])[0].max(), y))
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case circle fit x2 = {CASE_MM} mm (listing); strap {STRAP_MM} mm as a check",
           "case_circle_px": [round(cx, 1), round(cy, 1), round(rad, 1)]}
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
    # left edge on the case (crown on the right), both edges on the lugs and strap; top and bottom averaged
    half = lambda y: sum((sil[k][1] if abs(y) < 15 else (sil[k][1] + sil[k][2]) / 2) for k in (round(y, 2), round(-y, 2))) / 2
    strap = [2 * half(y) for y in np.arange(24, 32.01, 0.25)]
    inner = float(np.median(strap)) / 2
    tips = []
    for sy in (1, -1):
        tips.append(next(float(y) for y in np.arange(18, 26, 0.25)
                         if (sil[round(sy * y, 2)][1] + sil[round(sy * y, 2)][2]) / 2 < inner + 0.35))
    from_y = next(float(y) for y in np.arange(12, 20, 0.25) if half(y) > math.sqrt(max((CASE_MM / 2) ** 2 - y * y, 0)) + 0.15)
    out["lug"] = {"inner_x_mm": round(inner, 3), "tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)},
                  "from_y_mm": from_y, "outer_x_mm": round(max(half(y) for y in np.arange(from_y, tips[0], 0.25)), 3)}
    out["strap_photo_end_mm"] = {"top": round((py0 - np.nonzero(fg[:, px0])[0].min()) / S - 0.2, 2),
                                 "bottom": round((np.nonzero(fg[:, px0])[0].max() - py0) / S - 0.2, 2)}
    out["checks"] = {"strap_width_mm": round(2 * inner, 2), "listed_strap_mm": STRAP_MM, "lug_to_lug_mm": round(sum(tips), 2)}

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
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]

    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    subs = {}
    for k, sd in M["subdials"].items():
        c = sd["centre"]
        a = ang(sd["tip"], c)
        L = math.hypot(sd["tip"][0] - c[0], sd["tip"][1] - c[1])
        w0, w1 = sd["half"]
        shift = lambda poly: [[round(x + mm(c)[0], 3), round(y + mm(c)[1], 3)] for x, y in poly]
        subs[k] = {"centre_mm": mm(c), "hand_angle_deg": round(a, 2), "hand_length_mm": round(L / S, 3),
                   "hand_mm": shift(posed(a, lance([[0, w0], [L - 12, w1], [L, 0]]))), "tail_mm": shift(posed(a, lance(sd["tail"], -1)))}
    out["subdials"] = subs
    out["sub_hub_radius_mm"] = round(M["sub_hub_radius_px"] / S, 3)

    cr = M["crown"]
    out["crown"] = {"angle_deg": round(ang((cr["x_from_to"][0], cr["centre_y"])), 2), "radius_mm": round(cr["radius"] / S, 3),
                    "collar_radius_mm": round(cr["collar_radius"] / S, 3), "r_from_to_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}
    out["pushers"] = {k: {"angle_deg": a, "half_width_mm": round(w / S, 3), "outer_r_mm": round(r / S, 3)} for k, (a, w, r) in M["pushers"].items()}
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
        polys = [hd["outline_mm"] for hd in hands.values()] + [hands["seconds"]["tail_mm"], ] + [p for s_ in subs.values() for p in (s_["hand_mm"], s_["tail_mm"])]
        for poly in polys:
            cv2.polylines(ov, [np.array([Pp(p) for p in poly])], True, (0, 255, 255), 2)
        lg = out["lug"]
        for sy in (1, -1):
            cv2.line(ov, Pp((-20, sy * lg["tip_mm"]["mean"])), Pp((20, sy * lg["tip_mm"]["mean"])), (0, 128, 255), 2)
            cv2.line(ov, Pp((-20, sy * lg["from_y_mm"])), Pp((20, sy * lg["from_y_mm"])), (255, 255, 0), 1)
        for sx in (1, -1):
            cv2.line(ov, Pp((sx * inner, -36)), Pp((sx * inner, 36)), (0, 128, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "rings_mm", "lug", "strap_photo_end_mm", "checks", "crown", "pushers")},
                     default=float), "->", dest)
