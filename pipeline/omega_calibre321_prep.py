"""Phase 1 for the OMEGA Speedmaster Calibre 321 Chronograph 39.7 mm 311.30.40.30.01.001 (copy of pipeline/omega_moonwatch_prep.py, the Moonwatch template, bound to the Calibre 321
names): 2x working reference, trace JSON, dial and steel photo maps.

    python3 -B -m pipeline.omega_calibre321_prep [normalised sku]      # default 31130403001001
        reads    references/omega-speedmaster-calibre-321-<sku>/omega-<sku>_original.png (1024 x 1024 RGBA PNG, saved untouched)
                 and config/watches/omega-calibre321-<sku>-measure.json (measured on this photo)
        writes   references/omega-speedmaster-calibre-321-<sku>/omega-<sku>_2048x2048.png (2x Lanczos4 working copy, alpha kept),
                 config/watches/omega-calibre321-<sku>-trace.json, outputs/watches/omega-calibre321-<sku>/{dial_photo,steel_photo}.jpg (+ .json)

Differences from the Chronomat prep (all of them come from the photo, none from the recipe; the Calibre 321 differs from the Moonwatch only in its measure values):
  - the source is a PNG with alpha and the bracelet runs OFF the image at 12 and 6 o'clock (alpha rows 1 and 1023), so the steel map crop is clamped to the image (crop_px recorded);
  - the scale is NOT anchored on a fitted circle (the left silhouette is the twisted lug flank, not a circle): measure `scale_px_per_mm` is the mean of three published dimensions read on
    the photo (case width 39.7 mm from the circular left case flank, cross-checked with the lug gap and lug to lug, see `scale_basis` in the measure file); `bezel_out_circle_px` is only the black bezel ring circle;
  - `right_override_px` = [[row0, row1, x0, x1], ...] (photo px, rows inclusive, x linear in the row): the rows where the right silhouette is a chronograph pusher or the crown are
    replaced by the straight case-flank / crown-guard shoulder line (the 3D pushers and crown are added in the step); everything else, including the guard shoulders, stays the alpha edge;
  - the crown measure also carries `fluted_to_x` (end of the fluted barrel, the domed cap follows).
mm, x right, y toward 12, origin = hand pivot; the silhouette is the largest alpha component above half (the soft alpha rim of the render stays below it).
All pixel positions in the measure file are CONTINUOUS photo coordinates (pixel i spans [i, i+1]) = the convention of the texture projection in the step (u = x / width).
The dial map is a 2x crop of the photo (hands and print stay in it, the 3D hands cover them); the steel map is the whole watch from the photo, projected from the front.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SKU = (sys.argv[1] if len(sys.argv) > 1 else "31130403001001").lower()
MODEL = {"ref": "omega-speedmaster-calibre-321", "name": "omega-calibre321", "brand": "omega"}
NAME = "%s-%s" % (MODEL["name"], SKU)
REF = ROOT / ("references/%s-%s" % (MODEL["ref"], SKU))
SRC = REF / ("%s-%s_original.png" % (MODEL["brand"], SKU))
UP = REF / ("%s-%s_2048x2048.png" % (MODEL["brand"], SKU))
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)
PX = json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text())


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    assert im is not None and im.shape[2] == 4, "photo with alpha expected"
    px0, py0 = PX["pivot"]  # continuous photo px (hand pivot at hand height)
    S = float(PX["scale_px_per_mm"])
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
    ov = PX["right_override_px"]  # [[row0, row1, x0, x1], ...]: the right edge on those photo rows is the straight line x0 -> x1 (pusher / crown rows)

    def right_edge(row_c, alpha_right):  # row_c = continuous photo row of the silhouette sample (the override line is evaluated there, not on the pixel row, so its slope stays smooth)
        for r0, r1, x0, x1 in ov:
            if r0 <= row_c <= r1:
                return x0 + (x1 - x0) * (row_c - r0) / (r1 - r0)
        return alpha_right  # sub-pixel right edge of the alpha
    def edge_pair(r):  # sub-pixel left / right edge of pixel row r: 50 percent crossing of the soft alpha rim (linear between pixel centres), not the integer pixel edge
        xs = np.nonzero(fg[r])[0]
        al = im[r, :, 3].astype(float) / 255.0
        i, j = int(xs.min()), int(xs.max())
        left = (i - 0.5) + (0.5 - al[i - 1]) / (al[i] - al[i - 1]) if al[i] != al[i - 1] else float(i)
        right = (j + 0.5) + (al[j] - 0.5) / (al[j] - al[j + 1]) if al[j] != al[j + 1] else float(j + 1)
        return left, right
    prof = []  # alpha silhouette (edges interpolated between the two pixel rows around the continuous row); the pusher and crown rows take the override line
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        row_c = py0 - y * S
        r0 = int(math.floor(row_c - 0.5))  # pixel row r covers [r, r+1], centre r + 0.5
        w = row_c - 0.5 - r0
        (l0, r0e), (l1, r1e) = edge_pair(r0), edge_pair(r0 + 1)
        left, right = l0 + (l1 - l0) * w, r0e + (r1e - r0e) * w
        prof.append([round(float(y), 2), round(float((left - px0) / S), 3), round(float((right_edge(row_c, right) - px0) / S), 3)])
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    near = lambda y: half[min(half, key=lambda k: abs(k - y))]  # silhouette half width at the row nearest y mm
    hands = {}
    for k in ("hour", "minute", "seconds"):
        h = PX["hands"][k]
        hands[k] = {"length_mm": round(h["length_px"] / S, 3), "angle_deg": h["angle_deg"], "tail_mm": round(h["tail_px"] / S, 3)}
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "scale %.3f px/mm: case width 39.7 mm (left case flank circle) cross-checked with the lug gap and lug to lug read on the photo (%s)" % (S, "see measure file scale_basis"),
           "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "silhouette_y_left_right_mm": prof,
           "bracelet": {"half_width_at_tip_mm": [round(near((py0 - t) / S), 3) for t in PX.get("tip_rows_px", [])], "half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)],
                        "note": "Calibre 321 bracelet: three columns (outer, centre, outer) with their own joint rows (the outer columns share rows, the centre column is staggered); the silhouette narrows toward the ends"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3), "fluted_to_mm": round((c["fluted_to_x"] - px0) / S, 3)},
           "bezel": {"note": "tachymeter bezel: one black aluminium-look ring (wide inner chamfer, flat top bezel_in+chamfer .. bezel_out; scale numerals, dots and the TACHYMETRE text are photo texture); no steel coin ring (insert_out = bezel_out)"}}
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
    h_, w_ = fg.shape
    X0, Y0, X1, Y1 = max(0, int(cols[0]) - 4), max(0, int(rows[0]) - 4), min(w_, int(cols[-1]) + 5), min(h_, int(rows[-1]) + 5)  # clamped: the bracelet runs off the image
    near_ = cv2.dilate(fg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # keep only the watch plus its 4 px rim
    a = (im[Y0:Y1, X0:X1, 3] * near_[Y0:Y1, X0:X1])[..., None] / 255.0
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "rings_mm", "hands", "bracelet", "crown")} | {"dial_map": meta}


if __name__ == "__main__":
    print(json.dumps(build()))
