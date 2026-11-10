"""Cut the Hamilton H76709530 (Khaki Aviation Pilot Pioneer Mechanical Bronze) photo maps from the official front render: a
clean dial (hour, minute and small seconds hands removed) out to the bezel's inner edge, and the leather strap resampled to a
straight strip.

    python3 -B -m pipeline.hamilton_h76709530_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h76709530/dial_photo.jpg

Dial: the hand zones on the grained dial, grown over the render's soft shadows, are relit from the clean dial and regrained
with tiles from its largest clean squares (a turned copy would turn the embossed grain against the light); on the railway
track each pixel is copied from 6, 12 ... deg away about the pivot, with every bright print
and the small seconds disc protected as copy sources; the small seconds hand is filled by turning its disc about its centre. Strap: each row between its alpha edges, top strap in the left
half, bottom in the right half of strap_photo.jpg. Native resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h76305530_dial import boxes, poly_of
from pipeline.hamilton_h77616533_trace import load
from pipeline.hamilton_h82405130_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/hamilton-h76709530-trace.json"
OUT = ROOT / "outputs/watches/hamilton-h76709530/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.4
SHADOWS_MM = ((-0.4, -0.4), (-0.8, -0.8), (0.0, -0.6), (0.3, -0.3))  # the render's soft shadows fall lower left, about 1 mm
STRAP_W = 474  # map width per strap (19.4 mm at the render scale)
GROW_PX = 22  # the render's hand shadows reach this far past the hand zones
SHADE_PX = 45  # how far the hands darken the render's dial around their zones
ZERO_OF_10 = [666, 739, 710, 815, 11.5]  # photo px box and stroke; the hour tip ends inside it: the 0 is drawn again
ONE_OF_10 = [642, 760, 652, 800]  # a clean part of the 1's stroke: the numeral colour
RAILWAY_R_MM = 15.0  # inside it the grained dial, outside the railway track
SUBDIAL_R_MM = 4.3  # small seconds disc with its ring: filled about its own centre, never a copy source for the rest
NUMERALS = [[600, 690, 720, 790], [1160, 690, 1270, 790]]  # 10 and 2 next to the hand tips (photo px): narrow mask, the visible part stays


def strap_strip(img, alpha, rows, width):
    """Each row's strap (the only thing past the lug tips on the transparent background) resampled to `width`. The white
    stitching breaks a colour-based run, so the extent comes from the alpha."""
    out, used = [], []
    for y in rows:
        xs = np.nonzero(alpha[y] > 128)[0]
        if len(xs) < 0.8 * width:
            if out:
                break
            continue
        out.append(cv2.resize(img[y:y + 1, xs.min():xs.max() + 1], (width, 1), interpolation=cv2.INTER_AREA))
        used.append(int(y))
    return np.vstack(out), used


def fill_grain(win, todo, bad, sigma=60, seed=11):
    """Grained dial under the hands: a smooth lighting estimate from the clean dial (normalised blur) plus fine grain tiled
    from the largest clean squares of the same dial (random tiles, same orientation: a turned copy turns the embossed grain
    against the light). The shared lighting hides the tile seams. Returns the clean squares used."""
    good = ~bad
    f = win.astype(np.float32)
    g = good.astype(np.float32)
    wgt = cv2.GaussianBlur(g, (0, 0), sigma)[..., None]
    low = cv2.GaussianBlur(f * g[..., None], (0, 0), sigma) / np.maximum(wgt, 1e-4)
    detail = f - cv2.GaussianBlur(f, (0, 0), 6)
    dist = cv2.distanceTransform(good.astype(np.uint8), cv2.DIST_L2, 5)
    patches = []
    d = dist.copy()
    while len(patches) < 8:
        y, x = np.unravel_index(np.argmax(d), d.shape)
        r = int(d[y, x] * 0.7)
        if r < 10:
            break
        patches.append((x - r, y - r, 2 * r))
        cv2.circle(d, (int(x), int(y)), int(2 * d[y, x]), 0, -1)
    T = min(sz for _, _, sz in patches)
    rng = np.random.default_rng(seed)
    tex = np.zeros_like(detail)
    for ty in range(0, win.shape[0], T):
        for tx in range(0, win.shape[1], T):
            x0, y0, sz = patches[rng.integers(len(patches))]
            ox, oy = x0 + rng.integers(sz - T + 1), y0 + rng.integers(sz - T + 1)
            h_, w_ = min(T, win.shape[0] - ty), min(T, win.shape[1] - tx)
            tex[ty:ty + h_, tx:tx + w_] = detail[oy:oy + h_, ox:ox + w_]
    win[todo] = np.clip(low[todo] + tex[todo], 0, 255).astype(np.uint8)
    todo[:] = False
    return [[int(v) for v in pt] for pt in patches]


def central_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    hs = t["hands"]
    m = np.zeros(shape, np.uint8)
    to_px = lambda pts, dx, dy: np.array([[px0 + (x + dx) * S, py0 - (y + dy) * S] for x, y in pts], np.int32)
    for dx, dy in ((0, 0),) + tuple(shadows):
        cv2.circle(m, (int(px0 + dx * S), int(py0 - dy * S)), int((t["hub_radius_mm"][0] + margin) * S), 1, -1)
        for name in ("hour", "minute"):
            cv2.fillPoly(m, [to_px(poly_of(hs[name], "outline_mm", margin, margin), dx, dy)], 1)
    return m.astype(bool)


def subdial_mask(t, shape, sd, margin=0.25):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    cx, cy = sd["centre_mm"]
    a = math.radians(sd["angle_deg"])
    m = np.zeros(shape, np.uint8)
    p = lambda r: (int(px0 + (cx + r * math.sin(a)) * S), int(py0 - (cy + r * math.cos(a)) * S))
    cv2.line(m, p(-sd["tail_mm"]), p(sd["length_mm"]), 1, int(2 * (sd["half_mm"] + margin) * S))
    cv2.circle(m, p(0), int((sd["hub_mm"] + margin) * S), 1, -1)
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    R = int(math.ceil(t["bezel_rings_mm"]["insert_in"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "print_mech", "print_swiss_made"))
    for x0, y0, x1, y1 in NUMERALS:
        prints[y0:y1, x0:x1] = True
    prints = prints[sl]
    mask = np.where(prints, central_mask(t, shape, (), 0.1)[sl], central_mask(t, shape)[sl])
    gray = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY)
    yy, xx = np.mgrid[-R:R, -R:R]
    discs = {}
    for key, sd in {"seconds": t["small_seconds"]}.items():
        cx, cy = sd["centre_mm"]
        discs[key] = np.hypot(xx - cx * S, yy + cy * S) < SUBDIAL_R_MM * S
    subs = np.logical_or.reduce(list(discs.values()))
    beige = cv2.morphologyEx(((gray > 150) & ~mask).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # prints, not grain sparkle
    feats = cv2.dilate(beige, np.ones((11, 11), np.uint8)).astype(bool) | subs
    black = np.median(win[~mask & ~feats & (np.hypot(xx, yy) < 0.8 * R)].reshape(-1, 3), 0)
    inner = np.hypot(xx, yy) < RAILWAY_R_MM * S
    printed = cv2.dilate(((gray > 150) & ~mask).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    # the grained dial: the hand zones grown over the render's soft shadows (prints and subdial excluded) are relit and regrained
    grown = cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * GROW_PX + 1,) * 2)).astype(bool)
    mask = mask | (grown & inner & ~printed & ~subs)
    todo = mask & ~subs & inner
    shade = cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * SHADE_PX + 1,) * 2)).astype(bool)
    shifted = fill_grain(win, todo, shade | feats | subs | ~inner)  # the render's soft hand shadows reach past the zones: never a source
    todo |= mask & ~subs & (np.hypot(xx, yy) >= RAILWAY_R_MM * S)  # the railway track: turned copies (it repeats every 6 deg)
    low = np.broadcast_to(black.astype(np.float32), win.shape).copy()  # copies are the turned render itself, not relit to the shadowed edge
    moves = [(sgn * k * 6, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    used = {"central": fill(win, todo, mask | feats, low, moves, (R, R)), "grain_squares_px": shifted}
    unfilled = int(todo.sum())
    win[todo] = black
    hands = mask | np.logical_or.reduce([subdial_mask(t, shape, sd)[sl] for sd in [t["small_seconds"]]])
    for key, sd in {"seconds": t["small_seconds"]}.items():  # subdial hand and any central hand over the disc: turn the subdial about its centre
        cx, cy = sd["centre_mm"]
        todo_s = hands & discs[key]
        smoves = [(sgn * k * 15, 1.0) for k in range(1, 12) for sgn in (1, -1)]
        used["subdial " + key] = fill(win, todo_s, hands, win.astype(np.float32) * 0, smoves, (R + cx * S, R - cy * S))
    allmask = hands
    soft = cv2.GaussianBlur(allmask.astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    x0, y0, x1, y1, sw = ZERO_OF_10  # a stadium ring like the photo's 0, drawn at 4x and averaged down
    ox, oy = px0 - R, py0 - R
    a0, b0, a1, b1 = ONE_OF_10
    ink = np.median(img[b0:b1, a0:a1].reshape(-1, 3), 0)
    U, W, Hh = 4, x1 - x0, y1 - y0
    ring = np.zeros((Hh * U, W * U), np.uint8)
    for k, val in ((0, 255), (sw, 0)):
        r = int((W / 2 - k) * U)
        x_0, y_0, x_1, y_1 = int(k * U), int(k * U), int((W - k) * U), int((Hh - k) * U)
        cv2.rectangle(ring, (x_0, y_0 + r), (x_1, y_1 - r), val, -1)
        cv2.circle(ring, ((x_0 + x_1) // 2, y_0 + r), r, val, -1)
        cv2.circle(ring, ((x_0 + x_1) // 2, y_1 - r), r, val, -1)
    cov = cv2.resize(ring, (W, Hh), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
    sl0 = win[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    sl0[:] = (cov * ink + (1 - cov) * sl0).astype(np.uint8)
    sharpen = lambda a: cv2.addWeighted(a, 1 + SHARPEN[1], cv2.GaussianBlur(a, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    crop = sharpen(win)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(allmask.sum()), "lighting_only_px": unfilled,
            "filled_from": {g: ({k: v for k, v in u.items() if v} if isinstance(u, dict) else u) for g, u in used.items()}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")

    t0, t1 = t["manual_px"]["lug_tips_y"]
    alpha = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)[..., 3]
    top, top_rows = strap_strip(img, alpha, range(t0 - 5, -1, -1), STRAP_W)
    bot, bot_rows = strap_strip(img, alpha, range(t1 + 5, img.shape[0]), STRAP_W)
    n = max(len(top), len(bot))
    pad = lambda a: np.vstack([a, np.repeat(a[-1:], n - len(a), 0)])
    strap = sharpen(np.hstack([pad(top), pad(bot)]))
    sp = out.with_name("strap_photo.jpg")
    cv2.imwrite(str(sp), strap, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    smeta = {"size_px": [strap.shape[1], strap.shape[0]], "width_px": STRAP_W, "rows_px": {"top": top_rows, "bottom": bot_rows},
             "scale_px_per_mm": S, "lug_tips_px": [t0, t1]}
    sp.with_suffix(".json").write_text(json.dumps(smeta) + "\n")
    meta["strap"] = {"rows": {k: len(v) for k, v in smeta["rows_px"].items()}, "size_px": smeta["size_px"]}
    if review:
        shown = img[sl].copy()
        shown[allmask] = (0.5 * shown[allmask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
        cv2.imwrite(str(review.with_name(review.stem + "_strap.png")), strap)
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
