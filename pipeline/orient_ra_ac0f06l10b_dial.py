"""Cut the Orient RA-AC0F06L10B photo maps from the front photo: a clean dial (hands and their shadows removed) and the leather
strap resampled to a straight strip.

    python3 -B -m pipeline.orient_ra_ac0f06l10b_dial [out.jpg] [review.png]   # default outputs/watches/orient-ra-ac0f06l10b/dial_photo.jpg

Dial: same method as pipeline/orient_ra_wj0002l_dial.py (whose fill, polar lighting and sunburst grain it reuses): each hand
pixel is copied from the same radius 6, 12, 18 ... deg away about the index ring centre, then blended in the gradient domain.
The hands are masked about their own pivot (0.23 mm above the ring centre in the photo). The square map is centred on the
index ring centre and reaches the polished bezel's inner edge. Strap: each photo row of leather (darker than the steel and the
white background) is resampled between its own edges to a fixed width, top strap (12 o'clock) in the left half of
strap_photo.jpg, bottom strap in the right half; strap_photo.json lists the photo row of every map row.
Native photo resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.orient_ra_wj0002l_dial import fill, lighting, streaks

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-ra-ac0f06l10b-trace.json"
OUT = ROOT / "outputs/watches/orient-ra-ac0f06l10b/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.25
SHADOWS_MM = ((0.2, -0.25), (0.35, -0.45))  # soft shadow down-right (light from the upper left)
HUB_ZONE_MM = 1.15  # collar (1.07 mm)
PERIOD_DEG = 6
LEATHER = 140  # leather and its stitching are darker than this; steel and background are brighter
STRAP_W = 660  # map width per strap (22 mm at the photo scale)
STRAP_CENTRE_X = 962  # between the lug inner edges at the tips


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["hand_pivot_px"]
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
        for name in ("hour", "minute"):
            h = hs[name]
            al, ac = axes(h, x, y)
            rs, ws = zip(*h["outline_mm"])
            m |= (al > rs[0] - margin) & (al < rs[-1] + margin) & (ac < np.interp(al, rs, ws) + 1.5 * margin)
        h = hs["seconds"]
        al, ac = axes(h, x, y)
        m |= (al > -h["tail_mm"] - margin) & (al < h["length_mm"] + margin) & (ac < h["half_width_mm"] + margin)
        m |= (al > -h["tail_mm"] - margin) & (al <= 0) & (ac < h["tail_half_width_mm"] + margin)
    return m


def boxes(t, shape, keys, pad=8):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in keys:
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S) - pad, int(py0 - b[1] * S) - pad), (int(px0 + b[2] * S) + pad, int(py0 - b[3] * S) + pad), 1, -1)
    return m.astype(bool)


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = boxes(t, shape, ("date_window", "logo", "print_wr", "print_6")).astype(np.uint8)
    ix = t["indices"]
    for hr in range(1, 13):
        q = ix["index_12_mm"] if hr == 12 else ix["baton_mm"]
        a = math.radians(hr * 30)
        p0 = (int(px0 + (q["inner"] - 0.4) * S * math.sin(a)), int(py0 - (q["inner"] - 0.4) * S * math.cos(a)))
        p1 = (int(px0 + (q["outer"] + 0.4) * S * math.sin(a)), int(py0 - (q["outer"] + 0.4) * S * math.cos(a)))
        cv2.line(m, p0, p1, 1, int((2 * q["half_outer"] + 0.8) * S))
    return m.astype(bool)


def strap_strip(img, rows, centre_x):
    """Each photo row's leather run through the strap centre, resampled to STRAP_W; the first row without leather after the strip
    has started ends it."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    out, used = [], []
    for y in rows:
        dark = cv2.morphologyEx((gray[y] < LEATHER).astype(np.uint8)[None], cv2.MORPH_CLOSE, np.ones((1, 9), np.uint8))[0].astype(bool)
        if not dark[centre_x]:
            if out:
                break
            continue
        x0, x1 = centre_x, centre_x
        while x0 > 0 and dark[x0 - 1]:
            x0 -= 1
        while x1 < len(dark) - 1 and dark[x1 + 1]:
            x1 += 1
        if x1 - x0 < 0.8 * STRAP_W:  # rows next to the case (shadow, case side) are skipped until the leather spans the lugs
            if out:
                break
            continue
        out.append(cv2.resize(img[y:y + 1, x0:x1 + 1], (STRAP_W, 1), interpolation=cv2.INTER_AREA))
        used.append(int(y))
        centre_x = (x0 + x1) // 2  # the photo's strap runs at a slight slant
    return np.vstack(out), used


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil((t["bezel_inner_mm"] + 0.1) * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "print_wr", "print_6", "date_window"), pad=0)[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.1)[sl], hand_mask(t, shape)[sl])  # print the hand only grazes stays
    feats = feature_mask(t, shape)[sl]
    todo = mask.copy()
    bad = mask | feats
    low = lighting(win, bad, (R, R))
    moves = [(sgn * k * PERIOD_DEG, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    used = fill(win, todo, bad, low, moves, (R, R))
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo] + streaks(win, ~bad, (R, R))[todo], 0, 255).astype(np.uint8)
    # no gradient-domain blend: the period copies already match, and the blend darkened the minute hand zone next to the
    # bright 2 o'clock baton and the dark minute track ring
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    sharpen = lambda a: cv2.addWeighted(a, 1 + SHARPEN[1], cv2.GaussianBlur(a, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    crop = sharpen(win)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")

    # strap: top strap from the case outward (up), bottom strap from the case outward (down)
    t0, t1 = t["manual_px"]["lug_tips_y"]
    c0, c1 = t["manual_px"]["case_y"]
    top, top_rows = strap_strip(img, range(c0 - 4, -1, -1), STRAP_CENTRE_X)
    bot, bot_rows = strap_strip(img, range(c1 + 30, img.shape[0]), STRAP_CENTRE_X)
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
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
        cv2.imwrite(str(review.with_name(review.stem + "_strap.png")), strap)
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
