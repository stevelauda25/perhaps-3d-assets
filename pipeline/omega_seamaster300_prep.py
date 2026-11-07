"""Phase 1 for the OMEGA Seamaster 300 Co-Axial Master Chronometer 41 mm (234.30.41.21.01.001, steel, black dial, steel bracelet): copy of pipeline/omega_diver300m_prep.py
(untouched; same structure): 2x working reference, trace JSON, dial and steel photo maps.

    python3 -B -m pipeline.omega_seamaster300_prep [normalised sku]      # default 23430412101001
        reads    references/omega-seamaster-300-<sku>/omega-<sku>_original.png (1024 x 1024 RGBA PNG, saved untouched)
                 and config/watches/omega-seamaster300-<sku>-measure.json (YOU measure the photo)
        writes   references/omega-seamaster-300-<sku>/omega-<sku>_2048x2048.png (2x Lanczos4 working copy, alpha kept),
                 config/watches/omega-seamaster300-<sku>-trace.json, outputs/watches/omega-seamaster300-<sku>/{dial_photo,steel_photo}.jpg (+ .json)

Differences from the Diver 300M prep (all of them come from the photo):
  - the scale is anchored on the circle of the KNURLED COIN RING tooth tips (`bezel_out_circle_px` = [cx, cy, r], alpha edge on rays, r in photo px) = the 41 mm of the Catalog
    row (the left silhouette for rows 400..620 and the right silhouette outside the crown rows are that ring);
  - the crown rows take the left edge mirrored about the pivot (no crown housing shoulder, no helium valve on this model);
  - the bracelet runs OFF the image at 12 and 6 o'clock, so the steel map crop is clamped to the image (crop_px is recorded).
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
SKU = (sys.argv[1] if len(sys.argv) > 1 else "23430412101001").lower()
MODEL = {"ref": "omega-seamaster-300", "name": "omega-seamaster300", "brand": "omega", "case_mm": 41}  # case_mm = Catalog 2 size (case diameter)
NAME = "%s-%s" % (MODEL["name"], SKU)
REF = ROOT / ("references/%s-%s" % (MODEL["ref"], SKU))
SRC = REF / ("%s-%s_original.png" % (MODEL["brand"], SKU))
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

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (strap ends = image borders) sets the silhouette row range, 2 px inside the ends
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    c = PX["crown"]
    crown_lo, crown_hi = -(c["y1"] - py0) / S - 0.05, -(c["y0"] - py0) / S + 0.05  # crown box (continuous px) plus 0.05 mm: those rows take the mirrored left edge
    prof = []  # alpha silhouette; the crown rows are replaced by the mirrored left edge
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        xs = np.nonzero(fg[int(math.floor(py0 - y * S))])[0]
        left = (xs.min() - px0) / S
        right = (xs.max() + 1 - px0) / S  # right pixel edge
        prof.append([round(float(y), 2), round(float(left), 3), round(float(-left if crown_lo <= y <= crown_hi else right), 3)])
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    near = lambda y: half[min(half, key=lambda k: abs(k - y))]  # silhouette half width at the row nearest y mm
    hands = {}
    for k in ("hour", "minute", "seconds"):
        h = PX["hands"][k]
        hands[k] = {"length_mm": round(h["length_px"] / S, 3), "angle_deg": h["angle_deg"], "tail_mm": round(h["tail_px"] / S, 3)}
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "coin-ring tooth-tip circle radius %.2f px (alpha edge on rays) = case diameter %s mm" % (PX["bezel_out_circle_px"][2], CASE_MM),
           "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "silhouette_y_left_right_mm": prof,
           "bracelet": {"half_width_at_tip_mm": [round(near((py0 - t) / S), 3) for t in PX.get("tip_rows_px", [])], "half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)],
                        "note": "steel bracelet: three columns (polished outer links, brushed centre links); lug-wide at the case, narrows toward the ends"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "bezel": {"note": "rotating dive bezel: black ceramic insert bezel_in..insert_out (beige numerals, minute marks, lume pip in the photo) inside a steel knurled coin ring insert_out..bezel_out (the teeth are in the silhouette)"}}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: 2x crop out to the bezel, centred on the sub-pixel pivot (2x pixel centres sit at integer index coordinates, so continuous p -> 2p - 0.5)
    R = int(math.ceil(PX["rings"]["bezel_in"] + 3))
    crop = cv2.getRectSubPix(im2[..., :3], (4 * R, 4 * R), (2 * px0 - 0.5, 2 * py0 - 0.5))
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": "2x Lanczos4, sub-pixel centred crop"}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch from the photo (2x, composited on grey), projected on the case, bezel, crown and strap from the front; the crop is clamped to the image
    h_, w_ = fg.shape
    cols = np.nonzero(fg.any(axis=0))[0]  # the watch's alpha bbox plus a 4 px margin
    X0, Y0, X1, Y1 = max(0, int(cols[0]) - 4), max(0, int(rows[0]) - 4), min(w_, int(cols[-1]) + 5), min(h_, int(rows[-1]) + 5)
    near_ = cv2.dilate(fg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # keep only the watch plus its 4 px rim
    a = (im[Y0:Y1, X0:X1, 3] * near_[Y0:Y1, X0:X1])[..., None] / 255.0
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "rings_mm", "hands", "bracelet", "crown")} | {"dial_map": meta}


if __name__ == "__main__":
    print(json.dumps(build()))
