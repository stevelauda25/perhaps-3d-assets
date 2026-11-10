"""Measure the Hamilton H32515135 (Jazzmaster Viewmatic Auto 40 mm, bracelet) and H64455523 (Khaki Field King Auto 40 mm,
leather strap) official front renders into mm. numpy + OpenCV.

    python3 -B -m pipeline.hamilton_jazz_king_trace <sku> [overlay.png]   # -> config/watches/hamilton-<sku>-trace.json

Both references are Hamilton's 2000 x 2000 PNG renders with a transparent background (straight front, not turned). mm, x right,
y toward 12, origin = hand pivot. Anchor: the case silhouette on the pivot row at 9 o'clock = 20 mm (40 mm listing); the gap
between the lug inner edges (20 mm listed) is the check. Traced from the alpha channel: the whole head outline (case, lugs and
the crown-side flank or crown guards) per row, the crown rows capped at the flank behind the crown. Rings, crown, strap and
bracelet columns, and the hands are read from gridded crops and rotated hand strips (MANUAL_PX). Hand parts are polygons in
hand-local px (w across, d along the hand from the pivot; w right of a hand pointing at 12), [layer, material role, polygon].
Jazzmaster only: the applied kite indices (bright mask turned to 12, mean of the eight bar hours) and the applied numerals
12, 9 and 6 (bright mask in a box, with their holes) are traced as outlines.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

MANUAL_PX = {
    "h32515135": {
        "front": "references/hamilton-h32515135/front_official_2000x2000.png",
        "pivot": [998, 965],
        "photo_rot_deg": -1.3,  # the dial print is turned 1.3 deg counter-clockwise in the render (minute track tick phase; case and bracelet are straight)
        "case_left_px": 466, "case_mm": 40.0, "lug_width_mm": 20.0,
        # radii about the pivot (9 o'clock row, checked at 12 and 6): case flank edge, polished bezel (outer line, step, inner
        # edge), black rehaut ring, dial edge
        "rings": {"case": 466, "bezel_out": 451, "bezel_step": 425, "bezel_in": 408, "dial": 398},
        "lug_inner_x": [770, 1242],  # bracelet edges between the lugs (the bracelet sits 10 px right of the pivot: mean used)
        "crown": {"y_top_bottom": [893, 1043], "x_from_to": [1500, 1556], "teeth": 14},
        "crown_rows_cap": [885, 1050, 1502],  # rows hidden by the crown -> outline capped at the flank behind it
        # bracelet: column edges (|x| px from the bracelet centre), joint rows (px from the pivot along the bracelet, top side)
        "bracelet": {"centre_x": 1008, "edges": [49.5, 148.5, 236], "joints_outer": [567, 728, 895], "joints_mid": [507, 646, 825]},
        "hands": {
            "hour": {"angle": 302.5, "parts": [
                ["base", "metal", [[1, 222], [5, 200], [9, 150], [12, 100], [13, 40], [12, 20], [9, -5], [6, -30], [-6, -30], [-9, -5],
                                   [-12, 20], [-13, 40], [-12, 100], [-9, 150], [-5, 200], [-1, 222]]],
                ["top", "lume", [[0, 28], [6, 45], [6, 110], [3, 145], [0, 152], [-3, 145], [-6, 110], [-6, 45]]]]},
            "minute": {"angle": 48.3, "parts": [
                ["base", "metal", [[1, 365], [4, 330], [8, 250], [11, 150], [13, 50], [12, 20], [9, -5], [6, -45], [-6, -45], [-9, -5],
                                   [-12, 20], [-13, 50], [-11, 150], [-8, 250], [-4, 330], [-1, 365]]],
                ["top", "lume", [[0, 40], [5, 60], [5, 250], [2, 300], [0, 310], [-2, 300], [-5, 250], [-5, 60]]]]},
            "seconds": {"angle": 220.3, "parts": [
                ["base", "metal", [[-2.5, -112], [2.5, -112], [1.5, 410], [-1.5, 410]]],
                ["base", "metal", [[-5, -60], [5, -60], [5, -112], [-5, -112]]]]},
        },
        "hub": {"disc": 22, "pin": 6},
        "indices": {"band": [235, 360], "hours": [1, 2, 4, 5, 7, 8, 10, 11], "grow_px": 1},
        "applied_min": 95,  # applied steel: the shaded facets reach down to about 100 (black dial 0-50)
        # applied numerals: box [x0, y0, x1, y1] px
        "numerals": {"12": [930, 652, 1065, 728], "9": [678, 925, 768, 1012], "6": [968, 1210, 1040, 1292]},
    },
    "h64455523": {
        "front": "references/hamilton-h64455523/front_official_2000x2000.png",
        "pivot": [998, 986],
        "case_left_px": 536, "case_mm": 40.0, "lug_width_mm": 20.0,
        # case flank edge, the wide polished bezel (outer line, inner edge), black rehaut ring, dial edge
        "rings": {"case": 536, "bezel_out": 521, "bezel_step": 486, "bezel_in": 452, "dial": 442},
        "lug_inner_x": [733, 1270],
        "strap": {"top": {"x": [738, 1266]}, "bottom": {"x": [733, 1265]}},
        "crown": {"y_top_bottom": [925, 1075], "x_from_to": [1540, 1636], "teeth": 12},
        "crown_rows_cap": [918, 1088, 1542],
        "hands": {
            "hour": {"angle": 303.37, "parts": [
                ["base", "metal", [[1, 265], [1.5, 202], [3, 198], [17, 170], [13, 110], [9, 50], [5, 45], [5, 15], [-5, 15], [-5, 45], [-9, 50],
                                   [-13, 110], [-17, 170], [-3, 198], [-1.5, 202], [-1, 265]]],
                ["top", "lume", [[2, 193], [14, 168], [10, 110], [6, 55], [-6, 55], [-10, 110], [-14, 168], [-2, 193]]]]},
            "minute": {"angle": 50.29, "parts": [
                ["base", "metal", [[1, 378], [1.5, 302], [3, 297], [17, 250], [14, 190], [11, 120], [8, 50], [4, 45], [4, 15], [-4, 15], [-4, 45],
                                   [-8, 50], [-11, 120], [-14, 190], [-17, 250], [-3, 297], [-1.5, 302], [-1, 378]]],
                ["top", "lume", [[2, 293], [14, 248], [12, 190], [9, 120], [5, 54], [-5, 54], [-9, 120], [-12, 190], [-14, 248], [-2, 293]]]]},
            "seconds": {"angle": 222.62, "parts": [
                ["base", "metal", [[-2, -105], [2, -105], [1.2, 340], [-1.2, 340]]],
                ["base", "metal", [[-10, 335], [10, 335], [0, 378]]]]},
        },
        "hub": {"disc": 30, "pin": 7},
    },
}
ARTEFACTS = {
    "h32515135": ["the waffle pattern, minute track, logo, 'viewmatic' and the date window stay in the photo map",
                  "the render's bracelet sits 0.4 mm right of the hand pivot: the model bracelet is centred on the pivot",
                  "the bottom bracelet joints are lit differently in the render: the top side's joint rows are mirrored"],
    "h64455523": ["printed numerals, 24-hour ring, minute track, day and date windows and the logo stay in the photo map",
                  "the render's bezel lines sit about 0.3 mm lower than the pivot (slight camera tilt); the model is round about the pivot",
                  "the strap keepers and buckle are outside the render's crop"],
}


def load(path):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    a = im[..., 3:4] / 255.0
    return (im[..., :3] * a + 255 * (1 - a)).astype(np.uint8), im[..., 3]


def trace(sku, overlay=None):
    M = MANUAL_PX[sku]
    im, alpha = load(ROOT / M["front"])
    px0, py0 = M["pivot"]
    S = M["case_left_px"] / (M["case_mm"] / 2)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    pr = M.get("photo_rot_deg", 0.0)
    rot = lambda q, deg: [round(q[0] * math.cos(math.radians(deg)) + q[1] * math.sin(math.radians(deg)), 3),
                          round(-q[0] * math.sin(math.radians(deg)) + q[1] * math.cos(math.radians(deg)), 3)]
    dial = lambda q: rot(q, -pr)  # photo mm -> model mm for the dial parts (print, hands, applied indices and numerals)
    out = {"source": M["front"], "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0], "photo_rot_deg": pr,
           "photo_rot_note": "photo px = pivot + rot(model mm, photo_rot_deg) * scale (rot: clockwise deg); applies to the dial maps only",
           "anchor": "case silhouette at 9 o'clock on the pivot row = %.1f mm (listing)" % (M["case_mm"] / 2)}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["rings"].items()}

    # ---- head outline from the alpha channel: per row, the outermost head px beyond the strap / bracelet columns ----
    xl, xr = M["lug_inner_x"]
    xi = ((px0 - xl) + (xr - px0)) / 2 / S
    head = alpha > 128
    rows = []
    for y in range(0, alpha.shape[0]):
        xs = np.nonzero(head[y])[0]
        if not len(xs) or xs.min() > xl - 6 or xs.max() < xr + 6:  # only the strap or bracelet: past the lug tips
            continue
        rows.append((y, int(xs.min()), int(xs.max())))
    y_top, y_bot = rows[0][0], rows[-1][0]
    c0, c1, cx = M["crown_rows_cap"]
    left, right = [], []
    for y, a, b in rows[::4] + [rows[-1]]:
        if c0 <= y <= c1:
            b = min(b, cx)
        left.append(mm((a, y)))
        right.append(mm((b, y)))
    out["outline_mm"] = {"left": left, "right": right, "lug_inner_x_mm": round(xi, 3),
                         "tips_mm": [round((py0 - y_top) / S, 3), round((y_bot - py0) / S, 3)]}
    tip = (out["outline_mm"]["tips_mm"][0] + out["outline_mm"]["tips_mm"][1]) / 2
    # symmetric half outline for the model: |x| of each side per |y| (0.25 mm), mean of the 12 and 6 o'clock halves where both
    # exist; the halves are scaled to the mean tip first (the render's 6 o'clock half is a little longer)
    by_row = {y: (a, b) for y, a, b in rows}
    half = {"left": [], "right": []}
    tips_px = (py0 - y_top, y_bot - py0)
    for k in range(int(tip / 0.25) + 1):
        f = k * 0.25 / tip
        vals = {"left": [], "right": []}
        for sy, tp in ((-1, tips_px[0]), (1, tips_px[1])):
            y = int(round(py0 + sy * f * tp))
            if y in by_row:
                a, b = by_row[y]
                if c0 <= y <= c1:
                    b = min(b, cx)
                vals["left"].append((px0 - a) / S)
                vals["right"].append((b - px0) / S)
        for side in half:
            if vals[side]:
                half[side].append([round(k * 0.25, 3), round(float(np.mean(vals[side])), 3)])
    out["half_outline_mm"] = half
    out["lug"] = {"tip_y_mm": round(tip, 3), "inner_x_mm": round(xi, 3)}
    out["checks"] = {"lug_width_mm": round(2 * xi, 3), "lug_to_lug_mm": round(sum(out["outline_mm"]["tips_mm"]), 2),
                     "case_right_at_pivot_mm": mm((max(b for y, a, b in rows if abs(y - py0) < 3), py0))[0]}

    if "strap" in M:
        out["strap_mm"] = {k: {"x": [mm((x, 0))[0] for x in v["x"]], "tip_y": t}
                           for (k, v), t in zip(M["strap"].items(), out["outline_mm"]["tips_mm"])}
        out["checks"]["strap_width_mm"] = {k: round(v["x"][1] - v["x"][0], 3) for k, v in out["strap_mm"].items()}
    if "bracelet" in M:
        b = M["bracelet"]
        out["bracelet_mm"] = {"edges": [round(e / S, 3) for e in b["edges"]], "offset_x": round((b["centre_x"] - px0) / S, 3),
                              "joints_outer": [round(j / S, 3) for j in b["joints_outer"]],
                              "joints_mid": [round(j / S, 3) for j in b["joints_mid"]]}
        out["checks"]["bracelet_width_mm"] = round(2 * b["edges"][-1] / S, 3)

    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"centre_y_mm": mm((0, (yt + yb) / 2))[1], "radius_mm": round((yb - yt) / 2 / S, 3), "teeth": cr["teeth"],
                    "r_from_to_mm": [round((x - px0) / S, 3) for x in cr["x_from_to"]]}

    def to_mm(w, d, ang):
        a = math.radians(ang)
        return [round((w * math.cos(a) + d * math.sin(a)) / S, 3), round((-w * math.sin(a) + d * math.cos(a)) / S, 3)]
    hands = {}
    for name, h in M["hands"].items():
        L = max(p[1] for _, _, poly in h["parts"] for p in poly)
        hands[name] = {"angle_deg": h["angle"], "length_mm": round(L / S, 3),
                       "parts": [{"layer": ly, "mat": mt, "poly_mm": [dial(to_mm(w, d, h["angle"])) for w, d in poly]} for ly, mt, poly in h["parts"]]}
    out["hands"] = hands
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub"].items()}

    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    bright = ((im.min(2) > M.get("applied_min", 150)) & (hsv[..., 1] < 50)).astype(np.uint8)
    if "indices" in M:  # mean of the bar hours turned to 12: the dial pattern averages out, the index stays
        ix = M["indices"]
        r0, r1 = ix["band"]
        win = np.s_[py0 - r1:py0 - r0, px0 - 60:px0 + 61]
        acc = np.zeros((r1 - r0, 121), np.float32)
        for hr in ix["hours"]:
            Mr = cv2.getRotationMatrix2D((float(px0), float(py0)), 30.0 * hr + pr, 1.0)
            acc += cv2.warpAffine(bright.astype(np.float32), Mr, (im.shape[1], im.shape[0]), flags=cv2.INTER_LINEAR)[win]
        acc = (acc + acc[:, ::-1]) / 2 / len(ix["hours"])
        m = cv2.morphologyEx((acc > 0.5).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        m = cv2.dilate(m, np.ones((2 * ix["grow_px"] + 1,) * 2, np.uint8))
        cnt = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
        poly = cv2.approxPolyDP(cnt, 0.8, True)[:, 0]
        out["indices"] = {"bar": {"outline_mm": [[round((x - 60) / S, 3), round((r1 - y) / S, 3)] for x, y in poly[::-1]], "hours": ix["hours"]}}
    if "numerals" in M:  # applied numerals: outline and holes per glyph
        nums = {}
        for key, (x0, y0, x1, y1) in M["numerals"].items():
            m = cv2.morphologyEx(bright[y0:y1, x0:x1], cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
            shapes = []
            for i, cnt in enumerate(cnts):
                if hier[0][i][3] != -1 or cv2.contourArea(cnt) < 60:
                    continue
                holes = []
                j = hier[0][i][2]
                while j != -1:
                    if cv2.contourArea(cnts[j]) > 15:
                        holes.append([dial(mm((x + x0, y + y0))) for x, y in cv2.approxPolyDP(cnts[j], 0.7, True)[:, 0]])
                    j = hier[0][j][0]
                shapes.append({"outer": [dial(mm((x + x0, y + y0))) for x, y in cv2.approxPolyDP(cnt, 0.7, True)[:, 0]], "holes": holes})
            nums[key] = shapes
        out["numerals_mm"] = nums
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS[sku]

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        P0 = lambda q: (int(round(px0 + q[0] * S)), int(round(py0 - q[1] * S)))
        P = lambda q: P0(rot(q, pr))  # model mm -> photo px (identity off the dial when pr = 0)
        for k, r in M["rings"].items():
            cv2.circle(ov, (px0, py0), int(r), (255, 128, 0), 1)
        for side in ("left", "right"):
            cv2.polylines(ov, [np.array([P0(q) for q in out["outline_mm"][side]])], False, (0, 0, 255), 2)
        for h in hands.values():
            for part in h["parts"]:
                cv2.polylines(ov, [np.array([P(q) for q in part["poly_mm"]])], True, (0, 255, 0) if part["layer"] == "base" else (255, 0, 0), 1)
        for sh in out.get("indices", {}).values():
            for hr in sh["hours"]:
                a = math.radians(30 * hr)
                cv2.polylines(ov, [np.array([P((x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))) for x, y in sh["outline_mm"]])],
                              True, (255, 0, 255), 1)
        for shapes in out.get("numerals_mm", {}).values():
            for s in shapes:
                for lp in [s["outer"]] + s["holes"]:
                    cv2.polylines(ov, [np.array([P(q) for q in lp])], True, (255, 0, 255), 1)
        k = out["crown"]
        for x in k["r_from_to_mm"]:
            cv2.line(ov, P0((x, k["centre_y_mm"] - k["radius_mm"])), P0((x, k["centre_y_mm"] + k["radius_mm"])), (255, 0, 128), 2)
        for sx in (1, -1):
            cv2.line(ov, P0((sx * xi, tip)), P0((sx * xi, -tip)), (0, 200, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    sku = sys.argv[1]
    dest = ROOT / ("config/watches/hamilton-%s-trace.json" % sku)
    data = trace(sku, overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "checks", "crown", "lug")}, default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, "numerals", {k: len(v) for k, v in data.get("numerals_mm", {}).items()})
