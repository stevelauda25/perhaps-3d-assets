"""Cut a clean dial map for the Tissot T127.407.11.081.00 (Gentleman Powermatic 80 Open Heart) from the official front render,
the hands removed.

    python3 -B -m pipeline.tissot_t127407_dial [out.jpg] [review.png]   # default outputs/watches/tissot-t127.407.11.081.00/dial_photo.jpg

Sunray dial: the brightness changes with the angle, so the base is a local lighting estimate (masked normalised blur) and only
the detail is copied from the same radius 30, 60 ... deg, then 6, 12 ... deg away about the pivot (the minute track repeats
every 6 deg). Inside the open-heart aperture nothing repeats: the photo stays as it is there (the modelled hands sit on
the same pixels, 0.1 mm above them; an inpaint smeared the movement). The first T of TISSOT (crossed by the seconds hand)
is replaced by the clean last T. Indices, prints, lume dots and the aperture are never a copy source. Black print redrawn sharp at 4x (crisp_print); light unsharp mask, JPEG.
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
TRACE = ROOT / "config/watches/tissot-t127.407.11.081.00-trace.json"
OUT = ROOT / "outputs/watches/tissot-t127.407.11.081.00/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.35
SHADOWS_MM = ((0.3, -0.3), (0.15, -0.15), (0.1, -0.45))  # the render's hands throw a faint shadow down
LIGHT_SIGMA_PX = 14
HUB_PLAIN_PX = 40
T_SWAP = ((772, 917, 801, 949), (887, 917))  # photo px: first T box (x0 y0 x1 y1) <- last T at (x0, y0)
UP = 4  # output px per photo px: the print is redrawn at this scale
INK_BG_SIGMA_PX = 6
INK_STEP = 18  # grey levels below the local dial: ink
INK_CUT = 0.45  # ink coverage at the redrawn edge
INK_SMOOTH = 0.55  # photo px
INK_DARKEN = 0.6  # the photo's ink is black; the viewer's lighting lifts the map
INK_EDGE = 3.0  # coverage -> alpha gain: about 1 output px of anti-aliasing


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    hs = t["hands"]
    m = np.zeros(shape, np.uint8)
    to_px = lambda pts, dx, dy: np.array([[px0 + (x + dx) * S, py0 - (y + dy) * S] for x, y in pts], np.int32)
    for dx, dy in ((0, 0),) + tuple(shadows):
        cv2.circle(m, (int(px0 + dx * S), int(py0 - dy * S)), int((t["hub_radius_mm"][0] + margin) * S), 1, -1)
        for name in ("hour", "minute"):
            cv2.fillPoly(m, [to_px(poly_of(hs[name], "outline_mm", margin, margin), dx, dy)], 1)
        h = hs["seconds"]
        a = math.radians(h["angle_deg"])
        p = lambda r: (int(px0 + (r * math.sin(a) + dx) * S), int(py0 - (r * math.cos(a) + dy) * S))
        cv2.line(m, p(-h["tail_mm"] - margin), p(h["length_mm"] + margin), 1, max(3, int(2 * (h["half_width_mm"] + margin) * S)))
    return m.astype(bool)


def index_mask(t, shape, pad, beyond):
    """The twelve batons, padded by pad mm, reaching beyond mm past the outer end."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    ix = t["index"]
    for h in range(12):
        a = math.radians(h * 30)
        q = [(ix["half_inner"] + pad, ix["inner"] - pad), (ix["half_outer"] + pad, ix["outer"] + beyond), (-ix["half_outer"] - pad, ix["outer"] + beyond),
             (-ix["half_inner"] - pad, ix["inner"] - pad)]
        cv2.fillPoly(m, [np.array([(px0 + (x * math.cos(a) + y * math.sin(a)) * S, py0 - (-x * math.sin(a) + y * math.cos(a)) * S) for x, y in q], np.int32)], 1)
    return m.astype(bool)


def feature_mask(t, shape):
    """Indices, lume dots outside them (1 mm past the outer end) and the prints: never a copy source."""
    return index_mask(t, shape, 0.2, 1.0) | boxes(t, shape, ("logo", "print_1853", "print_powermatic", "print_swiss_made"))


def crisp_print(win, on_dial, bg_ok, blank):
    """UP x map: cubic upsample, then the black print (minute track, TISSOT 1853, Powermatic 80, Swiss Made) redrawn from its
    ink coverage cut at half (sub-pixel edges, about 1 px anti-aliasing) over an ink-free background, so the edges stay sharp
    when the viewer zooms in. Under blank (the modelled batons) only the clean background stays. Returns the map and the ink alpha."""
    g = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY).astype(np.float32)
    clean = bg_ok & on_dial
    blur = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
    rough = blur(g * clean, INK_BG_SIGMA_PX) / np.maximum(blur(clean.astype(np.float32), INK_BG_SIGMA_PX), 1e-3)
    inkish = cv2.dilate(((rough - g > INK_STEP) & on_dial).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    clean = (clean & ~inkish).astype(np.float32)
    bg = blur(win.astype(np.float32) * clean[..., None], INK_BG_SIGMA_PX) / np.maximum(blur(clean, INK_BG_SIGMA_PX)[..., None], 1e-3)
    bgg = bg.mean(2)
    level = float(np.percentile(g[inkish], 3))  # full-coverage ink grey
    ink_bgr = np.median(win[inkish & (g <= level + 8)], 0).astype(np.float32) * INK_DARKEN
    size = (win.shape[1] * UP, win.shape[0] * UP)
    up = lambda a: cv2.resize(a, size, interpolation=cv2.INTER_CUBIC)
    winU, bgU, gU, bggU = up(win.astype(np.float32)), up(bg), up(g), up(bgg)
    cov = blur(np.clip((bggU - gU) / np.maximum(bggU - level, 1.0), 0, 1.2), INK_SMOOTH * UP)  # photo grain off the edges
    a = np.clip((cov - INK_CUT) * INK_EDGE + 0.5, 0, 1) * (up(on_dial.astype(np.float32)) > 0.5)
    near = blur(cv2.dilate((cov > 0.08).astype(np.uint8), np.ones((2 * UP + 1,) * 2, np.uint8)).astype(np.float32), UP)[..., None]
    near = np.maximum(near, blur(up(blank.astype(np.float32)), UP)[..., None])
    base = near * bgU + (1 - near) * winU  # the ink's blurred skirt replaced by the clean background
    out = a[..., None] * ink_bgr + (1 - a[..., None]) * base
    return np.clip(out, 0, 255).astype(np.uint8), a


def aperture_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.array([(px0 + x * S, py0 - y * S) for x, y in t["aperture_mm"]], np.int32)], 1)
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    R = int(math.ceil(t["rings_mm"]["bezel_in"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    mask = hand_mask(t, shape)[sl]
    feats = feature_mask(t, shape)[sl]
    ap = aperture_mask(t, shape)[sl]
    ap_wide = cv2.dilate(ap.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)  # the rim's outer glow
    yy, xx = np.mgrid[-R:R, -R:R]
    rr = np.hypot(xx, yy)

    # on the dial: lighting estimate (normalised blur of the clean dial) + rotated detail
    clean = (~mask & ~feats & ~ap_wide & (rr < t["rings_mm"]["dial"] * S)).astype(np.float32)
    num = cv2.GaussianBlur(win.astype(np.float32) * clean[..., None], (0, 0), LIGHT_SIGMA_PX)
    den = cv2.GaussianBlur(clean, (0, 0), LIGHT_SIGMA_PX)[..., None]
    low = num / np.maximum(den, 1e-3)
    todo = mask & ~ap
    moves = [(sgn * k * 30, 1.0) for k in range(1, 6) for sgn in (1, -1)] + [(sgn * k * 6, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    todo &= rr > HUB_PLAIN_PX  # next to the hub every copy source is a hand or the aperture: lighting only
    used = fill(win, todo, mask | feats | ap_wide, low, moves, (R, R))
    todo |= mask & ~ap & (rr <= HUB_PLAIN_PX)
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur((mask & ~ap).astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    (x0, y0, x1, y1), (sx, sy) = T_SWAP
    ox, oy = px0 - R, py0 - R
    src = img[sy:sy + y1 - y0, sx:sx + x1 - x0].astype(np.float32)
    bg = low[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    ink = src.min((0, 1))
    a = np.clip((bg.mean(2) - src.mean(2)) / max(1.0, float(bg.mean() - ink.mean())), 0, 1)[..., None]  # ink coverage of the clean T
    win[y0 - oy:y1 - oy, x0 - ox:x1 - ox] = np.clip(a * src + (1 - a) * bg, 0, 255).astype(np.uint8)
    on_dial = (rr < t["rings_mm"]["dial"] * S) & ~ap_wide & ~index_mask(t, shape, 0.15, 0.1)[sl]
    win, ink = crisp_print(win, on_dial, ~mask & ~index_mask(t, shape, 0.2, 1.0)[sl] & ~ap_wide, index_mask(t, shape, 0.12, 0.08)[sl])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0] * UP), -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "aperture_kept_px": int((mask & ap).sum()), "lighting_only_px": unfilled,
            "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([cv2.resize(shown, crop.shape[1::-1], interpolation=cv2.INTER_NEAREST), crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
