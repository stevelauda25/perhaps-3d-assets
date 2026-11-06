"""Phase 1 for the Tudor Royal 40 variants (copy of tudor_royal36_prep.py with the 40 mm anchor, the silhouette row range read from the
alpha and no Royal 36 keys): 2x working reference, trace JSON, dial and steel photo maps.

    python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0001     # lower-case SKU; a bare 0001 means m2840d1a0-0001
        reads    references/tudor-royal-40-<sku>/tudor-<sku>_900x1200.png
                 config/watches/tudor-royal40-<sku>-measure.json   (pixel measurements read from that photo, see -0001)
        writes   the 2x reference, config/watches/tudor-royal40-<sku>-trace.json,
                 outputs/watches/tudor-royal40-<sku>/{dial_photo,steel_photo}.jpg (+ .json)

Source: the catalogue photo (900 x 1200, transparent background, front view with a little perspective). Anchor: case diameter
40 mm (model name, catalog 2) from the left edge of the silhouette on the pivot row (the right side carries the crown).
mm, x right, y toward 12, origin = hand pivot. Pixel positions are read from gridded crops (+-2 px = +-0.15 mm); the case outline
is the alpha silhouette. The dial map is a crop of the photo at 2x (Lanczos): hands and print stay in it, so the 3D hands cover
the photographed ones at the photographed time (10:09:xx) and the minute hand still hides the II numeral as it does in the photo.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ARG = sys.argv[1] if len(sys.argv) > 1 else "m2840d1a0-0001"
SKU = ARG if "-" in ARG else "m2840d1a0-" + ARG  # lower-case SKU; a bare 4-digit suffix means a Royal 40 M2840D1A0-<suffix>
SIZE = {"m2840d1a0": "40"}[SKU.split("-")[0]]
NAME = "tudor-royal%s-%s" % (SIZE, SKU)
REF = ROOT / ("references/tudor-royal-%s-%s" % (SIZE, SKU))
SRC = REF / ("tudor-%s_900x1200.png" % SKU)
UP = REF / ("tudor-%s_1800x2400.png" % SKU)
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)
PX = {k: (tuple(v) if isinstance(v, list) and all(isinstance(i, (int, float)) for i in v) else v)
      for k, v in json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text()).items()}
CASE_MM = float(SIZE)  # the model name is the case diameter in mm



def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    px0, py0 = PX["pivot"]
    S = 2 * (px0 - PX["case_edge_left_x"]) / CASE_MM
    if not UP.exists():
        cv2.imwrite(str(UP), cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4))
    fg = im[..., 3] > 128  # silhouette = alpha above half (the drop shadow stays below it)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(p[0] - px0, p[1] - py0) / S, 3), round(math.degrees(math.atan2(p[0] - px0, py0 - p[1])) % 360, 2))

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (bracelet ends) sets the silhouette row range, 2 px inside the ends
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    c = PX["crown"]
    crown_half = (c["y1"] - c["y0"]) / 2 / S + 0.25  # rows inside the crown's height take the mirrored left edge
    prof = []  # alpha silhouette; the crown rows are replaced by the mirrored left edge
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        xs = np.nonzero(fg[int(round(py0 - y * S))])[0]
        left = (xs.min() - px0) / S
        right = (xs.max() + 1 - px0) / S  # right pixel edge
        prof.append([round(float(y), 2), round(float(left), 3), round(float(right if abs(y) > crown_half else -left), 3)])
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    near = lambda y: half[min(half, key=lambda k: abs(k - y))]  # silhouette half width at the row nearest y mm
    hands = {}
    for k in ("hour", "minute", "seconds"):
        L, a = polar(PX[k + "_tip"])
        hands[k] = {"length_mm": L, "angle_deg": a, "tail_mm": polar(PX[k + "_tail"])[0]}
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "case diameter 40 mm (Royal 40) from the silhouette left of the pivot", "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "silhouette_y_left_right_mm": prof,
           "bracelet": {"half_width_at_tip_mm": [round(near((py0 - t) / S), 3) for t in PX["tip_rows_px"]], "half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)], "channel_mm": PX["channel_mm"],
                        "polished_shift": 0.5, "note": "brushed rows with two polished channels; the photo's bracelet narrows to the ends (perspective plus curl)"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "hand_lume": {"hour": PX["hour_lume"], "minute": PX["minute_lume"]},
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "date_window_mm": mm((PX["date"]["x0"], PX["date"]["y0"])) + mm((PX["date"]["x1"], PX["date"]["y1"])),
           "bezel": {"segments": PX.get("segments", 48), "ribbed_centres_deg": "7.5 + 15 k (plain segments centred at 0, 15, 30 ... deg)", "ribs_per_segment": 5}}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: 2x crop out to the bezel
    R = int(math.ceil(PX["rings"]["bezel_in"] + 3))
    crop = cv2.resize(im[py0 - R:py0 + R, px0 - R:px0 + R, :3], None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": "2x Lanczos4"}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch from the photo (2x, composited on grey), projected on the case, bezel, crown and bracelet from the front
    cols = np.nonzero(fg.any(axis=0))[0]  # the watch's alpha bbox plus a 4 px margin
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    a = im[Y0:Y1, X0:X1, 3:4] / 255.0
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "rings_mm", "hands", "bracelet", "crown")} | {"dial_map": meta}


if __name__ == "__main__":
    print(json.dumps(build()))
