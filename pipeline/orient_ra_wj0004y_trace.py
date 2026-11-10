"""Measure the Orient RA-WJ0004Y (Mako Solar) front photo into mm. numpy + OpenCV.

    python3 -B -m pipeline.orient_ra_wj0004y_trace [out.json] [overlay.png]   # default config/watches/orient-ra-wj0004y-trace.json

Native 1855 x 3183 retailer photo, straight-on (bezel circle centred 2.6 px from the hand pivot). Anchor: case width through
the pivot row = 39.9 mm (listing; left flank mirrored about the bezel centre, the crown covers the right one). Check: the
bracelet between the lugs (20 mm listed). mm, x right, y toward 12, origin = hand pivot. Rings, lug tips, bracelet joints,
hands and crown: MANUAL_PX from gridded crops (+-0.1 mm). Applied indices, numerals and the ORIENT letters: white blobs of the
photo (lume / letters), frames grown around them; hands cut out.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.orient_ra_ak0705r10b_trace import _grow, blobs

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-ra-wj0004y/front_1855x3183.jpg"
OUT = ROOT / "config/watches/orient-ra-wj0004y-trace.json"
CASE_MM = 39.9  # listing: 39.9 mm, 20 mm bracelet
BG = 238

MANUAL_PX = {
    "hand_pivot": [899, 1636],
    "bezel_centre": [901.6, 1636.1],  # circle fit on the bezel's dark outer edge
    # radii about the bezel centre: bezel outer edge, insert outer / inner, crystal edge, dial edge (rehaut foot)
    "rings_px": {"bezel_outer": 717, "insert_outer": 710, "insert_inner": 590, "crystal_edge": 575, "dial_edge": 553},
    "crown_rows": [1520, 1760],  # right silhouette rows covered by the crown
    "crown": {"y_top_bottom": [1525, 1750], "x_from_to": [1656, 1786], "teeth": 20},
    "lug_tips_y": [763, 2522],
    "lug_inner_x": [530, 1273],
    "notch_y": [1000, 2272],  # case edge between the lugs (under the bezel), top and bottom
    "bracelet_columns_x": [735, 1098],  # centre column edges near the case
    "bracelet_outer_joints_y": [774, 521, 237],  # top: outer column joints from the case outward
    "bracelet_centre_joints_y": [790, 553, 295],
    # hands: tip point (axis), stations [r, half width] of the steel outline along pivot -> tip, tail [r, half], lume [r, half]
    "hands": {
        "hour": {"tip": [637, 1463], "length": 314,
                 "stations": [[0, 12], [30, 12], [60, 11], [85, 10], [105, 13], [120, 16], [135, 19], [150, 21.5], [165, 23], [180, 25.5],
                              [195, 27], [210, 29.5], [225, 28], [240, 22], [255, 19], [270, 17], [285, 13], [300, 7.5]],
                 "tail": [[15, 11], [26, 0]],
                 "lume": [[86, 0], [92, 4], [105, 10], [120, 13], [135, 16], [150, 18.5], [165, 19.5], [180, 22.5], [195, 24], [210, 26.5],
                          [225, 24.5], [240, 16.5], [252, 6], [260, 0]]},
        "minute": {"tip": [1244, 1355], "length": 448,
                   "stations": [[0, 10], [20, 12], [40, 12], [60, 11.5], [80, 12], [100, 12.5], [120, 12], [140, 12.5], [160, 13.5],
                                [180, 14.5], [200, 15.5], [220, 17.5], [240, 18.5], [260, 19.5], [280, 21], [300, 22], [320, 23.5],
                                [340, 24], [360, 25.5], [380, 23], [400, 14], [420, 11.5], [440, 5]],
                   "tail": [[15, 10], [30, 8], [40, 0]],
                   "lume": [[95, 0], [100, 7], [120, 9], [140, 10], [160, 11], [180, 12], [200, 13], [220, 15], [240, 16], [260, 17],
                            [280, 18.5], [300, 19.5], [320, 21], [340, 21.5], [360, 22.5], [380, 20], [395, 10], [402, 0]]},
        "seconds": {"tip": [1370, 1790], "length": 495,
                    "stations": [[0, 6], [40, 3], [150, 2.5], [270, 2.5], [285, 6], [480, 3.5]],
                    "tail": [[20, 10], [60, 13], [100, 15.5], [168, 15.5]], "tail_round": 15.5, "orange_from": 280},
    },
    "hub_px": [25, 12],  # hub radius, cap radius
    "index_r": [300, 540], "white_v": 165, "white_s": 50, "frame_px": 4, "min_area": 600,
    "logo_box": [[780, 1430], [1022, 1486]],
    "date_box": [[1235, 1560], [1365, 1690]],  # printed date window: not an applied index
}
ARTEFACTS = ["minute track, crest, solar-powered, Water Resistant 20 bar, the date and the bezel insert print stay in the photo map",
             "hand shadows fall to the lower right; the seconds counterweight lies over the hour hand's root"]


def hand_poly(o, h, stations):
    u = np.float32(h["tip"]) - o
    u /= np.hypot(*u)
    n = np.float32([-u[1], u[0]])
    return np.float32([o + u * r + n * w for r, w in stations] + [o + u * r - n * w for r, w in stations[::-1]]), u


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    bx, by = M["bezel_centre"]
    o = np.float32([px0, py0])
    fg = (im.min(2) < BG)
    edge = {}
    for row in range(fg.shape[0]):
        xs = np.nonzero(fg[row])[0]
        if len(xs):
            edge[row] = (int(xs.min()), int(xs.max()))
    S = 2 * (bx - min(edge[r][0] for r in range(int(by) - 60, int(by) + 60))) / CASE_MM
    mm = lambda p: [round((float(p[0]) - px0) / S, 3), round(-(float(p[1]) - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width through the pivot row = {CASE_MM} mm (listing), left flank mirrored about the bezel centre",
           "bezel_offset_mm": mm((bx, by)), "rings_mm": {k: round(v / S, 3) for k, v in M["rings_px"].items()}}

    # ---- case silhouette about the bezel centre (right edge interpolated across the crown), lug tips, bracelet ----
    c0, c1 = M["crown_rows"]
    right = lambda row: edge[row][1] if not c0 < row < c1 else edge[c0][1] + (edge[c1][1] - edge[c0][1]) * (row - c0) / (c1 - c0)
    prof = []
    for y_mm in np.arange(-40.0, 40.01, 0.25):
        row = int(round(by - y_mm * S))
        if row in edge:
            prof.append([round(float(y_mm), 2), round((bx - edge[row][0]) / S, 3), round((right(row) - bx) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    tips = [abs(mm((0, y))[1]) for y in M["lug_tips_y"]]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    li = M["lug_inner_x"]
    out["lug_inner_x_mm"] = round((li[1] - li[0]) / 2 / S, 3)
    out["notch_mm"] = round(sum(abs(mm((0, y))[1]) for y in M["notch_y"]) / 2, 3)
    out["bracelet_half_y_mm"] = [[y, round((l + r) / 2, 3)] for y, l, r in prof if y > tips[0] + 1.0 or y < -tips[1] - 1.0]
    cc = M["bracelet_columns_x"]
    out["bracelet_centre_fraction"] = round((cc[1] - cc[0]) / (li[1] - li[0]), 3)
    oj, cj = M["bracelet_outer_joints_y"], M["bracelet_centre_joints_y"]
    out["bracelet_pitch_mm"] = round((oj[0] - oj[1] + cj[0] - cj[1]) / 2 / S, 3)  # first rows only
    out["bracelet_outer_start_mm"] = abs(mm((0, oj[0]))[1])
    out["bracelet_centre_start_mm"] = abs(mm((0, cj[0]))[1])
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_between_lugs_mm": round(2 * out["lug_inner_x_mm"], 2), "listed_mm": 20.0,
                     "bezel_mm": round(2 * M["rings_px"]["bezel_outer"] / S, 2)}

    # ---- hands ----
    ang = lambda v: round(math.degrees(math.atan2(v[0], -v[1])) % 360, 2)
    hands, hand_px = {}, {}
    for name, h in M["hands"].items():
        tail = [(-r, w) for r, w in h["tail"]]
        if h.get("tail_round"):
            rr, rc = h["tail_round"], tail[-1][0]
            tail = tail[:-1] + [(rc - rr * math.sin(a), rr * math.cos(a)) for a in [i * math.pi / 16 for i in range(9)]]
        st = sorted(tail + [tuple(s) for s in h["stations"]] + [(h["length"], 0.0)])
        poly, u = hand_poly(o, h, st)
        hand_px[name] = poly
        hands[name] = {"angle_deg": ang(u), "length_mm": round(h["length"] / S, 3), "outline_mm": [mm(p) for p in poly],
                       "stations_mm": [[round(r / S, 3), round(w / S, 3)] for r, w in st]}
        if "lume" in h:
            hands[name]["lume_mm"] = [[round(r / S, 3), round(w / S, 3)] for r, w in h["lume"]]
        if "orange_from" in h:
            hands[name]["orange_from_mm"] = round(h["orange_from"] / S, 3)
    out["hands"] = hands
    out["hub_mm"] = [round(v / S, 3) for v in M["hub_px"]]

    # ---- applied indices and numerals (white lume, frame grown round it), ORIENT letters: hands and date cut out ----
    hmask = np.zeros(fg.shape, np.uint8)
    for poly in hand_px.values():
        cv2.fillPoly(hmask, [np.int32(np.round(_grow(poly, 4)))], 1)
    yy, xx = np.mgrid[0:fg.shape[0], 0:fg.shape[1]]
    rr = np.hypot(xx - px0, yy - py0)
    white = (hsv[..., 2] > M["white_v"]) & (hsv[..., 1] < M["white_s"])
    ann = (rr > M["index_r"][0]) & (rr < M["index_r"][1])
    (d0, e0), (d1, e1) = M["date_box"]
    ann[e0:e1, d0:d1] = False
    lume = cv2.morphologyEx((white & ann).astype(np.uint8) & (1 - hmask), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(lume)
    lume = np.isin(lab, [k for k in range(1, n) if stats[k, cv2.CC_STAT_AREA] >= M["min_area"]]).astype(np.uint8)
    lume = cv2.morphologyEx(lume, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    frame = cv2.dilate(lume, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * M["frame_px"] + 1,) * 2))
    out["indices"] = {"frames": blobs(frame, 300, S, mm), "lume": blobs(lume, 200, S, mm)}
    (bx0, by0), (bx1, by1) = M["logo_box"]
    logo = np.zeros_like(lume)
    logo[by0:by1, bx0:bx1] = white[by0:by1, bx0:bx1]
    logo = cv2.morphologyEx(logo, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    out["logo"] = blobs(logo, 40, S, mm)
    out["date_box_mm"] = mm((d0, e0)) + mm((d1, e1))

    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"centre_y_mm": mm((0, (yt + yb) / 2))[1], "radius_mm": round((yb - yt) / 2 / S, 3), "teeth": cr["teeth"],
                    "x_from_to_mm": [mm((x, 0))[0] for x in cr["x_from_to"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r in M["rings_px"].values():
            cv2.circle(ov, (int(bx), int(by)), r, (255, 128, 0), 1)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, (int(bx - l * S), int(by - y_mm * S)), 2, (0, 255, 0), -1)
            cv2.circle(ov, (int(bx + r_ * S), int(by - y_mm * S)), 2, (0, 160, 0), -1)
        for h in hands.values():
            cv2.polylines(ov, [np.array([Pp(q) for q in h["outline_mm"]])], True, (0, 200, 255), 1)
        for sh in out["indices"]["frames"] + out["indices"]["lume"] + out["logo"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([Pp(q) for q in lp])], True, (255, 0, 255), 1)
        for y in M["bracelet_outer_joints_y"]:
            cv2.line(ov, (li[0], y), (cc[0], y), (0, 0, 255), 2)
        for y in M["bracelet_centre_joints_y"]:
            cv2.line(ov, (cc[0], y), (cc[1], y), (0, 0, 255), 2)
        for y in M["lug_tips_y"] + M["notch_y"]:
            cv2.line(ov, (li[0] - 80, y), (li[1] + 80, y), (0, 128, 255), 1)
        k = out["crown"]
        for x in k["x_from_to_mm"]:
            cv2.line(ov, Pp((x, k["centre_y_mm"] - k["radius_mm"])), Pp((x, k["centre_y_mm"] + k["radius_mm"])), (255, 0, 128), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "bezel_offset_mm", "rings_mm", "lug_tip_mm", "lug_inner_x_mm", "notch_mm",
                                           "bracelet_centre_fraction", "bracelet_pitch_mm", "bracelet_outer_start_mm", "bracelet_centre_start_mm",
                                           "checks", "crown")}, default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, "frames", len(data["indices"]["frames"]),
          "lume", len(data["indices"]["lume"]), "logo", len(data["logo"]))
