"""Cut the SNA411P1 photo maps from the straightened photo: dial + bezel insert (hands removed) and the NATO strap atlas.

    python3 -B -m pipeline.seiko_sna411_map [out_dir] [review.png]     # default outputs/watches/seiko-sna411p1-var-nato3/

dial_photo.jpg: square centred on the dial centre, half HALF_MM, covering the dial and the bezel insert (the build maps the
insert around its own photo centre). The hour, minute and yellow chrono hands and the hub are removed: each pixel takes the
lighting from around the hand and the detail from the same radius 6, 12, 18 ... deg away (60-tick tracks on the dial). The
dial print is not periodic, so a hand's own footprint may hold wrong print; the hand geometry covers it at the photo pose.
Subdial hands stay. Light unsharp mask, JPEG.

strap_photo.jpg: rows of the 12 o'clock strap end, each row's strap edges mapped to the full width (the stripes run along
the strap, so any stretch of rows is a fair sample). The build mirrors it along the strap.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-sna411p1-var-nato3-trace.json"
OUT = ROOT / "outputs/watches/seiko-sna411p1-var-nato3"
HALF_MM = 21.5
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.15
LOW_SIGMA_PX = 20
PERIOD_DEG = 6
EDGE_INSET_MM = (0.2, 0.6)  # left, right: the right edge of the 12 o'clock end curls over (grey fibres)


def hand_mask(t, shape, margin=MARGIN_MM):
    S = t["scale_px_per_mm"]
    px0, py0 = t["manual_px"]["hand_pivot"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    x, y = (xx - px0) / S, -(yy - py0) / S
    m = np.hypot(x, y) < t["hub_radius_mm"] + margin
    for name, h in t["hands"].items():
        a = math.radians(h["angle_deg"])
        ux, uy = math.sin(a), math.cos(a)
        along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
        if name == "chrono":
            m |= (along > -h["tail_mm"] - margin) & (along < 3.0) & (across < h["root_half_mm"] + margin)  # root, as built
            m |= (along > 0) & (along < h["length_mm"] + margin) & (across < h["needle_half_mm"] + margin)  # needle: keeps MIN. and 60 beside it
            m |= (along > -h["tail_mm"] - 2 * margin) & (along < -h["tail_apex_mm"] + margin) & (across < h["tail_base_half_mm"] + margin)
        else:  # sword outline, widened by the margin
            ys, ws = zip(*[(y_, x_) for x_, y_ in h["half_outline_mm"]])
            m |= (along > ys[0] - margin) & (along < h["length_mm"] + margin) & (across < np.interp(along, ys[1:], ws[1:]) + margin)
    return m


def dial_map(t, img):
    S = t["scale_px_per_mm"]
    cx, cy = t["origin_px"]
    R = int(math.ceil(HALF_MM * S))
    sl = np.s_[cy - R:cy + R, cx - R:cx + R]
    win = img[sl].copy()
    mask = hand_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    valid = (~mask).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    c = (float(R), float(R))
    for k in range(1, 30):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D(c, deg, 1.0)
            src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~mask).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
        if not todo.any():
            break
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    return cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0), mask, sl, int(todo.sum())


def strap_atlas(t, img):
    S = t["scale_px_per_mm"]
    b, g, r = (img[..., k].astype(int) for k in range(3))
    body = (img.max(2) < 140) | ((r > 140) & (g < 110))  # black or red weave; steel and background are brighter and grey
    W = int(round(2 * 11.0 * S))
    r0, r1 = t["manual_px"]["strap_px"]["rows_top"]
    rows = np.arange(r0, r1)
    edges = []
    for row in rows:
        xs = np.nonzero(body[row, 600:1800])[0] + 600
        edges.append([xs.min(), xs.max()])
    edges = np.array([np.median(np.array(edges)[max(0, k - 15):k + 16], 0) for k in range(len(rows))], float)
    edges += [EDGE_INSET_MM[0] * S, -EDGE_INSET_MM[1] * S]
    # the stripes lean (perspective): per row, the four red/black boundaries go to their median place across the strap
    red = cv2.GaussianBlur(((r > 140) & (g < 110)).astype(np.float32), (0, 0), 3)
    knots = []
    for row, (e0, e1) in zip(rows, edges):
        xs = np.arange(int(e0), int(e1))
        f = red[row, xs] > 0.5
        flips = xs[1:][f[1:] != f[:-1]]
        knots.append([e0] + list(flips[:4]) + [e1] if len(flips) >= 4 else None)
    good = [k for k in knots if k is not None]
    frac = np.median([(np.array(k) - k[0]) / (k[-1] - k[0]) for k in good], 0)
    ok = [k is not None and np.abs((np.array(k) - k[0]) / (k[-1] - k[0]) - frac).max() < 0.05 for k in knots]  # drop rows misread by a stray fibre
    K = np.array([k if o else [np.nan] * 6 for k, o in zip(knots, ok)], float)
    j = (np.arange(W) + 0.5) / W
    mx = np.zeros((len(rows), W), np.float32)
    for i in range(len(rows)):
        mx[i] = np.interp(j, frac, np.nanmedian(K[max(0, i - 10):i + 11], 0))  # smooth along the strap
    my = np.repeat(rows[:, None].astype(np.float32), W, 1)
    atlas = cv2.remap(img, mx, my, cv2.INTER_CUBIC)
    return atlas, {"size_px": [W, len(rows)], "length_mm": round(len(rows) / S, 3), "rows_px": [int(r0), int(r1)]}


def build(out_dir=OUT, review=None):
    t = json.loads(TRACE.read_text())
    img = cv2.imread(str(ROOT / t["source"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    crop, mask, sl, unfilled = dial_map(t, img)
    cv2.imwrite(str(out_dir / "dial_photo.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    S = t["scale_px_per_mm"]
    meta = {"source": t["source"], "centre_px": t["origin_px"], "half_size_mm": round(crop.shape[0] / 2 / S, 4), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled}
    (out_dir / "dial_photo.json").write_text(json.dumps(meta, indent=1) + "\n")
    atlas, lay = strap_atlas(t, img)
    cv2.imwrite(str(out_dir / "strap_photo.jpg"), atlas, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    (out_dir / "strap_photo.json").write_text(json.dumps(lay, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2000, 1000), interpolation=cv2.INTER_AREA))
    return meta, lay


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
