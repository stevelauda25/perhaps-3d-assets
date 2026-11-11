"""Measure the Bulova 98A273 (Marine Star Automatic 44 mm, gold tone, black dial, open heart) official front render
(1347 x 2048, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.bulova_98a273_trace [out.json] [overlay.png]   # default config/watches/bulova-98a273-trace.json

mm, x right, y toward 12, origin = hand pivot. Anchor: the black polygon ring's silhouette at 9 and 3 o'clock = the official
44 mm case width; the official 24 mm lug width and 51 mm case length are the checks. Traced from the render: the case and lug
silhouette (alpha, 12 and 6 o'clock averaged), the black ring's outer edge per degree (dark run outside the gold bezel), the
bezel circles, the subdial and open-heart rings, and the applied gold numerals and logo (gold mask, hands cut out; II is
completed from its mirror image about its own radius). Hands, crown, screws and bracelet joints are read from gridded crops and
hand-aligned strips (MANUAL_PX, about +-0.05 mm). Hands are in hand-local px: w across, d along the hand from the pivot.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load
from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/bulova-98a273/front_official_1347x2048.png"
OUT = ROOT / "config/watches/bulova-98a273-trace.json"
CASE_MM = 44.0  # Bulova official case width
LISTED = {"lug_width_mm": 24.0, "case_length_mm": 51.0, "thickness_mm": 13.45}

MANUAL_PX = {
    "hand_pivot": [617, 996],
    "bezel_flat_px": 469,  # polished inner slope of the gold bezel ends here, brushed flat top outside
    "chapter_in_px": 380,  # black chapter ring with the printed minute numerals: dial map
    # six black screws on the gold bezel (12, 2, 4, 6, 8, 10)
    "screws": {"r": 510, "angles": [0, 60, 120, 180, 240, 300], "radius": 34, "socket": 15},
    "crown": {"centre_y": 993, "x_from_to": [1209, 1331], "radius": 84, "teeth": 16, "collar_x": 1195},
    "crown_rows": [905, 1082],  # the crown hides the case edge between these rows: the case edge is held at collar_x
    "lug_tip_rows": [311, 1693],
    # bracelet: five columns (|x| edges centre / middle / outer), joints = dark rows per column nearest the case
    "bracelet_edges_x": {"centre": [534, 697], "middle": [436, 786], "outer": [294, 932]},
    "end_link_from_rows": [396, 1593],  # end link meets the case
    "joints_outer_rows": [[301, 174], [1691, 1833]],  # outer and centre columns
    "joints_mid_rows": [[249, 123], [1757, 1900]],
    "hands": {
        # gold frame, white lume, an open window near the hub; outline = [d, half width]
        "hour": {"angle": 304.6, "outline": [[-20, 31], [40, 31], [60, 23.5], [125, 23.5], [182, 28], [258, 0]],
                 "window": [44, 104, 15], "lume": [[0, 233], [19, 185], [18, 127], [-18, 127], [-19, 185]]},
        "minute": {"angle": 53.4, "outline": [[-20, 31], [40, 31], [60, 23.5], [160, 23.5], [297, 25.5], [378, 0]],
                   "window": [65, 140, 14], "lume": [[0, 365], [18, 297], [17, 157], [-17, 157], [-18, 297]]},
    },
    "hub": {"collar": 31, "pin": 12.5},
    # small seconds at 4: gold hand, paddle tail
    "subdial": {"centre": [716, 1123], "ring": [123, 149], "hand_angle": 253.6, "hand_length": 105, "tail": 52,
                "tail_half": 8, "half_at_hub": 4, "half_at_tip": 1.2, "hub": 10},
    "heart_guess": [520, 1159],  # open heart: the gold ring's centre is fitted from here
    "numeral_band_px": [250, 380],
    "mirror_numerals": {"II": 60.0},  # the minute hand covers the inner end of II
}
ARTEFACTS = ["chapter ring prints, sunray dial, BULOVA / Marine Star / 200m / AUTOMATIC 21 JEWELS, subdial print and the open "
             "heart's movement stay in the dial map",
             "the render's bracelet curves away from the camera: the link pitch is read on the 6 o'clock side (less foreshortened)",
             "the open heart is transparent in the render: the dial map fills it with dark movement shadow"]


def trace(path=FRONT, overlay=None):
    raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    im = load(path)
    fg = raw[..., 3] > 128
    hsv = cv2.cvtColor(raw[..., :3], cv2.COLOR_BGR2HSV)
    h, s_, v = (hsv[..., i].astype(int) for i in range(3))
    gold = (((v > 70) & (s_ > 60)) | ((v > 150) & (s_ > 30))) & (h > 8) & (h < 35) & fg  # gold tone in light and shade
    dark = (v < 110) & fg
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # ---- gold bezel: inner edge (gold after the black chapter ring) and outer edge (dark after the gold), on rays ----
    inner, outer = [], []
    for a in np.arange(0, 360, 2.0):
        for r in np.arange(430, 470, 0.5):
            x, y = (int(round(v)) for v in at(r, a))
            if gold[y, x]:
                inner.append(at(r, a))
                break
        for r in np.arange(540, 600, 0.5):
            x, y = (int(round(v)) for v in at(r, a))
            if dark[y, x]:
                outer.append(at(r, a))
                break
    bi = fit_circle(np.array(inner))
    bo = fit_circle(np.array(outer))

    # ---- black ring: outer edge per degree (end of the dark run outside the gold bezel), anchor at 9 and 3 ----
    ring = []
    for a in range(360):
        r0 = bo[2] - 2
        r, seen = r0, False
        while r < 680:
            x, y = (int(round(v)) for v in at(r, a))
            if dark[y, x]:
                seen = True
            elif seen and r > bo[2] + 3 and (gold[y, x] or not fg[y, x]):  # the ring's outer face reflects grey: run to gold or air
                break
            r += 0.5
        ring.append(r)
    skirt = []  # the silhouette just outside the black ring (gold corner facets under its notches)
    for a, r in enumerate(ring):
        r2 = r
        while r2 < r + 40:
            x, y = (int(round(v)) for v in at(r2 + 0.5, a))
            if not fg[y, x]:
                break
            r2 += 0.5
        skirt.append(r2)
    side = [ring[a] for a in list(range(84, 97)) + list(range(264, 277))]
    S = 2 * float(np.mean(side)) / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(float(v) / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "black ring silhouette at 9 and 3 o'clock = %.0f mm (Bulova official case width)" % CASE_MM}
    out["rings_mm"] = {"chapter_in": f(M["chapter_in_px"]), "bezel_in": f(bi[2]), "bezel_flat": f(M["bezel_flat_px"]), "bezel_out": f(bo[2])}
    out["bezel_centre_mm"] = {"inner": mm(bi[:2]), "outer": mm(bo[:2])}
    out["black_ring_r_mm"] = [f(r) for r in ring]  # index = clockwise degrees from 12
    out["silhouette_r_mm"] = [f(r) for r in skirt]  # alpha edge along the same rays, at most 40 px past the ring

    # ---- case and lug silhouette: left / right edge per |y| (12 and 6 averaged); crown rows held at the collar ----
    c0, c1 = M["crown_rows"]
    half = {"left": [], "right": []}
    t0, t1 = M["lug_tip_rows"]
    tip = ((py0 - t0) + (t1 - py0)) / 2 / S
    for y_mm in np.arange(0, tip + 0.001, 0.25):
        vals = {"left": [], "right": []}
        for sy in (1, -1):
            row = int(round(py0 - sy * y_mm * S))
            xs = np.nonzero(fg[row])[0]
            xr = xs.max()
            if c0 <= row <= c1:
                xr = min(xr, M["crown"]["collar_x"])
            vals["left"].append((px0 - xs.min()) / S)
            vals["right"].append((xr - px0) / S)
        for k in half:
            half[k].append([round(float(y_mm), 3), round(float(np.mean(vals[k])), 3)])
    out["half_outline_mm"] = half
    be = M["bracelet_edges_x"]
    e = {k: ((px0 - v[0]) + (v[1] - px0)) / 2 / S for k, v in be.items()}
    out["lug"] = {"tip_y_mm": round(tip, 3), "tips_photo_mm": [f(py0 - t0), f(t1 - py0)], "inner_x_mm": round(e["outer"], 3)}

    # ---- bracelet: five columns, joints nearest the case, pitch from the 6 o'clock side ----
    jo, jm = M["joints_outer_rows"], M["joints_mid_rows"]
    out["bracelet_mm"] = {
        "edges": [round(e["centre"], 3), round(e["middle"], 3), round(e["outer"], 3)],
        "end_from": round(((py0 - M["end_link_from_rows"][0]) + (M["end_link_from_rows"][1] - py0)) / 2 / S, 3),
        "joints_outer": [round(((py0 - jo[0][0]) + (jo[1][0] - py0)) / 2 / S, 3)],
        "joints_mid": [round(((py0 - jm[0][0]) + (jm[1][0] - py0)) / 2 / S, 3)],
        "pitch_12_6": [f(jo[0][0] - jo[0][1]), f(jo[1][1] - jo[1][0])],
        "pitch": f(((jo[1][1] - jo[1][0]) + (jm[1][1] - jm[1][0])) / 2),
    }
    out["checks"] = {"lug_width_mm": round(2 * e["outer"], 3), "case_length_mm": round(2 * tip, 3), "listed": LISTED,
                     "bezel_in_vs_out_centre_px": [round(bi[0] - bo[0], 1), round(bi[1] - bo[1], 1)]}

    # ---- crown, screws ----
    cr = M["crown"]
    out["crown"] = {"centre_y_mm": mm((0, cr["centre_y"]))[1], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"],
                    "r_from_to_mm": [f(x - px0) for x in cr["x_from_to"]], "collar_mm": f(cr["collar_x"] - px0)}
    sc = M["screws"]
    out["screws"] = {"r_mm": f(sc["r"]), "angles_deg": sc["angles"], "radius_mm": f(sc["radius"]), "socket_mm": f(sc["socket"])}

    # ---- hands: hand-local px -> model mm ----
    def to_mm(w, d, ang):
        a = math.radians(ang)
        return [round((w * math.cos(a) + d * math.sin(a)) / S, 3), round((-w * math.sin(a) + d * math.cos(a)) / S, 3)]
    hands = {}
    for name, h in M["hands"].items():
        o = h["outline"]
        poly = [(-v, d) for d, v in o[::-1]] + [(v, d) for d, v in o[:-1]]  # tip once, both tail corners
        d0, d1, hw = h["window"]
        hands[name] = {"angle_deg": h["angle"], "length_mm": f(o[-1][0]),
                       "outline_mm": [to_mm(w, d, h["angle"]) for w, d in poly],
                       "window_mm": [to_mm(w, d, h["angle"]) for w, d in ((-hw, d0), (hw, d0), (hw, d1), (-hw, d1))],
                       "lume_mm": [to_mm(w, d, h["angle"]) for w, d in h["lume"][::-1]]}
    out["hands"] = hands
    out["hub_mm"] = {k: f(v) for k, v in M["hub"].items()}
    sd = M["subdial"]
    cx, cy = sd["centre"]
    out["subdial"] = {"centre_mm": mm((cx, cy)), "ring_mm": [f(v) for v in sd["ring"]], "hand_angle_deg": sd["hand_angle"],
                      "hand_length_mm": f(sd["hand_length"]), "tail_mm": f(sd["tail"]), "tail_half_mm": f(sd["tail_half"]),
                      "half_mm": [f(sd["half_at_hub"]), f(sd["half_at_tip"])], "hub_mm": f(sd["hub"])}

    # ---- open heart: gold ring fitted from the outer edge (scan inward from outside) ----
    hx, hy = M["heart_guess"]
    pts = []
    for a in np.arange(0, 360, 3.0):
        if 20 < a < 140:  # the subdial ring joins the heart ring here
            continue
        for r in np.arange(170, 120, -0.5):
            x, y = int(round(hx + r * math.sin(math.radians(a)))), int(round(hy - r * math.cos(math.radians(a))))
            if gold[y, x]:
                pts.append((hx + r * math.sin(math.radians(a)), hy - r * math.cos(math.radians(a))))
                break
    hc = fit_circle(np.array(pts))
    out["heart"] = {"centre_mm": mm(hc[:2]), "ring_out_mm": f(hc[2]), "ring_in_mm": f(hc[2] - 11)}

    # ---- applied gold numerals and logo: gold mask in the numeral band, hands and rings cut out ----
    hm = np.zeros(fg.shape, np.uint8)
    P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
    for h in hands.values():
        cv2.fillPoly(hm, [np.array([P(p) for p in h["outline_mm"]], np.int32)], 1)
    hm = cv2.dilate(hm, np.ones((9, 9), np.uint8)).astype(bool)
    yy, xx = np.mgrid[0:fg.shape[0], 0:fg.shape[1]]
    rr = np.hypot(xx - px0, yy - py0)
    b0, b1 = M["numeral_band_px"]
    keep = gold & ~hm & (rr < M["chapter_in_px"]) & (np.hypot(xx - cx, yy - cy) > sd["ring"][1] + 6) & \
        (np.hypot(xx - hc[0], yy - hc[1]) > hc[2] + 6) & (rr > 120)
    m = keep.astype(np.uint8)
    for name, deg in M["mirror_numerals"].items():  # mirror about the numeral's own radius, only where the hand hid it
        u = np.array([math.sin(math.radians(deg)), -math.cos(math.radians(deg))])  # the radius in image axes
        A = 2 * np.outer(u, u) - np.eye(2)
        Mr = np.c_[A, np.array([px0, py0]) - A @ np.array([px0, py0])]
        mirrored = cv2.warpAffine(m, Mr.astype(np.float64), m.shape[::-1], flags=cv2.INTER_NEAREST)
        near = (np.abs(((np.degrees(np.arctan2(xx - px0, py0 - yy)) - deg + 180) % 360) - 180) < 12) & (rr > b0) & (rr < b1)
        m |= (mirrored.astype(bool) & hm & near).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    shapes = []
    for i, cnt in enumerate(cnts):
        if hier[0][i][3] != -1 or cv2.contourArea(cnt) < 120:
            continue
        poly = lambda c: [mm((float(x), float(y))) for x, y in cv2.approxPolyDP(c, 0.7, True)[:, 0][::-1]]
        holes = [poly(cnts[j]) for j in range(len(cnts)) if hier[0][j][3] == i and cv2.contourArea(cnts[j]) > 15]
        shapes.append({"outer": poly(cnt), "holes": holes, "area_px": int(cv2.contourArea(cnt))})
    out["applied_gold_mm"] = shapes

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        Q = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for c_ in (bi, bo, hc):
            cv2.circle(ov, (int(c_[0]), int(c_[1])), int(c_[2]), (0, 0, 255), 1)
        cv2.polylines(ov, [np.array([at(r, a) for a, r in enumerate(ring)], np.int32)], True, (0, 200, 255), 1)
        for k in half:
            sx = 1 if k == "right" else -1
            for sy in (1, -1):
                cv2.polylines(ov, [np.array([Q((sx * x, sy * y)) for y, x in half[k]], np.int32)], False, (255, 128, 0), 1)
        for h in hands.values():
            for key in ("outline_mm", "window_mm", "lume_mm"):
                cv2.polylines(ov, [np.array([Q(p) for p in h[key]], np.int32)], True, (0, 255, 0), 1)
        for sh in shapes:
            cv2.polylines(ov, [np.array([Q(p) for p in sh["outer"]], np.int32)] + [np.array([Q(p) for p in hl], np.int32) for hl in sh["holes"]],
                          True, (255, 0, 255), 1)
        for a in sc["angles"]:
            cv2.circle(ov, tuple(int(v) for v in at(sc["r"], a)), sc["radius"], (0, 255, 255), 1)
        cv2.circle(ov, (cx, cy), sd["ring"][0], (0, 255, 255), 1)
        cv2.circle(ov, (cx, cy), sd["ring"][1], (0, 255, 255), 1)
        k = out["crown"]
        for x in k["r_from_to_mm"]:
            cv2.line(ov, Q((x, k["centre_y_mm"] - k["radius_mm"])), Q((x, k["centre_y_mm"] + k["radius_mm"])), (255, 0, 128), 2)
        for rows in (jo, jm, [M["end_link_from_rows"]]):
            for pair in rows:
                for y in pair:
                    cv2.line(ov, (280, y), (950, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "bezel_centre_mm", "lug", "bracelet_mm", "checks", "crown",
                                           "heart", "subdial")}, default=float), "->", dest)
    print("applied gold shapes", len(data["applied_gold_mm"]), sorted(s["area_px"] for s in data["applied_gold_mm"]))
