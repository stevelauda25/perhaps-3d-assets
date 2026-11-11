"""Measure the Bulova 96B431 (Marine Star Precisionist 43 mm, yellow wave dial, black twelve-sided bezel, black rubber strap)
official front render (1253 x 2048, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.bulova_96b431_trace [out.json] [overlay.png]   # default config/watches/bulova-96b431-trace.json

mm, x right, y toward 12, origin = hand pivot. Anchor: the official 43 mm case width = the bezel's polished twelve-sided rim
flat to flat (9 o'clock silhouette and the flats at 12 and 6); the official 22 mm lug width is the check. Traced: the yellow
dial edge (circle fit), the black insert's and the rim's flats (twelve-sided, flats at 12, 1, 2 ...), the case and lug
silhouette (alpha, 12 and 6 o'clock averaged), the strap's width per mm past the lug tips, the applied indices (lume mask in
each hour's frame turned to 12, mean of the hours no hand covers; frame = lume grown by the steel rim) and the applied logo
(steel mask in its box). Hands, crown and lug corners are read from gridded crops and hand-aligned strips (MANUAL_PX, about
+-0.05 mm). Hands are in hand-local px: w across, d along the hand from the pivot.
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
FRONT = ROOT / "references/bulova-96b431/front_official_1253x2048.png"
OUT = ROOT / "config/watches/bulova-96b431-trace.json"
CASE_MM = 43.0  # Bulova official case width
LISTED = {"lug_width_mm": 22.0, "case_length_mm": 50.0, "thickness_mm": 12.1}

MANUAL_PX = {
    "hand_pivot": [586, 986],
    "sides": 12,  # bezel: twelve flats at 0, 30, 60 ... deg
    "crown": {"centre_y": 1002, "x_from_to": [1160, 1237], "radius": 86, "teeth": 14, "collar_x": 1150},
    "crown_rows": [905, 1100],
    "lug_tip_rows": [357, 1657],  # the render's 6 o'clock lugs are 1.6 mm longer: the model uses the mean
    "notch_rows": [421, 1558],  # straight case edge between the lugs (the strap end tucks under it)
    "lug_inner_x": [295, 880],
    "hands": {
        # polished steel frame, white lume, an open window near the hub; outline = [d, half width]
        "hour": {"angle": 301.4, "outline": [[-72, 21], [0, 21], [45, 21], [100, 25.5], [211, 28.5], [247, 0]],
                 "window": [47, 88, 15], "lume": [[0, 235], [19.5, 205], [18, 103], [-18, 103], [-19.5, 205]]},
        "minute": {"angle": 57.4, "outline": [[-101, 19], [15, 19], [40, 12], [95, 19], [180, 19.5], [337, 17.5], [372, 0]],
                   "window": [52, 85, 10.5], "lume": [[0, 360], [12, 337], [13.5, 330], [13.5, 97], [-13.5, 97], [-13.5, 330], [-12, 337]]},
    },
    # seconds: steel needle and tail, red-framed lume triangle, red stick to the tip
    "seconds": {"angle": 209.0, "needle_half": 2, "tail": 123, "tail_half": 10.6, "neck": [30, 4], "tri": [240, 290, 22], "stick": [290, 387, 3]},
    "hub": {"disc": 20, "pin": 6},
    "indices": {"band": [300, 400], "frame_px": 4, "types": {"bar": [1, 4, 5, 6, 8, 9, 10, 11], "short": [3]},
                "place": {"bar": [1, 2, 4, 5, 6, 7, 8, 9, 10, 11], "short": [3]}},
    "logo_box": [535, 600, 637, 735],
}
ARTEFACTS = ["hour and minute hands run through the hub into short flat tails; the seconds hand has a broad flat tail",
             "wave dial pattern, yellow minute track, BULOVA / Marine Star / 200m / 262 kHz prints, the date window with its "
             "frame and the bezel insert's numerals and markers stay in the dial map",
             "the minute hand covers the 2 o'clock index and the seconds hand the 7 o'clock one: both use the mean bar shape",
             "lug tips are 23.9 mm (12) and 25.5 mm (6) from the pivot in the render, the model uses the mean"]


def trace(path=FRONT, overlay=None):
    raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    im = load(path)
    fg = raw[..., 3] > 128
    hsv = cv2.cvtColor(raw[..., :3], cv2.COLOR_BGR2HSV)
    h, s_, v = (hsv[..., i].astype(int) for i in range(3))
    yellow = (s_ > 100) & (h > 15) & (h < 40) & (v > 120)
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # ---- yellow dial edge (circle fit), insert and rim flats ----
    edge = []
    for a in np.arange(0, 360, 2.0):
        r = 420.0
        while r < 460:
            x, y = (int(round(q)) for q in at(r, a))
            if not yellow[y, x]:
                break
            r += 0.5
        edge.append(at(r, a))
    dc = fit_circle(np.array(edge))
    ins, rim = [], []
    c7 = math.cos(math.radians(7))
    for k in range(M["sides"]):
        vals = []
        for off in (-7.0, 7.0):  # 7 deg off each flat's middle: the insert's numerals and markers sit on the middles
            a = 30.0 * k + off
            r = 470.0
            while r < 620:  # black insert ends where the polished rim starts
                x, y = (int(round(q)) for q in at(r, a))
                if v[y, x] > 140:
                    break
                r += 0.5
            vals.append(r * c7)
            if k in (8, 9, 10):  # 8, 9 and 10 o'clock: the rim's outer flat is the silhouette
                r2 = r
                while r2 < 640 and fg[(lambda q: (int(round(q[1])), int(round(q[0]))))(at(r2, a))]:
                    r2 += 0.5
                rim.append(r2 * c7)
        ins.append(float(np.mean(vals)))
    rim_ap = float(np.mean(rim))
    S = 2 * rim_ap / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda q: round(float(q) / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "bezel rim flat to flat = %.0f mm (Bulova official case width)" % CASE_MM}
    out["rings_mm"] = {"dial": f(dc[2]), "insert_in": f(dc[2]), "insert_apothem": f(np.median(sorted(ins)[len(ins) // 2:])), "rim_apothem": f(rim_ap)}
    out["dial_centre_mm"] = mm(dc[:2])
    out["insert_flats_mm"] = [f(r) for r in ins]
    out["sides"] = M["sides"]

    # ---- case and lug silhouette (12 and 6 averaged); crown rows held at the collar ----
    t0, t1 = M["lug_tip_rows"]
    tip = ((py0 - t0) + (t1 - py0)) / 2 / S
    n0, n1 = M["notch_rows"]
    c0, c1 = M["crown_rows"]
    half = {"left": [], "right": []}
    for y_mm in np.arange(0, tip + 0.001, 0.25):
        vals = {"left": [], "right": []}
        for sy, (row_tip, ph) in ((1, (t0, py0 - t0)), (-1, (t1, t1 - py0))):
            row = int(round(py0 - sy * y_mm * S * ph / (tip * S)))  # each side scaled to the mean tip
            xs = np.nonzero(fg[row])[0]
            xr = xs.max()
            if c0 <= row <= c1:
                xr = min(xr, M["crown"]["collar_x"])
            vals["left"].append((px0 - xs.min()) / S)
            vals["right"].append((xr - px0) / S)
        for k in half:
            half[k].append([round(float(y_mm), 3), round(float(np.mean(vals[k])), 3)])
    out["half_outline_mm"] = half
    xl, xr_ = M["lug_inner_x"]
    out["lug"] = {"tip_y_mm": round(tip, 3), "tips_photo_mm": [f(py0 - t0), f(t1 - py0)], "inner_x_mm": f(((px0 - xl) + (xr_ - px0)) / 2),
                  "notch_y_mm": f(((py0 - n0) + (n1 - py0)) / 2)}
    out["checks"] = {"lug_width_mm": f(xr_ - xl), "case_length_mm": round(2 * tip, 3), "listed": LISTED,
                     "dial_vs_pivot_px": [round(dc[0] - px0, 1), round(dc[1] - py0, 1)]}

    # ---- strap: half width per mm past the lug tip (both ends averaged), and the photo rows it spans ----
    widths = []
    for k in range(0, 200):
        s_mm = k * 0.1
        ws = []
        for sy, row0 in ((1, t0), (-1, t1)):
            row = int(round(row0 - sy * s_mm * S))
            if not 0 <= row < fg.shape[0]:
                continue
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                ws.append((xs.max() - xs.min()) / 2 / S)
        if len(ws) == 2:
            widths.append([round(s_mm, 2), round(float(np.mean(ws)), 3)])
    out["strap"] = {"half_width_by_s_mm": widths, "tip_rows": [t0, t1], "notch_rows": [n0, n1]}

    # ---- crown ----
    cr = M["crown"]
    out["crown"] = {"centre_y_mm": mm((0, cr["centre_y"]))[1], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"],
                    "r_from_to_mm": [f(x - px0) for x in cr["x_from_to"]], "collar_mm": f(cr["collar_x"] - px0)}

    # ---- hands: hand-local px -> model mm ----
    def to_mm(w, d, ang):
        a = math.radians(ang)
        return [round((w * math.cos(a) + d * math.sin(a)) / S, 3), round((-w * math.sin(a) + d * math.cos(a)) / S, 3)]
    hands = {}
    for name, hd in M["hands"].items():
        o = hd["outline"]
        poly = [(-q, d) for d, q in o[::-1]] + [(q, d) for d, q in o[:-1]]  # tip once, both tail corners
        d0, d1, hw = hd["window"]
        hands[name] = {"angle_deg": hd["angle"], "length_mm": f(o[-1][0]),
                       "outline_mm": [to_mm(w, d, hd["angle"]) for w, d in poly],
                       "window_mm": [to_mm(w, d, hd["angle"]) for w, d in ((-hw, d0), (hw, d0), (hw, d1), (-hw, d1))],
                       "lume_mm": [to_mm(w, d, hd["angle"]) for w, d in hd["lume"][::-1]]}
    sc = M["seconds"]
    a = sc["angle"]
    (b0, b1, bh), (s0, s1, sh) = sc["tri"], sc["stick"]
    inset = 5
    hands["seconds"] = {"angle_deg": a, "length_mm": f(s1),
                        "needle_mm": [to_mm(w, d, a) for w, d in ((-sc["neck"][1], -sc["neck"][0]), (sc["neck"][1], -sc["neck"][0]),
                                                                 (sc["needle_half"], b0), (-sc["needle_half"], b0))],
                        "tail_mm": [to_mm(w, d, a) for w, d in ((-sc["tail_half"], -sc["tail"]), (sc["tail_half"], -sc["tail"]),
                                                               (sc["tail_half"], -sc["neck"][0]), (-sc["tail_half"], -sc["neck"][0]))],
                        "triangle_mm": [to_mm(w, d, a) for w, d in ((-bh, b0), (bh, b0), (0, b1))],
                        "triangle_lume_mm": [to_mm(w, d, a) for w, d in ((-bh + 2 * inset, b0 + inset), (bh - 2 * inset, b0 + inset), (0, b1 - 2.2 * inset))],
                        "stick_mm": [to_mm(w, d, a) for w, d in ((-sh, s0 - 4), (sh, s0 - 4), (sh * 0.7, s1), (-sh * 0.7, s1))]}
    out["hands"] = hands
    out["hub_mm"] = {k: f(q) for k, q in M["hub"].items()}

    # ---- applied indices: lume mask turned to 12 per hour, mean of the free hours; frame = lume grown ----
    ix = M["indices"]
    r0, r1 = ix["band"]
    lume = ((s_ < 45) & (v > 200)).astype(np.float32)
    win = np.s_[py0 - r1:py0 - r0, px0 - 60:px0 + 61]
    shapes = {}
    for kind, hours in ix["types"].items():
        acc = np.zeros((r1 - r0, 121), np.float32)
        for hr in hours:
            Mr = cv2.getRotationMatrix2D((float(px0), float(py0)), 30.0 * hr, 1.0)
            acc += cv2.warpAffine(lume, Mr, (raw.shape[1], raw.shape[0]), flags=cv2.INTER_LINEAR)[win]
        acc = (acc + acc[:, ::-1]) / 2
        m = (acc / len(hours) > 0.5).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        pts = {}
        for key, grow in (("lume_mm", 0), ("frame_mm", ix["frame_px"])):
            mk = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1,) * 2)) if grow else m
            cnt = max(cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
            poly = cv2.approxPolyDP(cnt, 0.8, True)[:, 0]
            pts[key] = [[round((x - 60) / S, 3), round((r1 - y) / S, 3)] for x, y in poly[::-1]]
        shapes[kind] = dict(pts, hours=ix["place"][kind])
    out["indices"] = shapes

    # ---- applied logo: steel (unsaturated) pixels in its box, outline with holes ----
    x0, y0, x1, y1 = M["logo_box"]
    lm = np.zeros(fg.shape, np.uint8)
    lm[y0:y1, x0:x1] = ((s_ < 70) & (v > 90))[y0:y1, x0:x1]
    lm = cv2.morphologyEx(lm, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    cnts, hier = cv2.findContours(lm, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    logo = []
    for i, cnt in enumerate(cnts):
        if hier[0][i][3] != -1 or cv2.contourArea(cnt) < 200:
            continue
        poly = lambda c: [mm((float(x), float(y))) for x, y in cv2.approxPolyDP(c, 0.7, True)[:, 0][::-1]]
        logo.append({"outer": poly(cnt), "holes": [poly(cnts[j]) for j in range(len(cnts)) if hier[0][j][3] == i and cv2.contourArea(cnts[j]) > 30]})
    out["logo_mm"] = logo

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        Q = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(dc[0]), int(dc[1])), int(dc[2]), (0, 0, 255), 1)
        for ap in (np.median(sorted(ins)[len(ins) // 2:]), rim_ap):
            R = ap / math.cos(math.pi / M["sides"])
            cv2.polylines(ov, [np.array([at(R, 15 + 30 * k) for k in range(12)], np.int32)], True, (0, 200, 255), 1)
        for k in half:
            sx = 1 if k == "right" else -1
            for sy in (1, -1):
                cv2.polylines(ov, [np.array([Q((sx * x, sy * y)) for y, x in half[k]], np.int32)], False, (255, 128, 0), 1)
        for hd in hands.values():
            for key in ("outline_mm", "window_mm", "lume_mm", "needle_mm", "triangle_mm", "stick_mm", "tail_mm"):
                if key in hd:
                    cv2.polylines(ov, [np.array([Q(p) for p in hd[key]], np.int32)], True, (0, 255, 0), 1)
        for sh in shapes.values():
            for hr in sh["hours"]:
                for key in ("lume_mm", "frame_mm"):
                    cv2.polylines(ov, [np.array([Q(rot_(p, 30 * hr)) for p in sh[key]], np.int32)], True, (255, 0, 255), 1)
        for lg_ in logo:
            cv2.polylines(ov, [np.array([Q(p) for p in lg_["outer"]], np.int32)] + [np.array([Q(p) for p in hl], np.int32) for hl in lg_["holes"]], True, (255, 0, 255), 1)
        k_ = out["crown"]
        for x in k_["r_from_to_mm"]:
            cv2.line(ov, Q((x, k_["centre_y_mm"] - k_["radius_mm"])), Q((x, k_["centre_y_mm"] + k_["radius_mm"])), (255, 0, 128), 2)
        for y in M["lug_tip_rows"] + M["notch_rows"]:
            cv2.line(ov, (250, y), (930, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


def rot_(p, deg):
    t = math.radians(deg)
    return (p[0] * math.cos(t) + p[1] * math.sin(t), -p[0] * math.sin(t) + p[1] * math.cos(t))


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "dial_centre_mm", "insert_flats_mm", "lug", "checks", "crown")}, default=float), "->", dest)
    print("strap half width", data["strap"]["half_width_by_s_mm"][::20], "logo parts", len(data["logo_mm"]))
