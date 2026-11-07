"""Black Bay 58 variant of pipeline/tudor_bb54_prep.py (same inputs/outputs; crown rows follow the crown box even when it is off the pivot row, no date window needed,
rotating bezel with insert in the trace; the watch is the LARGEST alpha component, so the catalogue photo's logo / tick marks beside the watch are ignored
in the silhouette and the steel map): 2x working reference, trace JSON, dial and steel photo maps.

    python3 -B -m pipeline.tudor_bb58_prep <lower-case sku>      # e.g. m7939a1a0nu-0001
        reads    references/<ref>-<sku>/tudor-<sku>_900x1200.png and config/watches/<name>-<sku>-measure.json (YOU measure the photo)
        writes   the 2x reference, config/watches/<name>-<sku>-trace.json, outputs/watches/<name>-<sku>/{dial_photo,steel_photo}.jpg (+ .json)
    <ref>/<name> come from the registry, e.g. tudor-black-bay-58 / tudor-bb58.

Anchor: case diameter from the registry, from the left edge of the silhouette on the pivot row (the right side carries the crown).
mm, x right, y toward 12, origin = hand pivot; the silhouette is the alpha above half. The dial map is a 2x crop of the photo (hands and print
stay in it, the 3D hands cover them); the steel map is the whole watch from the photo, projected from the front.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SKU = sys.argv[1].lower()  # lower-case SKU, e.g. m79950-0001; the prefix before the dash picks the model in config/watches/tudor-models.json
MODEL = json.loads((ROOT / "config/watches/tudor-models.json").read_text())[SKU.split("-")[0]]
NAME = "%s-%s" % (MODEL["name"], SKU)
REF = ROOT / ("references/%s-%s" % (MODEL["ref"], SKU))
SRC = REF / ("tudor-%s_900x1200.png" % SKU)
UP = REF / ("tudor-%s_1800x2400.png" % SKU)
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)
PX = {k: (tuple(v) if isinstance(v, list) and all(isinstance(i, (int, float)) for i in v) else v)
      for k, v in json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text()).items()}
CASE_MM = float(MODEL["case_mm"])  # case diameter in mm (model size in the catalog)



def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    px0, py0 = PX["pivot"]
    S = 2 * (px0 - PX["case_edge_left_x"]) / CASE_MM
    if not UP.exists():
        cv2.imwrite(str(UP), cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4))
    n_, lab, stats, _ = cv2.connectedComponentsWithStats((im[..., 3] > 128).astype(np.uint8), connectivity=8)
    fg = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))  # silhouette = largest alpha component above half (the drop shadow stays below it; the logo / ticks are other components)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(p[0] - px0, p[1] - py0) / S, 3), round(math.degrees(math.atan2(p[0] - px0, py0 - p[1])) % 360, 2))

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (bracelet ends) sets the silhouette row range, 2 px inside the ends
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    c = PX["crown"]
    crown_lo, crown_hi = -(c["y1"] + 1 - py0) / S - 0.25, -(c["y0"] - py0) / S + 0.25  # crown box (mm, may be off the pivot row) plus a margin: those rows take the mirrored left edge
    prof = []  # alpha silhouette; the crown rows are replaced by the mirrored left edge
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        xs = np.nonzero(fg[int(round(py0 - y * S))])[0]
        left = (xs.min() - px0) / S
        right = (xs.max() + 1 - px0) / S  # right pixel edge
        prof.append([round(float(y), 2), round(float(left), 3), round(float(-left if crown_lo <= y <= crown_hi else right), 3)])
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    near = lambda y: half[min(half, key=lambda k: abs(k - y))]  # silhouette half width at the row nearest y mm
    hands = {}
    for k in ("hour", "minute", "seconds"):
        L, a = polar(PX[k + "_tip"])
        hands[k] = {"length_mm": L, "angle_deg": a, "tail_mm": polar(PX[k + "_tail"])[0]}
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "case diameter %s mm from the silhouette left of the pivot" % CASE_MM, "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "silhouette_y_left_right_mm": prof,
           "bracelet": {"half_width_at_tip_mm": [round(near((py0 - t) / S), 3) for t in PX.get("tip_rows_px", [])], "half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)], "channel_mm": PX.get("channel_mm"),
                        "polished_shift": 0.5, "note": "five-column jubilee-style bracelet (outer, inner, centre, inner, outer) with staggered joints; the silhouette narrows slightly to the ends (perspective)"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "hand_lume": {"hour": PX["hour_lume"], "minute": PX["minute_lume"]},
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "bezel": {"note": "rotating dive bezel: black insert (numerals, markers, triangle in the photo) inside a steel coin-edge ring; rings.insert_out = end of the insert"}}
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
    near = cv2.dilate(fg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # drop shadow and logo: keep only the watch plus its 4 px rim
    a = (im[Y0:Y1, X0:X1, 3] * near[Y0:Y1, X0:X1])[..., None] / 255.0
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "rings_mm", "hands", "bracelet", "crown")} | {"dial_map": meta}


if __name__ == "__main__":
    print(json.dumps(build()))
