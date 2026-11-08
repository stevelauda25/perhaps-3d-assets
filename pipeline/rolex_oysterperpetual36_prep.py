"""Phase 1 for the Rolex Oyster Perpetual 36 family (126000, lavender dial; other 36 mm dials follow it).
Native-size workflow (1920 x 2857 RGBA catalogue render, no enlargement): trace JSON, dial map and steel map, texture cap 2048 px.

    python3 -B -m pipeline.rolex_oysterperpetual36_prep <key>      # e.g. 126000
        reads    config/watches/rolex-oysterperpetual36-<key>-measure.json (YOU measure the photo) and the photo named in it ("reference_dir" / "photo")
        writes   config/watches/rolex-oysterperpetual36-<key>-trace.json, outputs/watches/rolex-oysterperpetual36-<key>/{dial_photo,steel_photo}.jpg (+ .json)

Anchor: the listed 36 mm case = the case flank on the pivot row to the mirror flank about the case centre x (`case_centre_x`; the right flank is hidden by the
crown, so the left one is mirrored): scale = 2 * (case_centre_x - case_edge_left_x) / case_mm. mm, x right, y toward 12, origin = hand pivot. The silhouette is the
alpha above half (largest component); crown rows take the mirrored left edge. Dial map = native crop out to the bezel; steel map = the whole watch from the photo
(composited on grey), capped at `steel_max_px` on the long side (scale recorded in the json), projected from the front on case, bezel, crown and bracelet.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KEY = sys.argv[1].lower()
NAME = "rolex-oysterperpetual36-%s" % KEY
MEASURE = ROOT / ("config/watches/%s-measure.json" % NAME)
PX = json.loads(MEASURE.read_text())
SRC = ROOT / PX["photo"]
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    px0, py0 = PX["pivot"]
    S = 2 * (PX["case_centre_x"] - PX["case_edge_left_x"]) / PX["case_mm"]
    n_, lab, stats, _ = cv2.connectedComponentsWithStats((im[..., 3] > 128).astype(np.uint8), connectivity=8)
    fg = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))  # silhouette = largest alpha component above half
    cx_mm = (PX["case_centre_x"] - px0) / S  # case centre relative to the pivot (the photo has the pivot a few px right of it)
    rows = np.nonzero(fg.any(axis=1))[0]
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    c = PX["crown"]
    crown_lo, crown_hi = -(c["y1"] + 1 - py0) / S - 0.25, -(c["y0"] - py0) / S + 0.25  # crown box plus a margin: those rows take the mirrored left edge
    prof = []
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        xs = np.nonzero(fg[int(round(py0 - y * S))])[0]
        left = (xs.min() - px0) / S
        right = (xs.max() + 1 - px0) / S
        prof.append([round(float(y), 2), round(float(left), 3), round(float(2 * cx_mm - left if crown_lo <= y <= crown_hi else right), 3)])
    cc = PX["ring_centre_px"]
    hands = {k: dict(v) for k, v in PX["hands"].items()}  # {angle_deg, length_mm, tail_mm}: measured by perpendicular edge scans, see the measure note
    out = {"source": str(SRC.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0], "native_size_px": [im.shape[1], im.shape[0]],
           "anchor": "case diameter %s mm = 2 x (case centre x %s - left flank x %s) / S at the pivot row" % (PX["case_mm"], PX["case_centre_x"], PX["case_edge_left_x"]),
           "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "ring_centre_mm": [round((cc[0] - px0) / S, 3), round(-(cc[1] - py0) / S, 3)],
           "silhouette_y_left_right_mm": prof,
           "tips_mm": [round((py0 - t) / S, 3) for t in PX["tip_rows_px"]],
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "bracelet_px": PX.get("bracelet_px", {})}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: native crop out to the bezel, centred on the pivot
    R = int(math.ceil(PX["rings"]["bezel_in"] + abs(cc[0] - px0) + abs(cc[1] - py0) + 3))
    crop = im[py0 - R:py0 + R, px0 - R:px0 + R, :3]
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, PX.get("dial_quality", 93)])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": int(crop.shape[0]), "scale": 1.0}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch (alpha bbox plus a 4 px margin) composited on grey, capped at steel_max_px on the long side
    cols = np.nonzero(fg.any(axis=0))[0]
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    a = (im[Y0:Y1, X0:X1, 3] * fg[Y0:Y1, X0:X1])[..., None] / 255.0  # pixels outside the watch component (none here) stay grey
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    k = min(1.0, PX.get("steel_max_px", 2048) / max(flat.shape[:2]))
    steel = cv2.resize(flat, None, fx=k, fy=k, interpolation=cv2.INTER_AREA) if k < 1 else flat
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, PX.get("steel_quality", 92)])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [int(steel.shape[1]), int(steel.shape[0])], "scale": round(k, 5)}) + "\n")
    return {"scale_px_per_mm": out["scale_px_per_mm"], "rings_mm": out["rings_mm"], "ring_centre_mm": out["ring_centre_mm"], "tips_mm": out["tips_mm"], "crown": out["crown"],
            "dial_map": meta, "steel_map": {"size_px": [int(steel.shape[1]), int(steel.shape[0])], "scale": round(k, 5)}}


if __name__ == "__main__":
    print(json.dumps(build()))
