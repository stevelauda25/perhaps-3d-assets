"""Measure the Fossil Carraway FS6012 front photo (white background, working copy 2802 x 5774) into mm. numpy + OpenCV.

    python3 -B -m pipeline.fossil_fs6012_trace [out.json] [overlay.png]   # default config/watches/fossil-fs6012-trace.json

Anchor: case width across the outer flanks (rows clear of the crown and the horns) = 30 mm (listing "case diameter 30 mm");
the strap width between the brancards is reported as a check against the 22 mm listing. mm, x right, y toward 12, origin =
hand pivot. Rectangular case read from the photo: outer flank (lower side step), brushed brancards that run up into the
horns, polished bars above and below the dial frame, dial opening. Hands, hub, crown and the case lines come from 20 px
gridded crops (MANUAL_PX, about +-0.15 mm). Hands are stored posed.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/fossil-fs6012/front_2802x5774.png"
OUT = ROOT / "config/watches/fossil-fs6012-trace.json"
CASE_MM = 30.0  # listing: case diameter 30 mm, read as the case width without the crown (strap then measures 22 mm)

MANUAL_PX = {
    "hand_pivot": [1310, 2906],
    # case columns (x px, left / right): outer flank meets the raised brancard; brancard inner edge = dial frame outer edge
    "step_x": [342, 2268],
    "brancard_inner_x": [502, 2115],
    # case rows (y px): top bar from the strap to the dial frame, frame to the dial opening, the same below
    "bar_top_y": [1678, 1885],
    "bar_bottom_y": [3925, 4175],
    # dial opening (cream dial visible inside the polished frame walls): x0, y0, x1, y1
    "dial_rect": [565, 1965, 2045, 3865],
    # (distance from the pivot, half width) from the hub to the tip
    "hour": {"tip": [994, 2683], "profile": [[0, 12], [92, 12], [125, 34], [277, 34], [300, 9], [312, 8], [378, 6], [387, 0]],
             "lume": [[118, 0], [135, 20], [265, 22], [292, 0]]},  # black lozenge hand with a lume window and a pointer
    "minute": {"tip": [1942, 2505], "profile": [[0, 12], [95, 12], [125, 23], [465, 22], [495, 11], [744, 10], [749, 0]],
               "lume": [[125, 0], [140, 13], [470, 13], [486, 0]]},
    "seconds": {"tip": [1570, 3467], "profile": [[0, 5], [200, 4.5], [600, 2.5], [618, 0]],
                "tail": [[0, 8], [80, 8.5], [255, 15], [272, 13], [283, 0]]},  # long black counterweight tail toward 11
    "hub_px": {"radius": 77, "pin": 17},
    # crown at 3: neck and fluted body with a rounded end (x px on the centre row)
    "crown": {"centre_y": 2928, "neck_radius": 172, "radius": 225, "end_radius": 170, "x_from_to": [2385, 2440, 2545, 2582]},
}
ARTEFACTS = ["Roman numerals, minute track, printed frame lines, FOSSIL and the raised centre panel stay in the dial map (flat)",
             "the photo is a product shot taken from slightly below: the bottom bar shows its sloped top face, so it reads longer than the top bar",
             "the top strap folds out on the right just above the horn; the case rows come from the left side, which is clean"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 225
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    rows = list(range(1800, 2600, 5)) + list(range(3300, 4000, 5))  # clear of the crown and the horn corners
    left = float(np.median([np.nonzero(fg[y])[0].min() for y in rows]))
    right = float(np.median([np.nonzero(fg[y])[0].max() for y in rows]))
    S = (right - left) / CASE_MM
    mx = lambda x: round((x - px0) / S, 3)
    my = lambda y: round((py0 - y) / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width across the flanks (median of rows clear of crown and horns, {right - left:.0f} px) = {CASE_MM} mm (listing)",
           "case_x_mm": [mx(left), mx(right)]}

    h = fg.shape[0]
    prof = []
    for y_mm in np.arange(-38.0, 38.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    sil = {p[0]: p for p in prof}
    inner = sum(abs(mx(x)) for x in M["brancard_inner_x"]) / 2
    step = sum(abs(mx(x)) for x in M["step_x"]) / 2
    # horn tips and flank ends from the left edge (the top strap folds out on the right): first row from outside inward
    # where the silhouette is wider than the brancard gap / the step
    first = lambda sy, lim: next(float(y) for y in np.arange(30, 10, -0.25) if sil[round(sy * y, 2)][1] > lim + 0.15)
    tips = {"top": first(1, inner), "bottom": first(-1, inner)}
    flank = {"top": first(1, step), "bottom": first(-1, step)}
    strap_l = float(np.median([sil[round(sy * y, 2)][1] for sy in (1, -1) for y in np.arange(21.5, 24.01, 0.25)]))
    out["case"] = {"brancard_inner_x_mm": round(inner, 3), "step_x_mm": round(step, 3), "horn_tip_mm": tips, "flank_end_mm": flank,
                   "bar_top_y_mm": [my(y) for y in M["bar_top_y"]], "bar_bottom_y_mm": [my(y) for y in M["bar_bottom_y"]],
                   "dial_rect_mm": [mx(M["dial_rect"][0]), my(M["dial_rect"][1]), mx(M["dial_rect"][2]), my(M["dial_rect"][3])]}
    out["strap_photo_end_mm"] = {"top": round((py0 - np.nonzero(fg[:, px0])[0].min()) / S - 0.2, 2),
                                 "bottom": round((np.nonzero(fg[:, px0])[0].max() - py0) / S - 0.2, 2)}
    out["checks"] = {"strap_width_between_brancards_mm": round(2 * inner, 2), "strap_width_left_x2_mm": round(2 * strap_l, 2),
                     "lug_to_lug_mm": round(tips["top"] + tips["bottom"], 2)}

    def posed(angle, local):  # local (x across, y along) px -> posed mm
        t = math.radians(angle)
        return [[round((x * math.cos(t) + y * math.sin(t)) / S, 3), round((-x * math.sin(t) + y * math.cos(t)) / S, 3)] for x, y in local]

    def lance(profile, sign=1):
        right_ = [(w, sign * d) for d, w in profile]
        return right_ + [(-w, sign * d) for d, w in reversed(profile) if w > 0]

    ang = lambda p, o=(px0, py0): math.degrees(math.atan2(p[0] - o[0], o[1] - p[1])) % 360
    hands = {}
    for name in ("hour", "minute", "seconds"):
        hm = M[name]
        a = ang(hm["tip"])
        hands[name] = {"angle_deg": round(a, 2), "length_mm": round(hm["profile"][-1][0] / S, 3), "outline_mm": posed(a, lance(hm["profile"]))}
        if "lume" in hm:
            hands[name]["lume_mm"] = posed(a, lance(hm["lume"]))
    hands["seconds"]["tail_mm"] = posed(hands["seconds"]["angle_deg"], lance(M["seconds"]["tail"], -1))
    out["hands"] = hands
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub_px"].items()}

    cr = M["crown"]
    out["crown"] = {"angle_deg": round(ang((cr["x_from_to"][1], cr["centre_y"])), 2), "radius_mm": round(cr["radius"] / S, 3),
                    "neck_radius_mm": round(cr["neck_radius"] / S, 3), "end_radius_mm": round(cr["end_radius"] / S, 3),
                    "r_from_to_mm": [mx(x) for x in cr["x_from_to"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for y_mm, l, r_ in prof:
            cv2.circle(ov, Pp((-l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, Pp((r_, y_mm)), 3, (0, 255, 0), -1)
        polys = [hd["outline_mm"] for hd in hands.values()] + [hands["seconds"]["tail_mm"]] + [hd["lume_mm"] for hd in hands.values() if "lume_mm" in hd]
        for poly in polys:
            cv2.polylines(ov, [np.array([Pp(p) for p in poly])], True, (0, 255, 255), 2)
        cv2.circle(ov, (px0, py0), M["hub_px"]["radius"], (255, 0, 255), 2)
        c = out["case"]
        x0, y0, x1, y1 = c["dial_rect_mm"]
        cv2.rectangle(ov, Pp((x0, y0)), Pp((x1, y1)), (255, 128, 0), 2)
        for sx in (1, -1):
            for x_, col in ((c["brancard_inner_x_mm"], (0, 128, 255)), (c["step_x_mm"], (255, 0, 128))):
                cv2.line(ov, Pp((sx * x_, -24)), Pp((sx * x_, 24)), col, 2)
        for y_ in c["bar_top_y_mm"] + c["bar_bottom_y_mm"]:
            cv2.line(ov, Pp((-12, y_)), Pp((12, y_)), (255, 255, 0), 2)
        for sy, k in ((1, "top"), (-1, "bottom")):
            cv2.line(ov, Pp((-16, sy * c["horn_tip_mm"][k])), Pp((16, sy * c["horn_tip_mm"][k])), (0, 128, 255), 2)
            cv2.line(ov, Pp((-16, sy * c["flank_end_mm"][k])), Pp((16, sy * c["flank_end_mm"][k])), (255, 0, 128), 1)
        k = out["crown"]
        for r_ in k["r_from_to_mm"]:
            cv2.line(ov, Pp((r_, -k["radius_mm"] - 0.3)), Pp((r_, k["radius_mm"] - 0.3)), (255, 0, 128), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_x_mm", "case", "strap_photo_end_mm", "checks", "crown")},
                     default=float), "->", dest)
