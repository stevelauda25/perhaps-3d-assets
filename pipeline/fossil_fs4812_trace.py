"""Measure the Fossil Grant FS4812 front photo (white background, 2900 x 2900) into mm. numpy + OpenCV.

    python3 -B -m pipeline.fossil_fs4812_trace [out.json] [overlay.png]   # default config/watches/fossil-fs4812-trace.json

Anchor: case circle (left flank plus the bezel's top and bottom edges; the right flank carries the crown, pushers and the
crown-side lobe) = 44 mm (listing); strap width and lug-to-lug are reported as checks. mm, x right, y toward 12, origin =
hand pivot. Hands, sub-dials, hubs, pushers and crown come from 10 px gridded crops (MANUAL_PX, about +-0.15 mm); hand
angles from a scan of the white pixels along rays from each pivot, widths from perpendicular scans. Hands are stored posed.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/fossil-fs4812/front_2900x2900.png"
OUT = ROOT / "config/watches/fossil-fs4812-trace.json"
CASE_MM = 44.0  # listing: case diameter 44 mm

MANUAL_PX = {
    "hand_pivot": [1413, 1445],
    # polished bezel inner edge, inner edge of the minute-track flange (= flat dial edge)
    "ring_radius_px": {"bezel_inner": 638, "flange_inner": 547},
    # (distance from the pivot, half width) from the hub to the tip; lume = white insert inside the polished frame
    "hour": {"angle": 299.6, "profile": [[0, 22], [60, 24], [120, 30.5], [180, 37], [245, 44.5], [258, 44], [300, 21], [332, 0]],
             "lume": [[45, 14], [120, 23], [180, 30], [245, 37], [258, 36], [295, 15], [318, 0]]},  # sword with a pointed tip
    "minute": {"angle": 59.6, "profile": [[0, 20], [120, 22.5], [240, 30], [360, 37], [452, 43.5], [480, 32], [512, 12], [542, 0]],
               "lume": [[45, 12], [120, 15.5], [240, 23], [360, 30], [452, 36], [480, 25], [505, 7], [520, 0]]},
    "seconds": {"angle": 209.0, "profile": [[0, 7], [200, 6], [400, 5], [540, 3.5], [590, 0]],  # chrono seconds needle
                "tail": [[0, 8], [120, 8], [129, 0]]},
    "hub_px": {"radius": 28, "pin": 10},
    "subdials": {
        "left": {"centre": [1154, 1450], "angle": 0.5, "profile": [[0, 10], [24, 9], [60, 8], [90, 6], [104, 4], [114, 0]]},
        "right": {"centre": [1670, 1457], "angle": 359.0, "profile": [[0, 10], [24, 9], [60, 8], [90, 6], [104, 4], [114, 0]]},
        "bottom": {"centre": [1412, 1709], "angle": 1.1, "profile": [[0, 10], [56, 9], [90, 9], [104, 7], [130, 6], [140, 3.5], [155, 0]]},
    },
    "sub_hub_px": {"radius": 20, "pin": 6},
    # knurled crown at 3: neck start, knurl start, knurl end (x px on the pivot row), radius
    "crown": {"radius": 100, "neck_radius": 60, "x_from": [2170, 2195, 2252]},
    # chrono pushers at 2 and 4: axis angle, radial from-to (px from the pivot), radius, stem radius
    "pushers": {"angles": [59.8, 120.2], "r_from_to": [781, 833], "radius": 57, "stem_radius": 32},
    # crown-side lobe of the case between the pushers: silhouette rows (y px) and its edge beside the crown
    "lobe": {"y_from_to": [1110, 1780], "crown_rows": [1335, 1555], "x_at_crown": 2190},
}
ARTEFACTS = ["Roman numerals, FOSSIL logo, sub-dial scales and the recessed chrono track stay in the dial map (flat)",
             "minute track with 5-60 numbers on the flange: in the dial map, mapped onto a cone",
             "the bezel's black reflection on the left and right is lighting, not a second colour: one polished bezel"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    g = im.mean(2)
    fg = im.min(2) < 215
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    pts = [(np.nonzero(fg[y])[0].min(), y) for y in range(1050, 1850, 5)]
    for x in range(1250, 1580, 10):  # bezel edges over the dark strap: first bright pixel
        pts.append((x, next(y for y in range(550, 800) if g[y, x] > 150)))
        pts.append((x, next(y for y in range(2350, 2100, -1) if g[y, x] > 150)))
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case circle fit x2 = {CASE_MM} mm (listing)", "case_circle_px": [round(cx, 1), round(cy, 1), round(rad, 1)],
           "case_centre_off_pivot_mm": mm((cx, cy))}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["ring_radius_px"].items()}
    out["rings_mm"]["case"] = CASE_MM / 2

    h = fg.shape[0]
    prof = []
    for y_mm in np.arange(-40, 40.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    sil = {p[0]: p for p in prof}
    both = lambda y: sum((sil[k][1] + sil[k][2]) / 2 for k in (round(y, 2), round(-y, 2))) / 2
    half = lambda y: (sil[round(y, 2)][1] + sil[round(-y, 2)][1]) / 2  # lugs: left flank only (the right carries pushers and the lobe)
    inner = float(np.median([both(y) for y in np.arange(28, 30.01, 0.25)]))  # strap just past the lug tips, still flat
    tips = []
    for sy in (1, -1):
        tips.append(next(float(y) for y in np.arange(20, 30, 0.25)
                         if sil[round(sy * y, 2)][1] < inner + 0.3))
    from_y = next(float(y) for y in np.arange(12, 22, 0.25) if half(y) > math.sqrt(max(CASE_MM ** 2 / 4 - y * y, 0)) + 0.15)
    out["lug"] = {"inner_x_mm": round(inner, 3), "tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)},
                  "from_y_mm": from_y, "outer_x_mm": round(max(half(y) for y in np.arange(from_y, tips[0], 0.25)), 3)}
    out["checks"] = {"strap_width_mm": round(2 * inner, 2), "lug_to_lug_mm": round(sum(tips), 2)}

    def posed(angle, local):  # local (x across, y along) px -> posed mm about the pivot
        t = math.radians(angle)
        return [[round((x * math.cos(t) + y * math.sin(t)) / S, 3), round((-x * math.sin(t) + y * math.cos(t)) / S, 3)] for x, y in local]

    def lance(profile, sign=1):
        right = [(w, sign * d) for d, w in profile]
        return right + [(-w, sign * d) for d, w in reversed(profile) if w > 0]

    hands = {}
    for name in ("hour", "minute", "seconds"):
        hm = M[name]
        hands[name] = {"angle_deg": hm["angle"], "length_mm": round(hm["profile"][-1][0] / S, 3), "outline_mm": posed(hm["angle"], lance(hm["profile"]))}
        if "lume" in hm:
            hands[name]["lume_mm"] = posed(hm["angle"], lance(hm["lume"]))
    hands["seconds"]["tail_mm"] = posed(M["seconds"]["angle"], lance(M["seconds"]["tail"], -1))
    out["hands"] = hands
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub_px"].items()}

    subs = {}
    for k, sd in M["subdials"].items():
        cm = mm(sd["centre"])
        subs[k] = {"centre_mm": cm, "hand_angle_deg": sd["angle"], "hand_length_mm": round(sd["profile"][-1][0] / S, 3),
                   "hand_mm": [[round(x + cm[0], 3), round(y + cm[1], 3)] for x, y in posed(sd["angle"], lance(sd["profile"]))]}
    out["subdials"] = subs
    out["sub_hub_mm"] = {k: round(v / S, 3) for k, v in M["sub_hub_px"].items()}

    cr = M["crown"]
    out["crown"] = {"angle_deg": 90.0, "radius_mm": round(cr["radius"] / S, 3), "neck_radius_mm": round(cr["neck_radius"] / S, 3),
                    "r_from_to_mm": [round((x - px0) / S, 3) for x in cr["x_from"]]}
    pu = M["pushers"]
    out["pushers"] = {"angles_deg": pu["angles"], "r_from_to_mm": [round(v / S, 3) for v in pu["r_from_to"]],
                      "radius_mm": round(pu["radius"] / S, 3), "stem_radius_mm": round(pu["stem_radius"] / S, 3)}
    lb = M["lobe"]
    rows = range(lb["y_from_to"][0], lb["y_from_to"][1] + 1, 5)
    out["lobe_right_mm"] = [[round(-(y - py0) / S, 3), round(((lb["x_at_crown"] if lb["crown_rows"][0] <= y <= lb["crown_rows"][1]
                                                              else np.nonzero(fg[y])[0].max()) - px0) / S, 3)] for y in rows]
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
        polys = [hd[k] for hd in hands.values() for k in ("outline_mm", "lume_mm", "tail_mm") if k in hd] + [s["hand_mm"] for s in subs.values()]
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
            cv2.line(ov, Pp((sx * inner, -38)), Pp((sx * inner, 38)), (0, 128, 255), 1)
        cv2.polylines(ov, [np.array([Pp((x, y)) for y, x in out["lobe_right_mm"]])], False, (255, 0, 128), 2)
        k = out["crown"]
        for r_ in k["r_from_to_mm"]:
            cv2.line(ov, Pp((r_, -k["radius_mm"])), Pp((r_, k["radius_mm"])), (255, 0, 128), 2)
        for a in pu["angles"]:
            t = math.radians(a)
            for r_ in pu["r_from_to"]:
                c0 = (px0 + r_ * math.sin(t), py0 - r_ * math.cos(t))
                d = (pu["radius"] * math.cos(t), pu["radius"] * math.sin(t))
                cv2.line(ov, (int(c0[0] - d[0]), int(c0[1] - d[1])), (int(c0[0] + d[0]), int(c0[1] + d[1])), (255, 0, 128), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "case_centre_off_pivot_mm", "rings_mm", "lug", "checks", "crown", "pushers")},
                     default=float), "->", dest)
