"""Phase 1 for the PATEK PHILIPPE Cubitus 5821/1A (45 mm steel case, green embossed dial, steel bracelet; catalog 2 row 103): trace JSON, dial and steel photo maps.
Copy of pipeline/patek_aquanaut42_prep.py (untouched; the Aquanaut 5168G prep) with these changes for the Cubitus:
  - the scale is anchored on BOTH flanks of the 45 mm case (measure.anchor: left_rows, right_rows = row ranges of the median sub-pixel alpha edge): S = (right - left) / case_mm (the photo is not centred on the pivot);
  - the window (face edge of the bezel) is a traced polygon too (measure.aperture.polygon_px, rays from the pivot; the scan of the Aquanaut prep remains as the fallback);
  - the bezel outer edge is a measured polygon (measure.bezel_outer.polygon_px, the rounded octagon with corner chamfers), written to the trace as bezel_outer_mm.polygon_mm; the step samples it by rays;
  - crown rows are replaced by the right flank line (x0 / x1 may be "right_flank");
  - the bracelet is steel with joints measured per side (the step spec lists them): the strap outline is the silhouette itself (no lug inner walls, no flare lines);
  - the steel map is downscaled to 2048 px on the long side (mobile target; steel_photo.json "scale" = map px per photo px), the dial map is a native crop.

    python3 -B -m pipeline.patek_cubitus45_prep [key]            # key = 58211a (reference folder references/patek-cubitus-5821-1a, config files patek-cubitus45-<key>-*)
        reads    references/patek-cubitus-5821-1a/patek-<key>_original.png (untouched) and config/watches/patek-cubitus45-<key>-measure.json (YOU measure the photo)
        writes   config/watches/patek-cubitus45-<key>-trace.json, outputs/watches/patek-cubitus45-<key>/{dial_photo,steel_photo}.jpg (+ .json)

mm, x right, y toward 12, origin = hand pivot; the silhouette is the largest alpha component above half. All pixel positions are CONTINUOUS photo coordinates.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KEY = (sys.argv[1] if len(sys.argv) > 1 else "58211a").lower()
MODEL = {"ref": "patek-cubitus-5821-1a", "name": "patek-cubitus45"}
NAME = "%s-%s" % (MODEL["name"], KEY)
REF = ROOT / ("references/%s" % MODEL["ref"])
SRC = REF / ("patek-%s_original.png" % KEY)
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


def poly_rays(poly, px0, py0, n=720):
    """Distance (px) from the pivot to the closed polygon (continuous photo px, y down) along n equal angles, counter-clockwise from +x on screen (furthest hit)."""
    segs = list(zip(poly, poly[1:] + poly[:1]))
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        dx, dy = math.cos(a), -math.sin(a)
        best = 0.0
        for (x1, y1), (x2, y2) in segs:
            x1, y1, x2, y2 = x1 - px0, y1 - py0, x2 - px0, y2 - py0
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = (x1 * ey - y1 * ex) / den
            u = (x1 * dy - y1 * dx) / den
            if t > 0 and -1e-9 <= u <= 1 + 1e-9:
                best = max(best, t)
        out.append(best)
    return np.array(out)


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
    an = PX["anchor"]
    xl = float(np.median([left(r) for r in range(an["left_rows"][0], an["left_rows"][1] + 1)]))
    xr = float(np.median([right(r) for a_, b_ in an["right_rows"] for r in range(a_, b_ + 1)]))
    S = (xr - xl) / CASE_MM  # both flanks of the 45 mm case
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (strap ends) sets the silhouette row range, 2 px inside the ends
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    repl = []
    for c in PX["crown_replace"]:
        c = dict(c)
        for k in ("x0", "x1"):
            if c[k] == "right_flank":
                c[k] = xr
        repl.append(c)

    def edge(side, r):  # silhouette edge of row r (px); crown rows follow the replacement lines
        for c in repl:
            if c["side"] == side and c["y0"] <= r <= c["y1"]:
                return c["x0"] + (c["x1"] - c["x0"]) * (r - c["y0"]) / (c["y1"] - c["y0"])
        return left(r) if side == "left" else right(r)
    prof = []
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        r = int(math.floor(py0 - y * S))
        el, er = edge("left", r), edge("right", r)
        prof.append([round(float(y), 2), round((el - px0) / S, 3), round((er - px0) / S, 3)])
    sprof = prof  # steel bracelet: the strap outline is the silhouette
    half = {p[0]: (p[2] - p[1]) / 2 for p in prof}
    hands = {}
    for k in ("hour", "minute", "seconds"):
        h = PX["hands"][k]
        hands[k] = {"length_mm": round(h["length_px"] / S, 3), "angle_deg": h["angle_deg"], "tail_mm": round(h["tail_px"] / S, 3)}

    flat = (im[..., :3] * alpha[..., None] + 128 * (1 - alpha[..., None])).astype(np.uint8)  # watch flattened on grey (window scan sees no transparency)
    g = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY)
    ap = PX["aperture"]
    rap = poly_rays([tuple(p) for p in ap["polygon_px"]], px0, py0, ap["n"]) if "polygon_px" in ap else scan_aperture(g, px0, py0, ap)
    bo = PX["bezel_outer"]
    out = {"source": str(SRC.relative_to(ROOT)), "working": "native size (no enlargement)", "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": "case width %s mm = right flank %.2f px - left flank %.2f px (median alpha edges, see measure.anchor)" % (CASE_MM, xr, xl),
           "bezel_outer_mm": {"polygon_mm": [mm(p) for p in bo["polygon_px"]]},
           "aperture": {"n": len(rap), "face_edge_r_mm": [round(float(v) / S, 4) for v in rap], "chamfer_mm": round(ap["chamfer_px"] / S, 3),
                        "note": "radius from the pivot of the window edge of the brushed bezel face along n rays counter-clockwise from +x (angle 2 pi k / n); the dial window edge is chamfer_mm inside it"},
           "silhouette_y_left_right_mm": prof, "strap_y_left_right_mm": sprof,
           "bracelet": {"half_width_end_mm": [round(half[y_hi], 3), round(half[y_lo], 3)],
                        "note": "steel bracelet: link pieces between measured joints (spec strap.pieces_mm), outline = silhouette; polished inserts / brushed links are texture"},
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
    k = min(1.0, 2048.0 / max(steel.shape[:2]))  # mobile target: textures <= 2048 px on the long side (INTER_AREA); `scale` = map px per photo px
    if k < 1.0:
        steel = cv2.resize(steel, (int(round(steel.shape[1] * k)), int(round(steel.shape[0] * k))), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, 90])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "scale": round(steel.shape[0] / (Y1 - Y0), 6), "upscale": "none" if k == 1.0 else "none (native photo pixels, downscaled by %.4f to 2048 px long side)" % k}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "hands", "bracelet", "crowns")} | {"dial_map": meta, "silhouette_rows_mm": [y_lo, y_hi], "aperture_r_mm_range": [round(min(rap) / S, 2), round(max(rap) / S, 2)]}


if __name__ == "__main__":
    print(json.dumps(build()))
