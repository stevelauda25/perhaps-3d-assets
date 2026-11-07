"""Phase 1 for the PATEK PHILIPPE Calatrava 6007G (copy of pipeline/breitling_navitimer41_prep.py, untouched): trace JSON, dial and steel photo maps at the NATIVE photo size.
Changes against the Navitimer prep: MODEL / file names; the source is a 1920 x 2691 RGBA PNG (large, sharp studio render), so there is NO 2x working copy: every pixel position is in native
photo px and the maps are crops at scale 1 (`steel_photo.json` carries "scale": 1, read by pipeline/steps/watch_patek_calatrava6007g.py); one mirror-row range (the crown) about the case circle
centre; pockets (transparent gaps between a lug and the strap lining) are detected per row from the alpha runs between `pocket_rows_px` with gaps wider than `pocket_min_gap_px`
(the lug inner edge slopes, so no fixed x); hands are polar for the two profile hands (hour, minute), the central seconds hand is a free polygon in the spec; the strap is leather.

    python3 -B -m pipeline.patek_calatrava6007g_prep [variant key]      # default 6007g-blue
        reads    references/patek-calatrava-<variant key>/patek-<variant key>_original.png (1920 x 2691 RGBA PNG, saved untouched)
                 and config/watches/patek-calatrava6007g-<variant key>-measure.json (YOU measure the photo)
        writes   config/watches/patek-calatrava6007g-<variant key>-trace.json, outputs/watches/patek-calatrava6007g-<variant key>/{dial_photo,steel_photo}.jpg (+ .json)

mm, x right, y toward 12, origin = hand pivot; the silhouette is the largest alpha component above half (the soft alpha rim and the drop shadow stay below it).
The scale is anchored on the case circle fitted to the left / top / bottom silhouette (bezel_out_circle_px = [cx, cy, r] in photo px, r = case diameter / 2), not on a point left of the pivot.
All pixel positions in the measure file are CONTINUOUS photo coordinates (pixel i spans [i, i+1]); the dial crop is centred on the sub-pixel pivot with cv2.getRectSubPix.
The dial map is a native crop of the photo (hands and print stay in it, the 3D hands cover them); the steel map is the whole watch from the photo, projected from the front.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VAR = (sys.argv[1] if len(sys.argv) > 1 else "6007g-blue").lower()
MODEL = {"ref": "patek-calatrava", "name": "patek-calatrava6007g", "brand": "patek", "case_mm": 40}  # case_mm = Catalog 2 size (case diameter)
NAME = "%s-%s" % (MODEL["name"], VAR)
REF = ROOT / ("references/%s-%s" % (MODEL["ref"], VAR))
SRC = REF / ("%s-%s_original.png" % (MODEL["brand"], VAR))
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
    n_, lab, stats, _ = cv2.connectedComponentsWithStats((im[..., 3] > 128).astype(np.uint8), connectivity=8)
    fg = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))  # silhouette = largest alpha component above half
    polar = lambda L, a: [round(L / S, 3), round(a, 2)]

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (strap ends) sets the silhouette row range, 2 px inside the ends
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    c = PX["crown"]
    mir = [(-(b - py0) / S - 0.05, -(a - py0) / S + 0.05) for a, b in PX["mirror_rows_px"]]  # crown row range (continuous px -> mm) plus 0.05 mm: those rows take the left edge mirrored about the case circle centre
    ax = PX["mirror_axis_x_px"]
    prof = []  # alpha silhouette; the crown rows are replaced by the mirrored left edge
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        xs = np.nonzero(fg[int(math.floor(py0 - y * S))])[0]
        left = (xs.min() - px0) / S
        right = (xs.max() + 1 - px0) / S  # right pixel edge
        prof.append([round(float(y), 2), round(float(left), 3), round(float((2 * ax - xs.min() - px0) / S if any(lo <= y <= hi for lo, hi in mir) else right), 3)])
    # transparent pockets between a lug and the strap lining / leather (rows where the alpha runs are lug | lining | lug with gaps wider than pocket_min_gap_px): cutters for the case slab (one polygon per pocket, mm)
    cut = {"top": [[], []], "bottom": [[], []]}
    g_min = PX["pocket_min_gap_px"]
    for side, (r0, r1) in PX["pocket_rows_px"].items():
        for r in range(r0, r1):
            d = np.diff(np.r_[0, fg[r].astype(int), 0])
            runs = list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))
            if len(runs) >= 3 and runs[1][0] - runs[0][1] >= g_min and runs[-1][0] - runs[-2][1] >= g_min:
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
    for k, h in PX["hands"].items():
        hands[k] = {"length_mm": round(h["length_px"] / S, 3), "angle_deg": h["angle_deg"], "tail_mm": round(h["tail_px"] / S, 3)}
    out = {"source": str(SRC.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0], "native_size_px": [im.shape[1], im.shape[0]],
           "anchor": "case circle radius %.2f px (fit to the silhouette, crown rows excluded) = case diameter %s mm" % (PX["bezel_out_circle_px"][2], CASE_MM),
           "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "silhouette_y_left_right_mm": prof, "case_cutters_mm": cutters,
           "bracelet": {"half_width_at_tip_mm": [round(near((py0 - t) / S), 3) for t in PX.get("tip_rows_px", [])], "half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)],
                        "note": "black leather strap with contrast stitching and a coloured lining (one section, flat photo projection): wide at the lugs, narrowing toward the rounded ends"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "bezel": {"note": "polished domed bezel (smooth, no teeth); rings.bezel_in = crystal edge, rings.bezel_out = outer radius of the bezel lathe about the ring centre"}}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: native crop out to the bezel, centred on the sub-pixel pivot (pixel centres sit at integer index coordinates, so continuous p -> p - 0.5)
    R = int(math.ceil(PX["rings"]["bezel_in"] + 3))
    crop = cv2.getRectSubPix(im[..., :3], (2 * R, 2 * R), (px0 - 0.5, py0 - 0.5))
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": "none (native photo pixels, sub-pixel centred crop)"}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch from the photo (native, composited on grey), projected on the case, bezel, crown and strap from the front
    cols = np.nonzero(fg.any(axis=0))[0]  # the watch's alpha bbox plus a 4 px margin
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    near_ = cv2.dilate(fg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # keep only the watch plus its 4 px rim
    a = (im[Y0:Y1, X0:X1, 3] * near_[Y0:Y1, X0:X1])[..., None] / 255.0
    steel = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 90])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "scale": 1, "upscale": "none (native photo pixels)"}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "rings_mm", "hands", "bracelet", "crown")} | {"dial_map": meta, "cutters": {k: [len(p) for p in v] for k, v in cutters.items()}}


if __name__ == "__main__":
    print(json.dumps(build()))
