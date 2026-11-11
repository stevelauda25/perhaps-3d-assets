"""Cut the dial map for the Bulova 96B251 (Lunar Pilot chronograph, leather strap) from the official front render: the hour,
minute and chronograph hands removed, the applied indices blanked (they are modelled), the white print redrawn sharp at 4x;
and the strap map (strap_photo.jpg next to it).

    python3 -B -m pipeline.bulova_96b251_dial [out.jpg] [review.png]   # default outputs/watches/bulova-96b251/dial_photo.jpg

Same as pipeline/bulova_96b258_dial.py for the dial. Strap: each row past the horn tips between its alpha edges resampled to
STRAP_W (as pipeline/hamilton_h76709530_dial.py), top strap in the left half, bottom strap in the right half.

Square map to the bezel's inner edge (dial, chapter ring and tachymeter flange). Each hand pixel gets a local lighting estimate
(masked normalised blur) plus detail copied from the same radius 30, 60 ... deg, then 6, 12 ... deg away about the pivot;
inside a subdial the copy turns about the subdial centre instead (concentric grooves). Prints, indices and the date window
are never a copy source. The three subdial needles stay in the map: the modelled needles sit on the same pixels and the
numerals they cross stay whole. Then the print (white ink, the date window) is redrawn from its coverage cut at half over
an ink-free background at UP x the render's resolution, so it stays sharp in the dial close-up; light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load
from pipeline.hamilton_h76709530_dial import strap_strip
from pipeline.hamilton_h82405130_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/bulova-96b251-trace.json"
OUT = ROOT / "outputs/watches/bulova-96b251/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 92
MARGIN_PX = 6
SHADOW_PX = ((3, 3), (6, 6))  # the render's hands throw a faint shadow down to the right
LIGHT_SIGMA_PX = 12
LEVEL_SIGMA_PX = 10
UP = 4
INK_BG_SIGMA_PX = 6
INK_STEP = 60  # grey levels above the local dial: ink (the subdial grooves stay below)
INK_CUT = 0.45
INK_SMOOTH = 0.5  # photo px
INK_EDGE = 3.0
STRAP_W = 536  # map width per strap: 20 mm at the render scale


def outline_poly(h, S, pad):
    t = math.radians(h["angle_deg"])
    pts = [(r * S, v * S + pad) for r, v in h["outline_mm"]]
    pts[0], pts[-1] = (pts[0][0] - pad, pts[0][1]), (pts[-1][0] + pad, pts[-1][1])
    loop = [(v, r) for r, v in pts] + [(-v, r) for r, v in pts[::-1]]
    return [(x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)) for x, y in loop]


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOW_PX:
        for name in ("hour", "minute", "chrono"):
            cv2.fillPoly(m, [np.array([(px0 + x + dx, py0 - y + dy) for x, y in outline_poly(t["hands"][name], S, MARGIN_PX)], np.int32)], 1)
        cv2.circle(m, (px0 + dx, py0 + dy), int(t["hub_radius_mm"][0] * S + MARGIN_PX), 1, -1)
    return m.astype(bool)


def index_mask(t, shape, pad):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["index"]
    m = np.zeros(shape, np.uint8)
    for hr in range(12):
        a = math.radians(hr * 30)
        r0, hw = (ix["square_inner"], ix["square_half"]) if hr in (3, 6, 9) else (ix["inner"], ix["half_12"] if hr == 0 else ix["half"])
        q = [(hw + pad, r0 - pad), (hw + pad, ix["outer"] + pad), (-hw - pad, ix["outer"] + pad), (-hw - pad, r0 - pad)]
        cv2.fillPoly(m, [np.array([(px0 + (x * math.cos(a) + y * math.sin(a)) * S, py0 - (-x * math.sin(a) + y * math.cos(a)) * S) for x, y in q], np.int32)], 1)
    return m.astype(bool)


def crisp_light_print(win, on_dial, bg_ok, blank, ink_min=0):
    """UP x map: cubic upsample; the light print redrawn from its ink coverage cut at INK_CUT over an ink-free background
    (about 1 output px of anti-aliasing). Under blank (the modelled indices) only the background stays. Ink must also have every
    channel above ink_min (white print, not a coloured highlight); only ink and its skirt are redrawn, the rest is the photo."""
    g = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY).astype(np.float32)
    blur = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
    clean = bg_ok & on_dial
    rough = blur(g * clean, INK_BG_SIGMA_PX) / np.maximum(blur(clean.astype(np.float32), INK_BG_SIGMA_PX), 1e-3)
    inkish = cv2.dilate(((g - rough > INK_STEP) & on_dial & (win.min(2) > ink_min)).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    clean = (clean & ~inkish & ~blank).astype(np.float32)
    bg = blur(win.astype(np.float32) * clean[..., None], INK_BG_SIGMA_PX) / np.maximum(blur(clean, INK_BG_SIGMA_PX)[..., None], 1e-3)
    level = float(np.percentile(g[inkish], 97))  # full-coverage ink grey
    ink_bgr = np.median(win[inkish & (g >= level - 10)], 0).astype(np.float32)
    size = (win.shape[1] * UP, win.shape[0] * UP)
    up = lambda a: cv2.resize(a, size, interpolation=cv2.INTER_CUBIC)
    winU, bgU, gU = up(win.astype(np.float32)), up(bg), up(g)
    bggU = bgU.mean(2)
    cov = blur(np.clip((gU - bggU) / np.maximum(level - bggU, 1.0), 0, 1.2), INK_SMOOTH * UP) * (up(inkish.astype(np.float32)) > 0.5)
    a = np.clip((cov - INK_CUT) * INK_EDGE + 0.5, 0, 1) * (up(on_dial.astype(np.float32)) > 0.5) * (1 - np.clip(up(blank.astype(np.float32)), 0, 1))
    near = blur(cv2.dilate((cov > 0.08).astype(np.uint8), np.ones((2 * UP + 1,) * 2, np.uint8)).astype(np.float32), UP)[..., None]
    near = np.maximum(near, blur(up(blank.astype(np.float32)), UP)[..., None])
    base = near * bgU + (1 - near) * winU
    out = a[..., None] * ink_bgr + (1 - a[..., None]) * base
    return np.clip(out, 0, 255).astype(np.uint8), {"ink_grey": round(level, 1), "ink_bgr": [round(float(v), 1) for v in ink_bgr]}


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    shape = img.shape[:2]
    R = int(math.ceil(t["rings_mm"]["bezel_in"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    mask = hand_mask(t, shape)[sl]
    idx = index_mask(t, shape, 0.25)[sl]
    g = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY).astype(np.float32)
    feats = cv2.dilate((g > 110).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~mask | idx  # prints, date, indices
    yy, xx = np.mgrid[-R:R, -R:R]
    rr = np.hypot(xx, yy)
    clean = (~mask & ~feats).astype(np.float32)
    low = cv2.GaussianBlur(win.astype(np.float32) * clean[..., None], (0, 0), LIGHT_SIGMA_PX) / \
        np.maximum(cv2.GaussianBlur(clean, (0, 0), LIGHT_SIGMA_PX)[..., None], 1e-3)
    sb = t["subs"]
    in_sub = np.zeros(win.shape[:2], bool)
    used = {}
    for k, (cx, cy) in enumerate(sb["centres_mm"]):
        scx, scy = R + cx * S, R - cy * S
        disc = np.hypot(xx + R - scx, yy + R - scy) < sb["radius_mm"] * S + 2
        in_sub |= disc
        todo = mask & disc
        moves = [(sg * j * 6, 1.0) for j in range(1, 30) for sg in (1, -1)]
        used.update({"sub%d %s" % (k, a): b for a, b in fill(win, todo, mask | feats, low, moves, (scx, scy)).items()})
        win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    todo = mask & ~in_sub
    moves = [(sg * j * 30, 1.0) for j in range(1, 6) for sg in (1, -1)] + [(sg * j * 6, 1.0) for j in range(1, 30) for sg in (1, -1)]
    used.update(fill(win, todo, mask | feats | in_sub, low, moves, (R, R)))
    left = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    # match the filled zones to the dial right next to them (the copies come out a few grey levels dark on the black dial)
    ring = (cv2.dilate(mask.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~mask & ~feats).astype(np.float32)
    mloc = lambda a, w: cv2.GaussianBlur(a * w[..., None], (0, 0), LEVEL_SIGMA_PX) / np.maximum(cv2.GaussianBlur(w, (0, 0), LEVEL_SIGMA_PX)[..., None], 1e-3)
    shift = mloc(img[sl].astype(np.float32), ring) - mloc(win.astype(np.float32), mask.astype(np.float32))
    win[mask] = np.clip(win[mask] + shift[mask], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    on_dial = rr < R - 1
    win, ink = crisp_light_print(win, on_dial, np.ones_like(mask), index_mask(t, shape, 0.25)[sl])  # the filled hand zones are clean dial now
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0] * UP), -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": UP,
            "masked_px": int(mask.sum()), "lighting_only_px": left, "ink": ink, "filled_from": {k: v for k, v in used.items() if v}}
    # strap: the rows past the horn tips (the strap is the only thing there on the transparent background)
    t0, t1 = t["manual_px"]["lug_tips_y"]
    alpha = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)[..., 3]
    top, top_rows = strap_strip(img, alpha, range(t0 - 5, -1, -1), STRAP_W)
    bot, bot_rows = strap_strip(img, alpha, range(t1 + 5, img.shape[0]), STRAP_W)
    n = max(len(top), len(bot))
    pad = lambda a: np.vstack([a, np.repeat(a[-1:], n - len(a), 0)])
    strap = np.hstack([pad(top), pad(bot)])
    strap = cv2.addWeighted(strap, 1 + SHARPEN[1], cv2.GaussianBlur(strap, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    sp = out.with_name("strap_photo.jpg")
    cv2.imwrite(str(sp), strap, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    sp.with_suffix(".json").write_text(json.dumps({"size_px": [strap.shape[1], strap.shape[0]], "width_px": STRAP_W, "rows_px": {"top": top_rows, "bottom": bot_rows},
                                                   "scale_px_per_mm": S, "lug_tips_px": [t0, t1]}) + "\n")
    meta["strap"] = {"rows": [len(top_rows), len(bot_rows)], "size_px": [strap.shape[1], strap.shape[0]]}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([cv2.resize(shown, crop.shape[1::-1], interpolation=cv2.INTER_NEAREST), crop]), (2000, 1000),
                                            interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print({k: m[k] for k in ("size_px", "masked_px", "lighting_only_px", "ink", "strap")}, "->", dest)
