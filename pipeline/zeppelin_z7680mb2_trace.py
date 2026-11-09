"""Measure the Zeppelin 100 Jahre chronograph Z7680MB2 front photo (white background, 2700 x 4292) into mm. numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z7680mb2_trace [out.json] [overlay.png]   # default config/watches/zeppelin-z7680mb2-trace.json

Anchor: case circle (fitted on both flanks clear of the crown and pushers) = 42 mm (listing); the bracelet width next to the
lugs is reported as a check. mm, x right, y toward 12, origin = hand pivot. The case circle centre sits 11 px right of and
15 px under the pivot (camera slightly off-axis); the model keeps the case on the pivot. Rings come from a radial brightness
profile; hands, sub-dials, crown, pushers and bracelet joints from 10-50 px gridded crops (MANUAL_PX, about +-0.1 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/zeppelin-z7680mb2/front_2700x4292.jpg"
OUT = ROOT / "config/watches/zeppelin-z7680mb2-trace.json"
CASE_MM = 42.0  # listing: 42 mm case, 13 mm thick

MANUAL_PX = {
    "hand_pivot": [1220, 2141],
    "ring_radius_px": {"bezel_inner": 1008, "telemeter_inner": 948, "dial_edge": 890},
    # lollipop hands: tip, lume leaf (from, to, half width), lume disc (centre distance, lume radius, steel ring radius), body half width
    "hour": {"tip": [717, 1800], "leaf": [60, 260, 22], "disc": [386, 22, 34], "half": 9},
    "minute": {"tip": [1845, 1634], "leaf": [60, 300, 22], "disc": [576, 24, 36], "half": 9},
    "chrono": {"tip": [1215, 1305], "half": 6, "tail": 330, "tail_half": 15, "hub": 33},
    "subdials": {
        "left": {"centre": [880, 2072], "hand": [[0, 97], [40, 0], [0, -60], [-40, 0]], "tail_disc": [-80, 20], "hub": 22, "angle_from": [877, 1975]},
        "right": {"centre": [1567, 2062], "hand": [[7, 0], [7, 125], [0, 133], [-7, 125], [-7, 0], [-9, -75], [9, -75]], "hub": 37, "angle_from": [1515, 1940]},
        "alarm_a": {"centre": [1225, 2497], "hand": [[16, 0], [12, 200], [0, 228], [-12, 200], [-16, 0]], "hub": 35, "angle_from": [1173, 2275]},
        "alarm_b": {"centre": [1225, 2497], "hand": [[14, 0], [10, 150], [0, 173], [-10, 150], [-14, 0]], "hub": 0, "angle_from": [1305, 2650]},
    },
    "crown": {"centre_y": 2140, "radius": 145, "x_from_to": [2325, 2355, 2545, 2600]},  # case edge, flutes start, flutes end, domed end
    "pushers": [{"head_centre": [2300, 1575], "head_radius": 78, "stem_radius": 94, "r_from_to": [1080, 1195, 1290]},
                {"head_centre": [2300, 2730], "head_radius": 78, "stem_radius": 94, "r_from_to": [1080, 1195, 1290]}],
    # bracelet (top half, where the photo is straight): outer first joint = lug tip, centre first joint half a row later
    "bracelet_edges_x": [680, 1780],
    "centre_half_px": 215, "centre_polish_half_px": 155,
    "outer_joints_y": [925, 660, 380],
    "centre_joints_y": [790, 510, 260],
}
ARTEFACTS = ["case seen slightly off-axis: bottom lugs and bracelet look longer than the top ones (top values used, mirrored)",
             "crystal reflections on the telemeter ring at 2-5 o'clock: stay in the photo map",
             "the listing says mesh bracelet; the photo shows a three-column link bracelet (Irsyad 2026-11-09: follow the photo)"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 225
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    pts = []
    for y in list(range(1500, 1800, 10)) + list(range(2500, 2800, 10)):
        pts.append((np.nonzero(fg[y])[0].min(), y))
    for y in list(range(1760, 1950, 10)) + list(range(2360, 2540, 10)):
        pts.append((np.nonzero(fg[y])[0].max(), y))
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case circle fit x2 = {CASE_MM} mm (listing); bracelet width next to the lugs as a check",
           "case_circle_px": [round(cx, 1), round(cy, 1), round(rad, 1)]}
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
    bx0, bx1 = M["bracelet_edges_x"]
    bhw = (bx1 - bx0) / 2 / S
    out["bracelet_half_width_mm"] = round(bhw, 3)
    out["bracelet_centre_half"] = round(M["centre_half_px"] / ((bx1 - bx0) / 2), 3)
    out["bracelet_centre_polish_half"] = round(M["centre_polish_half_px"] / ((bx1 - bx0) / 2), 3)
    oj = [(py0 - y) / S for y in M["outer_joints_y"]]
    cj = [(py0 - y) / S for y in M["centre_joints_y"]]
    out["bracelet_pitch_mm"] = round((oj[-1] - oj[0] + cj[-1] - cj[0]) / (len(oj) - 1 + len(cj) - 1), 3)
    out["bracelet_outer_first_joint_mm"] = round(oj[0], 3)
    out["bracelet_centre_first_joint_mm"] = round(cj[0], 3)
    # lug tips: where the silhouette narrows to the bracelet (both edges), top and bottom
    tips = []
    for sy in (1, -1):
        tips.append(next(float(y) for y in np.arange(20, 28, 0.25)
                         if (sil[round(sy * y, 2)][1] + sil[round(sy * y, 2)][2]) / 2 < bhw + 0.3))
    half = lambda y: sum((sil[k][1] + sil[k][2]) / 2 for k in (round(y, 2), round(-y, 2))) / 2
    left = lambda y: (sil[round(y, 2)][1] + sil[round(-y, 2)][1]) / 2  # left edge only: the pushers sit on the right
    from_y = next(float(y) for y in np.arange(12, 22, 0.25) if left(y) > math.sqrt(max(CASE_MM ** 2 / 4 - y * y, 0)) + 0.15)
    out["lug"] = {"tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}, "from_y_mm": from_y,
                  "outer_x_mm": round(max(left(y) for y in np.arange(from_y, tips[0], 0.25)), 3)}
    out["checks"] = {"bracelet_width_mm": round(2 * bhw, 2), "lug_to_lug_mm": round(sum(tips), 2)}

    ang = lambda p, o=(px0, py0): math.degrees(math.atan2(p[0] - o[0], o[1] - p[1])) % 360

    def posed(angle, local, origin=(0.0, 0.0)):  # local (x across, y along) px -> posed mm
        t = math.radians(angle)
        return [[round(origin[0] + (x * math.cos(t) + y * math.sin(t)) / S, 3), round(origin[1] + (-x * math.sin(t) + y * math.cos(t)) / S, 3)]
                for x, y in local]

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        a, L = ang(hm["tip"]), math.hypot(hm["tip"][0] - px0, hm["tip"][1] - py0)
        w, (l0, l1, lw), (dc, dr, ds) = hm["half"], hm["leaf"], hm["disc"]
        body = [(w, -20), (w * 1.6, l0), (lw + 6, (l0 + l1) / 2), (w, l1 + 20), (w * 0.8, L - 15), (0, L), (-w * 0.8, L - 15), (-w, l1 + 20),
                (-lw - 6, (l0 + l1) / 2), (-w * 1.6, l0), (-w, -20)]
        leaf = [(0, l0 + 8), (lw, (l0 + l1) / 2), (0, l1 - 6), (-lw, (l0 + l1) / 2)]
        hands[name] = {"angle_deg": round(a, 2), "length_mm": round(L / S, 3), "outline_mm": posed(a, body), "leaf_mm": posed(a, leaf),
                       "disc_centre_mm": posed(a, [(0, dc)])[0], "disc_lume_r_mm": round(dr / S, 3), "disc_ring_r_mm": round(ds / S, 3)}
    ch = M["chrono"]
    a, L = ang(ch["tip"]), math.hypot(ch["tip"][0] - px0, ch["tip"][1] - py0)
    w, tl, tw = ch["half"], ch["tail"], ch["tail_half"]
    hands["chrono"] = {"angle_deg": round(a, 2), "length_mm": round(L / S, 3), "hub_r_mm": round(ch["hub"] / S, 3),
                       "outline_mm": posed(a, [(w, 0), (w * 0.7, L - 10), (0, L), (-w * 0.7, L - 10), (-w, 0), (-tw, -40), (-tw, -tl + 10),
                                               (0, -tl), (tw, -tl + 10), (tw, -40)])}
    subs = {}
    for k, sd in M["subdials"].items():
        c_ = sd["centre"]
        a = ang(sd["angle_from"], c_)
        e = {"centre_mm": mm(c_), "angle_deg": round(a, 2), "hub_r_mm": round(sd["hub"] / S, 3), "outline_mm": posed(a, sd["hand"], mm(c_))}
        if "tail_disc" in sd:
            e["tail_disc_mm"] = posed(a, [(0, sd["tail_disc"][0])], mm(c_))[0] + [round(sd["tail_disc"][1] / S, 3)]
        subs[k] = e
    out["hands"] = hands
    out["subdials"] = subs

    cr = M["crown"]
    out["crown"] = {"angle_deg": round(ang((cr["x_from_to"][0], cr["centre_y"])), 2), "radius_mm": round(cr["radius"] / S, 3),
                    "r_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}
    out["pushers"] = [{"angle_deg": round(ang(p["head_centre"]), 2), "head_radius_mm": round(p["head_radius"] / S, 3),
                       "stem_radius_mm": round(p["stem_radius"] / S, 3), "r_from_to_mm": [round(v / S, 3) for v in p["r_from_to"]]} for p in M["pushers"]]
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
        polys = [hd["outline_mm"] for hd in hands.values()] + [hands[n]["leaf_mm"] for n in ("hour", "minute")] + [s["outline_mm"] for s in subs.values()]
        for poly in polys:
            cv2.polylines(ov, [np.array([Pp(p) for p in poly])], True, (0, 255, 255), 2)
        for n in ("hour", "minute"):
            cv2.circle(ov, Pp(hands[n]["disc_centre_mm"]), int(hands[n]["disc_ring_r_mm"] * S), (0, 255, 255), 2)
        for sy in (1, -1):
            for y in [out["lug"]["tip_mm"]["mean"], out["bracelet_centre_first_joint_mm"]]:
                cv2.line(ov, Pp((-12, sy * y)), Pp((12, sy * y)), (0, 128, 255), 2)
        for sx in (1, -1):
            for f in (1, out["bracelet_centre_half"]):
                cv2.line(ov, Pp((sx * f * bhw, -42)), Pp((sx * f * bhw, 42)), (255, 0, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "rings_mm", "lug", "bracelet_half_width_mm", "bracelet_pitch_mm",
                                           "bracelet_centre_first_joint_mm", "checks", "crown", "pushers")}, default=float), "->", dest)
