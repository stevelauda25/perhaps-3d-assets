"""Phase 1 for the Cartier Santos de Cartier Large (square case with a screwed bezel, integrated steel bracelet): silhouette mask from the JPEG, 2x working
reference, trace JSON, dial and steel photo maps. Model-specific copy of pipeline/cartier_tankmustxl_prep.py (photo WITHOUT alpha, no pivot-centred rings).

    python3 -B -m pipeline.cartier_santoslarge_prep wssa0018
        reads    references/cartier-santos-large-<sku>/cartier-<sku>_original.jpg and config/watches/cartier-santoslarge-<sku>-measure.json (YOU measure the photo)
        writes   the 2x reference (PNG), config/watches/cartier-santoslarge-<sku>-trace.json,
                 outputs/watches/cartier-santoslarge-<sku>/{silhouette_mask.png,dial_photo.jpg,steel_photo.jpg} (+ .json crop boxes)

Mask from the JPEG (no alpha): flood fill from the image border over the light background with a neighbour-to-neighbour tolerance (measure.mask_tol, 6 grey
levels; the background is a soft gradient with a drop shadow, the steel edge steps are 8+), then close 3x3, fill holes, keep the largest component, median 3x3
and a 0.7 px Gaussian for a soft alpha. The silhouette is the alpha above half.
Scale: the case width of the Catalog row (39.8 mm) on the silhouette between the case flanks (rows measure.width_rows); the horn-to-horn height is only recorded.
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
NAME = "cartier-santoslarge-%s" % SKU
REF = ROOT / ("references/cartier-santos-large-%s" % SKU)
SRC = REF / ("cartier-%s_original.jpg" % SKU)
UP = REF / ("cartier-%s_1500x1500.png" % SKU)
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
OUT = ROOT / ("outputs/watches/%s" % NAME)
STEEL, DIAL, MASK = OUT / "steel_photo.jpg", OUT / "dial_photo.jpg", OUT / "silhouette_mask.png"
PX = json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text())


def silhouette(im, tol):
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
    return cv2.GaussianBlur(fg, (0, 0), 0.7)


def rounded_rect(x0, y0, x1, y1, r, n=8):
    """Closed polygon (px) of a rounded rectangle, clockwise on screen (image y down), starting at the top-left corner."""
    pts = []
    for cx, cy, a0 in ((x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_COLOR)
    px0, py0 = PX["pivot"]
    if not UP.exists():
        cv2.imwrite(str(UP), cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4))
    OUT.mkdir(parents=True, exist_ok=True)
    alpha = silhouette(im, PX["mask_tol"])
    cv2.imwrite(str(MASK), alpha)
    fg = alpha > 127

    rows = np.nonzero(fg.sum(axis=1) > 100)[0]  # rows that hold the bracelet
    left = lambda r: np.nonzero(fg[r])[0].min() - 0.5
    right = lambda r: np.nonzero(fg[r])[0].max() + 0.5
    r0, r1 = PX["width_rows"]
    xl, xr = float(np.median([left(r) for r in range(r0, r1)])), float(np.median([right(r) for r in range(r0, r1)]))
    S = (xr - xl) / PX["anchor"]["width_mm"]
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    dmm = lambda y: round(abs(py0 - y) / S, 3)  # distance of an image row from the pivot row
    hz = PX["horn"]
    y_hi = math.floor((py0 - (rows[0] + 1)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 1) - py0) / S * 4) / 4
    gx = PX["guard_x"]
    cr0, cr1 = PX["crown_rows"]
    prof = []  # alpha silhouette per 0.25 mm row; the crown rows keep the guard line (the crown is its own part)
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        r = int(round(py0 - y * S))
        rr = min(right(r), gx) if cr0 <= r <= cr1 else right(r)
        prof.append([round(float(y), 2), round((left(r) - px0) / S, 3), round((rr - px0) / S, 3)])

    for col in (1, 2):  # two light passes of a 1-2-1 smoothing along each edge (the mask's one-pixel staircase), never across a step (horn ends, guard line: more than 0.8 mm)
        for _ in range(2):
            v = [p[col] for p in prof]
            for i in range(1, len(v) - 1):
                if abs(v[i] - v[i - 1]) < 0.8 and abs(v[i] - v[i + 1]) < 0.8:
                    prof[i][col] = round((v[i - 1] + 2 * v[i] + v[i + 1]) / 4, 3)

    def polar(p):
        return (round(math.hypot(p[0] - px0, p[1] - py0) / S, 3), round(math.degrees(math.atan2(p[0] - px0, py0 - p[1])) % 360, 2))
    hands = {}
    for k in ("hour", "minute", "seconds"):
        L, a = polar(PX[k + "_tip"])
        hands[k] = {"length_mm": L, "angle_deg": a}
    hands["seconds"]["tail_mm"], hands["seconds"]["tail_angle_deg"] = polar(PX["seconds_tail"])

    def pieces(bounds, side):  # joint rows outward from the case -> [[d0, d1], ...] distances from the pivot; the far end of the last piece = silhouette end
        end = (rows[0] - 0.5) if side == "top" else (rows[-1] + 0.5)
        ds = [dmm(y) for y in bounds] + [dmm(end)]
        return [[ds[i], ds[i + 1]] for i in range(len(ds) - 1)]

    b = PX["bezel"]
    tl = [tuple(p) for p in b["tl"]]
    cx, cy = b["cx"], b["cy"]
    quad = lambda f: [f(p) for p in tl]
    # full outline, top centre -> left -> bottom -> right -> back (the quarters are mirrored about cx / cy; junction points are not repeated)
    bl, br, trq = quad(lambda p: (p[0], 2 * cy - p[1]))[::-1], quad(lambda p: (2 * cx - p[0], 2 * cy - p[1])), quad(lambda p: (2 * cx - p[0], p[1]))[::-1]
    outline = quad(lambda p: p) + bl[1:] + br[1:] + trq[1:-1]
    o, d = PX["opening"], PX["dial_rect"]
    c = PX["crown"]
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "case width %s mm = silhouette %.1f px between the case flanks (rows %d..%d)" % (PX["anchor"]["width_mm"], xr - xl, r0, r1),
           "mask": "flood fill from the border (neighbour tolerance %d) + close, fill, largest component, median 3, gaussian 0.7; silhouette = alpha > 127" % PX["mask_tol"],
           "case": {"left_mm": round((xl - px0) / S, 3), "right_mm": round((xr - px0) / S, 3), "top_mm": round(-(hz["top_y"] - py0) / S, 3), "bottom_mm": round(-(hz["bottom_y"] - py0) / S, 3),
                    "lug_to_lug_mm": round((hz["bottom_y"] - hz["top_y"]) / S, 3), "listed_lug_to_lug_mm": PX["anchor"]["listed_lug_to_lug_mm"],
                    "bezel_outline_mm": [mm(p) for p in outline],
                    "opening_mm": {"outline": [mm(p) for p in rounded_rect(o["x0"], o["y0"], o["x1"], o["y1"], o["r"])]},
                    "dial_rect_mm": mm((d["x0"], d["y0"])) + mm((d["x1"], d["y1"])),
                    "dial_outline_mm": [mm(p) for p in rounded_rect(d["x0"], d["y0"], d["x1"], d["y1"], d["r"])],
                    "screws_mm": [mm(p) for p in PX["screws"]], "screw_radius_mm": round(PX["screw_r"] / S, 3)},
           "silhouette_y_left_right_mm": prof,
           "end_link_x_mm": {k: [round((v[0] - px0) / S, 3), round((v[1] - px0) / S, 3)] for k, v in PX["end_link_x"].items()},
           "bracelet": {"pieces_mm": {s: pieces(PX["pieces_px"][s], s) for s in ("top", "bottom")},
                        "ends_y_mm": [round(-(rows[0] - 0.5 - py0) / S, 3), round(-(rows[-1] + 0.5 - py0) / S, 3)],
                        "note": "pieces_mm = [y0, y1] distances from the pivot per side, ordered outward from the case (the first piece is the end link between the horns)"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "crown": {"centre_y_mm": round(-(c["centre_y"] - py0) / S, 3), "x_mm": [round((c["profile_px"][0][1] - px0) / S, 3), round((c["profile_px"][-1][1] - px0) / S, 3)],
                     "profile_mm": [[round(r_ / S, 3), round((x_ - px0) / S, 3)] for r_, x_ in c["profile_px"]]}}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: 2x crop of the dial surface plus a 3 px margin (printed dial, minute track, numerals, date window and the photographed hands stay in it)
    X0, Y0, X1, Y1 = int(d["x0"]) - 3, int(d["y0"]) - 3, int(d["x1"]) + 4, int(d["y1"]) + 4
    crop = cv2.resize(im[Y0:Y1, X0:X1], None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    DIAL.with_suffix(".json").write_text(json.dumps({"source": out["source"], "crop_px": [X0, Y0, X1, Y1], "size_px": [crop.shape[1], crop.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    # steel map: the whole watch (2x, composited on grey with the soft alpha), projected on the case, bezel, crown, bracelet and hands from the front
    cols = np.nonzero(fg.any(axis=0))[0]
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    a = alpha[Y0:Y1, X0:X1, None] / 255.0
    flat = (im[Y0:Y1, X0:X1] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {"scale_px_per_mm": out["scale_px_per_mm"], "case": {k: v for k, v in out["case"].items() if k.endswith("_mm") and not isinstance(v, (list, dict))},
            "hands": hands, "crown_x_mm": out["crown"]["x_mm"], "ends_y_mm": out["bracelet"]["ends_y_mm"], "pieces": out["bracelet"]["pieces_mm"]}


if __name__ == "__main__":
    print(json.dumps(build()))
