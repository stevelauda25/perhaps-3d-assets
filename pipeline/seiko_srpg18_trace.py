"""Measure the Seiko Prospex SRPG18J1 front photo (transparent background, 3306 x 3306) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.seiko_srpg18_trace [out.json] [overlay.png]     # default config/watches/seiko-srpg18j1-trace.json

Anchor: case width on the flanks = 42.4 mm (Seiko listing); the 20 mm lug width is reported as a check against the strap at
the case. mm, x right, y toward 12, origin = hand pivot. Ring radii, indices, hands and crown come from gridded crops
(MANUAL_PX, about +-0.1 mm); hands are stored as posed outlines so the dial map and the build use the same shapes.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-srpg18j1/front_3306.png"
OUT = ROOT / "config/watches/seiko-srpg18j1-trace.json"
CASE_MM = 42.4  # listing: diameter 42.4, length 45.2, thickness 11.7, lug width 20
LUG_WIDTH_MM = 20.0

MANUAL_PX = {
    "hand_pivot": [1639, 1653],
    "ring_radius_px": {"teeth_tip": 801, "teeth_root": 771, "insert_outer": 744, "insert_inner": 604,
                       "crystal_edge": 586, "flange_outer": 584, "dial_edge": 530},
    "notch_y_px": [900, 2378],  # case edge between the horns, under the bezel teeth (top, bottom)
    "horn_inner_x_px": [1240, 2040],
    "teeth_count": 150,  # coin-edge bezel: about 33 px pitch at r 790 px
    # hands, hand-local outlines (x across, y along, px); angle from the tip
    "hour_tip": [1368, 1453],
    "hour_outline": [[0, 337], [67, 130], [24, 130], [24, 20], [30, -24], [0, -44], [-30, -24], [-24, 20], [-24, 130], [-67, 130]],
    "hour_lume": [[[0, 321], [49, 141], [-49, 141]], [[14, 122], [14, 56], [-14, 56], [-14, 122]]],
    "minute_tip": [2046, 1327],
    "minute_outline": [[0, 522], [30, 462], [25, 40], [26, -20], [0, -50], [-26, -20], [-25, 40], [-30, 462]],
    "minute_lume": [[[0, 492], [20, 455], [16, 64], [-16, 64], [-20, 455]]],
    "seconds_tip": [1147, 1808],
    "seconds_half_width_px": 4,
    "seconds_disc_px": [174, 27, 19],  # lollipop on the tail: centre distance, outer radius, lume radius
    "hub_radius_px": [44, 16],
    # applied indices: inner r, outer r, inner half width, outer half width (px); 12 has a centre bar, 3/6/9/12 a stick inward
    "index_px": {"bar": [360, 497, 28, 28], "cardinal": [346, 499, 39, 52], "12": [351, 505, 50, 92]},
    "index_stick_px": {"inner_r": 293, "half_width": 8},
    "index_frame_px": 11,
    "index_bar_12_half_px": 8,
    # printed parts kept clear of the hand fill (x0, y0, x1, y1)
    "logo_seiko": [1485, 1385, 1745, 1465],
    "logo_x": [1595, 1730, 1685, 1805],
    "print_automatic_20bar": [1505, 1810, 1775, 1910],
    "date_window": [1870, 1880, 2000, 1990],
    "print_6": [1560, 2170, 1720, 2215],
    "crown_centre": [2370, 2120],
    "crown_radius_px": 118,
    "crown_r_px": [790, 955],  # along its axis from the pivot: inner end (inside the case) to the outer face
}
ARTEFACTS = ["the strap's dark shadow line and the teeth above the strap between the horns: stay in the photo map",
             "hand shadows on the dial are faint (lower right): masked with the hands"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    fg = im[..., 3] > 128
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    h = fg.shape[0]
    rows = range(py0 - 50, py0 + 50)
    flank = [(px0 - np.nonzero(fg[r])[0].min()) for r in rows]
    S = 2 * max(flank) / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"left case flank at the pivot row x2 = {CASE_MM} mm (listing); lug width {LUG_WIDTH_MM} mm as a check"}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["ring_radius_px"].items()}
    out["notch_mm"] = round(((py0 - M["notch_y_px"][0]) + (M["notch_y_px"][1] - py0)) / 2 / S, 3)
    out["horn_inner_x_mm"] = round((M["horn_inner_x_px"][1] - M["horn_inner_x_px"][0]) / 2 / S, 3)
    out["teeth_count"] = M["teeth_count"]

    # left edge only (the crown is on the right), top and bottom averaged later in the build
    prof = []
    for y_mm in np.arange(-41.75, 41.76, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    half = {p[0]: p[1] for p in prof}
    tips = [next(y for y in np.arange(18, 30, 0.25) if half[round(sy * y, 2)] < out["horn_inner_x_mm"] + 0.35) for sy in (1, -1)]
    out["horn_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    near = [p[1] + p[2] for p in prof if tips[0] + 0.5 <= p[0] <= tips[0] + 3 or -tips[1] - 3 <= p[0] <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "listed_length_mm": 45.2,
                     "strap_past_horns_mm": round(float(np.median(near)), 2), "listed_lug_width_mm": LUG_WIDTH_MM}

    def posed(tip, local):
        t = math.atan2(tip[0] - px0, py0 - tip[1])  # clock angle of the hand
        return [[round((x * math.cos(t) + y * math.sin(t)) / S, 3), round((-x * math.sin(t) + y * math.cos(t)) / S, 3)] for x, y in local]

    hands = {}
    for name in ("hour", "minute"):
        tip = M[name + "_tip"]
        hands[name] = {"angle_deg": round(math.degrees(math.atan2(tip[0] - px0, py0 - tip[1])) % 360, 2),
                       "length_mm": round(math.hypot(tip[0] - px0, tip[1] - py0) / S, 3),
                       "outline_mm": posed(tip, M[name + "_outline"]), "lume_mm": [posed(tip, lp) for lp in M[name + "_lume"]]}
    tip = M["seconds_tip"]
    L, w = math.hypot(tip[0] - px0, tip[1] - py0), M["seconds_half_width_px"]
    dc, dr, dl = M["seconds_disc_px"]
    hands["seconds"] = {"angle_deg": round(math.degrees(math.atan2(tip[0] - px0, py0 - tip[1])) % 360, 2), "length_mm": round(L / S, 3),
                        "outline_mm": posed(tip, [[0, L], [w, L - 6], [w, 0], [w + 2, -dc + dr], [-w - 2, -dc + dr], [-w, 0], [-w, L - 6]]),
                        "disc_centre_mm": posed(tip, [[0, -dc]])[0], "disc_radius_mm": round(dr / S, 3), "disc_lume_radius_mm": round(dl / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]

    ix = {}
    for kind, (r0, r1, w0, w1) in M["index_px"].items():
        fr = M["index_frame_px"]
        ix[kind] = {"outline": [[round(v / S, 3) for v in p] for p in ((-w0, r0), (w0, r0), (w1, r1), (-w1, r1))],
                    "lume": [[round(v / S, 3) for v in p] for p in ((-w0 + fr, r0 + fr), (w0 - fr, r0 + fr), (w1 - fr * 1.2, r1 - fr), (-w1 + fr * 1.2, r1 - fr))]}
    out["indices"] = {"shapes_mm": ix, "stick_inner_mm": round(M["index_stick_px"]["inner_r"] / S, 3),
                      "stick_half_width_mm": round(M["index_stick_px"]["half_width"] / S, 3),
                      "bar_12_half_width_mm": round(M["index_bar_12_half_px"] / S, 3),
                      "layout": "applied rose gold frames with lume: trapezoids at 12 (two lume halves), 3, 6, 9 with a stick inward; bars elsewhere"}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("logo_seiko", "logo_x", "print_automatic_20bar", "date_window", "print_6"):
        out[k] = box(M[k])
    c = M["crown_centre"]
    out["crown"] = {"angle_deg": round(math.degrees(math.atan2(c[0] - px0, py0 - c[1])) % 360, 2),
                    "radius_mm": round(M["crown_radius_px"] / S, 3), "r_from_to_mm": [round(v / S, 3) for v in M["crown_r_px"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY)
        ov = cv2.cvtColor(ov, cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r in M["ring_radius_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 128, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((-l, y_mm)), 3, (0, 255, 0), -1)
        for hd in hands.values():
            cv2.polylines(ov, [np.array([P(p) for p in hd["outline_mm"]])], True, (0, 255, 255), 2)
            for lp in hd.get("lume_mm", []):
                cv2.polylines(ov, [np.array([P(p) for p in lp])], True, (0, 128, 255), 1)
        for hr in range(1, 13):
            sh = ix["12" if hr == 12 else "cardinal" if hr % 3 == 0 else "bar"]
            t = math.radians(hr * 30)
            rotp = lambda p: P((p[0] * math.cos(t) + p[1] * math.sin(t), -p[0] * math.sin(t) + p[1] * math.cos(t)))
            cv2.polylines(ov, [np.array([rotp(p) for p in sh["outline"]])], True, (255, 0, 255), 2)
        for k in ("logo_seiko", "logo_x", "print_automatic_20bar", "date_window", "print_6"):
            cv2.rectangle(ov, tuple(M[k][:2]), tuple(M[k][2:]), (0, 200, 255), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "notch_mm", "horn_inner_x_mm", "horn_tip_mm", "checks", "crown")},
                     default=float), "->", dest)
