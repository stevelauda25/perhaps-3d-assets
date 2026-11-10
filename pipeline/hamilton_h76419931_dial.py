"""Cut the Hamilton H76419931 (Khaki Aviation Pilot Pioneer Mechanical) photo maps from the official front render: a clean
dial (hands removed) out to the polished bezel ring, and the grey NATO strap resampled to a straight strip.

    python3 -B -m pipeline.hamilton_h76419931_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h76419931/dial_photo.jpg

Dial: on the grained dial inside the chapter ring the hand zones are relit from the clean dial and regrained with tiles from
its largest clean squares (pipeline.hamilton_h76709530_dial.fill_grain: a turned copy would turn the grain against the
light); on the chapter ring each pixel is copied from 6, 12 ... deg away about the pivot. Strap: each row between its alpha
edges (pipeline.hamilton_h77616533_dial.strap_strip), top strap in the left half, bottom in the right half of strap_photo.jpg.
Native resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h76305530_dial import boxes, poly_of
from pipeline.hamilton_h77616533_trace import load
from pipeline.hamilton_h76709530_dial import fill_grain
from pipeline.hamilton_h77616533_dial import strap_strip
from pipeline.hamilton_h82405130_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/hamilton-h76419931-trace.json"
OUT = ROOT / "outputs/watches/hamilton-h76419931/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.3
SHADOWS_MM = ((0.25, -0.25),)
NUMERALS = [[452, 455, 500, 506], [715, 462, 752, 506], [538, 624, 562, 642]]  # 10, 2, M of MECHANICAL (render px): narrow mask
ZERO_OF_10 = [467, 460, 490]  # x0, y0, y1 of the 0 (render px); the hour tip covers its right half: the left half is mirrored about x 478.5
CHAPTER_PX = 180  # inner edge of the chapter ring (render px about the pivot): grain inside, turned copies outside
GROW_PX = 8  # the render's hand shadows reach this far past the hand zones
STRAP_W = 270  # map width per strap (16.7 mm at the render scale)


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
        cv2.line(m, p(-h["tail_mm"]), p(h["length_mm"]), 1, int(2 * (h["half_width_mm"] + margin) * S))
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    R = int(math.ceil(t["rings_mm"]["bezel_in"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "print_mech", "print_swiss_made"))
    for x0, y0, x1, y1 in NUMERALS:
        prints[y0:y1, x0:x1] = True
    prints = prints[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.15)[sl], hand_mask(t, shape)[sl])
    gray = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY)
    yy, xx = np.mgrid[-R:R, -R:R]
    rr = np.hypot(xx, yy)
    inner = rr < CHAPTER_PX
    printed = cv2.morphologyEx(((gray > 110) & ~mask).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    feats = cv2.dilate(printed, np.ones((9, 9), np.uint8)).astype(bool)
    grown = cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * GROW_PX + 1,) * 2)).astype(bool)
    mask = mask | (grown & inner & ~feats & ~prints)
    todo = mask & inner
    shade = cv2.dilate(mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))).astype(bool)
    squares = fill_grain(win, todo, shade | feats | prints | ~inner)  # print boxes never feed the grain tiles
    todo = mask & ~inner
    low = np.zeros(win.shape, np.float32)
    moves = [(sgn * k * 30, 1.0) for k in range(1, 6) for sgn in (1, -1)] + [(sgn * k * 6, 1.0) for k in range(1, 30) for sgn in (1, -1)]  # dots every 30 deg
    used = fill(win, todo, mask | (feats & inner), low, moves, (R, R))
    used["grain_squares_px"] = squares
    unfilled = int(todo.sum())
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    ox, oy = px0 - R, py0 - R
    x0, y0, y1 = ZERO_OF_10
    w0 = 12  # left half width (the 0 is 23 px wide, centre column 478.5)
    left = img[y0 - 2:y1 + 9, x0:x0 + w0]
    win[y0 - 2 - oy:y1 + 9 - oy, x0 + w0 - ox:x0 + 2 * w0 - ox] = left[:, ::-1]
    sharpen = lambda a: cv2.addWeighted(a, 1 + SHARPEN[1], cv2.GaussianBlur(a, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    crop = sharpen(win)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")

    y0c, y1c = t["manual_px"]["case_rows_px"]
    alpha = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)[..., 3]
    top, top_rows = strap_strip(img, alpha, range(y0c - 4, -1, -1), STRAP_W)
    bot, bot_rows = strap_strip(img, alpha, range(y1c + 4, img.shape[0]), STRAP_W)
    n = max(len(top), len(bot))
    pad = lambda a: np.vstack([a, np.repeat(a[-1:], n - len(a), 0)])
    strap = sharpen(np.hstack([pad(top), pad(bot)]))
    sp = out.with_name("strap_photo.jpg")
    cv2.imwrite(str(sp), strap, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    smeta = {"size_px": [strap.shape[1], strap.shape[0]], "width_px": STRAP_W, "rows_px": {"top": top_rows, "bottom": bot_rows},
             "scale_px_per_mm": S, "lug_tips_px": [y0c, y1c]}
    sp.with_suffix(".json").write_text(json.dumps(smeta) + "\n")
    meta["strap"] = {"rows": {k: len(v) for k, v in smeta["rows_px"].items()}}
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
