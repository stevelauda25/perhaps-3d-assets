"""Phase 1 for the ROLEX Explorer II 226570 (42 mm steel, white dial, fixed matt 24 h bezel, crown guards, date with Cyclops, 4 hands incl. the orange GMT hand, Oyster bracelet): trace JSON, dial and steel photo maps.
Variant-named copy of pipeline/rolex_explorer40_prep.py (untouched; same recipe and measure-file structure) with these changes:
  - file names: model name rolex-explorer2, key = normalized SKU (226570);
  - measure.anchor.right_px (optional): the scale is (right_px - left flank) / case_mm (the bezel outer width) instead of (pivot - left flank) / (case_mm / 2): the Explorer II bezel is not centred on the hand pivot;
  - measure.aperture.face / .window = {"centre_px", "half_px": [ax, ay]} (optional): two ellipses, the brushed bezel face inner edge (trace aperture.face_edge_r_mm) and the dial window = outer edge of the rehaut ring
    (trace aperture.window_r_mm), both as polar radii from the pivot along n rays (the polished bevel between them is the chamfer; the old measure.aperture.circle / scan path still works);
  - hands: every key of measure.hands (hour, minute, seconds and any extra hand such as the GMT hand) becomes trace.hands[name].outline_mm: the GMT-style 24 h hand is just one more polygon.
Run:
    python3 -B -m pipeline.rolex_explorer2_prep <key>          # key = 226570
        reads    config/watches/rolex-explorer2-<key>-measure.json (YOU measure the photo; names measure.reference_dir) and the one rolex-*_original.* in that folder (untouched)
        writes   config/watches/rolex-explorer2-<key>-trace.json, outputs/watches/rolex-explorer2-<key>/{dial_photo,steel_photo}.jpg (+ .json)
mm, x right, y toward 12, origin = hand pivot; the silhouette is the largest alpha component above half.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KEY = (sys.argv[1] if len(sys.argv) > 1 else "224270").lower()
NAME = "rolex-explorer2-%s" % KEY
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)
PX = json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text())
REF = ROOT / PX["reference_dir"]
SRC = next(REF.glob("rolex-*_original.*"))
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


def load_source():
    """BGRA working image: native RGBA, or (no alpha) the enlarged RGB with a flood-fill silhouette mask."""
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    assert im is not None
    k = float(PX.get("upscale", 1))
    if k != 1:
        im = cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_LANCZOS4)
    if im.ndim == 3 and im.shape[2] == 4:
        return im
    bgr = im if im.ndim == 3 else cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    tol = int(PX["mask"]["bg_tol"])
    h, w = bgr.shape[:2]
    pad = cv2.copyMakeBorder(bgr, 1, 1, 1, 1, cv2.BORDER_REPLICATE)
    mask = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(pad, mask, (0, 0), (0, 0, 0), (tol,) * 3, (tol,) * 3, cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | 8 | (255 << 8))  # fixed range: compare with the white seed, so the soft edge cannot creep into the watch
    bg = mask[2:-2, 2:-2] > 0  # border-connected near-white background (holes inside the watch stay foreground)
    fg = (~bg).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    a = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 0.8)  # soft 1 px edge
    return np.dstack([bgr, (a * 255).astype(np.uint8)])


def build():
    im = load_source()
    px0, py0 = PX["pivot"]  # continuous working px (hand pivot = centre of the small hub)
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
    if "right_px" in PX["anchor"]:  # bezel outer width = case_mm (the bezel is not centred on the pivot)
        S = (PX["anchor"]["right_px"] - xl) / CASE_MM
    else:
        S = (px0 - xl) / (CASE_MM / 2)  # the left flank of the case is half the case width from the pivot
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]

    rows = np.nonzero(fg.any(axis=1))[0]  # alpha extent of the watch (bracelet ends) sets the silhouette row range, 2 px inside the ends
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
    prof = []
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        r = int(math.floor(py0 - y * S))
        prof.append([round(float(y), 2), round((edge("left", r) - px0) / S, 3), round((edge("right", r) - px0) / S, 3)])
    hands = {}
    for k in PX["hands"]:
        h = PX["hands"][k]
        hands[k] = {"outline_mm": [[round(x / S, 3), round(y / S, 3)] for x, y in h["polygon_px"]], "note": h.get("note", "")}

    # bracelet: rows (outer links) as [near, far] mm from the pivot per side, centre pieces as y near / far, x left / right, corner radius (mm)
    br = PX["bracelet"]
    rows_mm = {"top": [[round((py0 - b) / S, 3), round((py0 - a) / S, 3)] for a, b in br["rows_px"]["top"]],
               "bottom": [[round((a - py0) / S, 3), round((b - py0) / S, 3)] for a, b in br["rows_px"]["bottom"]]}
    pieces_mm = []
    for p in br["pieces_px"]:
        near, far = ((py0 - p["y1"]) / S, (py0 - p["y0"]) / S) if p["side"] == "top" else ((p["y0"] - py0) / S, (p["y1"] - py0) / S)
        pieces_mm.append({"side": p["side"], "y_mm": [round(near, 3), round(far, 3)], "x_mm": [round((p["x0"] - px0) / S, 3), round((p["x1"] - px0) / S, 3)], "r_mm": round(p["r"] / S, 3)})

    flat = (im[..., :3] * alpha[..., None] + 128 * (1 - alpha[..., None])).astype(np.uint8)  # watch flattened on grey (window scan sees no transparency)
    g = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY)
    ap = PX["aperture"]
    def ellipse_r(e):  # polar radius from the pivot to the ellipse (centre, half axes) along n rays: positive root of the ray / ellipse equation
        (ex, ey), (ax, ay) = e["centre_px"], e["half_px"]
        out_ = []
        for k in range(int(ap["n"])):
            a = 2 * math.pi * k / int(ap["n"])
            ux, uy = math.cos(a), -math.sin(a)  # image y is down
            x0, y0 = px0 - ex, py0 - ey
            A = (ux / ax) ** 2 + (uy / ay) ** 2
            B = 2 * (x0 * ux / ax ** 2 + y0 * uy / ay ** 2)
            C = (x0 / ax) ** 2 + (y0 / ay) ** 2 - 1
            out_.append((-B + math.sqrt(B * B - 4 * A * C)) / (2 * A))
        return np.array(out_)
    if "face" in ap:  # brushed face inner edge and the rehaut outer edge (window) as two ellipses
        rap = ellipse_r(ap["face"])
        rwin = ellipse_r(ap["window"])
    elif "circle" in ap:  # bezel inner edge = fitted circle; radius from the pivot along n rays
        ccx, ccy = ap["circle"]["centre_px"]
        rr = ap["circle"]["r_px"]
        rap = np.array([max(t for t in np.arange(rr - 40, rr + 40, 0.05) if math.hypot(px0 + t * math.cos(a) - ccx, py0 - t * math.sin(a) - ccy) <= rr)
                        for a in (2 * math.pi * k / int(ap["n"]) for k in range(int(ap["n"])))])
        rwin = rap - ap["chamfer_px"]
    else:
        rap = scan_aperture(g, px0, py0, ap, int(ap.get("n", 720)))
        rwin = rap - ap["chamfer_px"]
    bo = PX["bezel_outer"]
    out = {"source": str(SRC.relative_to(ROOT)), "working": "native size (no enlargement)" if PX.get("upscale", 1) == 1 else "Lanczos x%s of the source" % PX["upscale"],
           "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": ("case width %s mm = bezel outer width: left flank (median alpha edge over rows %d..%d = %.2f px) to the right bezel edge (%.1f px)" % (CASE_MM, r0, r1, xl, PX["anchor"]["right_px"])
                     if "right_px" in PX["anchor"] else
                     "case width %s mm: the left flank of the case (median alpha edge over rows %d..%d = %.2f px) lies %s mm left of the pivot" % (CASE_MM, r0, r1, xl, CASE_MM / 2)),
           "bezel_outer_mm": {"centre": mm(bo["centre_px"]), "half_axes": [round(bo["half_x_px"] / S, 3), round(bo["half_y_px"] / S, 3)], "exponent": bo["exponent"], "bevel_mm": round(bo.get("bevel_px", 0) / S, 3)},
           "aperture": {"n": len(rap), "face_edge_r_mm": [round(float(v) / S, 4) for v in rap], "window_r_mm": [round(float(v) / S, 4) for v in rwin], "chamfer_mm": round(ap["chamfer_px"] / S, 3),
                        "note": "radii from the pivot along n rays counter-clockwise from +x (angle 2 pi k / n): face_edge = inner edge of the brushed bezel face, window_r = outer edge of the rehaut ring (dial window); the polished bevel between them is the chamfer"},
           "silhouette_y_left_right_mm": prof, "strap_y_left_right_mm": prof,
           "bracelet": {"rows_mm": rows_mm, "pieces_mm": pieces_mm, "note": "brushed outer-link rows (edges = silhouette) and polished centre pieces (rounded rectangles); y = mm from the pivot, near / far"},
           "hands": hands, "hub_radius_mm": [round(PX["hub_r_px"][0] / S, 3), round(PX["hub_r_px"][1] / S, 3)],
           "crowns": [{"name": c["name"], "base_mm": mm(c["base_px"]), "angle_deg": c["angle_deg"], "profile_mm": [[round(a / S, 3), round(b / S, 3)] for a, b in c["profile_px"]]} for c in PX["crowns"]]}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: crop out to the window, centred on the sub-pixel pivot (pixel centres sit at integer index coordinates: continuous p -> p - 0.5)
    rmax = np.maximum(rap, rwin)
    cxo = [px0 + float(rmax[k]) * math.cos(2 * math.pi * k / len(rap)) for k in range(len(rap))]
    cyo = [py0 - float(rmax[k]) * math.sin(2 * math.pi * k / len(rap)) for k in range(len(rap))]
    R = int(math.ceil(max(max(abs(x - px0) for x in cxo), max(abs(y - py0) for y in cyo)) + 4))
    crop = cv2.getRectSubPix(im[..., :3], (2 * R, 2 * R), (px0 - 0.5, py0 - 0.5))
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, 93])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": "none (native)" if PX.get("upscale", 1) == 1 else "x%s" % PX["upscale"]}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch from the photo (composited on grey), projected on the case, bezel, crown and bracelet from the front; capped at steel_max_px (long side)
    cols = np.nonzero(fg.any(axis=0))[0]  # the watch's alpha bbox plus a 4 px margin
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    near_ = cv2.dilate(fg.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # keep only the watch plus its 4 px rim (no drop shadow)
    a = (im[Y0:Y1, X0:X1, 3] * near_[Y0:Y1, X0:X1])[..., None] / 255.0
    steel = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    ks = min(1.0, PX.get("steel_max_px", 2048) / max(steel.shape[:2]))
    if ks < 1.0:
        steel = cv2.resize(steel, (round(steel.shape[1] * ks), round(steel.shape[0] * ks)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, PX.get("steel_quality", 90)])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [steel.shape[1], steel.shape[0]], "scale": round(ks, 5), "upscale": "none (native, capped at %d px)" % PX.get("steel_max_px", 2048)}) + "\n")
    return {k: out[k] for k in ("scale_px_per_mm", "bracelet", "crowns", "bezel_outer_mm")} | {"dial_map": meta, "steel_map": [steel.shape[1], steel.shape[0], round(ks, 4)], "silhouette_rows_mm": [y_lo, y_hi],
                                                                                                           "aperture_r_mm_range": [round(min(rap) / S, 2), round(max(rap) / S, 2)], "window_r_mm_range": [round(min(rwin) / S, 2), round(max(rwin) / S, 2)]}


if __name__ == "__main__":
    print(json.dumps(build()))
