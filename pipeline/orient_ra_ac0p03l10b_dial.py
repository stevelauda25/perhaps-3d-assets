"""Cut the Orient RA-AC0P03L10B photo maps from the front photo: a clean dial (hands and their shadows removed) and the leather
suede strap resampled to a straight strip (rows past each lug tip, between the strap's own edges on the white background).

    python3 -B -m pipeline.orient_ra_ac0p03l10b_dial [out.jpg] [review.png]   # default outputs/watches/orient-ra-ac0p03l10b/dial_photo.jpg

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

from pipeline.orient_ra_ac0f06l10b_dial import boxes, feature_mask, hand_mask
from pipeline.orient_ra_wj0002l_dial import fill, lighting, streaks
from pipeline.orient_re_av00_dial import strap_strip

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-ra-ac0p03l10b-trace.json"
OUT = ROOT / "outputs/watches/orient-ra-ac0p03l10b/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
PERIOD_DEG = 6
STRAP_W = 614  # map width per strap (22 mm at the photo scale)
STRAP_CENTRE_X = 958  # strap centre past the lug tips
STRAP_END_Y = 1880  # the photo's bottom strap ends (rounded end, shadow) below this row
# the hands sit higher than the dial and the photo is taken a little from below: the hub, the counterweight and the hands'
# shadows show about 1 mm lower than the hand axes, so the hand zones are repeated there
SHADOWS_MM = ((0.07, -0.5), (0.07, -0.97), (0.25, -0.75))
HUB_PX, HUB_R_MM = (962, 848), 2.5


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil((t["bezel_inner_mm"] + 0.1) * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "print_wr", "print_6", "date_window"), pad=0)[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.1)[sl], hand_mask(t, shape, SHADOWS_MM, 0.4)[sl])  # print the hand only grazes stays
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mask |= (np.hypot(xx - HUB_PX[0], yy - HUB_PX[1]) < HUB_R_MM * S)[sl]  # hub and the seconds counterweight at dial level
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
