"""Cut the Hamilton H76305530 (Khaki Aviation Pilot Auto) photo maps from the front photo: a clean dial (hands and their
shadows removed) and the brown leather strap resampled to a straight strip.

    python3 -B -m pipeline.hamilton_h76305530_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h76305530/dial_photo.jpg

Dial: same method as pipeline/hamilton_h82405130_dial.py on a flat black base: each hand pixel is copied from the same radius
30, 60 ... deg away (numerals and chapter-ring blocks repeat every 30 deg), then 6, 12 ... deg. Every bright print outside the
hands is protected as a copy source. The hands are masked from their traced outlines; the open skeleton windows (hour tip,
minute root) keep the photo, which is the dial seen through them. The map reaches the chapter ring's outer edge. Strap: each
photo row of leather past the lug tips is resampled between its own edges (pipeline.orient_re_av00_dial.strap_strip), top
strap in the left half, bottom strap in the right half of strap_photo.jpg. Native resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h82405130_dial import fill
from pipeline.orient_re_av00_dial import strap_strip

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/hamilton-h76305530-trace.json"
OUT = ROOT / "outputs/watches/hamilton-h76305530/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.4
SHADOWS_MM = ((0.45, -0.45), (0.25, -0.25))  # light from the upper left
HUB_ZONE_MM = 0.95
STRAP_W = 707  # map width per strap (19.5 mm at the photo scale)
STRAP_CENTRE_X = 808
STRAP_END_Y = 2480  # the bottom strap's rounded end below this row


def poly_of(h, key, r_pad=0.0, w_pad=0.0):
    """Hand outline (or window) in mm about the pivot: [r, half] pairs mirrored, turned to the hand angle."""
    t = math.radians(h["angle_deg"])
    pts = h[key]
    side = [(r, v + w_pad) for r, v in pts]
    side[0], side[-1] = (side[0][0] - r_pad, side[0][1]), (side[-1][0] + r_pad, side[-1][1])
    loop = [(v, r) for r, v in side] + [(-v, r) for r, v in side[::-1]]
    return [(x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)) for x, y in loop]


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    hs = t["hands"]
    m = np.zeros(shape, np.uint8)
    win = np.zeros(shape, np.uint8)
    to_px = lambda pts, dx, dy: np.array([[px0 + (x + dx) * S, py0 - (y + dy) * S] for x, y in pts], np.int32)
    for dx, dy in ((0, 0),) + tuple(shadows):
        cv2.circle(m, (int(px0 + dx * S), int(py0 - dy * S)), int((HUB_ZONE_MM + margin) * S), 1, -1)
        for name in ("hour", "minute"):
            h = hs[name]
            cv2.fillPoly(m, [to_px(poly_of(h, "outline_mm", margin, margin), dx, dy)], 1)
            tl, tw = h["tail_mm"]
            a = math.radians(h["angle_deg"])
            end = (-tl * math.sin(a) + dx, -tl * math.cos(a) + dy)
            cv2.line(m, (int(px0 + dx * S), int(py0 - dy * S)), (int(px0 + end[0] * S), int(py0 - end[1] * S)), 1, int(2 * (tw + margin) * S))
        h = hs["seconds"]
        a = math.radians(h["angle_deg"])
        u = (math.sin(a), math.cos(a))
        p = lambda r: (int(px0 + (r * u[0] + dx) * S), int(py0 - (r * u[1] + dy) * S))
        cv2.line(m, p(-h["tail_mm"]), p(h["length_mm"]), 1, int(2 * (h["half_width_mm"] + margin) * S))
        a0, aw = h["arrow_mm"]
        tri = [(aw + margin, a0 - margin), (-aw - margin, a0 - margin), (0, h["length_mm"] + margin)]
        cv2.fillPoly(m, [to_px([(x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)) for x, y in tri], dx, dy)], 1)
        cv2.circle(m, p(-h["tail_mm"]), int((h["ring_mm"][0] + margin) * S), 1, -1)
    for name in ("hour", "minute"):  # the open skeleton parts show the dial: keep the photo inside them (inset by the margin)
        cv2.fillPoly(win, [to_px(poly_of(hs[name], "window_mm", -0.08, -0.08), 0, 0)], 1)
    return m.astype(bool) & ~cv2.erode(win, np.ones((5, 5), np.uint8)).astype(bool)


def boxes(t, shape, keys):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in keys:
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S), int(py0 - b[1] * S)), (int(px0 + b[2] * S), int(py0 - b[3] * S)), 1, -1)
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["rings_mm"]["chapter"] * S))
    assert py0 - R >= 0 and px0 - R >= 0
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "print_auto", "print_swiss_made"))[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.12)[sl], hand_mask(t, shape)[sl])  # print the hand only crosses stays
    gray = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY)
    rr = np.hypot(*np.mgrid[-R:R, -R:R])
    # every bright print on the dial outside the hands must not be copied into a hand zone; the chapter ring's marks repeat
    # every 6 / 30 deg and are copied
    feats = cv2.dilate(((gray > 90) & ~mask & (rr < t["rings_mm"]["dial"] * S - 3)).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    black = np.median(win[~mask & ~feats & (rr < t["rings_mm"]["dial"] * S * 0.95)].reshape(-1, 3), 0)
    todo = mask.copy()
    bad = mask | feats
    low = np.broadcast_to(black.astype(np.float32), win.shape).copy()
    moves = [(sgn * k * 30, 1.0) for k in range(1, 6) for sgn in (1, -1)] + [(sgn * k * 6, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    used = fill(win, todo, bad, low, moves, (R, R))
    unfilled = int(todo.sum())
    win[todo] = black
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
    top, top_rows = strap_strip(img, range(t0 - 5, -1, -1), STRAP_CENTRE_X, STRAP_W)
    bot, bot_rows = strap_strip(img, range(t1 + 5, STRAP_END_Y), STRAP_CENTRE_X, STRAP_W)
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
