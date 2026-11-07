"""Phase 1 for the AUDEMARS PIGUET Royal Oak Offshore Diver 42 (15720ST; first Audemars Piguet): 2x working reference, trace JSON, dial and steel photo maps.
Model-specific copy of pipeline/breitling_superocean42_prep.py (untouched), adapted to the AP catalogue photo and to the octagonal, screwed case.

    python3 -B -m pipeline.audemars_offshorediver42_prep [variant key]      # default 15720st-green (the blue one is 15720st-blue)
        reads    references/audemars-royal-oak-offshore-diver-<key>/audemars-<key>_1200x1626.png (the larger rendition, PNG with alpha; the 400 x 542 catalogue
                 file audemars-<key>_original.png stays untouched next to it) and config/watches/audemars-offshorediver42-<key>-measure.json (YOU measure the photo)
        writes   references/audemars-royal-oak-offshore-diver-<key>/audemars-<key>_2400x3252.png (2x Lanczos4 working copy, alpha kept),
                 config/watches/audemars-offshorediver42-<key>-trace.json, outputs/watches/audemars-offshorediver42-<key>/{dial_photo,steel_photo}.jpg (+ .json)

Differences from the Breitling prep (all of them come from the photo / the case, none from the recipe):
  - the watch fills only a third of the 1200 x 1626 canvas (344 x 506 px); everything is measured in the 1200 x 1626 pixel frame (continuous coordinates: pixel i spans [i, i+1]);
  - the scale is anchored on the 42 mm width of the octagonal case: the LEFT flat of the case (silhouette median over measure.anchor.rows, sub-pixel alpha edge) lies 21 mm left of the
    hand pivot (the right flat is hidden by the crown guard), S = (pivot x - left edge) / 21;
  - there are no circle-fitted rings: the measure file holds an OCTAGON (outer bezel edge: left / right / top / bottom flats of a regular octagon, vertices derived here),
    the round opening of the rotating bezel as a circle [cx, cy, r], the screws, and any number of crowns (hexagonal black crown body plus a rose-gold ring, each on its own axis);
  - crown rows of the silhouette are replaced by straight lines (measure.crown_replace: side, y0, y1, x at y0, x at y1), the crowns are separate parts.
mm, x right, y toward 12, origin = hand pivot; the silhouette is the largest alpha component above half.
The dial map is a 2x crop of the photo out to the opening of the bezel (the rotating ring, its sector, the waffle dial and the photographed hands stay in it, the 3D hands cover them);
the steel map is the whole watch from the photo, projected from the front.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KEY = (sys.argv[1] if len(sys.argv) > 1 else "15720st-green").lower()
MODEL = {"ref": "audemars-royal-oak-offshore-diver", "name": "audemars-offshorediver42", "brand": "audemars", "case_mm": 42}  # case_mm = Catalog 2 size (width across the octagon flats)
NAME = "%s-%s" % (MODEL["name"], KEY)
REF = ROOT / ("references/%s-%s" % (MODEL["ref"], KEY))
SRC = REF / ("%s-%s_1200x1626.png" % (MODEL["brand"], KEY))
UP = REF / ("%s-%s_2400x3252.png" % (MODEL["brand"], KEY))
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)
PX = json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text())
CASE_MM = float(MODEL["case_mm"])


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    assert im is not None and im.shape[2] == 4, "photo with alpha expected"
    px0, py0 = PX["pivot"]  # continuous photo px (hand pivot at hand height)
    alpha = im[..., 3].astype(np.float32) / 255.0
    n_, lab, stats, _ = cv2.connectedComponentsWithStats((im[..., 3] > 128).astype(np.uint8), connectivity=8)
    fg = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))  # silhouette = largest alpha component above half

    def left(r):  # continuous left edge of row r: the first pixel above half alpha, minus its missing coverage
        i = int(np.nonzero(fg[r])[0].min())
        return float(i + 1 - alpha[r, i])

    def right(r):
        j = int(np.nonzero(fg[r])[0].max())
        return float(j + alpha[r, j])
    r0, r1 = PX["anchor"]["rows"]
    xl = float(np.median([left(r) for r in range(r0, r1 + 1)]))
    S = (px0 - xl) / (CASE_MM / 2)  # the left flat of the case is half the case width from the pivot
    im2 = cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    if not UP.exists():
        cv2.imwrite(str(UP), im2)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda L, a: [round(L / S, 3), round(a, 2)]

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (strap ends) sets the silhouette row range, 2 px inside the ends
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    repl = PX["crown_replace"]

    def edge(side, r):  # silhouette edge of row r (px); crown rows follow the replacement lines
        for c in repl:
            if c["side"] == side and c["y0"] <= r <= c["y1"]:
                return c["x0"] + (c["x1"] - c["x0"]) * (r - c["y0"]) / (c["y1"] - c["y0"])
        return left(r) if side == "left" else right(r)
    prof = []
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        r = int(math.floor(py0 - y * S))
        prof.append([round(float(y), 2), round((edge("left", r) - px0) / S, 3), round((edge("right", r) - px0) / S, 3)])
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    near = lambda y: half[min(half, key=lambda k: abs(k - y))]
    hands = {}
    for k in ("hour", "minute", "seconds"):
        h = PX["hands"][k]
        hands[k] = {"length_mm": round(h["length_px"] / S, 3), "angle_deg": h["angle_deg"], "tail_mm": round(h["tail_px"] / S, 3)}

    # octagon (outer edge of the bezel): regular octagon stretched to the measured flats; counter-clockwise polygon in mm
    o = PX["octagon"]
    t = math.tan(math.radians(22.5))
    cxo, cyo = (o["left_x"] + o["right_x"]) / 2, (o["top_y"] + o["bottom_y"]) / 2
    ax, ay = (o["right_x"] - o["left_x"]) / 2, (o["bottom_y"] - o["top_y"]) / 2
    oct_px = [(cxo + ax, cyo - ay * t), (cxo + ax * t, cyo - ay), (cxo - ax * t, cyo - ay), (cxo - ax, cyo - ay * t),
              (cxo - ax, cyo + ay * t), (cxo - ax * t, cyo + ay), (cxo + ax * t, cyo + ay), (cxo + ax, cyo + ay * t)]  # starts right-upper, runs counter-clockwise (image y is down)
    oc = PX["opening_circle_px"]
    crowns = []
    for c in PX["crowns"]:
        crowns.append({"name": c["name"], "base_mm": mm(c["base_px"]), "angle_deg": c["angle_deg"], "hex_len_mm": round(c["hex_len_px"] / S, 3), "hex_r_mm": round(c["hex_r_px"] / S, 3),
                       "ring_len_mm": round(c["ring_len_px"] / S, 3), "ring_r_mm": round(c["ring_r_px"] / S, 3)})
    out = {"source": str(SRC.relative_to(ROOT)), "working_2x": str(UP.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "case width %s mm: the left flat of the octagonal case (median alpha edge over rows %d..%d = %.2f px) lies %s mm left of the pivot" % (CASE_MM, r0, r1, xl, CASE_MM / 2),
           "octagon_mm": [mm(p) for p in oct_px],
           "opening": {"centre_mm": mm(oc[:2]), "radius_mm": round(oc[2] / S, 3), "dial_flat_mm": round(PX["dial_flat_r_px"] / S, 3), "ring_in_mm": round(PX["ring_in_r_px"] / S, 3)},
           "screws_mm": [mm(p) for p in PX["screws_px"]], "screw_radius_mm": round(PX["screw_r_px"] / S, 3),
           "silhouette_y_left_right_mm": prof,
           "bracelet": {"half_width_at_tip_mm": [round(near((py0 - t_) / S), 3) for t_ in PX.get("tip_rows_px", [])], "half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)],
                        "note": "green rubber strap: tapers toward both ends, two side sections and a centre section between two seams, a shallow notch in the centre of each end"},
           "hands": hands, "hub_radius_mm": round(PX["hub_r"] / S, 3), "crowns": crowns}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: 2x crop out to the opening of the bezel (rotating ring included), centred on the sub-pixel pivot (2x pixel centres sit at integer index coordinates: continuous p -> 2p - 0.5)
    R = int(math.ceil(oc[2] + math.hypot(oc[0] - px0, oc[1] - py0) + 3))
    crop = cv2.getRectSubPix(im2[..., :3], (4 * R, 4 * R), (2 * px0 - 0.5, 2 * py0 - 0.5))
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": "2x Lanczos4, sub-pixel centred crop"}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch from the photo (2x, composited on grey), projected on the case, bezel, crowns and strap from the front
    cols = np.nonzero(fg.any(axis=0))[0]  # the watch's alpha bbox plus a 4 px margin
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    near_ = cv2.dilate(fg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # keep only the watch plus its 4 px rim
    a = (im[Y0:Y1, X0:X1, 3] * near_[Y0:Y1, X0:X1])[..., None] / 255.0
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    steel = cv2.resize(flat, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 92])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "upscale": "2x Lanczos4"}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "hands", "bracelet", "crowns", "opening")} | {"dial_map": meta, "silhouette_rows_mm": [y_lo, y_hi]}


if __name__ == "__main__":
    print(json.dumps(build()))
