"""Phase 1 for the Tudor Royal 36 M2836C1A0-0101 (black dial, Roman numerals): 2x working reference, trace JSON and dial photo map.

    python3 -B -m pipeline.tudor_royal36_prep      # writes the 2x reference, config/watches/tudor-royal36-m2836c1a0-0101-trace.json,
                                                  # outputs/watches/tudor-royal36-m2836c1a0-0101/dial_photo.jpg (+ .json)

Source: the catalogue photo (900 x 1200, transparent background, front view with a little perspective). Anchor: case diameter
36 mm (model name, catalog 2) from the left edge of the silhouette on the pivot row (the right side carries the crown).
mm, x right, y toward 12, origin = hand pivot. Pixel positions are read from gridded crops (+-2 px = +-0.15 mm); the case outline
is the alpha silhouette. The dial map is a crop of the photo at 2x (Lanczos): hands and print stay in it, so the 3D hands cover
the photographed ones at the photographed time (10:09:xx) and the minute hand still hides the II numeral as it does in the photo.
"""
import json
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references/tudor-royal-36-m2836c1a0-0101"
SRC = REF / "tudor-m2836c1a0-0101_900x1200.png"
UP = REF / "tudor-m2836c1a0-0101_1800x2400.png"
TRACE = ROOT / "config/watches/tudor-royal36-m2836c1a0-0101-trace.json"
STEEL = ROOT / "outputs/watches/tudor-royal36-m2836c1a0-0101/steel_photo.jpg"
DIAL = ROOT / "outputs/watches/tudor-royal36-m2836c1a0-0101/dial_photo.jpg"
CASE_MM = 36.0

PX = {
    "pivot": (448, 664), "case_edge_left_x": 195,
    "rings": {"bezel_in": 216, "crystal_edge": 213, "dial_flat": 207, "bezel_out": 248},
    "hour_tip": (357, 609), "minute_tip": (612, 586), "seconds_tip": (318, 790),
    "hour_tail": (485, 688), "minute_tail": (418, 684), "seconds_tail": (478, 632),
    "hub_r": 20, "hour_lume": (0.2, 0.8), "minute_lume": (0.35, 0.86),
    "crown": {"x0": 700, "x1": 740, "y0": 622, "y1": 710},
    "date": {"x0": 565, "y0": 647, "x1": 614, "y1": 688},
    # bracelet columns, 6 o'clock side: polished channels |x| 2.5..4.5 mm (px 412..385 / 482..510), brushed rows joint at 380, 330, 286, 256
    "channel_mm": [2.5, 4.5],
}


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    px0, py0 = PX["pivot"]
    S = 2 * (px0 - PX["case_edge_left_x"]) / CASE_MM
    if not UP.exists():
        cv2.imwrite(str(UP), cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4))
    fg = im[..., 3] > 200
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(p[0] - px0, p[1] - py0) / S, 3), round(math.degrees(math.atan2(p[0] - px0, py0 - p[1])) % 360, 2))

    prof = []  # alpha silhouette; the crown rows are replaced by the mirrored left edge
    for y in np.arange(-32.5, 29.76, 0.25):
        xs = np.nonzero(fg[int(round(py0 - y * S))])[0]
        left = (xs.min() - px0) / S
        right = (xs.max() - px0) / S
        prof.append([round(float(y), 2), round(float(left), 3), round(float(right if abs(y) > 3.5 else -left), 3)])
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    hands = {}
    for k in ("hour", "minute", "seconds"):
        L, a = polar(PX[k + "_tip"])
        hands[k] = {"length_mm": L, "angle_deg": a, "tail_mm": polar(PX[k + "_tail"])[0]}
    c = PX["crown"]
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "case diameter 36 mm (Royal 36) from the silhouette left of the pivot", "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "silhouette_y_left_right_mm": prof,
           "bracelet": {"half_width_at_tip_mm": round(half[20.25], 3), "half_width_end_mm": round(half[29.75], 3), "channel_mm": PX["channel_mm"],
                        "polished_shift": 0.5, "note": "brushed rows with two polished channels; the photo's bracelet narrows to the ends (perspective plus curl)"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "hand_lume": {"hour": PX["hour_lume"], "minute": PX["minute_lume"]},
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3),
                     "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "date_window_mm": mm((PX["date"]["x0"], PX["date"]["y0"])) + mm((PX["date"]["x1"], PX["date"]["y1"])),
           "bezel": {"segments": 48, "ribbed_centres_deg": "7.5 + 15 k (plain segments centred at 0, 15, 30 ... deg)", "ribs_per_segment": 5}}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: 2x crop out to the bezel
    R = int(math.ceil(PX["rings"]["bezel_in"] + 3))
    crop = cv2.resize(im[py0 - R:py0 + R, px0 - R:px0 + R, :3], None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": "2x Lanczos4"}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch from the photo (2x, composited on grey), projected on the case, bezel, crown and bracelet from the front
    X0, Y0, X1, Y1 = 180, 230, 760, 1135
    a = im[Y0:Y1, X0:X1, 3:4] / 255.0
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "rings_mm", "hands", "bracelet", "crown")} | {"dial_map": meta}


if __name__ == "__main__":
    print(json.dumps(build()))
