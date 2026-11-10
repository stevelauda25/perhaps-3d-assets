"""Cut a clean dial map for the Hamilton H70515137 (Khaki Field Auto 42 mm) from the official front render, the hands removed.

    python3 -B -m pipeline.hamilton_h70515137_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h70515137/dial_photo.jpg

Same method as pipeline/hamilton_h77616533_dial.py on a flat black base: each hand pixel is copied from the same radius 30,
60 ... deg, then 6, 12 ... deg away about the pivot (numerals, the 13-24 ring and the chapter ring repeat), with every bright
print protected as a copy source. The map reaches the polished bezel's inner edge. Native resolution, light unsharp mask, JPEG.
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
TRACE = ROOT / "config/watches/hamilton-h70515137-trace.json"
OUT = ROOT / "outputs/watches/hamilton-h70515137/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.3
SHADOWS_MM = ((0.25, -0.25),)
NUMERALS = []  # photo px boxes where only a narrow mask is used
# the minute hand hides 14: drawn again from the 1 of 13 and the 4 of 24 (photo px: dst x0 y0, src x0 y0 x1 y1), placed as the
# mirror of 22 about the 12-6 line
DIGITS_14 = [((1084, 812), (1015, 742, 1030, 771)), ((1107, 812), (943, 711, 968, 740))]
CHAPTER_PX = 380  # inner edge of the grey chapter ring (photo px about the pivot)
H_BOX = [830, 806, 857, 834]  # the H of HAMILTON: the hour hand covers its left leg; the right half is mirrored over


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
        cv2.circle(m, p(-h["tail_mm"]), int((h["disc_mm"] + margin) * S), 1, -1)
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    R = int(math.ceil(t["rings_mm"]["bezel_in"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "print_khaki", "date_window"))
    for x0, y0, x1, y1 in NUMERALS:
        prints[y0:y1, x0:x1] = True
    prints = prints[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.3)[sl], hand_mask(t, shape)[sl])
    gray = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY)
    yy, xx = np.mgrid[-R:R, -R:R]
    # bright prints inside the chapter ring are never a copy source; the chapter ring itself repeats every 6 deg and is copied
    feats = cv2.dilate(((gray > 90) & ~mask & (np.hypot(xx, yy) < CHAPTER_PX)).astype(np.uint8), np.ones((11, 11), np.uint8)).astype(bool)
    black = np.median(win[~mask & ~feats & (np.hypot(xx, yy) < 0.6 * R)].reshape(-1, 3), 0)
    todo = mask.copy()
    low = np.broadcast_to(black.astype(np.float32), win.shape).copy()
    moves = [(sgn * k * 30, 1.0) for k in range(1, 6) for sgn in (1, -1)] + [(sgn * k * 6, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    used = fill(win, todo, mask | feats, low, moves, (R, R))
    unfilled = int(todo.sum())
    win[todo] = np.median(win[~mask & ~feats & (np.hypot(xx, yy) < 2.5 * S)].reshape(-1, 3), 0)  # the hub zone: the dial colour next to it
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    ox, oy = px0 - R, py0 - R
    clean = win.copy()
    for (dx_, dy_), (x0, y0, x1, y1) in DIGITS_14:
        win[dy_ - oy:dy_ - oy + y1 - y0, dx_ - ox:dx_ - ox + x1 - x0] = clean[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    x0, y0, x1, y1 = H_BOX
    half = (x1 - x0) // 2
    win[y0 - oy:y1 - oy, x0 - ox:x0 - ox + half] = clean[y0 - oy:y1 - oy, x1 - ox - half:x1 - ox][:, ::-1]
    sharpen = lambda a: cv2.addWeighted(a, 1 + SHARPEN[1], cv2.GaussianBlur(a, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    crop = sharpen(win)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
