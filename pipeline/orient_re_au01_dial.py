"""Cut a clean dial map for the Orient Star RE-AU0108G / RE-AU0110N from the front photo, hands and their shadows removed.

    python3 -B -m pipeline.orient_re_au01_dial <sku> [review.png]     # -> outputs/watches/orient-re-<sku>/dial_photo.jpg

The dial is concentric (sunburst centre, grooved ring) and the minute track repeats every 6 deg, so each hand pixel is copied
from the same radius 6, 12, 18 ... deg away about the pivot over a polar lighting estimate (pipeline/orient_ra_wj0002l_dial.py);
the hub zone keeps the smooth lighting. Hand pixels on the power reserve crescent are copied from its mirror image about the
crescent's vertical axis first. Square map centred on the hand pivot out to the crystal ring, native resolution of Orient's
2000 px render, light unsharp mask, JPEG.
Hand outlines are the build's (config/watches/orient-re-<sku>-trace.json). Rebuild with --force after regenerating.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.orient_ra_wj0002l_dial import fill, lighting, streaks

ROOT = Path(__file__).resolve().parents[1]
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.2
SHADOWS_MM = ((0.15, -0.15), (0.3, -0.3))  # Orient's renders: short soft shadows right and down
PERIOD_DEG = 6
PLAIN_SUNBURST_MM = 9.4  # the grooved ring starts at 9.6 mm
STEEL_SAT = 60  # HSV saturation: steel hands below, copper dial about 90-115


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
    S, (px0, py0) = t["scale_px_per_mm"], t.get("hand_pivot_px", t["origin_px"])  # hands about their own pivot
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
    mask = np.where(keep.astype(bool), hand_mask(t, img.shape[:2], (), 0.05), mask)
    # both renders share one template and hand pose: the steel hands are the unsaturated pixels of the copper RE-AU0108G
    # render near the traced outlines (the grey RE-AU0110N dial cannot be told from steel by colour)
    ref = cv2.cvtColor(cv2.imread(str(ROOT / "references/orient-re-au0108g/front_official_2000x2000.webp")), cv2.COLOR_BGR2HSV)
    zone = hand_mask(t, img.shape[:2], SHADOWS_MM, 0.9) & ~feature_mask(t, img.shape[:2])
    steel = cv2.dilate(((ref[..., 1] < STEEL_SAT) & zone).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    mask = (mask | (steel & ~keep.astype(bool)))[sl]
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

    # 2) everything else: the same radius 6, 12, 18 ... deg away about the pivot (sunburst, grooved ring and minute track are
    #    concentric and the track repeats every 6 deg) over a polar lighting estimate; the hub zone keeps the smooth lighting
    low = lighting(win, bad, (R, R))
    plain = np.hypot(xx - R, yy - R) < PLAIN_SUNBURST_MM * S  # inside the grooved ring: plain sunburst, lighting plus grain
    ring = todo & ~plain
    fill(win, ring, bad, low, [(sg * k * PERIOD_DEG, 1.0) for k in range(1, 30) for sg in (1, -1)], (R, R))
    rest = ring | (todo & plain)
    rows_copied = int(rest.sum())
    win[rest] = np.clip(low[rest] + streaks(win, ~bad, (R, R))[rest], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "mirrored_on_crescent_px": mirrored, "lighting_only_px": rows_copied}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta, out


if __name__ == "__main__":
    meta, dest = build(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(meta, "->", dest)
