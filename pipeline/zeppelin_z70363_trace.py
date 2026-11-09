"""Measure the Zeppelin LZ129 Hindenburg Z70363 (7036-3) front photo (white background, 2648 x 2648) into mm. numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z70363_trace [out.json] [overlay.png]   # default config/watches/zeppelin-z70363-trace.json

Anchor: case circle (fitted on both flanks away from the crown, pusher and lugs) = 40 mm (listing); the strap width
(20 mm, the listing's 10 mm lug width is wrong) is reported as a check. mm, x right, y toward 12, origin = hand pivot.
The photo looks slightly from below: the case circle centre sits 6 px under the pivot, the model keeps the case on the pivot.
Hands, sub-dials, crown and pusher come from 10 px gridded crops (MANUAL_PX, about +-0.1 mm); hands are stored posed.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/zeppelin-z70363/front_2648.png"
OUT = ROOT / "config/watches/zeppelin-z70363-trace.json"
CASE_MM = 40.0  # listing: case 40 mm; strap measured 20 mm (listing says lug width 10 mm, wrong)
STRAP_MM = 20.0

MANUAL_PX = {
    "hand_pivot": [1319, 1282],
    "ring_radius_px": {"bezel_inner": 664, "dial_edge": 636},
    # lance hands: tip, then (distance from the pivot, half width) from the hub to the tip
    "hour": {"tip": [962, 1052], "profile": [[0, 6], [60, 5], [186, 4], [196, 12], [212, 18], [232, 20], [256, 17], [280, 11],
                                              [304, 5], [316, 3.5], [416, 3.5], [425, 0]]},
    "minute": {"tip": [1792, 953], "profile": [[0, 6], [100, 6.5], [200, 9], [300, 10.5], [380, 10], [450, 7.5], [530, 4], [576, 0]]},
    "seconds": {"tip": [902, 1670], "profile": [[0, 4.5], [540, 4], [570, 0]],
                "tail": [[0, 6], [40, 9], [80, 10], [120, 7], [150, 2], [156, 0]]},  # rose gold counterweight
    "week": {"tip_centre": [1725, 1745], "profile": [[0, 4.5], [585, 4]], "crescent_px": [32, 22, 80]},  # outer r, inner r, half span deg
    "hub_radius_px": [45, 22],
    "subdials": {"day": {"centre": [1081, 1286], "ring_r": 150, "tip": [965, 1183]},
                 "date": {"centre": [1563, 1290], "ring_r": 160, "tip": [1677, 1180]}},
    "sub_hand_half_px": 5,
    "sub_hub_radius_px": 25,
    "crown": {"centre_y": 1290, "radius": 108, "collar_radius": 63, "x_from_to": [1999, 2045, 2130]},
    "pusher": {"head_centre": [1995, 1665], "head_radius": 60, "stem_radius": 30, "r_from_to": [688, 750, 809]},
}
ARTEFACTS = ["case side visible at the bottom (perspective from below): the bottom flank is 14 px wider than the top",
             "crystal glare over the date ring at 11-12 o'clock of the right sub-dial: stays in the photo map",
             "strap cut by the photo edge 33.6 mm above the pivot: the curled strap end reuses the last photo row"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 215
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    # case circle on the flanks: left 900-1150 and 1420-1650, right only clear of crown and pusher
    pts = []
    for y in list(range(900, 1150, 5)) + list(range(1420, 1650, 5)):
        pts.append((np.nonzero(fg[y])[0].min(), y))
    for y in list(range(900, 1100, 5)) + list(range(1430, 1550, 5)):
        pts.append((np.nonzero(fg[y])[0].max(), y))
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
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
    # left edge on the case (crown and pusher on the right), both edges on the lugs and strap; top and bottom averaged
    half = lambda y: sum((sil[k][1] if abs(y) < 15 else (sil[k][1] + sil[k][2]) / 2) for k in (round(y, 2), round(-y, 2))) / 2
    strap = [2 * half(y) for y in np.arange(24, 32.01, 0.25)]
    inner = float(np.median(strap)) / 2
    tips = []
    for sy in (1, -1):
        tips.append(next(float(y) for y in np.arange(18, 26, 0.25)
                         if (sil[round(sy * y, 2)][1] + sil[round(sy * y, 2)][2]) / 2 < inner + 0.35))
    from_y = next(float(y) for y in np.arange(12, 20, 0.25) if half(y) > math.sqrt(max(400 - y * y, 0)) + 0.15)
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
    wk = M["week"]
    a = ang(wk["tip_centre"])
    rc = math.hypot(wk["tip_centre"][0] - px0, wk["tip_centre"][1] - py0)
    ro, ri, span = wk["crescent_px"]
    arc = [(ro * math.sin(math.radians(180 + d)), rc + ro * math.cos(math.radians(180 + d))) for d in np.linspace(-span, span, 25)]
    arc += [(ri * math.sin(math.radians(180 + d)), rc + ri * math.cos(math.radians(180 + d))) for d in np.linspace(span, -span, 25)]
    hands["week"] = {"angle_deg": round(a, 2), "length_mm": round(wk["profile"][-1][0] / S, 3), "outline_mm": posed(a, lance(wk["profile"])),
                     "crescent_mm": posed(a, arc), "note": "calendar-week hand: steel shaft, rose gold crescent at the tip"}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]

    subs = {}
    for k, sd in M["subdials"].items():
        c = sd["centre"]
        a = ang(sd["tip"], c)
        L = math.hypot(sd["tip"][0] - c[0], sd["tip"][1] - c[1])
        w = M["sub_hand_half_px"]
        loc = posed(a, [(w, 0), (w, L - 8), (0, L), (-w, L - 8), (-w, 0)])
        subs[k] = {"centre_mm": mm(c), "ring_r_mm": round(sd["ring_r"] / S, 3), "hand_angle_deg": round(a, 2), "hand_length_mm": round(L / S, 3),
                   "hand_mm": [[round(x + mm(c)[0], 3), round(y + mm(c)[1], 3)] for x, y in loc]}
    out["subdials"] = subs
    out["sub_hub_radius_mm"] = round(M["sub_hub_radius_px"] / S, 3)

    cr = M["crown"]
    out["crown"] = {"angle_deg": round(ang((cr["x_from_to"][0], cr["centre_y"])), 2), "radius_mm": round(cr["radius"] / S, 3),
                    "collar_radius_mm": round(cr["collar_radius"] / S, 3), "r_from_to_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}
    pu = M["pusher"]
    out["pusher"] = {"angle_deg": round(ang(pu["head_centre"]), 2), "head_radius_mm": round(pu["head_radius"] / S, 3),
                     "stem_radius_mm": round(pu["stem_radius"] / S, 3), "r_from_to_mm": [round(v / S, 3) for v in pu["r_from_to"]]}
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
        polys = [hd["outline_mm"] for hd in hands.values()] + [hands["seconds"]["tail_mm"], hands["week"]["crescent_mm"]]
        polys += [s["hand_mm"] for s in subs.values()]
        for poly in polys:
            cv2.polylines(ov, [np.array([Pp(p) for p in poly])], True, (0, 255, 255), 2)
        for s in subs.values():
            cv2.circle(ov, Pp(s["centre_mm"]), int(s["ring_r_mm"] * S), (255, 0, 255), 2)
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
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "rings_mm", "lug", "strap_photo_end_mm", "checks", "crown", "pusher")},
                     default=float), "->", dest)
