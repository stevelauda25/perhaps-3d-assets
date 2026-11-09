"""Measure the Zeppelin 100 Jahre chronograph Z8680MB3 front photo (white background, 2636 x 4096) into mm. numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z8680mb3_trace [out.json] [overlay.png]   # default config/watches/zeppelin-z8680mb3-trace.json

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
FRONT = ROOT / "references/zeppelin-z8680mb3/front_2636x4096.png"
OUT = ROOT / "config/watches/zeppelin-z8680mb3-trace.json"
CASE_MM = 42.0  # listing: 42 mm case, 11 mm thick
HAND_DARK = 80  # grey level: hands are < 60, their shadows 80-140, the cream dial > 200
HAND_ZONE_PX = 18

MANUAL_PX = {
    "hand_pivot": [1247, 2032],
    "ring_radius_px": {"bezel_inner": 916, "telemeter_inner": 860, "dial_edge": 800},
    # black lollipop hands: tip, leaf (from, to, half width), open ring (centre distance, inner radius, outer radius), body half width
    "hour": {"tip": [766, 1717], "leaf": [80, 260, 15], "disc": [354, 19, 33], "half": 7},
    "minute": {"tip": [1721, 1426], "leaf": [80, 340, 11], "disc": [554, 20, 36], "half": 6},
    "chrono": {"tip": [1233, 1262], "half": 4, "tail": 305, "tail_half": 8, "hub": 30},
    "subdials": {
        "left": {"centre": [924, 1967], "hand": [[0, 120], [32, 0], [0, -60], [-32, 0]], "tail_disc": [-84, 16], "hub": 18, "angle_from": [927, 1840]},
        "right": {"centre": [1572, 1955], "hand": [[4, 0], [3, 212], [0, 218], [-3, 212], [-4, 0], [-3, -60], [3, -60]], "tail_disc": [-68, 9], "hub": 30, "angle_from": [1615, 1742]},
        "alarm_a": {"centre": [1252, 2366], "hand": [[6, 0], [4, 200], [0, 212], [-4, 200], [-6, 0], [-14, -50], [0, -85], [14, -50]], "hub": 25, "angle_from": [1296, 2159]},
        "alarm_b": {"centre": [1252, 2366], "hand": [[12, 0], [16, 80], [5, 140], [0, 150], [-5, 140], [-7, 0], [-28, -40], [0, -85], [28, -40]], "hub": 0, "angle_from": [1329, 2491]},
    },
    "crown": {"centre_y": 2011, "radius": 128, "x_from_to": [2254, 2267, 2437, 2488]},  # case edge, flutes start, flutes end, domed end
    "pushers": [{"head_centre": [2230, 1473], "head_radius": 72, "stem_radius": 88, "r_from_to": [1018, 1100, 1185]},
                {"head_centre": [2230, 2591], "head_radius": 72, "stem_radius": 88, "r_from_to": [1018, 1100, 1185]}],
    # bracelet (top half, where the photo is straight): outer first joint = lug tip, centre first joint half a row later
    "bracelet_edges_x": [734, 1780],
    "centre_half_px": 200, "centre_polish_half_px": 142,
    "outer_joints_y": [858, 608, 358],
    "centre_joints_y": [730, 495, 253],
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
    for y in list(range(1450, 1800, 10)) + list(range(2300, 2650, 10)):
        pts.append((np.nonzero(fg[y])[0].min(), y))
    for y in list(range(1650, 1850, 10)) + list(range(2200, 2420, 10)):
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
    # exact hand shapes: black hands on the cream dial threshold cleanly inside each hand's zone (rough outline + 18 px)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    Pp = lambda xy: (px0 + xy[0] * S, py0 - xy[1] * S)

    def zone(polys, circles=(), grow=HAND_ZONE_PX):
        z_ = np.zeros(gray.shape, np.uint8)
        for poly in polys:
            cv2.fillPoly(z_, [np.round([Pp(q) for q in poly]).astype(np.int32)], 1)
        for c_, r_ in circles:
            cv2.circle(z_, tuple(int(v) for v in Pp(c_)), int(r_ * S), 1, -1)
        return cv2.dilate(z_, np.ones((3, 3), np.uint8), iterations=grow)

    def pieces(z_, holes, k, dark=HAND_DARK, min_area=300):
        m = ((gray < dark) & (z_ > 0)).astype(np.uint8)
        for c_, r_ in holes:  # rings and hubs are built as separate round parts
            cv2.circle(m, tuple(int(v) for v in Pp(c_)), int(round(r_ * S)), 0, -1)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))  # drops thin dial print
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        return [[[round((x - px0) / S, 3), round(-(y - py0) / S, 3)] for x, y in cv2.approxPolyDP(c_, 0.8, True)[:, 0]]
                for c_ in cs if cv2.contourArea(c_) > min_area]

    for n in ("hour", "minute"):  # ring centre and hole radius from the bright hole inside each ring
        h_, (_, ri, ro) = hands[n], M[n]["disc"]
        cx_, cy_ = (int(round(v)) for v in Pp(h_["disc_centre_mm"]))
        win = (gray[cy_ - 60:cy_ + 61, cx_ - 60:cx_ + 61] > 150).astype(np.uint8)
        _, lab = cv2.connectedComponents(win)
        ys, xs = np.nonzero(lab == lab[60, 60])
        hull = cv2.convexHull(np.c_[xs, ys].astype(np.int32))  # convex hull: dial print seen through the hole (the "2") counts as hole
        mo = cv2.moments(hull)
        h_["disc_centre_mm"] = [round((cx_ - 60 + mo["m10"] / mo["m00"] - px0) / S, 3), round(-(cy_ - 60 + mo["m01"] / mo["m00"] - py0) / S, 3)]
        h_["disc_lume_r_mm"] = round(math.sqrt(mo["m00"] / math.pi) / S, 3)
        h_["disc_ring_r_mm"] = round(h_["disc_lume_r_mm"] + (ro - ri) / S, 3)
    hub_r = hands["chrono"]["hub_r_mm"] * 1.8
    zones = {n: zone([hands[n]["outline_mm"]], [(hands[n]["disc_centre_mm"], hands[n]["disc_ring_r_mm"])]) for n in ("hour", "minute")}
    for n in ("hour", "minute"):
        hands[n]["pieces_mm"] = pieces(zones[n], [((0, 0), hub_r), (hands[n]["disc_centre_mm"], hands[n]["disc_ring_r_mm"] - 0.03)], 7)
    for k in ("left", "right"):
        sd = subs[k]
        circ = [(sd["tail_disc_mm"][:2], sd["tail_disc_mm"][2])] if "tail_disc_mm" in sd else []
        z_ = zone([sd["outline_mm"]], circ, 18 if k == "left" else 6) & (1 - zones["hour"])  # thin needle: tight zone keeps the "60" out
        sd["pieces_mm"] = pieces(z_, [(sd["centre_mm"], sd["hub_r_mm"] * 1.3)] if k == "right" else [], 3, 120)  # polished centre line: looser
    # alarm sub-dial: the thick bar from the main hub, both arrow hands and their tails overlap; traced as one black group
    tail = [q for q in hands["chrono"]["outline_mm"] if q[1] < 0]
    z_ = zone([subs["alarm_a"]["outline_mm"], subs["alarm_b"]["outline_mm"], tail + [[0.4, 0.0], [-0.4, 0.0]]], grow=14)
    subs["alarm_a"]["pieces_mm"] = pieces(z_, [((0, 0), hub_r)], 3, 120, 800)  # 800 px2: keeps the arrow tail, drops bits of the printed "12"
    subs["alarm_b"]["pieces_mm"] = []
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
        polys = [q for hd in list(hands.values()) + list(subs.values()) for q in hd.get("pieces_mm", [hd["outline_mm"]])]
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
