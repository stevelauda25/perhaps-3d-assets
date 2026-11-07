"""Phase 1 for the Cartier Tank Must (rectangular case, brancard lugs, steel bracelet): silhouette mask from the JPEG, 2x working reference,
trace JSON, dial and steel photo maps. Model-specific copy of the Tudor prep (pipeline/tudor_prep.py), adapted for a photo WITHOUT alpha and a
rectangular case (no pivot-centred rings).

    python3 -B -m pipeline.cartier_tankmustxl_prep wsta0053
        reads    references/cartier-tank-must-xl-<sku>/cartier-<sku>_original.jpg and config/watches/cartier-tankmustxl-<sku>-measure.json (YOU measure the photo)
        writes   the 2x reference (PNG), config/watches/cartier-tankmustxl-<sku>-trace.json,
                 outputs/watches/cartier-tankmustxl-<sku>/{silhouette_mask.png,dial_photo.jpg,steel_photo.jpg} (+ .json crop boxes)

Mask from the JPEG (no alpha): flood fill from the image border over the near-white / light-grey background with a neighbour-to-neighbour tolerance of 4
grey levels (the background is a soft gradient with the drop shadow, the steel edge steps are 8+), then close 3x3, fill holes, keep the largest component,
median 3x3 (straightens the staircase the shadow gradient leaves) and a 0.7 px Gaussian for a soft alpha. The silhouette is the alpha above half.
Scale: the case width of the Catalog row (31 mm) on the silhouette between the brancard outer edges (mid rows); the lug-to-lug height (41 mm) is checked in the step.
mm, x right, y toward 12, origin = hand pivot; pixel coordinates are image indices (pixel centres at integers).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SKU = sys.argv[1].lower()
NAME = "cartier-tankmustxl-%s" % SKU
REF = ROOT / ("references/cartier-tank-must-xl-%s" % SKU)
SRC = REF / ("cartier-%s_original.jpg" % SKU)
UP = REF / ("cartier-%s_1500x1500.png" % SKU)
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
OUT = ROOT / ("outputs/watches/%s" % NAME)
STEEL, DIAL, MASK = OUT / "steel_photo.jpg", OUT / "dial_photo.jpg", OUT / "silhouette_mask.png"
PX = json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text())


def silhouette(im, tol=4):
    h, w = im.shape[:2]
    pad = cv2.copyMakeBorder(im, 1, 1, 1, 1, cv2.BORDER_REPLICATE)
    m = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(pad.copy(), m, (0, 0), (0, 0, 0), (tol,) * 3, (tol,) * 3, cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    fg = (m[2:h + 2, 2:w + 2] == 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    fg = np.zeros_like(fg)
    cv2.drawContours(fg, [max(cnts, key=cv2.contourArea)], -1, 1, -1)  # largest component, holes filled
    fg = cv2.medianBlur(fg * 255, 3)
    alpha = cv2.GaussianBlur(fg, (0, 0), 0.7)
    return alpha


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_COLOR)
    px0, py0 = PX["pivot"]
    if not UP.exists():
        cv2.imwrite(str(UP), cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4))
    OUT.mkdir(parents=True, exist_ok=True)
    alpha = silhouette(im)
    cv2.imwrite(str(MASK), alpha)
    fg = alpha > 127

    rows_all = np.nonzero(fg.sum(axis=1) > 100)[0]  # rows that hold the bracelet (the crown alone is narrower)
    left = lambda r: np.nonzero(fg[r])[0].min() - 0.5
    right = lambda r: np.nonzero(fg[r])[0].max() + 0.5
    mid = range(260, 340)  # rows between the case shoulders and the crown: brancard outer edges
    xl, xr = float(np.median([left(r) for r in mid])), float(np.median([right(r) for r in mid]))
    S = (xr - xl) / PX["anchor"]["width_mm"]
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    dmm = lambda y: round(abs(py0 - y) / S, 3)  # distance of an image row from the pivot row
    br_rows = [r for r in rows_all if left(r) < PX["brancard"]["inner_left_x"] - 2 and r < 440]  # brancard top rows (rounded corner, outer edge left of the inner edge)
    br_rows_b = [r for r in rows_all if left(r) < PX["brancard"]["inner_left_x"] - 2 and r > 440 and r < 560]
    top_y = br_rows[0] - 0.5
    bot_y = None
    for r in range(600, 440, -1):  # last row below the pivot whose left edge is still left of the brancard (two probes 6 px apart reject shadow noise)
        if left(r) < PX["brancard"]["inner_left_x"] - 2 and left(r - 6) < PX["brancard"]["inner_left_x"] - 2:
            bot_y = r + 0.5
            break
    bot_y = bot_y if bot_y is not None else br_rows_b[-1] + 0.5

    rows = rows_all
    y_hi = math.floor((py0 - (rows[0] + 1)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 1) - py0) / S * 4) / 4
    c = PX["crown"]
    crown_rows = (c["y0"] - 1, c["y1"] + 1)
    prof = []  # alpha silhouette per 0.25 mm row; the crown rows keep the case's right edge (the crown is its own part)
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        r = int(round(py0 - y * S))
        rr = xr if crown_rows[0] <= r <= crown_rows[1] else right(r)
        prof.append([round(float(y), 2), round((left(r) - px0) / S, 3), round((rr - px0) / S, 3)])

    def polar(p):
        return (round(math.hypot(p[0] - px0, p[1] - py0) / S, 3), round(math.degrees(math.atan2(p[0] - px0, py0 - p[1])) % 360, 2))
    hands = {}
    for k in ("hour", "minute", "seconds"):
        L, a = polar(PX[k + "_tip"])
        hands[k] = {"length_mm": L, "angle_deg": a, "tail_mm": polar(PX[k + "_tail"])[0], "tail_angle_deg": polar(PX[k + "_tail"])[1]}

    def pieces(lst, side):  # [[y_px, y_px], ...] -> [[d0, d1], ...] distances from the pivot, ordered outward; the far end of the last piece = silhouette end
        end = (rows[0] - 0.5) if side == "top" else (rows[-1] + 0.5)
        out = sorted([sorted([dmm(a), dmm(b)]) for a, b in lst])
        out[-1][1] = dmm(end)
        return out

    def centre_x(lst):  # [[y_px, left_px, right_px]] -> [[|y| mm, left mm, right mm]] ordered outward
        return sorted([[dmm(y), round((l - px0) / S, 3), round((r_ - px0) / S, 3)] for y, l, r_ in lst])
    bz = PX["bars"]
    dr = PX["dial_rect"]
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "case width %s mm = silhouette %.1f px between the brancard outer edges (rows 260..340)" % (PX["anchor"]["width_mm"], xr - xl),
           "mask": "flood fill from the border (neighbour tolerance 4) + close, fill, largest component, median 3, gaussian 0.7; silhouette = alpha > 127",
           "case": {"left_mm": round((xl - px0) / S, 3), "right_mm": round((xr - px0) / S, 3), "top_mm": round(-(top_y - py0) / S, 3), "bottom_mm": round(-(bot_y - py0) / S, 3),
                    "lug_to_lug_mm": round((bot_y - top_y) / S, 3),
                    "brancard_inner_x_mm": [round((PX["brancard"]["inner_left_x"] - px0) / S, 3), round((PX["brancard"]["inner_right_x"] - px0) / S, 3)],
                    "bar_top_y_mm": [round(-(bz["top"][0] - py0) / S, 3), round(-(bz["top"][1] - py0) / S, 3)],
                    "bar_bottom_y_mm": [round(-(bz["bottom"][0] - py0) / S, 3), round(-(bz["bottom"][1] - py0) / S, 3)],
                    "dial_rect_mm": mm((dr[0], dr[1])) + mm((dr[2], dr[3]))},
           "silhouette_y_left_right_mm": prof,
           "bracelet": {"pieces_mm": {k: {s: pieces(PX["pieces_px"][k][s], s) for s in ("top", "bottom")} for k in ("outer", "centre")},
                        "centre_x_mm": {s: centre_x(PX["centre_x_px"][s]) for s in ("top", "bottom")},
                        "ends_y_mm": [round(-(rows[0] - 0.5 - py0) / S, 3), round(-(rows[-1] + 0.5 - py0) / S, 3)],
                        "note": "pieces_mm = [y0, y1] distances from the pivot per column kind and side; centre_x_mm = [|y|, left x, right x] of the joint lines between the columns"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "steel_x1_mm": round((c["steel_x1"] - px0) / S, 3),
                     "widest_x_mm": round((c["widest_x"] - px0) / S, 3), "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3),
                     "cabochon_x_mm": [round((c["cabochon"]["x0"] - px0) / S, 3), round((c["cabochon"]["x1"] - px0) / S, 3)],
                     "cabochon_radius_mm": round((c["cabochon"]["y1"] - c["cabochon"]["y0"]) / 2 / S, 3),
                     "cabochon_centre_y_mm": round(-((c["cabochon"]["y0"] + c["cabochon"]["y1"]) / 2 - py0) / S, 3)}}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: 2x crop of the dial opening plus a 3 px margin (the printed dial, railroad track, numerals and the photographed hands stay in it)
    X0, Y0, X1, Y1 = int(dr[0]) - 3, int(dr[1]) - 3, int(dr[2]) + 4, int(dr[3]) + 4
    crop = cv2.resize(im[Y0:Y1, X0:X1], None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    DIAL.with_suffix(".json").write_text(json.dumps({"source": out["source"], "crop_px": [X0, Y0, X1, Y1], "size_px": [crop.shape[1], crop.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    # steel map: the whole watch (2x, composited on grey with the soft alpha), projected on the case, bars, crown, bracelet and hands from the front
    cols = np.nonzero(fg.any(axis=0))[0]
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows_all[0]) - 4, int(cols[-1]) + 5, int(rows_all[-1]) + 5
    a = alpha[Y0:Y1, X0:X1, None] / 255.0
    flat = (im[Y0:Y1, X0:X1] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {"scale_px_per_mm": out["scale_px_per_mm"], "case": out["case"], "hands": hands, "crown": out["crown"], "ends_y_mm": out["bracelet"]["ends_y_mm"],
            "pieces": out["bracelet"]["pieces_mm"]}


if __name__ == "__main__":
    print(json.dumps(build()))
