"""Phase 1 for the BREITLING Navitimer B01 Chronograph 41 (copy of pipeline/breitling_superocean42_prep.py, untouched): 2x working reference, trace JSON, dial and steel photo maps.
Changes against the Superocean prep: MODEL; the rows where the right silhouette is a crown or pusher (measure.mirror_rows_px, any number of ranges) take the left edge mirrored about
measure.mirror_axis_x_px (the bezel circle centre, not the pivot); the strap is leather (note only).

    python3 -B -m pipeline.breitling_navitimer41_prep [lower-case sku]      # default ab0139211b1p1
        reads    references/breitling-navitimer-b01-chronograph-41-<sku>/breitling-<sku>_original.webp (1024 x 1024 WebP with alpha, saved untouched)
                 and config/watches/breitling-navitimer41-<sku>-measure.json (YOU measure the photo)
        writes   references/breitling-navitimer-b01-chronograph-41-<sku>/breitling-<sku>_2048x2048.png (2x Lanczos4 working copy, alpha kept),
                 config/watches/breitling-navitimer41-<sku>-trace.json, outputs/watches/breitling-navitimer41-<sku>/{dial_photo,steel_photo}.jpg (+ .json)

Differences from the Tudor preps (all of them come from the photo, none from the recipe):
  - the source is a square 1024 px WebP (OpenCV reads it); there is no registry: the model constants are MODEL below (a later Breitling copies this file or edits MODEL);
  - the scale is anchored on the BEZEL circle fitted to the silhouette (bezel_out_circle_px = [cx, cy, r] in the measure file, r in photo px) = the 42 mm case
    diameter (the Superocean's coin-edge bezel is the widest part of the round case), not on a silhouette point left of the pivot;
  - all pixel positions in the measure file are CONTINUOUS photo coordinates (pixel i spans [i, i+1]), which is the convention of the texture projection in the step
    (u = x / width); the dial crop is centred on the sub-pixel pivot with cv2.getRectSubPix so that the map centre is exactly the origin;
  - hands are given in polar form (angle clockwise from 12, length and tail length in photo px from the pivot) because the hand tips are not isolated points on this photo
    (the minute and seconds hands overlap).
mm, x right, y toward 12, origin = hand pivot; the silhouette is the largest alpha component above half (the soft alpha rim of the render stays below it).
The dial map is a 2x crop of the photo (hands and print stay in it, the 3D hands cover them); the steel map is the whole watch from the photo, projected from the front.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SKU = (sys.argv[1] if len(sys.argv) > 1 else "ab0139211b1p1").lower()
MODEL = {"ref": "breitling-navitimer-b01-chronograph-41", "name": "breitling-navitimer41", "brand": "breitling", "case_mm": 41}  # case_mm = Catalog 2 size (bezel diameter)
NAME = "%s-%s" % (MODEL["name"], SKU)
REF = ROOT / ("references/%s-%s" % (MODEL["ref"], SKU))
SRC = REF / ("%s-%s_original.webp" % (MODEL["brand"], SKU))
UP = REF / ("%s-%s_2048x2048.png" % (MODEL["brand"], SKU))
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)
PX = json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text())
CASE_MM = float(MODEL["case_mm"])


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    assert im is not None and im.shape[2] == 4, "photo with alpha expected"
    px0, py0 = PX["pivot"]  # continuous photo px (hand pivot at hand height)
    S = 2 * PX["bezel_out_circle_px"][2] / CASE_MM
    im2 = cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    if not UP.exists():
        cv2.imwrite(str(UP), im2)
    n_, lab, stats, _ = cv2.connectedComponentsWithStats((im[..., 3] > 128).astype(np.uint8), connectivity=8)
    fg = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))  # silhouette = largest alpha component above half
    polar = lambda L, a: [round(L / S, 3), round(a, 2)]

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (strap ends) sets the silhouette row range, 2 px inside the ends
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    c = PX["crown"]
    mir = [(-(b - py0) / S - 0.05, -(a - py0) / S + 0.05) for a, b in PX["mirror_rows_px"]]  # crown / pusher row ranges (continuous px -> mm) plus 0.05 mm: those rows take the left edge mirrored about the bezel circle centre
    ax = PX["mirror_axis_x_px"]
    prof = []  # alpha silhouette; the crown / pusher rows are replaced by the mirrored left edge
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        xs = np.nonzero(fg[int(math.floor(py0 - y * S))])[0]
        left = (xs.min() - px0) / S
        right = (xs.max() + 1 - px0) / S  # right pixel edge
        prof.append([round(float(y), 2), round(float(left), 3), round(float((2 * ax - xs.min() - px0) / S if any(lo <= y <= hi for lo, hi in mir) else right), 3)])
    # transparent pockets between a lug, the bezel arc and the strap end (rows where the alpha runs are lug | bezel | lug): cutters for the case slab (one polygon per pocket, mm)
    cut = {"top": [[], []], "bottom": [[], []]}
    for r in list(range(150, 330)) + list(range(620, 780)):
        d = np.diff(np.r_[0, fg[r].astype(int), 0])
        runs = list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))
        if len(runs) >= 3 and abs(runs[0][1] - PX["lug_inner_px"][0]) <= 4 and abs(runs[-1][0] - PX["lug_inner_px"][1]) <= 4:
            side = "top" if r < py0 else "bottom"
            cut[side][0].append((r, runs[0][1], runs[1][0]))
            cut[side][1].append((r, runs[-2][1], runs[-1][0]))
    cutters = {}
    for side, ext in (("top", -PX["cutter_extend_px"]), ("bottom", PX["cutter_extend_px"])):
        cutters[side] = []
        for gr in cut[side]:
            if not gr:
                continue
            ys = [(py0 - (r + 0.5)) / S for r, _, _ in gr]
            ys[0] += (-ext / S) if side == "top" else 0.0  # extend toward the strap (hidden under it)
            ys[-1] += (-ext / S) if side == "bottom" else 0.0
            left = [[round((x0 - px0) / S, 3), round(y, 3)] for (r, x0, x1), y in zip(gr, ys)]
            right = [[round((x1 - px0) / S, 3), round(y, 3)] for (r, x0, x1), y in zip(gr, ys)]
            cutters[side].append(left + right[::-1])
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    near = lambda y: half[min(half, key=lambda k: abs(k - y))]  # silhouette half width at the row nearest y mm
    hands = {}
    for k in ("hour", "minute", "seconds"):
        h = PX["hands"][k]
        hands[k] = {"length_mm": round(h["length_px"] / S, 3), "angle_deg": h["angle_deg"], "tail_mm": round(h["tail_px"] / S, 3)}
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "bezel circle radius %.2f px (fit to the left silhouette) = case diameter %s mm" % (PX["bezel_out_circle_px"][2], CASE_MM),
           "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "silhouette_y_left_right_mm": prof, "case_cutters_mm": cutters,
           "bracelet": {"half_width_at_tip_mm": [round(near((py0 - t) / S), 3) for t in PX.get("tip_rows_px", [])], "half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)],
                        "note": "black leather strap with white stitching (one section, flat photo projection): wide at the lugs, narrowing toward the rounded ends (the 6 o'clock end is longer)"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "bezel": {"note": "fixed steel bezel with a 56-tooth coin edge and the engraved slide-rule scales (print in the photo); rings.insert_out = end of the flat scale ring, the coin ring runs to bezel_out"}}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: 2x crop out to the bezel, centred on the sub-pixel pivot (2x pixel centres sit at integer index coordinates, so continuous p -> 2p - 0.5)
    R = int(math.ceil(PX["rings"]["bezel_in"] + 3))
    crop = cv2.getRectSubPix(im2[..., :3], (4 * R, 4 * R), (2 * px0 - 0.5, 2 * py0 - 0.5))
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": "2x Lanczos4, sub-pixel centred crop"}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch from the photo (2x, composited on grey), projected on the case, bezel, crown and strap from the front
    cols = np.nonzero(fg.any(axis=0))[0]  # the watch's alpha bbox plus a 4 px margin
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    near_ = cv2.dilate(fg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # keep only the watch plus its 4 px rim
    a = (im[Y0:Y1, X0:X1, 3] * near_[Y0:Y1, X0:X1])[..., None] / 255.0
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "rings_mm", "hands", "bracelet", "crown")} | {"dial_map": meta}


if __name__ == "__main__":
    print(json.dumps(build()))
