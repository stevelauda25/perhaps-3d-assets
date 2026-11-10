"""Cut the Hamilton H77616533 (Khaki Aviation X-Wind Auto Chrono) photo maps from the official front render: a clean dial
(central and subdial hands removed) out to the steel bezel, and the leather strap resampled to a straight strip.

    python3 -B -m pipeline.hamilton_h77616533_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h77616533/dial_photo.jpg

Dial: same method as pipeline/hamilton_h76305530_dial.py on a flat black base: each central hand pixel is copied from the same
radius 30, 60 ... deg, then 6, 12 ... deg away about the pivot, with every bright print and the silver subdials protected as
copy sources. Each subdial hand is filled by turning that subdial about its own centre. The map reaches the bezel's inner
edge (the printed inner rotating ring is part of it). Strap: each row between its alpha edges, top strap in the left
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
TRACE = ROOT / "config/watches/hamilton-h77616533-trace.json"
OUT = ROOT / "outputs/watches/hamilton-h77616533/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.3
SHADOWS_MM = ((0.25, -0.25),)  # the render's soft shadow, lower right
STRAP_W = 536  # map width per strap (21.2 mm at the render scale)
SUBDIAL_R_MM = 4.7  # subdial discs with their outer rings: filled about their own centres, never a copy source for the rest
NUMERALS = [[717, 800, 793, 862], [1221, 805, 1283, 862]]  # 10 and 2 next to the hand tips (photo px): narrow mask, the visible part stays


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


def central_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    hs = t["hands"]
    m = np.zeros(shape, np.uint8)
    to_px = lambda pts, dx, dy: np.array([[px0 + (x + dx) * S, py0 - (y + dy) * S] for x, y in pts], np.int32)
    for dx, dy in ((0, 0),) + tuple(shadows):
        cv2.circle(m, (int(px0 + dx * S), int(py0 - dy * S)), int((t["hub_radius_mm"][0] + margin) * S), 1, -1)
        for name in ("hour", "minute"):
            cv2.fillPoly(m, [to_px(poly_of(hs[name], "outline_mm", margin, margin), dx, dy)], 1)
        h = hs["chrono"]
        a = math.radians(h["angle_deg"])
        p = lambda r: (int(px0 + (r * math.sin(a) + dx) * S), int(py0 - (r * math.cos(a) + dy) * S))
        cv2.line(m, p(-h["tail_mm"]), p(h["length_mm"]), 1, int(2 * (h["half_width_mm"] + margin) * S))
        a0, aw = h["arrow_mm"]
        tri = [(aw + margin, a0 - margin), (-aw - margin, a0 - margin), (0, h["length_mm"] + margin)]
        cv2.fillPoly(m, [to_px([(x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)) for x, y in tri], dx, dy)], 1)
    return m.astype(bool)


def subdial_mask(t, shape, sd, margin=0.15):
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
    R = int(math.ceil(t["rings_mm"]["dial"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "day_date", "print_khaki"))
    for x0, y0, x1, y1 in NUMERALS:
        prints[y0:y1, x0:x1] = True
    prints = prints[sl]
    mask = np.where(prints, central_mask(t, shape, (), 0.1)[sl], central_mask(t, shape)[sl])
    gray = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY)
    yy, xx = np.mgrid[-R:R, -R:R]
    discs = {}
    for key, sd in t["subdials"].items():
        cx, cy = sd["centre_mm"]
        discs[key] = np.hypot(xx - cx * S, yy + cy * S) < SUBDIAL_R_MM * S
    subs = np.logical_or.reduce(list(discs.values()))
    feats = cv2.dilate(((gray > 90) & ~mask).astype(np.uint8), np.ones((11, 11), np.uint8)).astype(bool) | subs
    black = np.median(win[~mask & ~feats & (np.hypot(xx, yy) < 0.8 * R)].reshape(-1, 3), 0)
    todo = mask & ~subs
    low = np.broadcast_to(black.astype(np.float32), win.shape).copy()
    moves = [(sgn * k * 30, 1.0) for k in range(1, 6) for sgn in (1, -1)] + [(sgn * k * 6, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    used = {"central": fill(win, todo, mask | feats, low, moves, (R, R))}
    unfilled = int(todo.sum())
    win[todo] = black
    hands = mask | np.logical_or.reduce([subdial_mask(t, shape, sd)[sl] for sd in t["subdials"].values()])
    for key, sd in t["subdials"].items():  # subdial hand and any central hand over the disc: turn the subdial about its centre
        cx, cy = sd["centre_mm"]
        todo_s = hands & discs[key]
        smoves = [(sgn * k * 15, 1.0) for k in range(1, 12) for sgn in (1, -1)]
        used["subdial " + key] = fill(win, todo_s, hands, win.astype(np.float32) * 0, smoves, (R + cx * S, R - cy * S))
    allmask = hands
    soft = cv2.GaussianBlur(allmask.astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    sharpen = lambda a: cv2.addWeighted(a, 1 + SHARPEN[1], cv2.GaussianBlur(a, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    crop = sharpen(win)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(allmask.sum()), "lighting_only_px": unfilled,
            "filled_from": {g: {k: v for k, v in u.items() if v} for g, u in used.items()}}
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
