"""Cut the SPB335J1 photo map (dial, bezel insert and strap) from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_spb335_dial [out.jpg] [review.png]     # default outputs/watches/seiko-spb335j1/dial_photo.jpg

Same fill as pipeline/seiko_srpg18_dial.py: the minute track has 60 ticks, so each hand pixel is copied from the same radius
6, 12, 18 ... deg away (first source that is neither a hand nor an index or print), lighting from around the hand. Hand zones
are the traced outlines from config/watches/seiko-spb335j1-trace.json. No colour grading (one photo only). The white
background is turned near black so the strap edges carry no white fringe. One map for every photo part: the full photo
height (strap) by the case width, centred on the hand pivot, at the photo's own resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-spb335j1-trace.json"
OUT = ROOT / "outputs/watches/seiko-spb335j1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
BG = 235  # white background: brighter than this on all channels
HALF_WIDTH_MM = 21.0  # map x range: the case flanks
MARGIN_MM = 0.25
SHADOWS_MM = ((0.35, 0.0), (0.6, 0.0), (0.35, -0.3), (0.3, 0.45))  # shadows fall to the right of the hands
LOW_SIGMA_PX = 30
PERIOD_DEG = 6
HUB_LIGHTING_MM = 0.6


def polys_px(t):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    return S, P


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, P = polys_px(t)
    m = np.zeros(shape, np.uint8)
    sec = t["hands"]["seconds"]
    for dx, dy in ((0, 0),) + shadows:
        for h in t["hands"].values():
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in h["outline_mm"]]).astype(np.int32)], 1)
        for lp in sec["lume_mm"]:
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in lp]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P(sec["dot_centre_mm"], dx, dy)), int(sec["dot_radius_mm"] * S), 1, -1)
        for poly in t["extra_hand_mask_mm"]:
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in poly]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_radius_mm"][0] * S * 1.6), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=int(margin * S / 1.5)).astype(bool)


def feature_mask(t, shape, prints_only=False):
    """Indices and prints never used as a fill source (prints_only: the prints a hand may only graze)."""
    S, P = polys_px(t)
    m = np.zeros(shape, np.uint8)
    pad = 0 if prints_only else 12
    for k in ("logo_seiko", "logo_x", "print_automatic_divers", "date_window", "print_6"):
        b = t[k]["x0_y0_x1_y1_mm"]
        (x0, y0), (x1, y1) = P(b[:2]), P(b[2:])
        cv2.rectangle(m, (int(x0) - pad, int(y0) - pad), (int(x1) + pad, int(y1) + pad), 1, -1)
    if prints_only:
        return m.astype(bool)
    ix = t["indices"]
    for hr in range(1, 13):
        sh = ix["shapes_mm"]["12" if hr == 12 else "cardinal" if hr % 3 == 0 else "bar"]["outline"]
        a = math.radians(hr * 30)
        pts = [P((x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))) for x, y in sh]
        cv2.fillPoly(m, [np.round(pts).astype(np.int32)], 1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=pad // 2 or 1).astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    n, lab = cv2.connectedComponents((img >= BG).all(2).astype(np.uint8))
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = cv2.dilate(np.isin(lab, list(edge)).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=3).astype(bool)
    img[bg] = 20  # outside the watch: near black, like the strap edge (white numerals inside the bezel stay)
    R = int(math.ceil(t["rings_mm"]["dial_edge"] * S + 0.6 * S))  # hand fill works inside the minute track
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    prints = feature_mask(t, img.shape[:2], prints_only=True)
    mask = np.where(prints, hand_mask(t, img.shape[:2], (), 0.15), hand_mask(t, img.shape[:2]))[sl]
    bad = mask | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    c = (R, R)
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    used = {}
    yy, xx = np.mgrid[0:win.shape[0], 0:win.shape[1]]
    hub = np.hypot(xx - R, yy - R) <= HUB_LIGHTING_MM * S  # whole disc round the pivot (hand glints, rotated tails): lighting only
    hub &= ~feature_mask(t, img.shape[:2], prints_only=True)[sl]  # the Prospex X sits just below
    win[hub] = np.clip(low[hub], 0, 255).astype(np.uint8)
    todo &= ~hub
    mask |= hub
    for k in range(1, 15):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D(c, deg, 1.0)
            src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            used["%d deg" % deg] = int(take.sum())
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = img.copy()
    clean[sl] = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    W = int(round(HALF_WIDTH_MM * S))
    crop = clean[:, px0 - W:px0 + W]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = 0.5 + x / (2 half_w), v = 0.5 + (y - centre_y) / (2 half_h)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_w_mm": round(W / S, 4), "half_h_mm": round(crop.shape[0] / 2 / S, 4),
            "centre_y_mm": round((py0 - crop.shape[0] / 2) / S, 4), "size_px": list(crop.shape[1::-1]),
"masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from_deg": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, clean[sl]]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
