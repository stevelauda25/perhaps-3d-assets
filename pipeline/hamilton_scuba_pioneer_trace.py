"""Measure the Hamilton H82395331 (Khaki Navy Scuba, 40 mm) and H76255810 (Khaki Aviation Pilot Pioneer, 38 mm) front
photos into mm. numpy + OpenCV.

    python3 -B -m pipeline.hamilton_scuba_pioneer_trace <sku> [overlay.png]   # -> config/watches/hamilton-<sku>-trace.json

Both are straight front photos on white: a round case under a coin-edge rotating bezel with a printed insert, four lugs, a
crown at 3 and a strap that runs straight off the top and bottom of the photo. mm, x right, y toward 12, origin = hand pivot.
Anchor: the outer bezel silhouette at 9 o'clock = the listed case diameter; the gap between the lug inner edges (listed lug
width) is the check. Rings, crown, strap edges and hands are read from gridded crops and rotated hand strips (MANUAL_PX, about
+-0.1 mm). Traced from the photo: the lug outlines (steel mask per lug, offset out from the inner edge per depth below the tip,
mean of the four lugs) and, for the Scuba, the applied index shapes (lume mask in each hour's frame, mean per shape type).
Hands are in hand-local px: (w, d) = (across, along the hand from the pivot), w to the right of a hand pointing at 12.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

MANUAL_PX = {
    "h82395331": {
        "front": "references/hamilton-h82395331/front_1786x2751.jpg",
        "case_mm": 40.0, "lug_width_mm": 20.0,
        "pivot": [830, 1344],
        "photo_rot_deg": -0.96,  # the photo is turned 0.96 deg counter-clockwise (11 index centres, std 0.06 deg); values below are on the straightened photo
        # radii about the pivot (same within +-3 px all round): outer smooth skirt (anchor), tooth tips, notch bottoms, polished
        # ring outside the insert, black insert (outer chamfer from 675), polished crystal ring, flat dial (orange track to 556)
        "rings": {"skirt": 751, "tooth_tip": 747, "notch": 725, "rim_in": 700, "insert_out": 690, "insert_in": 566,
                  "crystal": 556, "dial": 556},
        "teeth": 90,
        "lug_stop_mm": -0.1, "lug_min_y_mm": 9.0,  # trace the case flank outside the bezel, stop above the crown guards
        "lug_inner_x": [460, 1205],  # left / right lug inner edges (middle of the shadow gap), same at the top and bottom
        "lug_tips_y": [444, 2266],  # inner lug corners, 12 / 6 o'clock (the photo's 6 o'clock half is 0.6 mm longer)
        "strap": {"top": {"x": [481, 1201]}, "bottom": {"x": [471, 1197]}},  # the rubber strap's own edges
        "strap_colour": "orange",
        "crown": {"centre_y": 1345, "radius": 122, "x_from_to": [1585, 1704], "teeth": 7},
        # crown guards: brushed case bulge at 3 o'clock, silhouette rows (the crown hides its edge between 1215 and 1460)
        "guard_rows": [1150, 1540], "guard_hidden": [1215, 1460, 1692],
        "hands": {
            # photo angles hour 305.0, minute 46.1, seconds 88.9 deg (+0.96 straightened); shapes from rotated strips
            "hour": {"angle": 305.96, "flat_tip": True,
                     "right": [[27, 35], [29, 60], [31, 100], [26, 150], [21, 200], [14, 250], [10.5, 300], [10.5, 311]],
                     "left": [[-28, 35], [-27, 60], [-24, 100], [-22, 150], [-19, 200], [-16, 250], [-12, 300], [-10.5, 311]],
                     "tail": [[-33, -32], [-18, -78], [20, -78], [35, -32]],
                     "lume_d": [56, 305], "tail_black": True},
            "minute": {"angle": 47.06, "flat_tip": True,
                       "right": [[27, 35], [26, 60], [30, 150], [27, 200], [22, 280], [15, 400], [8, 480], [7, 505]],
                       "left": [[-30, 35], [-27, 60], [-24, 150], [-22, 200], [-19, 300], [-16, 400], [-13, 480], [-12.5, 505]],
                       "tail": [[-30, -15], [-24, -52], [-11.5, -102], [11.5, -102], [24, -52], [30, -15]],
                       "lume_d": [56, 498], "tail_black": True},
            "seconds": {"angle": 89.86, "parts": [
                ["base", "black", [[-2.5, -40], [2.5, -40], [2.5, 280], [-2.5, 280]]],  # stick
                ["base", "black", [[-12, -40], [12, -40], [12, -180], [-12, -180]]],  # rectangular tail
                ["base", "colour", [[-25.5, 280], [25.5, 280], [12.5, 415], [3, 430], [-3, 430], [-12.5, 415]]],  # orange arrow
                ["base", "colour", [[-3, 415], [3, 415], [1.8, 532], [-1.8, 532]]],  # orange needle to the tip
                ["top", "lume", [[-14, 290], [14, 290], [9, 380], [-9, 380]]]]},
        },
        "hub": {"disc": 37, "pin": 9},
        "indices": {"band": [340, 590], "frame_px": 5, "types": {"cardinal": [12, 6, 9], "bar": [1, 2, 4, 5, 7, 8, 10, 11]},
                    "place": {"cardinal": [12, 3, 6, 9], "bar": [1, 2, 4, 5, 7, 8, 10, 11]}},
    },
    "h76255810": {
        "front": "references/hamilton-h76255810/front_1209x1982.jpg",
        "case_mm": 38.0, "lug_width_mm": 18.0,
        "pivot": [553, 967],
        "photo_rot_deg": -0.28,  # 12 lume plots of the railroad track (std 0.2 deg); values below are on the straightened photo
        # outer bezel silhouette (anchor), fine coin-edge teeth, polished ring outside the green insert, polished crystal ring
        "rings": {"skirt": 498, "tooth_tip": 497, "notch": 489, "rim_in": 472, "insert_out": 467, "insert_in": 411,
                  "crystal": 398, "dial": 396},
        "teeth": 120,
        "bg_min": 248,  # the bright brushed steel reaches 240-247
        "lug_stop_mm": -0.1, "lug_min_y_mm": 5.0,  # the case flank shows outside the bezel down to about 10 o'clock: keep tracing it
        "lug_inner_x": [314, 791],
        "lug_tips_y": [382, 1570],  # the photo's 6 o'clock half is 0.7 mm longer
        "strap": {"top": {"x": [318, 783]}, "bottom": {"x": [323, 787]}},
        "strap_colour": "green",
        # onion crown: neck at the bezel, cone out to the full radius, fluted barrel, rounded end (axial px from the pivot, radius px)
        "crown": {"centre_y": 968, "radius": 93, "x_from_to": [1045, 1150], "teeth": 16,
                  "profile": [[492, 48], [512, 70], [537, 93], [580, 93], [597, 70]]},
        "hands": {
            # leaf hour hand (black frame, lume stem and leaf, a spine up the leaf), baton minute hand with three lume panels,
            # black seconds needle with a lozenge counterweight; photo angles + 0.28 straightened, + the strip axis offsets
            "hour": {"angle": 304.5, "flat_tip": True,
                     "right": [[11, 20], [11, 95], [13.5, 105], [25, 122], [31, 150], [29, 170], [16, 194], [6, 206], [2, 214], [1.5, 260], [0.8, 278]],
                     "left": [[-11, 20], [-11, 95], [-13.5, 105], [-25, 122], [-31, 150], [-29, 170], [-16, 194], [-6, 206], [-2, 214], [-1.5, 260], [-0.8, 278]],
                     "tail": [[-11, -10], [11, -10]],
                     "lume_d": [54, 206], "lume_breaks": [[112, 124]], "spine": [124, 190, 2.0]},
            "minute": {"angle": 41.9, "flat_tip": True,
                       "right": [[11, 25], [11, 50], [17.5, 150], [19.5, 240], [12, 252], [1.6, 262], [1.2, 320], [0.8, 392]],
                       "left": [[-11, 25], [-11, 50], [-17.5, 150], [-19.5, 240], [-12, 252], [-1.6, 262], [-1.2, 320], [-0.8, 392]],
                       "tail": [[-11, -10], [11, -10]],
                       "lume_d": [40, 245], "lume_breaks": [[67, 77], [172, 180]]},
            "seconds": {"angle": 162.5, "parts": [
                ["base", "black", [[-1.8, -40], [1.8, -40], [1.0, 384], [-1.0, 384]]],  # needle
                ["base", "black", [[-2, -40], [-2, -75], [-5.5, -88], [-2, -108], [0, -116], [2, -108], [5.5, -88], [2, -75], [2, -40]]]]},
        },
        "hub": {"disc": 33, "pin": 6},
    },
}
ARTEFACTS = {
    "h82395331": ["dial print, the orange minute track, numerals, logo, date window and the insert numerals stay in the photo map",
                  "the seconds hand crosses the 3 o'clock index: that index uses the mean cardinal shape",
                  "lug tips are 24.0 mm (12) and 24.6 mm (6) from the pivot in the photo, the model uses the mean"],
    "h76255810": ["Arabic numerals, railroad minute track with lume plots, logo and the insert print stay in the photo map",
                  "lug tips are 22.3 mm (12) and 23.0 mm (6) from the pivot in the photo, the model uses the mean",
                  "strap keepers stay in the strap photo map"],
}


def masks(im, strap_colour, bg_min=232):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    white = (im.min(2) > bg_min).astype(np.uint8)
    _, lab = cv2.connectedComponents(white)  # background = white regions touching the left or right photo edge
    bg = np.isin(lab, np.setdiff1d(np.unique(np.r_[lab[:, 0], lab[:, -1]]), [0]))
    white = bg
    if strap_colour == "orange":
        strap = (hsv[..., 1] > 110) & (hsv[..., 2] > 100)
    else:  # dark green leather
        strap = (hsv[..., 0] > 35) & (hsv[..., 0] < 95) & (hsv[..., 1] > 40) & (hsv[..., 2] < 140)
    return white, strap


def trace(sku, overlay=None):
    M = MANUAL_PX[sku]
    im0 = cv2.imread(str(ROOT / M["front"]))
    px0, py0 = M["pivot"]
    Mr = cv2.getRotationMatrix2D((float(px0), float(py0)), M["photo_rot_deg"], 1.0)  # straighten (cv2: positive = ccw)
    im = cv2.warpAffine(im0, Mr, (im0.shape[1], im0.shape[0]), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
    S = M["rings"]["skirt"] / (M["case_mm"] / 2)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": M["front"], "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "outer bezel silhouette at 9 o'clock = %.1f mm (listing)" % M["case_mm"],
           "photo_rot_deg": M["photo_rot_deg"], "photo_rot_note": "photo px = pivot + rot(model mm, photo_rot_deg) * scale (rot: clockwise deg)"}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["rings"].items()}
    out["teeth"] = M["teeth"]
    white, strap = masks(im, M["strap_colour"], M.get("bg_min", 232))

    # ---- lugs: offset out from the inner edge per depth below the inner corner, mean of the four lugs ----
    xl, xr = M["lug_inner_x"]
    inner_x = ((px0 - xl) + (xr - px0)) / 2 / S
    tips = [(py0 - M["lug_tips_y"][0]) / S, (M["lug_tips_y"][1] - py0) / S]
    tip = sum(tips) / 2
    R_case = M["rings"]["tooth_tip"] / S
    depths = [round(0.35 * k, 2) for k in range(60)]
    rows = []
    for d in depths:
        offs = []
        for sx, x_in in ((-1, xl), (1, xr)):
            for sy, ty in ((1, M["lug_tips_y"][0]), (-1, M["lug_tips_y"][1])):
                y = int(round(ty + sy * d * S))  # down from the 12 o'clock tips, up from the 6 o'clock tips
                x, n = x_in, 0
                while 0 < x < im.shape[1] - 1 and n < 3:  # outward to the first 3 white px
                    x += sx
                    n = n + 1 if white[y, x] else 0
                offs.append(abs(x - x_in) / S - 3 / S)
        rows.append((d, offs))
    table = []
    for d, offs in rows:
        y_mm = tip - d
        o = float(np.mean(offs))
        if math.hypot(inner_x + o, y_mm) < M["rings"]["skirt"] / S + M.get("lug_stop_mm", 0.25) or y_mm < M.get("lug_min_y_mm", 0):
            break  # reached the bezel (the case outline takes over), or the crown rows
        table.append([d, round(o, 3), round(float(np.std(offs)), 3)])
    out["lug"] = {"inner_x_mm": round(inner_x, 3), "tip_y_mm": round(tip, 3), "tips_photo_mm": [round(t, 3) for t in tips],
                  "outer_offset_by_depth": [r[:2] for r in table], "spread_mm": max(r[2] for r in table)}
    out["checks"] = {"lug_width_mm": round(2 * inner_x, 3), "lug_to_lug_mm": round(sum(tips), 2),
                     "strap_width_mm": {k: round((v["x"][1] - v["x"][0]) / S, 3) for k, v in M["strap"].items()}}
    out["strap_mm"] = {k: {"x": [mm((x, 0))[0] for x in v["x"]], "tip_y": round(t, 3)}
                       for (k, v), t in zip(M["strap"].items(), tips)}

    # ---- crown and crown guards ----
    cr = M["crown"]
    out["crown"] = {"centre_y_mm": mm((0, cr["centre_y"]))[1], "radius_mm": round(cr["radius"] / S, 3), "teeth": cr["teeth"],
                    "r_from_to_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}
    if "profile" in cr:
        out["crown"]["profile_mm"] = [[round(a_ / S, 3), round(r_ / S, 3)] for a_, r_ in cr["profile"]]
    if "guard_rows" in M:
        y0, y1 = M["guard_rows"]
        h0, h1, hx = M["guard_hidden"]
        edge = []
        for y in range(y0, y1 + 1, 10):
            xs = np.nonzero(~white[y, px0:])[0]
            x = px0 + xs.max() if len(xs) else px0
            if h0 <= y <= h1:
                x = min(x, hx)
            edge.append(mm((x, y)))
        # closed outline: right edge top to bottom, then back inside the bezel
        inside = [mm((px0 + 0.9 * M["rings"]["notch"] * math.cos(a), py0 + 0.9 * M["rings"]["notch"] * math.sin(a)))
                  for a in np.linspace(math.asin((y1 - py0) / M["rings"]["notch"]), math.asin((y0 - py0) / M["rings"]["notch"]), 12)]
        out["crown_guard_mm"] = edge + inside

    # ---- hands: hand-local px -> model mm (rotated clockwise by the hand angle) ----
    def to_mm(w, d, ang):
        a = math.radians(ang)
        x, y = w * math.cos(a) + d * math.sin(a), -w * math.sin(a) + d * math.cos(a)
        return [round(x / S, 3), round(y / S, 3)]
    hands = {}
    for name, h in M["hands"].items():
        a = h["angle"]
        parts = [list(p) for p in h.get("parts", [])]
        if "right" in h:
            right, left = h["right"], h["left"]
            parts.append(["base", "metal", [left[-1]] + list(reversed(left[:-1])) + h["tail"] + right])
            inset = 4.0  # frame around the lume (px)
            wl = lambda side, d: float(np.interp(d, [p[1] for p in side], [p[0] for p in side]))
            lo, hi = h["lume_d"]
            cuts = [lo] + [v for br in h.get("lume_breaks", []) for v in br] + [hi]
            for d0, d1 in zip(cuts[::2], cuts[1::2]):
                ds_ = [d for d in np.linspace(d0, d1, 12) if wl(right, d) - wl(left, d) > 2 * inset + 1]
                if len(ds_) > 1:
                    parts.append(["top", "lume", [(wl(left, d) + inset, d) for d in reversed(ds_)] + [(wl(right, d) - inset, d) for d in ds_]])
            if h.get("tail_black"):
                parts.append(["top", "black", [(w * 0.82, d * 0.94 if d < -40 else d - 6) for w, d in h["tail"]]])
            if "spine" in h:
                d0, d1, hw_ = h["spine"]
                parts.append(["top", "metal", [(-hw_, d0), (hw_, d0), (hw_, d1), (-hw_, d1)]])
        L = max(p[1] for _, _, poly in parts for p in poly)
        hands[name] = {"angle_deg": a, "length_mm": round(L / S, 3),
                       "parts": [{"layer": ly, "mat": mt, "poly_mm": [to_mm(float(w), float(d), a) for w, d in poly]} for ly, mt, poly in parts]}
    out["hands"] = hands
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub"].items()}

    # ---- applied indices: lume mask in each hour's frame (rotated to 12), mean per shape type ----
    if "indices" in M:
        ix = M["indices"]
        r0, r1 = ix["band"]
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        lume = ((im.min(2) > 140) & (hsv[..., 1] < 70)).astype(np.float32)
        win = np.s_[py0 - r1:py0 - r0, px0 - 90:px0 + 91]
        shapes = {}
        for kind, hours in ix["types"].items():
            acc = np.zeros((r1 - r0, 181), np.float32)
            for hr in hours:
                Mr = cv2.getRotationMatrix2D((float(px0), float(py0)), 30.0 * hr, 1.0)
                acc += cv2.warpAffine(lume, Mr, (im.shape[1], im.shape[0]), flags=cv2.INTER_LINEAR)[win]
            acc = (acc + acc[:, ::-1]) / 2  # the indices are symmetric about their radius
            m = (acc / len(hours) > 0.5).astype(np.uint8)
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            pts = {}
            for key, grow in (("lume_mm", 0), ("frame_mm", ix["frame_px"])):  # polished frame = lume grown by the dark rim
                mk = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1,) * 2)) if grow else m
                cnt = max(cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
                poly = cv2.approxPolyDP(cnt, 1.0, True)[:, 0]
                pts[key] = [[round((x - 90) / S, 3), round((r1 - y) / S, 3)] for x, y in poly[::-1]]  # image y down -> ccw in mm
            shapes[kind] = dict(pts, hours=ix["place"][kind])
        out["indices"] = shapes

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS[sku]

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for k, r in M["rings"].items():
            cv2.circle(ov, (px0, py0), int(r), (255, 128, 0) if k != "skirt" else (0, 0, 255), 1)
        for sx in (1, -1):
            for sy in (1, -1):
                pts = [(sx * inner_x, sy * tip)] + [(sx * (inner_x + o), sy * (tip - d)) for d, o in out["lug"]["outer_offset_by_depth"]]
                cv2.polylines(ov, [np.array([P(p) for p in pts])], False, (0, 200, 255), 2)
        for h in hands.values():
            for part in h["parts"]:
                cv2.polylines(ov, [np.array([P(p) for p in part["poly_mm"]])], True, (0, 255, 0) if part["layer"] == "base" else (255, 0, 0), 1)
        for sh in out.get("indices", {}).values():
            for hr in sh["hours"]:
                a = math.radians(30 * hr)
                pts = [(x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)) for x, y in sh["lume_mm"]]
                cv2.polylines(ov, [np.array([P(p) for p in pts])], True, (255, 0, 255), 1)
        k = out["crown"]
        for x in k["r_from_to_mm"]:
            cv2.line(ov, P((x, k["centre_y_mm"] - k["radius_mm"])), P((x, k["centre_y_mm"] + k["radius_mm"])), (255, 0, 128), 2)
        if "crown_guard_mm" in out:
            cv2.polylines(ov, [np.array([P(p) for p in out["crown_guard_mm"]])], True, (0, 128, 255), 2)
        for kk, sy in (("top", 1), ("bottom", -1)):
            s = out["strap_mm"][kk]
            cv2.line(ov, P((s["x"][0], sy * s["tip_y"])), P((s["x"][1], sy * s["tip_y"])), (0, 255, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    sku = sys.argv[1]
    dest = ROOT / ("config/watches/hamilton-%s-trace.json" % sku)
    data = trace(sku, overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "checks", "crown")}, default=float), "->", dest)
    print("lug", {k: v for k, v in data["lug"].items() if k != "outer_offset_by_depth"}, len(data["lug"]["outer_offset_by_depth"]), "rows")
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()})
