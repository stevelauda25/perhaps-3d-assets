"""Measure the Fossil Grant Chronograph FS4735 front photo (white background, 2130 x 2130) into mm. numpy + OpenCV.

    python3 -B -m pipeline.fossil_fs4735_trace [out.json] [overlay.png]   # default config/watches/fossil-fs4735-trace.json

Anchor: case circle (fitted on the left flank and the right flank clear of the pushers and crown guard) = 44 mm (listing);
the strap width is reported as a check. mm, x right, y toward 12, origin = hand pivot.
Hands: the white lume of the hour and minute hands is thresholded (min channel > 240, convex hull of the blob); the steel frame is the lume grown by
the frame width, joined to the hub by its convex hull. Seconds needle, subdial hands, pushers, crown and rings are read from
10-25 px gridded crops (MANUAL_PX, about +-0.1 mm). Hands are stored posed.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/fossil-fs4735/front_2130x2130.png"
OUT = ROOT / "config/watches/fossil-fs4735-trace.json"
CASE_MM = 44.0  # listing: case diameter 44 mm

MANUAL_PX = {
    "hand_pivot": [1039, 1065],
    # inner edge of the polished bezel (crystal opening), inner edge of the beige minute track (= flat dial edge)
    "ring_radius_px": {"bezel_inner": 488, "track_inner": 431},
    # a point inside each hand's lume blob; frame: steel border around the lume (px)
    "hour": {"lume_seed": [880, 975]},
    "minute": {"lume_seed": [1250, 935]},
    "frame_px": 4,
    "hub_px": {"radius": 13, "collar": 19},
    # silver chronograph seconds: tip and counterweight end on one line through the pivot, half widths
    "seconds": {"tip": [836, 1420], "tail": [1092, 985], "half_width": 2.2, "tail_half_width": 4.0},
    # subdial hands (all at 12 in the photo): hub centre, needle tip, hub radius
    "subdials": {"left": {"hub": [843, 1068], "tip": [835, 955]},
                 "right": {"hub": [1228, 1071], "tip": [1222, 960]},
                 "bottom": {"hub": [1032, 1262], "tip": [1029, 1145]}},
    "subdial_hub_px": 10, "subdial_half_width_px": 3.0,
    # pushers at 2 and 4: a point on the end cap; radius of the cylinder
    "pushers": {"top": [1590, 790], "bottom": [1585, 1355]}, "pusher_radius_px": 28,
    # knurled crown at 3: y top/bottom, x of the guard edge (tube start), x of the crown body start and end
    "crown": {"y_top_bottom": [985, 1142], "x_tube_body_end": [1600, 1615, 1658], "tube_radius_px": 52, "teeth": 24},
}
ARTEFACTS = ["Roman numerals, minute track, subdial rings and numerals, FOSSIL logo, lume squares and the concentric dial "
             "rings: kept in the dial map (flat)",
             "hour and minute frames are the lume grown by 4 px and hulled to the hub; the photo's steel border is 3-5 px"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    fg = im.min(2) < 215
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    # left flank between the lugs; the right flank only in the short runs between the lugs and the pushers
    pts = [(np.nonzero(fg[y])[0].min(), y) for y in range(720, 1430, 5)]
    pts += [(np.nonzero(fg[y])[0].max(), y) for y in list(range(700, 716, 5)) + list(range(1420, 1441, 5))]
    P_ = np.array(pts, float)
    A = np.c_[2 * P_[:, 0], 2 * P_[:, 1], np.ones(len(P_))]
    cx, cy, c = np.linalg.lstsq(A, (P_ ** 2).sum(1), rcond=None)[0]
    rad = math.sqrt(c + cx * cx + cy * cy)
    S = 2 * rad / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
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
    left = lambda y: sum(sil[k][1] for k in (round(y, 2), round(-y, 2))) / 2  # left edge only: the guard is on the right
    # strap just past the lug tips, where it is still flat to the camera
    inner = float(np.median([left(y) for y in np.arange(25.0, 27.01, 0.25)]))
    tips = []
    for sy in (1, -1):
        tips.append(next(float(y) for y in np.arange(20, 30, 0.25) if sil[round(sy * y, 2)][1] < inner + 0.3))
    from_y = next(float(y) for y in np.arange(12, 22, 0.25) if left(y) > math.sqrt(max(CASE_MM ** 2 / 4 - y * y, 0)) + 0.15)
    out["lug"] = {"inner_x_mm": round(inner, 3), "tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)},
                  "from_y_mm": from_y, "outer_x_mm": round(max(left(y) for y in np.arange(from_y, tips[0], 0.25)), 3)}
    # crown guard on the right: rows where the right edge leaves the case circle between the pushers
    guard = [[p[0], p[2]] for p in prof if abs(p[0]) < 9.5 and p[2] > math.sqrt(max(CASE_MM ** 2 / 4 - p[0] ** 2, 0)) + 0.1]
    out["guard_y_right_mm"] = guard
    out["strap_photo_end_mm"] = {"top": round((py0 - np.nonzero(fg[:, px0])[0].min()) / S - 0.2, 2),
                                 "bottom": round((np.nonzero(fg[:, px0])[0].max() - py0) / S - 0.2, 2)}
    out["checks"] = {"strap_width_mm": round(2 * inner, 2), "lug_to_lug_mm": round(sum(tips), 2)}

    # ---- hour and minute: lume blob, steel frame = lume grown and hulled to the hub ----
    bright = (im.min(2) > 240).astype(np.uint8)
    _, lab = cv2.connectedComponents(bright)
    ang = lambda dx, dy: math.degrees(math.atan2(dx, -dy)) % 360  # px vector -> clockwise from 12
    hands = {}
    for name in ("hour", "minute"):
        sx, sy = M[name]["lume_seed"]
        blob = (lab == lab[sy, sx]).astype(np.uint8)
        blob = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cnt = max(cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
        lume = cv2.convexHull(cnt)[:, 0]  # the lume reflection is patchy; its outline is convex
        grown = cv2.dilate(blob, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * M["frame_px"] + 1,) * 2))
        gp = cv2.findContours(grown, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0][:, 0]
        hub = [(px0 + M["hub_px"]["collar"] * math.cos(a), py0 + M["hub_px"]["collar"] * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
        hull = cv2.convexHull(np.float32(np.vstack([gp, hub])))[:, 0]
        far = max(gp, key=lambda p: math.hypot(p[0] - px0, p[1] - py0))
        hands[name] = {"angle_deg": round(ang(far[0] - px0, far[1] - py0), 2), "length_mm": round(math.hypot(far[0] - px0, far[1] - py0) / S, 3),
                       "outline_mm": [mm(p) for p in hull[::-1]], "lume_mm": [mm(p) for p in lume[::-1]]}  # image y down -> ccw in mm

    def needle(o, tip, hw_root, hw_tip, tail=None, hw_tail=0):
        u = np.float32(tip) - o
        L = float(np.hypot(*u))
        u /= L
        n = np.float32([-u[1], u[0]])
        pts = [o + u * L + n * hw_tip, o - n * hw_root if tail is None else o + n * hw_root, o - n * hw_root, o + u * L - n * hw_tip]
        if tail is not None:  # counterweight on the same line, rounded end
            Lt = float(np.hypot(*(np.float32(tail) - o)))
            pts = [o + u * L + n * hw_tip, o + n * hw_root, o - u * (Lt - hw_tail) + n * hw_tail]
            pts += [o - u * (Lt - hw_tail) + (n * math.cos(a) - u * math.sin(a)) * hw_tail for a in np.linspace(0, math.pi, 9)[1:-1]]
            pts += [o - u * (Lt - hw_tail) - n * hw_tail, o - n * hw_root, o + u * L - n * hw_tip]
        return [mm(p) for p in pts], ang(*u), L

    sm = M["seconds"]
    poly, a, L = needle(np.float32([px0, py0]), sm["tip"], sm["half_width"] + 1.0, sm["half_width"] - 0.8, sm["tail"], sm["tail_half_width"])
    hands["seconds"] = {"angle_deg": round(a, 2), "length_mm": round(L / S, 3), "outline_mm": poly}
    subs = {}
    for k, v in M["subdials"].items():
        o = np.float32(v["hub"])
        hw = M["subdial_half_width_px"]
        poly, a, L = needle(o, v["tip"], hw, hw * 0.5, o - (np.float32(v["tip"]) - o) * 0.25, hw * 1.4)
        subs[k] = {"centre_mm": mm(o), "angle_deg": round(a, 2), "length_mm": round(L / S, 3), "outline_mm": poly,
                   "hub_radius_mm": round(M["subdial_hub_px"] / S, 3)}
    out["hands"] = hands
    out["subdial_hands"] = subs
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub_px"].items()}
    out["pushers"] = {k: {"angle_deg": round(ang(p[0] - px0, p[1] - py0), 2), "end_r_mm": round(math.hypot(p[0] - px0, p[1] - py0) / S, 3)}
                      for k, p in M["pushers"].items()}
    out["pusher_radius_mm"] = round(M["pusher_radius_px"] / S, 3)

    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"angle_deg": round(ang(cr["x_tube_body_end"][1] - px0, (yt + yb) / 2 - py0), 2), "radius_mm": round((yb - yt) / 2 / S, 3),
                    "tube_radius_mm": round(cr["tube_radius_px"] / S, 3), "teeth": cr["teeth"],
                    "r_tube_body_end_mm": [round((x - px0) / S, 3) for x in cr["x_tube_body_end"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(cx), int(cy)), int(rad), (0, 0, 255), 2)
        for r in M["ring_radius_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 128, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, Pp((-l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, Pp((r_, y_mm)), 2, (0, 255, 0), -1)
        polys = [hd[k] for hd in hands.values() for k in ("outline_mm", "lume_mm") if k in hd] + [s["outline_mm"] for s in subs.values()]
        for p in polys:
            cv2.polylines(ov, [np.array([Pp(q) for q in p])], True, (0, 200, 255), 1)
        lg = out["lug"]
        for sy in (1, -1):
            cv2.line(ov, Pp((-20, sy * lg["tip_mm"]["mean"])), Pp((20, sy * lg["tip_mm"]["mean"])), (0, 128, 255), 2)
            cv2.line(ov, Pp((-20, sy * lg["from_y_mm"])), Pp((20, sy * lg["from_y_mm"])), (255, 255, 0), 1)
        for sx in (1, -1):
            cv2.line(ov, Pp((sx * inner, -38)), Pp((sx * inner, 38)), (0, 128, 255), 1)
        for p in out["pushers"].values():
            t = math.radians(p["angle_deg"])
            cv2.circle(ov, Pp((p["end_r_mm"] * math.sin(t), p["end_r_mm"] * math.cos(t))), int(M["pusher_radius_px"]), (255, 0, 255), 2)
        k = out["crown"]
        for r_ in k["r_tube_body_end_mm"]:
            cv2.line(ov, Pp((r_, -k["radius_mm"])), Pp((r_, k["radius_mm"])), (255, 0, 128), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "rings_mm", "lug", "strap_photo_end_mm", "checks", "crown", "pushers")},
                     default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, {k: v["angle_deg"] for k, v in data["subdial_hands"].items()},
          "guard rows", len(data["guard_y_right_mm"]))
