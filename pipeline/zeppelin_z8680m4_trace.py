"""Measure the Zeppelin 100 Jahre chronograph Z8680M4 (green dial, mesh bracelet) from the straightened front photo. numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z8680m4_rectify                       # first: outputs/watches/zeppelin-z8680m4/front_rectified.png
    python3 -B -m pipeline.zeppelin_z8680m4_trace [out.json] [overlay.png]  # default config/watches/zeppelin-z8680m4-trace.json

The only photo is taken from the left (about 3/4); the rectify step maps the dial plane to a front view at 75 px/mm. The
case, lugs, crown and pushers sit off that plane and stay skewed, so their sizes come from the Z7680MB2 trace (same 42 mm
100 Jahre case, straight photo): rings, silhouette, lug, crown, pushers and bracelet width are copied from it. Hands,
sub-dial hands and the mesh rows are read here from 20 px gridded crops (MANUAL_PX, about +-0.1 mm). mm, x right, y toward
12, origin = hand pivot.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RECT = ROOT / "outputs/watches/zeppelin-z8680m4/front_rectified.png"
CASE_TRACE = ROOT / "config/watches/zeppelin-z7680mb2-trace.json"
OUT = ROOT / "config/watches/zeppelin-z8680m4-trace.json"
COPIED = ("rings_mm", "silhouette_y_left_right_mm", "bracelet_half_width_mm", "lug", "crown", "pushers")

MANUAL_PX = {
    "hand_pivot": [1781, 2893],
    # steel lollipop hands: tip, leaf (from, to, half width), lume disc (centre distance, lume radius, ring radius), body half width
    # widths: the Z7680MB2 values x 1.44 (75 / 52.09 px/mm); tips and discs read here
    "hour": {"tip": [1068, 2389], "leaf": [86, 374, 32], "disc": [550, 32, 49], "half": 13},
    "minute": {"tip": [2822, 2350], "leaf": [86, 432, 32], "disc": [821, 35, 52], "half": 13},
    "chrono": {"tip": [1768, 1675], "half": 8, "tail": 450, "tail_half": 23, "hub": 47},
    "subdials": {
        "left": {"centre": [1301, 2791], "hand": [[0, 190], [20, 150], [62, 14], [30, -69], [-30, -69], [-62, 14], [-20, 150]],
                 "tail_disc": [-125, 36], "hub": 0, "angle_from": [1301, 2600]},
        "right": {"centre": [2291, 2789], "hand": [[7, 0], [6, 312], [0, 322], [-6, 312], [-7, 0], [-6, -90], [6, -90]],
                  "tail_disc": [-103, 25], "hub": 50, "angle_from": [2291, 2467]},
        "alarm_a": {"centre": [1799, 3406], "hand": [[16, 0], [10, 300], [0, 328], [-10, 300], [-16, 0]], "hub": 48, "angle_from": [1730, 3085]},
        "alarm_b": {"centre": [1799, 3406], "hand": [[20, 0], [12, 200], [0, 223], [-12, 200], [-20, 0], [-40, -60], [0, -105], [40, -60]],
                    "hub": 0, "angle_from": [1605, 3297]},
    },
    # Milanese mesh at 6 o'clock (seen almost face-on): edges and a clean band of whole rows, from the case outward
    "mesh_x": [1150, 2680],
    "mesh_rows_y": [4790, 5150],
}
ARTEFACTS = ["only one photo, from the left: case, lugs, crown and pushers from the Z7680MB2 trace (same case)",
             "the dial map's left edge (7-11 o'clock) shows the bezel's inner wall, seen from the side: stays in the photo map",
             "hands sit 0.2-0.8 mm above the dial plane: up to about 0.3 mm parallax toward 3 o'clock in the straightened photo"]


def trace(overlay=None):
    rect = json.loads(RECT.with_suffix(".json").read_text())
    case = json.loads(CASE_TRACE.read_text())
    S = rect["scale_px_per_mm"]
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(RECT.relative_to(ROOT)), "scale_px_per_mm": S, "origin_px": [px0, py0],
           "anchor": "homography of the lume dots and hubs to the Z7680MB2 dial (pipeline/zeppelin_z8680m4_rectify.py)",
           "case_from": str(CASE_TRACE.relative_to(ROOT))}
    out.update({k: case[k] for k in COPIED})

    ang = lambda p, o=(px0, py0): math.degrees(math.atan2(p[0] - o[0], o[1] - p[1])) % 360

    def posed(angle, local, origin=(0.0, 0.0)):  # local (x across, y along) px -> posed mm
        t = math.radians(angle)
        return [[round(origin[0] + (x * math.cos(t) + y * math.sin(t)) / S, 3), round(origin[1] + (-x * math.sin(t) + y * math.cos(t)) / S, 3)]
                for x, y in local]

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        a, L = ang(hm["tip"]), math.hypot(hm["tip"][0] - px0, hm["tip"][1] - py0)
        w, (l0, l1, lw), (dc, dr, dsr) = hm["half"], hm["leaf"], hm["disc"]
        body = [(w, -29), (w * 1.6, l0), (lw + 9, (l0 + l1) / 2), (w, l1 + 29), (w * 0.8, L - 22), (0, L), (-w * 0.8, L - 22), (-w, l1 + 29),
                (-lw - 9, (l0 + l1) / 2), (-w * 1.6, l0), (-w, -29)]
        leaf = [(0, l0 + 12), (lw, (l0 + l1) / 2), (0, l1 - 9), (-lw, (l0 + l1) / 2)]
        hands[name] = {"angle_deg": round(a, 2), "length_mm": round(L / S, 3), "outline_mm": posed(a, body), "leaf_mm": posed(a, leaf),
                       "disc_centre_mm": posed(a, [(0, dc)])[0], "disc_lume_r_mm": round(dr / S, 3), "disc_ring_r_mm": round(dsr / S, 3)}
    ch = M["chrono"]
    a, L = ang(ch["tip"]), math.hypot(ch["tip"][0] - px0, ch["tip"][1] - py0)
    w, tl, tw = ch["half"], ch["tail"], ch["tail_half"]
    hands["chrono"] = {"angle_deg": round(a, 2), "length_mm": round(L / S, 3), "hub_r_mm": round(ch["hub"] / S, 3),
                       "outline_mm": posed(a, [(w, 0), (w * 0.7, L - 14), (0, L), (-w * 0.7, L - 14), (-w, 0), (-tw, -58), (-tw, -tl + 14),
                                               (0, -tl), (tw, -tl + 14), (tw, -58)])}
    subs = {}
    for k, sd in M["subdials"].items():
        c_ = sd["centre"]
        a = ang(sd["angle_from"], c_)
        e = {"centre_mm": mm(c_), "angle_deg": round(a, 2), "hub_r_mm": round(sd["hub"] / S, 3), "outline_mm": posed(a, sd["hand"], mm(c_))}
        if "tail_disc" in sd:
            e["tail_disc_mm"] = posed(a, [(0, sd["tail_disc"][0])], mm(c_))[0] + [round(sd["tail_disc"][1] / S, 3)]
        subs[k] = e
    out["hands"], out["subdials"] = hands, subs
    out["mesh"] = {"width_mm": round((M["mesh_x"][1] - M["mesh_x"][0]) / S, 3), "band_mm": round((M["mesh_rows_y"][1] - M["mesh_rows_y"][0]) / S, 3)}
    out["checks"] = {"mesh_vs_bracelet_mm": round(out["mesh"]["width_mm"] - 2 * case["bracelet_half_width_mm"], 2)}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        im = cv2.imread(str(RECT))
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r in out["rings_mm"].values():
            cv2.circle(ov, (px0, py0), int(r * S), (255, 128, 0), 2)
        for y_mm, l, r_ in out["silhouette_y_left_right_mm"]:
            cv2.circle(ov, Pp((-l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, Pp((r_, y_mm)), 3, (0, 255, 0), -1)
        polys = [hd["outline_mm"] for hd in hands.values()] + [hands[n]["leaf_mm"] for n in ("hour", "minute")] + [s["outline_mm"] for s in subs.values()]
        for poly in polys:
            cv2.polylines(ov, [np.array([Pp(p) for p in poly])], True, (0, 255, 255), 2)
        for n in ("hour", "minute"):
            cv2.circle(ov, Pp(hands[n]["disc_centre_mm"]), int(hands[n]["disc_ring_r_mm"] * S), (0, 255, 255), 2)
        for s in subs.values():
            if "tail_disc_mm" in s:
                cv2.circle(ov, Pp(s["tail_disc_mm"][:2]), int(s["tail_disc_mm"][2] * S), (0, 255, 255), 2)
            if s["hub_r_mm"]:
                cv2.circle(ov, Pp(s["centre_mm"]), int(s["hub_r_mm"] * S), (0, 255, 255), 2)
        cv2.rectangle(ov, (M["mesh_x"][0], M["mesh_rows_y"][0]), (M["mesh_x"][1], M["mesh_rows_y"][1]), (255, 0, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "mesh", "checks")}, default=float),
          {k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, "->", dest)
