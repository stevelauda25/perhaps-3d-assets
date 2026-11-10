"""Cut a clean dial map for the Orient Star RE-AU0107E from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.orient_re_au0107e_dial [out.jpg] [review.png]   # default outputs/watches/orient-re-au0107e/dial_photo.jpg

Same method as pipeline/seiko_sur419_dial.py. The sunburst centre and the ribbed rings are rotationally even and the minute
track repeats every 6 deg, so each hand pixel is copied from the same radius 6, 12, 18 ... deg away (first source that is
neither a hand nor a printed or applied part). Inside the power reserve the hands are cut tight (no shadow band) and filled by
rotating about the power reserve pivot, so the silver arc stays whole. Square map centred on the hand pivot, out to the
crystal ring, at the 2x working copy's resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-re-au0107e-trace.json"
OUT = ROOT / "outputs/watches/orient-re-au0107e/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.35
SHADOWS_MM = ((0.5, -0.5), (0.3, -0.3))  # light from the upper left
LOW_SIGMA_PX = 40
HUB_ZONE_MM = 1.3  # collar (0.87 mm) and the dark root facets of the hour and minute hands
PERIOD_DEG = 6
PR_PIVOT_PX = (1120, 1555)  # power reserve hand pivot (its arc is centred here)
PR_ARC_PX = (275, 45)  # silver arc: mean radius about the pivot, half width
PR_ARC_END_X = 1215  # the arc ends under the minute hand; dial beyond it
PR_ZERO_PX = (1310, 1640, 1352, 1690)  # the power reserve's 0 beside the minute hand


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + tuple(shadows):
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < HUB_ZONE_MM + margin
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            w0, w1 = h.get("half_width_root_mm", h.get("half_width_mm")), h.get("half_width_tip_mm", h.get("half_width_mm"))
            hw = w0 + (w1 - w0) * np.clip(along / (0.85 * h["length_mm"]), 0, 1)  # tapers from the root to the tip
            m |= (along > 0) & (along < h["length_mm"] + margin) & (across < hw + margin)
            m |= (along > -h["tail_mm"] - margin) & (along <= 0) & (across < h["tail_half_width_mm"] + margin)
    return m


def boxes(t, shape, keys, pad=12):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in keys:
        b = t[k]["x0_y0_x1_y1_mm"] if k in t else t["indices"][k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S) - pad, int(py0 - b[1] * S) - pad), (int(px0 + b[2] * S) + pad, int(py0 - b[3] * S) + pad), 1, -1)
    return m.astype(bool)


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = boxes(t, shape, ("date_window", "logo", "power_reserve", "print_6", "numeral_12", "numeral_6", "index_3", "index_9")).astype(np.uint8)
    ix = t["indices"]
    for hr in (1, 2, 4, 5, 7, 8, 10, 11):
        a = math.radians(hr * 30)
        p0 = (int(px0 + (ix["inner_mm"] - 0.3) * S * math.sin(a)), int(py0 - (ix["inner_mm"] - 0.3) * S * math.cos(a)))
        p1 = (int(px0 + (ix["outer_mm"] + 0.3) * S * math.sin(a)), int(py0 - (ix["outer_mm"] + 0.3) * S * math.cos(a)))
        cv2.line(m, p0, p1, 1, int((ix["width_mm"] + 0.8) * S))
    for hr in range(12):  # printed lume dots
        a = math.radians(hr * 30)
        cv2.circle(m, (int(px0 + ix["dot_r_mm"] * S * math.sin(a)), int(py0 - ix["dot_r_mm"] * S * math.cos(a))), int(0.7 * S), 1, -1)
    return m.astype(bool)


def fill(win, todo, bad, low, moves, centre):
    detail = win.astype(np.float32) - low
    used = {}
    for deg, sc in moves:
        rot = cv2.getRotationMatrix2D(centre, deg, sc)
        src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
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
        low = est if low is None else np.where(wgt > 0.2, est, low)
    return cv2.warpPolar(low, (w, h), centre, R, flags + cv2.WARP_INVERSE_MAP)


def streaks(win, clean, centre, seed=7):
    """Radial sunburst grain: noise per angle, stretched along the radius, scaled to the clean dial's fine detail."""
    h, w = win.shape[:2]
    R, NA = min(h, w) // 2, 2880
    rng = np.random.default_rng(seed)
    pol = cv2.GaussianBlur(rng.standard_normal((NA, R)).astype(np.float32), (0, 0), sigmaX=25, sigmaY=0.8)
    pol /= pol.std()
    cart = cv2.warpPolar(pol, (w, h), centre, R, cv2.INTER_LINEAR + cv2.WARP_POLAR_LINEAR + cv2.WARP_INVERSE_MAP)
    g = win.astype(np.float32)
    fine = g - cv2.GaussianBlur(g, (0, 0), 3)
    ring = clean & (np.hypot(*np.mgrid[0:h, 0:w] - np.array(centre)[::-1, None, None]) < 300)
    return cart[..., None] * fine[ring].std(0)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    yy, xx = np.mgrid[0:2 * R, 0:2 * R]
    cx, cy = PR_PIVOT_PX[0] - (px0 - R), PR_PIVOT_PX[1] - (py0 - R)
    arc = boxes(t, shape, ("power_reserve",), pad=0)[sl] & (np.abs(np.hypot(xx - cx, yy - cy) - PR_ARC_PX[0]) < PR_ARC_PX[1]) & (xx + px0 - R < PR_ARC_END_X)
    zero = np.zeros(shape, bool)
    zero[PR_ZERO_PX[1]:PR_ZERO_PX[3], PR_ZERO_PX[0]:PR_ZERO_PX[2]] = True
    prints = boxes(t, shape, ("logo", "print_6", "date_window"), pad=0)[sl] | arc | zero[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.12)[sl], hand_mask(t, shape)[sl])  # print the hand only grazes stays
    feats = feature_mask(t, shape)[sl]

    # power reserve arc first: rotate about its own pivot, sources on the arc only
    todo = mask & arc
    bad_pr = mask | ~arc
    used = fill(win, todo, bad_pr, lighting(win, bad_pr), [(s * k * 3.0, 1.0) for k in range(1, 12) for s in (1, -1)], (cx, cy))
    left_pr = int(todo.sum())
    # the rest of the dial: whole minute-track periods about the hand pivot
    todo = (mask & ~arc) | todo
    bad = mask | feats
    low = lighting(win, bad, (R, R))
    moves = [(sgn * k * PERIOD_DEG, 1.0) for k in range(1, 30) for sgn in (1, -1)]  # the hub zone keeps the smooth polar lighting
    used.update(fill(win, todo, bad, low, moves, (R, R)))
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo] + streaks(win, ~bad, (R, R))[todo], 0, 255).astype(np.uint8)
    # gradient-domain blend of the filled zones (not the power reserve arc): their brightness meets the clean dial at the edge
    zone = cv2.dilate((mask & ~arc).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    x, y, w, h = cv2.boundingRect(zone)
    win = cv2.seamlessClone(win, img[sl].copy(), zone, (x + w // 2, y + h // 2), cv2.NORMAL_CLONE)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "power_reserve_unfilled_px": left_pr, "lighting_only_px": unfilled,
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
