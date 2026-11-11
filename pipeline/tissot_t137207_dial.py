"""Cut the dial map for the Tissot T137.207.11.091.00 (PRX Powermatic 80, green waffle dial) from the official front render: the
hands removed, the applied indices and the date frame blanked (they are modelled), the white print redrawn sharp at 4x.

    python3 -B -m pipeline.tissot_t137207_dial [out.jpg] [review.png]   # default outputs/watches/tissot-t137.207.11.091.00/dial_photo.jpg

Square map to the bezel's inner edge. The waffle grid is square and centred on the pivot, so each hand pixel takes its detail
from the same spot turned 90, 180 or 270 deg first (then 30 deg steps), over a local lighting estimate (masked normalised
blur: the dial darkens toward the edge). Prints, indices and the date window are never a copy source. The print (white ink,
minute track, date disc) is redrawn at 4x like pipeline/bulova_96b258_dial.py; light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline import bulova_96b258_dial as B
from pipeline.hamilton_h77616533_trace import load
from pipeline.hamilton_h82405130_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/tissot-t137.207.11.091.00-trace.json"
OUT = ROOT / "outputs/watches/tissot-t137.207.11.091.00/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 92
MARGIN_PX = 5
SHADOW_PX = ((3, 3), (5, 5))
LIGHT_SIGMA_PX = 10
LEVEL_SIGMA_PX = 10
HUB_PATCH_MAX_PX = 90  # the quarter-turn copies all land on a hand inside this radius
PRINT_BOX = (740, 950, 935, 995)  # photo px: POWERMATIC 80
INK_MIN = 150  # white print: every channel bright (the waffle's green highlights are not ink)


def hand_mask(t, shape, shadows=SHADOW_PX, margin=MARGIN_PX):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    hs = t["hands"]
    for dx, dy in ((0, 0),) + tuple(shadows):
        for name in ("hour", "minute"):
            cv2.fillPoly(m, [np.array([(px0 + x + dx, py0 - y + dy) for x, y in B.outline_poly(hs[name], S, margin)], np.int32)], 1)
        h = hs["seconds"]
        a = math.radians(h["angle_deg"])
        p = lambda r: (int(px0 + r * S * math.sin(a) + dx), int(py0 - r * S * math.cos(a) + dy))
        cv2.line(m, p(-h["tail_mm"]), p(h["length_mm"]), 1, int(2 * h["half_width_mm"] * S + 2 * margin))
        cv2.line(m, p(-h["tail_mm"]), p(-0.3), 1, int(2 * h["tail_half_mm"] * S + 2 * margin))
        cv2.circle(m, (px0 + dx, py0 + dy), int(t["hub_radius_mm"][0] * S + margin + 9), 1, -1)
    return m.astype(bool)


def index_mask(t, shape, pad):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["index"]
    m = np.zeros(shape, np.uint8)
    for hr in range(12):
        if hr == 3:
            continue
        a = math.radians(hr * 30)
        for off, hw in (((-ix["double_offset"], ix["double_half"]), (ix["double_offset"], ix["double_half"])) if hr == 0 else ((0, ix["half"]),)):
            q = [(off + hw + pad, ix["inner"] - pad), (off + hw + pad, ix["outer"] + pad), (off - hw - pad, ix["outer"] + pad), (off - hw - pad, ix["inner"] - pad)]
            cv2.fillPoly(m, [np.array([(px0 + (x * math.cos(a) + y * math.sin(a)) * S, py0 - (-x * math.sin(a) + y * math.cos(a)) * S) for x, y in q], np.int32)], 1)
    return m.astype(bool)


def date_masks(t, shape, pad_px):
    m = t["manual_px"]["date"]
    fr, op = np.zeros(shape, bool), np.zeros(shape, bool)
    x0, y0, x1, y1 = m["frame"]
    fr[y0 - pad_px:y1 + pad_px, x0 - pad_px:x1 + pad_px] = True
    x0, y0, x1, y1 = m["opening"]
    op[y0 + 1:y1 - 1, x0 + 1:x1 - 1] = True
    return fr, op


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    shape = img.shape[:2]
    R = int(math.ceil(t["rings_mm"]["bezel_in"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    mask = hand_mask(t, shape)[sl]
    x0, y0, x1, y1 = PRINT_BOX  # the seconds hand grazes the P of POWERMATIC: there only the hand itself goes
    narrow = hand_mask(t, shape, (), 1)[sl]
    box = np.zeros_like(mask)
    box[y0 - py0 + R:y1 - py0 + R, x0 - px0 + R:x1 - px0 + R] = True
    mask = np.where(box, narrow, mask)
    fr, op = (a[sl] for a in date_masks(t, shape, 3))
    idx = index_mask(t, shape, 0.15)[sl]
    g = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY).astype(np.float32)
    feats = cv2.dilate((g > 150).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~mask | idx | fr
    yy, xx = np.mgrid[-R:R, -R:R]
    rr = np.hypot(xx, yy)
    clean = (~mask & ~feats).astype(np.float32)
    low = cv2.GaussianBlur(win.astype(np.float32) * clean[..., None], (0, 0), LIGHT_SIGMA_PX) / \
        np.maximum(cv2.GaussianBlur(clean, (0, 0), LIGHT_SIGMA_PX)[..., None], 1e-3)
    todo = mask.copy()
    moves = [(90, 1.0), (-90, 1.0), (180, 1.0)]  # only quarter turns keep the square grid on itself
    used = fill(win, todo, mask | feats, low, moves, (R, R))
    # next to the hub every turned copy lands on a hand: copy the waffle from the best-matching spot elsewhere instead
    rh = int(max(rr[todo & (rr < HUB_PATCH_MAX_PX)].max(initial=0), t["hub_radius_mm"][0] * S + MARGIN_PX + 8))
    detail = win.astype(np.float32) - low
    ring_m = ((rr >= rh) & (rr < rh + 16) & ~mask & ~feats)[R - rh - 16:R + rh + 16, R - rh - 16:R + rh + 16]
    tpl = detail[R - rh - 16:R + rh + 16, R - rh - 16:R + rh + 16]
    score = cv2.matchTemplate(detail, tpl, cv2.TM_SQDIFF, mask=np.repeat(ring_m[..., None], 3, 2).astype(np.float32))
    oy, ox = np.mgrid[:score.shape[0], :score.shape[1]]
    cx = cy = R - rh - 16
    hub = (rr < rh + 2) & todo
    need = hub[R - rh - 16:R + rh + 16, R - rh - 16:R + rh + 16].astype(np.float32)
    hits = cv2.matchTemplate((mask | feats).astype(np.float32), need, cv2.TM_CCORR)  # bad source pixels under the pixels to fill
    score[(np.hypot(ox - cx, oy - cy) < 2 * rh) | (np.hypot(ox + rh + 16 - R, oy + rh + 16 - R) > R * 0.8) | (hits > 0.5)] = np.inf
    assert np.isfinite(score).any(), "no clean waffle patch for the hub"
    by, bx = np.unravel_index(np.argmin(score), score.shape)
    dy, dx = by - cy, bx - cx
    ys, xs = np.nonzero(hub)
    win[ys, xs] = np.clip(low[ys, xs] + detail[ys + dy, xs + dx], 0, 255).astype(np.uint8)
    todo &= ~hub
    used["hub patch from %+d %+d px" % (dx, dy)] = len(ys)
    left = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    ring = (cv2.dilate(mask.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~mask & ~feats).astype(np.float32)
    mloc = lambda a, w: cv2.GaussianBlur(a * w[..., None], (0, 0), LEVEL_SIGMA_PX) / np.maximum(cv2.GaussianBlur(w, (0, 0), LEVEL_SIGMA_PX)[..., None], 1e-3)
    shift = mloc(img[sl].astype(np.float32), ring) - mloc(win.astype(np.float32), mask.astype(np.float32))
    win[mask] = np.clip(win[mask] + shift[mask], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blank = index_mask(t, shape, 0.08)[sl] | (fr & ~op)
    keep = cv2.dilate(op.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)  # date disc: the photo as it is (dark digit on white)
    win, ink = B.crisp_light_print(win, (rr < R - 1) & ~keep, np.ones_like(mask), blank & ~keep, INK_MIN)
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0] * B.UP), -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "upscale": B.UP,
            "masked_px": int(mask.sum()), "lighting_only_px": left, "ink": ink, "filled_from": {k: v for k, v in used.items() if v}}
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
    print({k: m[k] for k in ("size_px", "masked_px", "lighting_only_px", "ink")}, "->", dest)
