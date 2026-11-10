"""Cut a clean dial map for the Orient RA-AC0E01B10B from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.orient_ra_ac0e01b10b_dial [out.jpg] [review.png]   # default outputs/watches/orient-ra-ac0e01b10b/dial_photo.jpg

Same method as pipeline/orient_ra_ac0q17y_dial.py: the black dial is rotationally even and the minute track repeats every
6 deg, so each hand pixel is copied from the same radius 6, 12, 18 ... deg away over a lighting estimate made in polar
coordinates; the hub zone keeps the lighting with a fine grain, and the filled zones are blended in the gradient domain.
Square map centred on the hand pivot, out to the polished bezel's inner edge, at the 2x working copy's resolution, light
unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-ra-ac0e01b10b-trace.json"
OUT = ROOT / "outputs/watches/orient-ra-ac0e01b10b/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.35
SHADOWS_MM = ((0.45, -0.45), (0.25, -0.25))  # light from the upper left
LOW_SIGMA_PX = 40
HUB_ZONE_MM = 1.0  # collar (0.93 mm)
PERIOD_DEG = 6


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    hs = t["hands"]
    m = np.zeros(shape, bool)

    def axes(h, x, y):
        ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
        return x * ux + y * uy, np.abs(-x * uy + y * ux)

    for dx, dy in ((0, 0),) + tuple(shadows):
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < HUB_ZONE_MM + margin
        for name in ("hour", "minute"):  # tapered stick to a point
            h = hs[name]
            al, ac = axes(h, x, y)
            L, (w0, w1) = h["length_mm"], h["half_width_mm"]
            hw = np.where(al < L - 1.0, w0 + (w1 - w0) * al / (L - 1.0), w1 * (L - al))
            m |= (al > -h["tail_mm"] - margin) & (al < L + margin) & (ac < np.maximum(hw, 0) + 1.5 * margin)
        h = hs["seconds"]
        al, ac = axes(h, x, y)
        m |= (al > 0) & (al < h["length_mm"] + margin) & (ac < h["half_width_mm"] + margin)
        m |= (al > -h["tail_mm"] - margin) & (al <= 0.2) & (ac < h["tail_half_width_mm"] + margin)
    return m


def boxes(t, shape, keys, pad=12):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in keys:
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S) - pad, int(py0 - b[1] * S) - pad), (int(px0 + b[2] * S) + pad, int(py0 - b[3] * S) + pad), 1, -1)
    return m.astype(bool)


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = boxes(t, shape, ("date_window", "logo", "print_6")).astype(np.uint8)
    ix = t["indices"]
    for hr in range(1, 13):
        a = math.radians(hr * 30)
        r0, r1 = ix["at_3"] if hr == 3 else (ix["inner_mm"], ix["outer_mm"])
        p0 = (int(px0 + (r0 - 0.4) * S * math.sin(a)), int(py0 - (r0 - 0.4) * S * math.cos(a)))
        p1 = (int(px0 + (r1 + 0.4) * S * math.sin(a)), int(py0 - (r1 + 0.4) * S * math.cos(a)))
        cv2.line(m, p0, p1, 1, int((ix["width_mm"] + 0.8) * S))
    return m.astype(bool)


def fill(win, todo, bad, low, moves, centre):
    detail = win.astype(np.float32) - low
    used = {}
    good = cv2.erode((~bad).astype(np.uint8), np.ones((5, 5), np.uint8))  # linear sampling next to a hand would pull its dark edge in
    for deg, sc in moves:
        rot = cv2.getRotationMatrix2D(centre, deg, sc)
        src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ok = cv2.warpAffine(good, rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
        take = todo & ok
        win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
        todo &= ~take
        used["%+.0f deg x%.0f" % (deg, 1 / sc)] = int(take.sum())
        if not todo.any():
            break
    return used


def lighting(win, bad, centre=None):
    """Smooth lighting under the hand zones. With a centre: estimated in polar coordinates about it, blurred along the angle
    (narrow) and the radius (wide), so the sunburst's bright and dark sectors carry across a hand instead of smearing."""
    valid = (~bad).astype(np.float32)
    if centre is None:
        low = None
        for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):
            wgt = cv2.GaussianBlur(valid[..., None], (0, 0), sig)[..., None]
            est = cv2.GaussianBlur(win.astype(np.float32) * valid[..., None], (0, 0), sig) / np.maximum(wgt, 1e-4)
            low = est if low is None else np.where(wgt > 0.15, est, low)
        return low
    h, w = win.shape[:2]
    R, NA = min(h, w) // 2, 2880  # out to the crystal ring (the corners are not needed)
    flags = cv2.INTER_LINEAR + cv2.WARP_POLAR_LINEAR
    pw = np.nan_to_num(cv2.warpPolar(win.astype(np.float32), (R, NA), centre, R, flags))
    pv = cv2.warpPolar(valid, (R, NA), centre, R, flags)[..., None]
    pad = NA // 4  # wrap around 360 deg
    wrap = lambda a: np.concatenate([a[-pad:], a, a[:pad]])
    low = None
    for sig_a, sig_r in ((240, 60), (64, 24), (16, 8)):  # wide first, then narrower where enough clean pixels are near
        wgt = cv2.GaussianBlur(wrap(pv), (0, 0), sigmaX=sig_r, sigmaY=sig_a)[pad:-pad][..., None]
        est = cv2.GaussianBlur(wrap(pw * pv), (0, 0), sigmaX=sig_r, sigmaY=sig_a)[pad:-pad] / np.maximum(wgt, 1e-4)
        a = np.clip((wgt - 0.1) / 0.3, 0, 1)  # soft hand-over: a hard threshold leaves a ring around the hub
        low = est if low is None else a * est + (1 - a) * low
    return cv2.warpPolar(low, (w, h), centre, R, flags + cv2.WARP_INVERSE_MAP)


def grain(win, clean, centre, seed=7):
    """Fine sand grain (the dial is grained, not brushed), scaled to the clean dial's fine detail near the hub."""
    h, w = win.shape[:2]
    noise = cv2.GaussianBlur(np.random.default_rng(seed).standard_normal((h, w)).astype(np.float32), (0, 0), 0.9)
    noise /= noise.std()
    g = win.astype(np.float32)
    fine = g - cv2.GaussianBlur(g, (0, 0), 3)
    ring = clean & (np.hypot(*np.mgrid[0:h, 0:w] - np.array(centre)[::-1, None, None]) < 300)
    return noise[..., None] * fine[ring].std(0)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["rings_mm"]["crystal"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "print_6", "date_window"), pad=0)[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.12)[sl], hand_mask(t, shape)[sl])  # print the hand only grazes stays
    feats = feature_mask(t, shape)[sl]
    # the rest of the dial: whole minute-track periods about the hand pivot
    todo = mask.copy()
    bad = mask | feats
    low = lighting(win, bad, (R, R))
    moves = [(sgn * k * PERIOD_DEG, 1.0) for k in range(1, 30) for sgn in (1, -1)]  # the hub zone keeps the smooth polar lighting
    used = fill(win, todo, bad, low, moves, (R, R))
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo] + grain(win, ~bad, (R, R))[todo], 0, 255).astype(np.uint8)
    # gradient-domain blend of the filled zones: their brightness meets the clean dial at the edge
    zone = cv2.dilate(mask.astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    x, y, w, h = cv2.boundingRect(zone)
    win = cv2.seamlessClone(win, img[sl].copy(), zone, (x + w // 2, y + h // 2), cv2.NORMAL_CLONE)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled,
            "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
