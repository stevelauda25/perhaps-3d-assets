"""Measure the Zeppelin 100 Jahre chronograph Z76802 (7680-2) front photo (white background in a thin grey frame, 2586 x 2586)
into mm. numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z76802_trace [out.json] [overlay.png]   # default config/watches/zeppelin-z76802-trace.json

Same watch head as Z7680MB2 on a black leather strap. Anchor: case circle (left flank and the right flank clear of the crown
and pushers) = 42 mm (listing); the strap width is reported as a check. mm, x right, y toward 12, origin = hand pivot (the case
circle centre sits 5 px left of and 4 px under it; the model keeps the case on the pivot). The photo is soft (about 30 px/mm),
so hand positions come from 10 px gridded crops (MANUAL_PX) and hand, ring and pusher sizes are the Z7680MB2 values in mm.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/zeppelin-z76802/front_2586.png"
OUT = ROOT / "config/watches/zeppelin-z76802-trace.json"
CASE_MM = 42.0  # listing: 42 mm case, 11 mm thick
FRAME_PX = (230, 2355)  # inside the photo's grey frame line

MANUAL_PX = {
    "hand_pivot": [1245, 1254],
    # same head as Z7680MB2: hand shapes and pushers in mm
    "rings_mm": {"bezel_inner": 19.5, "telemeter_inner": 18.3, "dial_edge": 17.08},  # bezel edge read from this photo (19.35 on Z7680MB2)
    # lollipop hands: tip px; lume leaf (from, to, half width), lume disc (centre distance, lume radius, steel ring radius), body half width in mm
    "hour": {"tip": [960, 1050], "leaf_mm": [1.15, 4.99, 0.42], "disc_mm": [7.41, 0.42, 0.65], "half_mm": 0.17},
    "minute": {"tip": [1615, 983], "leaf_mm": [1.15, 5.76, 0.42], "disc_mm": [11.06, 0.46, 0.69], "half_mm": 0.17},
    "chrono": {"tip": [1248, 777], "half_mm": 0.115, "tail_mm": 6.34, "tail_half_mm": 0.29, "hub_mm": 0.63},
    # sub-dial hands: centre px, outline px (x across, y along the pointer), pointer direction px, hub radius px
    "subdials": {
        "left": {"centre": [1050, 1207], "hand": [[0, 55], [23, 0], [0, -34], [-23, 0]], "tail_disc": [-55, 11], "hub": 12, "angle_from": [1050, 1100]},
        "right": {"centre": [1440, 1212], "hand": [[3.5, 0], [3.5, 128], [0, 135], [-3.5, 128], [-3.5, 0], [-4.5, -40], [4.5, -40]],
                  "tail_disc": [-44, 8], "hub": 20, "angle_from": [1362, 1322]},
        "alarm_a": {"centre": [1243, 1457], "hand": [[9, 0], [7, 115], [0, 130], [-7, 115], [-9, 0]], "hub": 20, "angle_from": [1340, 1370]},
        "alarm_b": {"centre": [1243, 1457], "hand": [[8, 0], [6, 82], [0, 95], [-6, 82], [-8, 0]], "hub": 0, "angle_from": [1165, 1405]},
    },
    "crown": {"centre_y": 1261, "radius": 91, "x_from_to": [1845, 1855, 1965, 1999]},  # case edge, flutes start, flutes end, domed end
    "pushers_mm": [{"angle_deg": 62.3, "head_radius_mm": 1.497, "stem_radius_mm": 1.804, "r_from_to_mm": [20.73, 22.94, 24.76]},
                   {"angle_deg": 118.6, "head_radius_mm": 1.497, "stem_radius_mm": 1.804, "r_from_to_mm": [20.73, 22.94, 24.76]}],
}
ARTEFACTS = ["photo is soft (upscaled, about 30 px/mm): the dial map is less sharp than the Z7680MB2 one",
             "the alarm hand's small paddle below the alarm hub stays in the dial map (flat)",
             "crystal reflections on the telemeter ring stay in the dial map"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 225
    a, b = FRAME_PX
    fg[:a], fg[b:], fg[:, :a], fg[:, b:] = 0, 0, 0, 0
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    pts = [(np.nonzero(fg[y])[0].min(), y) for y in range(1000, 1520, 5)]
    pts += [(np.nonzero(fg[y])[0].max(), y) for y in list(range(1100, 1170, 5)) + list(range(1360, 1450, 5))]
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case circle fit x2 = {CASE_MM} mm (listing); strap width as a check", "case_circle_px": [round(cx, 1), round(cy, 1), round(rad, 1)]}
    out["rings_mm"] = dict(M["rings_mm"], case=CASE_MM / 2)

    prof = []
    for y_mm in np.arange(-40.0, 40.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if a <= row < b:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    sil = {p[0]: p for p in prof}
    both = lambda y: sum((sil[k][1] + sil[k][2]) / 2 for k in (round(y, 2), round(-y, 2))) / 2
    left = lambda y: (sil[round(y, 2)][1] + sil[round(-y, 2)][1]) / 2  # left edge only: the pushers sit on the right
    inner = float(np.median([both(y) for y in np.arange(24.5, 26.51, 0.25)]))  # strap just past the lug tips
    tips = [next(float(y) for y in np.arange(20, 28, 0.25) if (sil[round(sy * y, 2)][1] + sil[round(sy * y, 2)][2]) / 2 < inner + 0.3) for sy in (1, -1)]
    from_y = next(float(y) for y in np.arange(12, 22, 0.25) if left(y) > math.sqrt(max(CASE_MM ** 2 / 4 - y * y, 0)) + 0.15)
    out["lug"] = {"inner_x_mm": round(inner, 3), "tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}, "from_y_mm": from_y,
                  "outer_x_mm": round(max(left(y) for y in np.arange(from_y, tips[0], 0.25)), 3)}
    col = np.nonzero(fg[:, px0])[0]
    out["strap_photo_end_mm"] = {"top": round((py0 - col.min()) / S - 0.2, 2), "bottom": round((col.max() - py0) / S - 0.2, 2)}
    out["checks"] = {"strap_width_mm": round(2 * inner, 2), "lug_to_lug_mm": round(sum(tips), 2)}

    ang = lambda p, o=(px0, py0): math.degrees(math.atan2(p[0] - o[0], o[1] - p[1])) % 360

    def posed(angle, local, origin=(0.0, 0.0), k=1 / S):  # local (x across, y along) -> posed mm; k = px to mm (1 for mm input)
        t = math.radians(angle)
        return [[round(origin[0] + (x * math.cos(t) + y * math.sin(t)) * k, 3), round(origin[1] + (-x * math.sin(t) + y * math.cos(t)) * k, 3)]
                for x, y in local]

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        a_, L = ang(hm["tip"]), math.hypot(hm["tip"][0] - px0, hm["tip"][1] - py0) / S
        w, (l0, l1, lw), (dc, dr, ds) = hm["half_mm"], hm["leaf_mm"], hm["disc_mm"]
        body = [(w, -0.38), (w * 1.6, l0), (lw + 0.12, (l0 + l1) / 2), (w, l1 + 0.38), (w * 0.8, L - 0.29), (0, L), (-w * 0.8, L - 0.29), (-w, l1 + 0.38),
                (-lw - 0.12, (l0 + l1) / 2), (-w * 1.6, l0), (-w, -0.38)]
        leaf = [(0, l0 + 0.15), (lw, (l0 + l1) / 2), (0, l1 - 0.12), (-lw, (l0 + l1) / 2)]
        hands[name] = {"angle_deg": round(a_, 2), "length_mm": round(L, 3), "outline_mm": posed(a_, body, k=1), "leaf_mm": posed(a_, leaf, k=1),
                       "disc_centre_mm": posed(a_, [(0, dc)], k=1)[0], "disc_lume_r_mm": dr, "disc_ring_r_mm": ds}
    ch = M["chrono"]
    a_, L = ang(ch["tip"]), math.hypot(ch["tip"][0] - px0, ch["tip"][1] - py0) / S
    w, tl, tw = ch["half_mm"], ch["tail_mm"], ch["tail_half_mm"]
    hands["chrono"] = {"angle_deg": round(a_, 2), "length_mm": round(L, 3), "hub_r_mm": ch["hub_mm"],
                       "outline_mm": posed(a_, [(w, 0), (w * 0.7, L - 0.19), (0, L), (-w * 0.7, L - 0.19), (-w, 0), (-tw, -0.77), (-tw, -tl + 0.19),
                                                (0, -tl), (tw, -tl + 0.19), (tw, -0.77)], k=1)}
    subs = {}
    for k_, sd in M["subdials"].items():
        c_ = sd["centre"]
        a_ = ang(sd["angle_from"], c_)
        e = {"centre_mm": mm(c_), "angle_deg": round(a_, 2), "hub_r_mm": round(sd["hub"] / S, 3), "outline_mm": posed(a_, sd["hand"], mm(c_))}
        if "tail_disc" in sd:
            e["tail_disc_mm"] = posed(a_, [(0, sd["tail_disc"][0])], mm(c_))[0] + [round(sd["tail_disc"][1] / S, 3)]
        subs[k_] = e
    out["hands"] = hands
    out["subdials"] = subs

    cr = M["crown"]
    out["crown"] = {"angle_deg": round(ang((cr["x_from_to"][0], cr["centre_y"])), 2), "radius_mm": round(cr["radius"] / S, 3),
                    "r_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}
    out["pushers"] = M["pushers_mm"]
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(cx), int(cy)), int(rad), (0, 0, 255), 1)
        for r in M["rings_mm"].values():
            cv2.circle(ov, (px0, py0), int(r * S), (255, 128, 0), 1)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, Pp((-l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, Pp((r_, y_mm)), 2, (0, 255, 0), -1)
        polys = [hd["outline_mm"] for hd in hands.values()] + [hands[n]["leaf_mm"] for n in ("hour", "minute")] + [s["outline_mm"] for s in subs.values()]
        for poly in polys:
            cv2.polylines(ov, [np.array([Pp(p) for p in poly])], True, (0, 255, 255), 1)
        circles = [(hands[n]["disc_centre_mm"], hands[n]["disc_ring_r_mm"]) for n in ("hour", "minute")]
        circles += [(s["tail_disc_mm"][:2], s["tail_disc_mm"][2]) for s in subs.values() if "tail_disc_mm" in s]
        circles += [(s["centre_mm"], s["hub_r_mm"]) for s in subs.values() if s["hub_r_mm"]]
        for c_, r in circles:
            cv2.circle(ov, Pp(c_), max(1, int(r * S)), (0, 255, 255), 1)
        for p in out["pushers"]:
            t_ = math.radians(p["angle_deg"])
            for r in p["r_from_to_mm"]:
                cv2.circle(ov, Pp((r * math.sin(t_), r * math.cos(t_))), int(p["head_radius_mm"] * S), (255, 0, 255), 1)
        k = out["crown"]
        for r in k["r_mm"]:
            cv2.line(ov, Pp((r, -k["radius_mm"])), Pp((r, k["radius_mm"])), (255, 0, 255), 1)
        lg = out["lug"]
        for sy in (1, -1):
            cv2.line(ov, Pp((-20, sy * lg["tip_mm"]["mean"])), Pp((20, sy * lg["tip_mm"]["mean"])), (0, 128, 255), 1)
            cv2.line(ov, Pp((-20, sy * lg["from_y_mm"])), Pp((20, sy * lg["from_y_mm"])), (255, 255, 0), 1)
        for sx in (1, -1):
            cv2.line(ov, Pp((sx * inner, -36)), Pp((sx * inner, 36)), (0, 128, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "lug", "strap_photo_end_mm", "checks", "crown")}, default=float), "->", dest)
