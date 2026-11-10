"""Cut the Hamilton H69439940 photo maps from the front photo: a clean dial (hands and their shadows removed) and the NATO strap
resampled to a straight strip.

    python3 -B -m pipeline.hamilton_h69439940_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h69439940/dial_photo.jpg

Same method as pipeline/orient_ra_ac0p03l10b_dial.py (fill and lighting from pipeline/orient_ra_wj0002l_dial.py): the hand
zones are the traced hand parts rasterised, grown by a margin and repeated at the shadow offsets; each zone pixel is copied
from the same radius 6, 12, 18 ... deg away (the minute track repeats every 6 deg) over a polar lighting estimate. Printed
numerals and the logo inside the minute track are never used as a source, so only plain dial is copied there; next to print
only the hand itself is replaced, inpainted from the print around it (print under a wide hand is not rebuilt: the 3D hands
cover it, posed at the photo's time). The square map is centred on the hand pivot and
reaches the bezel's inner edge. Strap: the bottom strap's rows past the lug tips resampled between its own edges
(pipeline/orient_re_av00_dial.strap_strip); strap_photo.json lists the photo row of every map row. Native resolution, light
unsharp mask, JPEG. build() is shared with pipeline/hamilton_h70405710_dial.py.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.orient_re_av00_dial import strap_strip
from pipeline.orient_ra_wj0002l_dial import fill, lighting

ROOT = Path(__file__).resolve().parents[1]
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
PERIOD_DEG = 6

CFG = {
    "trace": ROOT / "config/watches/hamilton-h69439940-trace.json",
    "out": ROOT / "outputs/watches/hamilton-h69439940/dial_photo.jpg",
    "margin_mm": 0.3,
    "shadows_mm": ((0.3, 0.0), (0.6, -0.05), (0.9, -0.1), (1.2, -0.15)),  # light from the left: the shadows fall to the right
    "hub_zone_mm": 1.35,
    "feature_r_mm": 12.5,  # inside the minute track (12.7-14.4 mm), which is copied 6 deg over
    "feature": lambda img: img[..., 2].astype(int) > 120,  # white and cream print on the blue dial
    "strap_centre_x": 895,
    "strap_width_px": 711,  # 20 mm at the photo scale
    "strap_end_y": 2790,  # the bottom strap's keeper ends below this row
}


def hand_mask(t, shape, margin, shadows, hub_zone):
    S, (px, py) = t["scale_px_per_mm"], t["hand_pivot_px"]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + tuple(shadows):
        for h in t["hands"].values():
            a = math.radians(h["angle_deg"])
            for p in h["parts"]:
                pts = [(px + (x * math.cos(a) + y * math.sin(a) + dx) * S, py - (-x * math.sin(a) + y * math.cos(a) + dy) * S)
                       for x, y in p["poly_mm"]]
                cv2.fillPoly(m, [np.round(np.array(pts) * 4).astype(np.int32)], 1, cv2.LINE_8, shift=2)
        cv2.circle(m, (int(round(px + dx * S)), int(round(py - dy * S))), int(hub_zone * S), 1, -1)
    k = int(2 * margin * S) | 1
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))).astype(bool)


def build(cfg, out, review=None):
    t = json.loads(cfg["trace"].read_text())
    S, (px, py) = t["scale_px_per_mm"], t["hand_pivot_px"]
    cx, cy = int(round(px)), int(round(py))
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil((t["bezel_inner_mm"] + 0.1) * S))
    sl = np.s_[cy - R:cy + R, cx - R:cx + R]
    win = img[sl].copy()
    full = hand_mask(t, img.shape[:2], cfg["margin_mm"], cfg["shadows_mm"], cfg["hub_zone_mm"])[sl]
    tight = hand_mask(t, img.shape[:2], 0.04, (), cfg["hub_zone_mm"])[sl]
    near = hand_mask(t, img.shape[:2], 0.3, (), cfg["hub_zone_mm"])[sl]  # the hands' own bright edge is not print
    yy, xx = np.mgrid[-R:R, -R:R]
    feats = cfg["feature"](win) & (np.hypot(xx, yy) < cfg["feature_r_mm"] * S) & ~near
    feats = cv2.dilate(feats.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    mask = np.where(feats, tight, full)  # print next to a hand keeps its pixels; only the hand itself is replaced there
    feats &= ~mask
    todo, bad = mask.copy(), mask | feats
    low = lighting(win, bad, (R, R))
    moves = [(sgn * k * PERIOD_DEG, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    used = fill(win, todo, bad, low, moves, (R, R))
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    # where a thin needle crossed print: inpaint from the strokes on both sides (wide hands cover their print in 3D)
    disk = lambda mm_: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * mm_ * S) | 1,) * 2)
    cut = (mask & cv2.dilate(feats.astype(np.uint8), disk(0.55)).astype(bool)).astype(np.uint8)
    cut &= ~cv2.dilate(cv2.morphologyEx(cut, cv2.MORPH_OPEN, disk(0.35)), disk(0.2))
    win = cv2.inpaint(win, cut * 255, 4, cv2.INPAINT_TELEA)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    sharpen = lambda a: cv2.addWeighted(a, 1 + SHARPEN[1], cv2.GaussianBlur(a, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    crop = sharpen(win)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [cx, cy], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")

    t0, t1 = t["manual_px"]["lug_tips_y"]
    W = cfg["strap_width_px"]
    top, top_rows = strap_strip(img, range(t0 - 5, -1, -1), cfg["strap_centre_x"], W)
    bot, bot_rows = strap_strip(img, range(t1 + 5, cfg["strap_end_y"]), cfg["strap_centre_x"], W)
    n = max(len(top), len(bot))
    pad = lambda a: np.vstack([a, np.repeat(a[-1:], n - len(a), 0)])
    strap = sharpen(np.hstack([pad(top), pad(bot)]))
    sp = out.with_name("strap_photo.jpg")
    cv2.imwrite(str(sp), strap, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    smeta = {"size_px": [strap.shape[1], strap.shape[0]], "width_px": W, "rows_px": {"top": top_rows, "bottom": bot_rows},
             "scale_px_per_mm": S, "lug_tips_px": [t0, t1]}
    sp.with_suffix(".json").write_text(json.dumps(smeta) + "\n")
    meta["strap"] = {"rows": {k: len(v) for k, v in smeta["rows_px"].items()}, "size_px": smeta["size_px"]}
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        shown[feats] = (0.5 * shown[feats] + [0, 127, 0]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
        cv2.imwrite(str(review.with_name(review.stem + "_strap.png")), strap)
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else CFG["out"]
    print(build(CFG, dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
