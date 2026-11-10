"""Measure the Emporio Armani Matteo AR11328 front photo (white background, 4442 x 4442, upscaled) into mm. numpy + OpenCV.

    python3 -B -m pipeline.emporio_armani_ar11328_trace [out.json] [overlay.png]   # default config/watches/emporio-armani-ar11328-trace.json

Anchor: case circle (fitted on both flanks clear of the crown and lugs) = 43 mm (listing); the end cap width is reported as
a check against the 20 mm listing. mm, x right, y toward 12, origin = hand pivot.
The photo is soft (about 4x upscaled), so the hands (plain batons), hub, lug arm inner edges, end caps, crown and rings are
read from 25-50 px gridded crops (MANUAL_PX, about +-0.1 mm); only the case circle and the outer silhouette are traced.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/emporio-armani-ar11328/front_4442x4442.png"
OUT = ROOT / "config/watches/emporio-armani-ar11328-trace.json"
CASE_MM = 43.0  # listing: case diameter 43 mm

MANUAL_PX = {
    "hand_pivot": [2150, 2218],
    # crystal opening (inner edge of the bezel lip, = flat dial edge); top of the bezel (highlight band, left flank)
    "ring_radius_px": {"bezel_inner": 955, "bezel_top": 1010},
    # baton hands: centre of the rounded tip, half width of the light part
    "hour": {"tip": [1625, 1972], "half_width": 15},
    "minute": {"tip": [2803, 1700], "half_width": 11},
    "seconds": {"tip": [1772, 2945], "half_width": 4.5},
    "hub_radius": 54,
    # solid end caps between the lug arms: x from/to, y case side / outer end (12 and 6 o'clock)
    "cap": {"x": [1622, 2700], "top_y": [1020, 655], "bottom_y": [3470, 3800]},
    # lug arm inner edge (window side), top-left arm: (x, y) from under the cap down to the case
    "arm_inner": [[1560, 1040], [1490, 1275]],
    "arm_inner_bottom": [[1560, 3400], [1475, 3250]],
    # mesh between the caps (both ends agree within 10 px)
    "mesh_x": [1670, 2638],
    "mesh_rows_y": [3840, 4400],
    # black crown at 3: y top/bottom, x of the case edge, x of the end
    "crown": {"y_top_bottom": [2072, 2390], "x_from_to": [3322, 3478], "teeth": 24},
}
ARTEFACTS = ["applied light blue bar indices, minute ticks, the eagle logo, EMPORIO ARMANI print and the black date window "
             "at 3 (21): kept in the dial map (flat)",
             "hands, hub and their dark halos removed from the dial map by a normalised blur fill"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 215
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    # case flanks near the pivot row; the right flank above and below the crown
    pts = [(np.nonzero(fg[y])[0].min(), y) for y in range(1750, 2700, 5)]
    pts += [(np.nonzero(fg[y])[0].max(), y) for y in list(range(1750, 2040, 5)) + list(range(2430, 2700, 5))]
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case circle fit x2 = {CASE_MM} mm (listing)", "case_circle_px": [round(cx, 1), round(cy, 1), round(rad, 1)]}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["ring_radius_px"].items()}
    out["rings_mm"]["case"] = CASE_MM / 2
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]

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

    cp = M["cap"]
    cap_hw = (cp["x"][1] - cp["x"][0]) / 2 / S
    cap_y = [(abs(py0 - cp["top_y"][i]) / S + abs(cp["bottom_y"][i] - py0) / S) / 2 for i in (0, 1)]
    # lug arm tip: last row (going out) where the silhouette is clearly wider than the end cap
    tips = []
    for sy in (1, -1):
        tips.append(max(float(y) for y in np.arange(18, 30, 0.25) if (sil[round(sy * y, 2)][1] + sil[round(sy * y, 2)][2]) / 2 > cap_hw + 0.6))
    from_y = next(float(y) for y in np.arange(8, 22, 0.25) if half(y) > math.sqrt(max(CASE_MM ** 2 / 4 - y * y, 0)) + 0.15)
    inner = [mm(p) for p in M["arm_inner"]]
    inner_b = [mm(p) for p in M["arm_inner_bottom"]]
    # mean of the four arms (x mirrored left -> right, 6 o'clock mirrored to 12): window edge as a straight line
    xs_ = lambda pts: [abs(p[0]) for p in pts]
    pA = np.array([[abs(p[0]), abs(p[1])] for p in inner + inner_b])
    k_, b_ = np.polyfit(pA[:, 1], pA[:, 0], 1)  # x = k y + b
    out["lug"] = {"tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}, "from_y_mm": from_y,
                  "outer_x_mm": round(max(half(y) for y in np.arange(from_y, tips[0], 0.25)), 3),
                  "inner_edge_x_of_y": [round(float(k_), 4), round(float(b_), 3)],
                  "inner_edge_y_mm": [round(float(pA[:, 1].min()), 3), round(float(pA[:, 1].max()), 3)]}
    out["cap_mm"] = {"half_width": round(cap_hw, 3), "from_y": round(cap_y[0], 3), "to_y": round(cap_y[1], 3)}
    out["mesh_mm"] = {"half_width": round((M["mesh_x"][1] - M["mesh_x"][0]) / 2 / S, 3),
                      "centre_x": round(((M["mesh_x"][0] + M["mesh_x"][1]) / 2 - px0) / S, 3)}
    out["checks"] = {"cap_width_mm": round(2 * cap_hw, 2), "mesh_width_mm": round(2 * out["mesh_mm"]["half_width"], 2),
                     "lug_to_lug_mm": round(sum(tips), 2), "case_centre_minus_pivot_mm": [round((cx - px0) / S, 3), round((py0 - cy) / S, 3)]}

    ang = lambda dx, dy: math.degrees(math.atan2(dx, dy)) % 360  # clockwise from 12
    hands = {}
    for name in ("hour", "minute", "seconds"):
        tx, ty = mm(M[name]["tip"])
        L, w = math.hypot(tx, ty), M[name]["half_width"] / S
        u, n = (tx / L, ty / L), (ty / L, -tx / L)
        # baton: straight sides from the hub, round tip (8 segments)
        pts = [(n[0] * w, n[1] * w)] + [(u[0] * L + w * (n[0] * math.cos(a) + u[0] * math.sin(a)), u[1] * L + w * (n[1] * math.cos(a) + u[1] * math.sin(a)))
                                         for a in np.linspace(0, math.pi, 9)] + [(-n[0] * w, -n[1] * w)]
        hands[name] = {"angle_deg": round(ang(tx, ty), 2), "length_mm": round(L + w, 3), "half_width_mm": round(w, 3),
                       "outline_mm": [[round(x, 3), round(y, 3)] for x, y in pts]}
    out["hands"] = hands
    out["hub_mm"] = {"radius": round(M["hub_radius"] / S, 3)}

    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"angle_deg": round(ang(cr["x_from_to"][0] - px0, py0 - (yt + yb) / 2), 2),
                    "radius_mm": round((yb - yt) / 2 / S, 3), "teeth": cr["teeth"],
                    "r_from_to_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(cx), int(cy)), int(rad), (0, 0, 255), 3)
        for r in M["ring_radius_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 128, 0), 3)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, Pp((-l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, Pp((r_, y_mm)), 3, (0, 255, 0), -1)
        for hd in hands.values():
            cv2.polylines(ov, [np.array([Pp(p) for p in hd["outline_mm"]])], True, (0, 255, 255), 2)
        cv2.circle(ov, (px0, py0), M["hub_radius"], (255, 0, 255), 2)
        lg = out["lug"]
        for sy in (1, -1):
            cv2.line(ov, Pp((-20, sy * lg["tip_mm"]["mean"])), Pp((20, sy * lg["tip_mm"]["mean"])), (0, 128, 255), 2)
            cv2.line(ov, Pp((-20, sy * lg["from_y_mm"])), Pp((20, sy * lg["from_y_mm"])), (255, 255, 0), 2)
            cv2.rectangle(ov, Pp((-cap_hw, sy * cap_y[0])), Pp((cap_hw, sy * cap_y[1])), (255, 0, 128), 3)
            for sx in (1, -1):
                y0_, y1_ = lg["inner_edge_y_mm"]
                cv2.line(ov, Pp((sx * (k_ * y0_ + b_), sy * y0_)), Pp((sx * (k_ * y1_ + b_), sy * y1_)), (0, 0, 255), 3)
        k = out["crown"]
        for r_ in k["r_from_to_mm"]:
            cv2.line(ov, Pp((r_, -k["radius_mm"])), Pp((r_, k["radius_mm"])), (255, 0, 128), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "rings_mm", "lug", "cap_mm", "mesh_mm", "checks", "crown", "hub_mm")},
                     default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"], v["half_width_mm"]) for k, v in data["hands"].items()})
