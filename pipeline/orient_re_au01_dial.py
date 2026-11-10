"""Cut a clean dial map for the Orient Star RE-AU0108G / RE-AU0110N from the front photo, hands and their shadows removed.

    python3 -B -m pipeline.orient_re_au01_dial <sku> [review.png]     # -> outputs/watches/orient-re-<sku>/dial_photo.jpg

The dial is concentric (sunburst centre, grooved ring), so in polar coordinates about the pivot each radius is interpolated
across the hand's angles from the clean dial on both sides (not printed or applied parts); inside the hub one flat colour.
Hand pixels on the power reserve crescent are copied from its mirror image about the crescent's vertical axis first.
Square map centred on the hand pivot out to the crystal ring, 2x working copy, light unsharp mask, JPEG.
Hand outlines are the build's (config/watches/orient-re-<sku>-trace.json). Rebuild with --force after regenerating.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.3
SHADOWS_MM = ((0.3, -0.3), (0.55, -0.55), (0.8, -0.75), (1.05, -0.95), (1.3, -1.1), (-0.3, 0.3), (-0.5, 0.5))  # light from the upper left: shadows fall right and down (seconds up to 1 mm)


def hand_polys(t):
    """Hand outlines in mm (same shapes as the build step)."""
    h = t["hands"]
    out = []
    for name in ("hour", "minute"):
        hd = h[name]
        L, tail, w, nk = hd["length_mm"], hd["tail_mm"], hd["half_width_mm"], hd["neck_half_width_mm"]
        half = [(0, -tail), (0.5 * nk, -0.5 * tail), (nk, 0), (nk, 1.0), (w, 1.4), (0, L)]
        out.append((half + [(-x, y) for x, y in half[::-1][1:-1]], hd["angle_deg"], (0, 0)))
    s = h["seconds"]
    nw, cw, L, tail = s["half_width_mm"], s["counterweight_half_width_mm"], s["length_mm"], s["tail_mm"]
    out.append(([(nw, 0), (nw, L), (-nw, L), (-nw, 0)], s["angle_deg"], (0, 0)))
    out.append(([(0, 0), (cw, -0.6), (cw, -tail + 0.4), (0, -tail), (-cw, -tail + 0.4), (-cw, -0.6)], s["angle_deg"], (0, 0)))
    p = h["pr"]
    pw, L = p["half_width_mm"], p["length_mm"]
    out.append(([(pw, 0), (pw * 0.35, L), (-pw * 0.35, L), (-pw, 0)], p["angle_deg"], tuple(p["pivot_mm"])))
    return out


def rot(x, y, deg):
    t = math.radians(deg)
    return (x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda x, y: (px0 + x * S, py0 - y * S)
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + tuple(shadows):
        for poly, deg, (cx, cy) in hand_polys(t):
            pts = [P(cx + rx + dx, cy + ry + dy) for rx, ry in (rot(x, y, deg) for x, y in poly)]
            cv2.fillPoly(m, [np.round(np.array(pts) * 4).astype(np.int32)], 1, shift=2)
        for (cx, cy), r in (((0, 0), t["hub_radius"] + 0.25), (tuple(t["hands"]["pr"]["pivot_mm"]), t["pr_cap_radius"])):
            cv2.circle(m, tuple(int(v) for v in P(cx + dx, cy + dy)), int(r * S), 1, -1)
    k = int(2 * margin * t["scale_px_per_mm"]) | 1
    return cv2.dilate(m, np.ones((k, k), np.uint8)).astype(bool)


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda x, y: (int(px0 + x * S), int(py0 - y * S))
    m = np.zeros(shape, np.uint8)
    for k in ("date_window", "logo_box", "print_6_box"):
        b = t[k]
        cv2.rectangle(m, P(b[0] - 0.3, b[1] - 0.3), P(b[2] + 0.3, b[3] + 0.3), 1, -1)
    for k in ("numeral_12", "numeral_6"):
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, P(b[0] - 0.3, b[3] + 0.3), P(b[2] + 0.3, b[1] - 0.3), 1, -1)
    ix = t["indices"]
    for hr in range(1, 13):
        a = math.radians(hr * 30)
        r0, r1, w = {3: (ix["at_3"]["inner"], ix["at_3"]["outer"], ix["at_3"]["width"]),
                     9: (ix["at_9"]["inner"], ix["at_9"]["outer"], ix["at_9"]["width"])}.get(hr, (ix["inner"], ix["outer"], ix["width"]))
        cv2.line(m, P((r0 - 0.4) * math.sin(a), (r0 - 0.4) * math.cos(a)), P((r1 + 1.2) * math.sin(a), (r1 + 1.2) * math.cos(a)), 1,
                 int((w + 0.8) * S))  # baton and its lume dot
    pa = t["pr_arc"]
    cv2.ellipse(m, P(*pa["centre"]), (int((pa["r_out"] + 0.4) * S),) * 2, 0, pa["from_deg"] - 95, pa["to_deg"] - 85, 1, -1)
    cv2.circle(m, P(*pa["centre"]), int((pa["r_in"] - 0.3) * S), 0, -1)  # inside the crescent is plain dial again
    for b in t["pr_print_boxes"]:
        cv2.rectangle(m, P(b[0] - 0.2, b[3] + 0.2), P(b[2] + 0.2, b[1] - 0.2), 1, -1)
    return m.astype(bool)


PLAIN_SUNBURST_MM = 9.6  # plain sunburst inside the grooved ring
RADIUS_MM = [17.2]  # map half size in mm (set by build)


def polar_fill(win, todo, bad, R):
    """Fill `todo` by linear interpolation along the angle at each radius between the nearest clean (not `bad`) samples.
    Radii with no clean sample (inside the hub) take the nearest clean radius outward."""
    n_r, n_a = R, int(2 * math.pi * R)
    flags = cv2.WARP_POLAR_LINEAR
    pol = cv2.warpPolar(win, (n_r, n_a), (R, R), R, flags | cv2.INTER_LINEAR).astype(np.float32)
    ok = cv2.warpPolar((~bad).astype(np.uint8) * 255, (n_r, n_a), (R, R), R, flags | cv2.INTER_NEAREST) > 127
    ok &= cv2.warpPolar((~todo).astype(np.uint8) * 255, (n_r, n_a), (R, R), R, flags | cv2.INTER_NEAREST) > 127
    ang = np.arange(n_a)
    inner = None
    for j in range(n_r):  # inside the hub nearly every angle is a hand: one flat colour from the first mostly clean radius
        if ok[:, j].mean() > 0.12:
            inner = j
            break
    flat = np.median(pol[ok[:, inner], inner], axis=0)
    for j in range(n_r):
        idx = np.nonzero(ok[:, j])[0]
        if j < inner:
            pol[:, j] = flat
            continue
        for ch in range(3):
            pol[:, j, ch] = np.interp(ang, idx, pol[idx, j, ch], period=n_a)
    # soften the per-radius banding in the plain sunburst (the grooved ring outside keeps its sharp radii)
    plain = int(PLAIN_SUNBURST_MM * R / RADIUS_MM[0])
    pol[:, :plain] = cv2.GaussianBlur(pol[:, :plain], (0, 0), sigmaX=6, sigmaY=0.1)
    copied = inner
    back = cv2.warpPolar(pol, (2 * R, 2 * R), (R, R), R, flags | cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    return np.clip(back, 0, 255).astype(np.uint8), copied


def build(sku, review=None):
    t = json.loads((ROOT / f"config/watches/orient-re-{sku}-trace.json").read_text())
    out = ROOT / f"outputs/watches/orient-re-{sku}/dial_photo.jpg"
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    mask = hand_mask(t, img.shape[:2])
    S_ = lambda x, y: (int(px0 + x * S), int(py0 - y * S))
    keep = np.zeros(mask.shape, np.uint8)  # prints a hand or its shadow only grazes: mask the bare hand there, keep the print
    for b in [t[k] for k in ("pr_zero_box", "logo_box", "print_6_box", "date_window")] + [t[k]["x0_y0_x1_y1_mm"] for k in ("numeral_12", "numeral_6")]:
        cv2.rectangle(keep, S_(b[0], max(b[1], b[3])), S_(b[2], min(b[1], b[3])), 1, -1)
    mask = np.where(keep.astype(bool), hand_mask(t, img.shape[:2], (), 0.05), mask)[sl]
    bad = mask | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()

    # 1) hand pixels on the power reserve crescent: mirror about the crescent's vertical axis
    pa = t["pr_arc"]
    yy, xx = np.mgrid[0:2 * R, 0:2 * R]
    acx, acy = R + pa["centre"][0] * S, R - pa["centre"][1] * S
    rr = np.hypot(xx - acx, yy - acy) / S
    th = np.degrees(np.arctan2(xx - acx, acy - yy)) % 360
    on_arc = (rr > pa["r_in"] - 0.1) & (rr < pa["r_out"] + 0.1) & (th > pa["from_deg"] - 3) & (th < pa["to_deg"] + 3)
    mx = np.clip(np.round(2 * acx - xx).astype(int), 0, 2 * R - 1)
    take = todo & on_arc & ~mask[yy, mx]
    win[take] = win[yy[take], mx[take]]
    todo &= ~take
    mirrored = int(take.sum())

    # 2) everything else: in polar coordinates about the pivot, interpolate each radius across the masked angles from the
    #    clean dial on both sides (the sunburst, grooved ring and track are concentric, so they continue along the angle)
    RADIUS_MM[0] = R / S
    filled, rows_copied = polar_fill(win, todo, bad, R)
    win[todo] = filled[todo]
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "mirrored_on_crescent_px": mirrored, "radii_without_clean_dial": rows_copied}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta, out


if __name__ == "__main__":
    meta, dest = build(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(meta, "->", dest)
