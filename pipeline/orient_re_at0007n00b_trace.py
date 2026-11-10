"""Measure the Orient Star RE-AT0007N00B front photo into mm. numpy + OpenCV.

    python3 -B -m pipeline.orient_re_at0007n00b_trace [out.json] [overlay.png]   # default config/watches/orient-re-at0007n00b-trace.json

Working reference: the 755 x 1126 retailer copy of the official render, enlarged 2x (Lanczos) as WATCH_PRODUCTION_WORKFLOW 0.2.
Anchor: case circle fitted on both flanks clear of the lugs and crown = 39.3 mm (listing); the strap between the lugs
(20.3 mm measured, 20 mm listed) is the check. mm, x right, y toward 12, origin = hand pivot.
The render is taken slightly from below: the case circle sits 0.9 mm below the pivot and the 6 o'clock lugs reach further
than the 12 o'clock ones. The model keeps the photo's own outline (the photo is projected on it from the front).
Hands, crown, rings, lug tips and strap edges are read from 20 px gridded crops (MANUAL_PX, about +-0.1 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-re-at0007n00b/front_2x_1510x2252.png"
OUT = ROOT / "config/watches/orient-re-at0007n00b-trace.json"
CASE_MM = 39.3  # listing: case diameter 39.3 mm

MANUAL_PX = {
    "hand_pivot": [720, 986],
    # dial flat edge (inner edge of the black minute track), crystal edge (inner edge of the polished bezel), about the pivot
    "ring_radius_px": {"dial_flat": 514, "crystal": 604},
    # hands: tip, tail end, half widths (base = widest point at base_r px from the pivot, hub = at the pivot)
    "hands": {"hour": {"tip": [452, 810], "tail": [822, 1062], "half_base": 21, "base_r": 90, "half_hub": 16},
              "minute": {"tip": [1112, 692], "tail": [660, 1040], "half_base": 15, "base_r": 110, "half_hub": 13},
              "seconds": {"tip": [428, 1424], "tail": [796, 869], "half_base": 3.5, "base_r": 30, "half_hub": 5}},
    "hub_px": 15,
    # per lug: tip row and inner (strap side) x; the outer edge is the silhouette
    "lugs": {"tl": {"tip_y": 270, "inner_x": 395}, "tr": {"tip_y": 288, "inner_x": 1091},
             "bl": {"tip_y": 1812, "inner_x": 365}, "br": {"tip_y": 1830, "inner_x": 1062}},
    # the deployant clasp hangs past the 4-5 o'clock lug: its outer edge is this line instead of the silhouette
    "br_outer_line": [[1200, 1640], [1150, 1830]],
    # crown at 3: y top / bottom, x where it leaves the case and of its end
    "crown": {"y_top_bottom": [912, 1135], "x_from_to": [1385, 1502], "teeth": 22},
}
ARTEFACTS = ["Roman numerals, applied indices, minute track, power reserve scale and hand, open-heart movement and the logo stay in the photo map (flat)",
             "hands are needles from the picked tips, tails and half widths; the photo shows on them, so a px of outline error shows dial pixels at the edge"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 235
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    pts = [(np.nonzero(fg[y])[0].min(), y) for y in range(760, 1240, 6)]
    pts += [(np.nonzero(fg[y])[0].max(), y) for y in list(range(760, 830, 6)) + list(range(1160, 1240, 6))]
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case circle fit x2 = {CASE_MM} mm (listing)", "case_circle_px": [round(cx, 1), round(cy, 1), round(rad, 1)],
           "case_centre_mm": mm((cx, cy)), "case_radius_mm": CASE_MM / 2}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["ring_radius_px"].items()}
    circle_x = lambda y, sx: cx + sx * math.sqrt(max(rad * rad - (y - cy) ** 2, 0))

    # ---- lugs: silhouette outer edge from the tip row to where it meets the case circle; straight inner edge ----
    (bx0, by0), (bx1, by1) = M["br_outer_line"]
    lugs = {}
    for key, lg in M["lugs"].items():
        sx, sy = (-1 if key[1] == "l" else 1), (1 if key[0] == "t" else -1)
        rows = range(lg["tip_y"], int(cy), 2) if sy > 0 else range(lg["tip_y"], int(cy), -2)
        edge = []
        for y in rows:
            xs = np.nonzero(fg[y])[0]
            x = xs.min() if sx < 0 else xs.max()
            if key == "br" and y > by0:
                x = min(x, bx0 + (bx1 - bx0) * (y - by0) / (by1 - by0))
            edge.append((float(x), y))
            if sx * (x - circle_x(y, sx)) < 2:  # back on the case circle
                break
        xs_ = np.array([p[0] for p in edge])
        xs_ = np.convolve(np.pad(xs_, 3, mode="edge"), np.ones(7) / 7, mode="valid")  # 14 px mean drops the rendering noise
        edge = [(x, y) for x, (_, y) in zip(xs_, edge)]
        y_end = edge[-1][1]
        into = [(circle_x(y_end + sy * k * 10, sx) - sx * 4, y_end + sy * k * 10) for k in range(1, 6)]  # 1.5 mm into the case
        poly = [(lg["inner_x"], lg["tip_y"])] + edge + into + [(lg["inner_x"], into[-1][1])]
        lugs[key] = {"outline_mm": [mm(p) for p in poly], "tip_y_mm": mm((0, lg["tip_y"]))[1], "inner_x_mm": mm((lg["inner_x"], 0))[0],
                     "meets_case_y_mm": mm((0, y_end))[1]}
    out["lugs"] = lugs
    out["strap_mm"] = {side: {"x": [lugs[side[0] + "l"]["inner_x_mm"], lugs[side[0] + "r"]["inner_x_mm"]],
                              "tip_y": round((abs(lugs[side[0] + "l"]["tip_y_mm"]) + abs(lugs[side[0] + "r"]["tip_y_mm"])) / 2, 3)}
                       for side in ("top", "bottom")}
    out["checks"] = {"strap_width_mm": {s: round(v["x"][1] - v["x"][0], 2) for s, v in out["strap_mm"].items()},
                     "lug_to_lug_mm": round(out["strap_mm"]["top"]["tip_y"] + out["strap_mm"]["bottom"]["tip_y"], 2)}

    # ---- hands: needles from tip to tail, widest at base_r ----
    ang = lambda dx, dy: math.degrees(math.atan2(dx, -dy)) % 360
    hands = {}
    o = np.float32([px0, py0])
    for name, h in M["hands"].items():
        u = np.float32(h["tip"]) - o
        L = float(np.hypot(*u))
        u /= L
        n = np.float32([-u[1], u[0]])
        Lt = float(np.hypot(*(np.float32(h["tail"]) - o)))
        b = o + u * h["base_r"]
        poly = [o + u * L, b - n * h["half_base"], o - n * h["half_hub"], o - u * Lt, o + n * h["half_hub"], b + n * h["half_base"]]
        hands[name] = {"angle_deg": round(ang(*u), 2), "length_mm": round(L / S, 3), "outline_mm": [mm(p) for p in poly]}
    out["hands"] = hands
    out["hub_mm"] = round(M["hub_px"] / S, 3)

    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"centre_y_mm": mm((0, (yt + yb) / 2))[1], "radius_mm": round((yb - yt) / 2 / S, 3), "teeth": cr["teeth"],
                    "x_from_to_mm": [mm((x, 0))[0] for x in cr["x_from_to"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(cx), int(cy)), int(rad), (0, 0, 255), 2)
        for r in M["ring_radius_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 128, 0), 2)
        for p in [v["outline_mm"] for v in lugs.values()] + [v["outline_mm"] for v in hands.values()]:
            cv2.polylines(ov, [np.array([Pp(q) for q in p])], True, (0, 200, 255), 2)
        for side, sy in (("top", 1), ("bottom", -1)):
            s = out["strap_mm"][side]
            cv2.line(ov, Pp((s["x"][0], sy * s["tip_y"])), Pp((s["x"][1], sy * s["tip_y"])), (0, 255, 0), 2)
        k = out["crown"]
        for x in k["x_from_to_mm"]:
            cv2.line(ov, Pp((x, k["centre_y_mm"] - k["radius_mm"])), Pp((x, k["centre_y_mm"] + k["radius_mm"])), (255, 0, 128), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "case_centre_mm", "rings_mm", "strap_mm", "checks", "crown")},
                     default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()},
          {k: (v["tip_y_mm"], v["meets_case_y_mm"], len(v["outline_mm"])) for k, v in data["lugs"].items()})
