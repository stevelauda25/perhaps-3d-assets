"""Phase 1 for the PATEK PHILIPPE Aquanaut 5168G blue (row 104): trace JSON, dial and steel photo maps.
Copy of pipeline/patek_aquanaut42_prep.py (untouched, the green template) with TWO changes: the steel map is downscaled to a 2048 px long side (INTER_AREA, json scale 0.9438) and measure.hands.<name>.offset_px (the photographed hand centre line sits off the hub centre, camera tilt) is written to the trace as hands.<name>.offset_mm, which the template step already reads.
Copy of pipeline/patek_aquanaut40_prep.py (untouched; the 5167A template) with two changes: the model name is patek-aquanaut42 (file names), and the strap inner walls inside the lug zone may be
a straight line between two measured points (measure.strap_inner_px "top_end" / "bottom_end": the 5168G strap flares / tapers between the lug start and the bezel, 5167A's walls were constant).
Generic over the 5168G variants: the blue sibling runs it read-only with its own measure file.

    python3 -B -m pipeline.patek_aquanaut42_prep <key> [config key]        # key = 5168g-green or 5168g-blue (reference folder references/patek-aquanaut-<key>, config files patek-aquanaut42-<key>-*)
        reads    references/patek-aquanaut-<ref key>/patek-*_original.png (the one catalogue file, untouched) and config/watches/patek-aquanaut42-<config key>-measure.json (YOU measure the photo)
        writes   config/watches/patek-aquanaut42-<config key>-trace.json, outputs/watches/patek-aquanaut42-<config key>/{dial_photo,steel_photo}.jpg (+ .json)

Original docstring of the 5167A prep follows.

Differences from the Audemars Piguet prep (all of them come from the photo / the case, none from the recipe):
  - the photo is large and sharp (watch 1307 x 2119 px, about 30 px/mm): everything is measured and mapped at NATIVE size (no 2x copy; the maps are native-size JPEGs, ~1 MB each, the GLB stays near 3 MB);
  - the scale is anchored on the listed case width (measure.case_mm, 40 mm for the 5167A, 42.2 for the 5168G): the LEFT flank of the case (silhouette median over measure.anchor.rows, sub-pixel alpha edge)
    lies half the case width left of the hand pivot, S = (pivot x - left edge) / (case_mm / 2); no circle fit;
  - the bezel is a smooth rounded octagon with a rounded-square window: the outer edge is a SUPERELLIPSE (measure.bezel_outer: centre, half axes, exponent, from the polished top / bottom edge rows and the flank)
    cut back to the silhouette; the inner edge (the window) is SCANNED here: along 720 rays from the pivot the innermost long bright run of the brushed bezel face starts at the window edge (measure.aperture);
  - one crown at 3 o'clock (fluted cylinder, profile list in the measure file); crown rows of the silhouette are replaced by a straight line (measure.crown_replace, x0/x1 may be "case_width":
    the notch wall at case_mm from the left flank);
  - the rubber strap is one piece with an embossed grid: outer edges = silhouette, but inside the lug zone the strap edges are the measured lug inner walls (measure.strap_inner_px), written to the trace.
mm, x right, y toward 12, origin = hand pivot; the silhouette is the largest alpha component above half.
The dial map is a native crop around the pivot out to the window; the steel map is the whole watch from the photo (flattened on grey), projected from the front.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REFKEY = (sys.argv[1] if len(sys.argv) > 1 else "5168g-green").lower()
KEY = (sys.argv[2] if len(sys.argv) > 2 else REFKEY).lower()
MODEL = {"ref": "patek-aquanaut", "name": "patek-aquanaut42"}
NAME = "%s-%s" % (MODEL["name"], KEY)
REF = ROOT / ("references/%s-%s" % (MODEL["ref"], REFKEY))
SRC = next(REF.glob("patek-*_original.png"))
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)
PX = json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text())
CASE_MM = float(PX["case_mm"])


def scan_aperture(g, px0, py0, ap, n=720):
    """Radius (px) of the window edge along n rays (counter-clockwise from +x): the start of the innermost long bright run (the brushed bezel face), smoothed circularly."""
    rr = np.arange(ap["r_start_px"], ap["r_end_px"], 0.5)
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        xs = (px0 - 0.5 + rr * math.cos(a)).astype(np.float32)
        ys = (py0 - 0.5 - rr * math.sin(a)).astype(np.float32)
        v = cv2.remap(g, xs.reshape(1, -1), ys.reshape(1, -1), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)[0]
        v = cv2.medianBlur(v.reshape(1, -1).astype(np.uint8), 9)[0]
        idx = np.nonzero(v > ap["bright_thr"])[0]
        runs = [q for q in np.split(idx, np.nonzero(np.diff(idx) > 16)[0] + 1) if len(q) >= ap["min_run_px"] * 2]
        out.append(float(rr[runs[0].min()]) if runs else np.nan)
    r = np.array(out)
    assert not np.isnan(r).any(), "window edge not found on some rays: lower measure.aperture.min_run_px or bright_thr"
    k = int(ap["median_half"])
    ext = np.concatenate([r[-k:], r, r[:k]])
    r = np.array([np.median(ext[i:i + 2 * k + 1]) for i in range(n)])
    m = int(ap["mean_half"])
    ext = np.concatenate([r[-m:], r, r[:m]])
    return np.array([ext[i:i + 2 * m + 1].mean() for i in range(n)])


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    assert im is not None and im.shape[2] == 4, "photo with alpha expected"
    px0, py0 = PX["pivot"]  # continuous photo px (hand pivot = centre of the small hub disc)
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
    S = (px0 - xl) / (CASE_MM / 2)  # the left flank of the case is half the case width from the pivot
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (strap ends) sets the silhouette row range, 2 px inside the ends
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    repl = []
    for c in PX["crown_replace"]:
        c = dict(c)
        for k in ("x0", "x1"):
            if c[k] == "case_width":
                c[k] = xl + CASE_MM * S
        repl.append(c)

    def edge(side, r):  # silhouette edge of row r (px); crown rows follow the replacement lines
        for c in repl:
            if c["side"] == side and c["y0"] <= r <= c["y1"]:
                return c["x0"] + (c["x1"] - c["x0"]) * (r - c["y0"]) / (c["y1"] - c["y0"])
        return left(r) if side == "left" else right(r)
    lerp = lambda a, b, u: [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]
    sp = PX["strap_inner_px"]  # inside the lug zone the strap edges are the lug inner walls: top (rows <= lug_top_row .. bezel), bottom
    prof, sprof = [], []
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        r = int(math.floor(py0 - y * S))
        el, er = edge("left", r), edge("right", r)
        prof.append([round(float(y), 2), round((el - px0) / S, 3), round((er - px0) / S, 3)])
        if sp["top_lug_row"] <= r <= sp["bezel_top_row"]:
            el, er = lerp(sp["top"], sp.get("top_end", sp["top"]), (r - sp["top_lug_row"]) / (sp["bezel_top_row"] - sp["top_lug_row"]))
        elif sp["bezel_bottom_row"] <= r <= sp["bottom_lug_row"]:
            el, er = lerp(sp["bottom"], sp.get("bottom_end", sp["bottom"]), (r - sp["bezel_bottom_row"]) / (sp["bottom_lug_row"] - sp["bezel_bottom_row"]))
        sprof.append([round(float(y), 2), round((el - px0) / S, 3), round((er - px0) / S, 3)])
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    hands = {}
    for k in ("hour", "minute", "seconds"):
        h = PX["hands"][k]
        hands[k] = {"length_mm": round(h["length_px"] / S, 3), "angle_deg": h["angle_deg"], "tail_mm": round(h["tail_px"] / S, 3), "offset_mm": round(h.get("offset_px", 0.0) / S, 3)}

    flat = (im[..., :3] * alpha[..., None] + 128 * (1 - alpha[..., None])).astype(np.uint8)  # watch flattened on grey (window scan sees no transparency)
    g = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY)
    ap = PX["aperture"]
    rap = scan_aperture(g, px0, py0, ap)
    bo = PX["bezel_outer"]
    out = {"source": str(SRC.relative_to(ROOT)), "working": "native size (no enlargement)", "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "case width %s mm: the left flank of the case (median alpha edge over rows %d..%d = %.2f px) lies %s mm left of the pivot" % (CASE_MM, r0, r1, xl, CASE_MM / 2),
           "bezel_outer_mm": {"centre": mm(bo["centre_px"]), "half_axes": [round(bo["half_x_px"] / S, 3), round(bo["half_y_px"] / S, 3)], "exponent": bo["exponent"]},
           "aperture": {"n": len(rap), "face_edge_r_mm": [round(float(v) / S, 4) for v in rap], "chamfer_mm": round(ap["chamfer_px"] / S, 3),
                        "note": "radius from the pivot of the window edge of the brushed bezel face along n rays counter-clockwise from +x (angle 2 pi k / n); the dial window edge is chamfer_mm inside it"},
           "silhouette_y_left_right_mm": prof, "strap_y_left_right_mm": sprof,
           "bracelet": {"half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)],
                        "note": "rubber strap with an embossed grid pad (texture only): one piece from under the bezel to the rounded ends"},
           "hands": hands, "hub_radius_mm": [round(PX["hub_r_px"][0] / S, 3), round(PX["hub_r_px"][1] / S, 3)],
           "crowns": [{"name": c["name"], "base_mm": mm(c["base_px"]), "angle_deg": c["angle_deg"], "profile_mm": [[round(a / S, 3), round(b / S, 3)] for a, b in c["profile_px"]]} for c in PX["crowns"]]}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: native crop out to the window, centred on the sub-pixel pivot (pixel centres sit at integer index coordinates: continuous p -> p - 0.5)
    cxo = [px0 + float(rap[k]) * math.cos(2 * math.pi * k / len(rap)) for k in range(len(rap))]
    cyo = [py0 - float(rap[k]) * math.sin(2 * math.pi * k / len(rap)) for k in range(len(rap))]
    R = int(math.ceil(max(max(abs(x - px0) for x in cxo), max(abs(y - py0) for y in cyo)) + 4))
    crop = cv2.getRectSubPix(im[..., :3], (2 * R, 2 * R), (px0 - 0.5, py0 - 0.5))
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": "none (native)"}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch from the photo (native, composited on grey), projected on the case, bezel, crown and strap from the front
    cols = np.nonzero(fg.any(axis=0))[0]  # the watch's alpha bbox plus a 4 px margin
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    near_ = cv2.dilate(fg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # keep only the watch plus its 4 px rim (no drop shadow)
    a = (im[Y0:Y1, X0:X1, 3] * near_[Y0:Y1, X0:X1])[..., None] / 255.0
    steel = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    k = min(1.0, 2048.0 / steel.shape[0])  # mobile target: texture long side <= 2048 px (blue only; the green map is native 2179 px)
    if k < 1.0:
        steel = cv2.resize(steel, (round(steel.shape[1] * k), round(steel.shape[0] * k)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 90])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "scale": round(steel.shape[0] / (Y1 - Y0), 6), "upscale": "none (native, downscaled by %.4f to a 2048 px long side)" % k}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "hands", "bracelet", "crowns", "bezel_outer_mm")} | {"dial_map": meta, "silhouette_rows_mm": [y_lo, y_hi], "aperture_r_mm_range": [round(min(rap) / S, 2), round(max(rap) / S, 2)]}


if __name__ == "__main__":
    print(json.dumps(build()))
