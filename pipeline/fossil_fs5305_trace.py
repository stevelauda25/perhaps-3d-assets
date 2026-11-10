"""Measure the Fossil The Minimalist FS5305 front photo (white background, 2606 x 2606) into mm. numpy + OpenCV.

    python3 -B -m pipeline.fossil_fs5305_trace [out.json] [overlay.png]   # default config/watches/fossil-fs5305-trace.json

Anchor: case circle (fitted on both flanks clear of the crown and lugs) = 44 mm (listing); the strap width is reported as a
check. mm, x right, y toward 12, origin = hand pivot.
Hands: each hand's centre line is fitted on its bright part (beige lume, orange seconds) along rays from the pivot; the lume
and orange widths are scanned along that line, the black frames around the lume and the needle tips come from 10-20 px
gridded crops (MANUAL_PX, about +-0.1 mm). Hands are stored posed. Crown and rings from gridded crops.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/fossil-fs5305/front_2606x2606.png"
OUT = ROOT / "config/watches/fossil-fs5305-trace.json"
CASE_MM = 44.0  # listing: case diameter 44 mm

MANUAL_PX = {
    "hand_pivot": [1280, 1304],
    # inner edge of the polished bezel (crystal opening), inner edge of the flat minute track (= flat dial edge)
    "ring_radius_px": {"bezel_inner": 600, "track_inner": 540},
    # tip: a point on the bright part, for the first axis guess; scan: distance range of the bright part;
    # frame: black frame (distance, half width) from the pivot to the needle tip
    "hour": {"tip": [962, 1130], "scan": [80, 270],
             "frame": [[0, 4], [58, 4], [72, 19], [268, 19], [292, 6], [300, 3.5], [360, 1.5], [364, 0]]},
    "minute": {"tip": [1577, 1132], "scan": [72, 318],
               "frame": [[0, 4], [52, 4], [64, 18], [318, 18], [344, 4], [350, 3], [424, 1.5], [428, 0]]},
    "seconds": {"tip": [1013, 1757], "scan": [40, 480]},  # orange needle, half widths scanned
    "seconds_tail": {"tip": [1370, 1140], "scan": [24, 186]},  # orange spear counterweight
    "hub_px": {"radius": 27, "collar": 33},  # orange seconds hub, black hour/minute collar under it
    # knurled crown at 3: y top/bottom, x of the case edge, x of the end
    "crown": {"y_top_bottom": [1238, 1380], "x_from_to": [1987, 2036], "teeth": 20},
}
ARTEFACTS = ["applied bar indices (beige with dark outlines), the FOSSIL logo, minute track ticks, the orange track numerals and the "
             "orange marker at 6: kept in the dial map (flat)",
             "black frames of the hour and minute hands are black on the black dial: widths read from gridded crops, not thresholds"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 215
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    # case flanks near the pivot row; the right flank above and below the crown
    pts = [(np.nonzero(fg[y])[0].min(), y) for y in range(950, 1650, 5)]
    pts += [(np.nonzero(fg[y])[0].max(), y) for y in list(range(900, 1180, 5)) + list(range(1440, 1700, 5))]
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case circle fit x2 = {CASE_MM} mm (listing)", "case_circle_px": [round(cx, 1), round(cy, 1), round(rad, 1)]}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["ring_radius_px"].items()}
    out["rings_mm"]["case"] = CASE_MM / 2

    h = fg.shape[0]
    prof = []
    for y_mm in np.arange(-40.0, 40.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    sil = {p[0]: p for p in prof}
    half = lambda y: sum((sil[k][1] + sil[k][2]) / 2 for k in (round(y, 2), round(-y, 2))) / 2
    # strap just past the lug tips (26-28 mm), where it is still flat to the camera
    inner = float(np.median([half(y) for y in np.arange(26, 28.01, 0.25)]))
    tips = []
    for sy in (1, -1):
        tips.append(next(float(y) for y in np.arange(20, 30, 0.25)
                         if (sil[round(sy * y, 2)][1] + sil[round(sy * y, 2)][2]) / 2 < inner + 0.3))
    from_y = next(float(y) for y in np.arange(12, 22, 0.25) if half(y) > math.sqrt(max(CASE_MM ** 2 / 4 - y * y, 0)) + 0.15)
    out["lug"] = {"inner_x_mm": round(inner, 3), "tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)},
                  "from_y_mm": from_y, "outer_x_mm": round(max(half(y) for y in np.arange(from_y, tips[0], 0.25)), 3)}
    out["strap_photo_end_mm"] = {"top": round((py0 - np.nonzero(fg[:, px0])[0].min()) / S - 0.2, 2),
                                 "bottom": round((np.nonzero(fg[:, px0])[0].max() - py0) / S - 0.2, 2)}
    out["checks"] = {"strap_width_mm": round(2 * inner, 2), "lug_to_lug_mm": round(sum(tips), 2)}

    f = im.astype(np.float32)
    masks = {"lume": f.min(2) > 140, "orange": f[..., 2] - f[..., 0] > 90}
    pv = np.float32([px0, py0])

    def scan(mask, tip, rng, half_px=24, step=2.0):
        """Fit the hand's centre line on the bright part, then (distance, half width) along it, in px."""
        t = np.float32(tip)
        u = (t - pv) / float(np.hypot(*(t - pv)))
        rows = []
        for _ in range(2):  # second pass on the fitted line
            n = np.float32([-u[1], u[0]])
            rows = []
            for s in np.arange(rng[0], rng[1] + 0.1, step):
                ws = [w for w in np.arange(-half_px, half_px + 0.5, 0.5)
                      if mask[int(round(pv[1] + u[1] * s + n[1] * w)), int(round(pv[0] + u[0] * s + n[0] * w))]]
                if ws:
                    rows.append((float(s), (min(ws) + max(ws)) / 2, (max(ws) - min(ws)) / 2))
            R = np.array(rows)
            c1, c0 = np.polyfit(R[:, 0], R[:, 1], 1)
            if _ == 0:
                u = u + n * c1
                u /= float(np.hypot(*u))
                off = c0
        n = np.float32([-u[1], u[0]])
        o = pv + n * float(off)  # the line's foot at the pivot (hands sit a few px off the hub centre in the photo)
        return o, u, n, [(r[0], r[2]) for r in rows]

    def smooth(prof, k=5):
        w = [p[1] for p in prof]
        return [(prof[i][0], float(np.median(w[max(i - k, 0):i + k + 1]))) for i in range(len(prof))]

    def poly(o, u, n, profile, sign=1):  # (distance, half width) about the fitted line -> outline mm
        side = [(d, w) for d, w in profile]
        pts = [o + u * (sign * d) + n * w for d, w in side] + [o + u * (sign * d) - n * w for d, w in reversed(side) if w > 0]
        return [[round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)] for p in pts]

    ang = lambda u: math.degrees(math.atan2(u[0], -u[1])) % 360
    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        o, u, n, lp = scan(masks["lume"], hm["tip"], hm["scan"])
        lp = smooth(lp)
        d0, d1 = lp[0][0], lp[-1][0]
        # lume: rounded start, measured body, pointed end
        lume = [(d0 - 6, 0), (d0 - 4, lp[0][1] * 0.6)] + [(d, w) for d, w in lp] + [(d1 + 8, 0)]
        hands[name] = {"angle_deg": round(ang(u), 2), "length_mm": round(hm["frame"][-1][0] / S, 3),
                       "outline_mm": poly(o, u, n, hm["frame"]), "lume_mm": poly(o, u, n, lume),
                       "lume_half_width_mm": round(float(np.median([w for _, w in lp])) / S, 3)}
    o, u, n, sp = scan(masks["orange"], M["seconds"]["tip"], M["seconds"]["scan"], half_px=16)
    sp = smooth(sp, 8)
    # needle from the hub; the scanned half width includes the anti-aliased edge, so 1 px less
    sec = [(0, sp[0][1] - 1)] + [(d, w - 1) for d, w in sp[::10]] + [(M["seconds"]["scan"][1] + 40, 1.5), (M["seconds"]["scan"][1] + 46, 0)]
    hands["seconds"] = {"angle_deg": round(ang(u), 2), "length_mm": round(sec[-1][0] / S, 3), "outline_mm": poly(o, u, n, sec)}
    _, ut, _, tp = scan(masks["orange"], M["seconds_tail"]["tip"], M["seconds_tail"]["scan"], half_px=24, step=3.0)
    tp = smooth(tp, 3)
    tail = [(0, tp[0][1] - 1)] + [(d, w - 1) for d, w in tp[::4] if d < 168] + [(176, 10), (186, 4), (191, 0)]
    hands["seconds"]["tail_mm"] = poly(o, u, n, tail, -1)  # on the needle's own line (the scanned tail line agrees within 1 deg)
    hands["seconds"]["tail_angle_deg"] = round(ang(ut), 2)
    out["hands"] = hands
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub_px"].items()}

    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"angle_deg": round(ang(np.float32([1, -(py0 - (yt + yb) / 2) / (cr["x_from_to"][0] - px0)])), 2),
                    "radius_mm": round((yb - yt) / 2 / S, 3), "teeth": cr["teeth"],
                    "r_from_to_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(cx), int(cy)), int(rad), (0, 0, 255), 2)
        for r in M["ring_radius_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 128, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, Pp((-l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, Pp((r_, y_mm)), 2, (0, 255, 0), -1)
        for hd in hands.values():
            for k, col in (("outline_mm", (0, 255, 255)), ("lume_mm", (255, 255, 0)), ("tail_mm", (0, 255, 255))):
                if k in hd:
                    cv2.polylines(ov, [np.array([Pp(p) for p in hd[k]])], True, col, 1)
        for r in M["hub_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 0, 255), 1)
        lg = out["lug"]
        for sy in (1, -1):
            cv2.line(ov, Pp((-20, sy * lg["tip_mm"]["mean"])), Pp((20, sy * lg["tip_mm"]["mean"])), (0, 128, 255), 2)
            cv2.line(ov, Pp((-20, sy * lg["from_y_mm"])), Pp((20, sy * lg["from_y_mm"])), (255, 255, 0), 1)
        for sx in (1, -1):
            cv2.line(ov, Pp((sx * inner, -38)), Pp((sx * inner, 38)), (0, 128, 255), 1)
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
    print({k: (v["angle_deg"], v.get("lume_half_width_mm")) for k, v in data["hands"].items()}, data["hands"]["seconds"]["tail_angle_deg"])
