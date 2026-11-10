"""Cut a clean dial map for the Orient RA-AA0C02L19B from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.orient_ra_aa0c02l19b_dial [out.jpg] [review.png]   # default outputs/watches/orient-ra-aa0c02l19b/dial_photo.jpg

Same method as pipeline/orient_ra_ac0f06l10b_dial.py (hand mask about the hand pivot, boxes) and
pipeline/orient_ra_wj0002l_dial.py (period fill, polar lighting, sunburst grain): each hand pixel is copied from the same radius
6, 12, 18 ... deg away about the index ring centre. No gradient-domain blend (it darkened zones next to bright bars). The square
map is centred on the index ring centre and reaches the brushed bezel's inner edge. Native resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.orient_ra_ac0f06l10b_dial import boxes, hand_mask
from pipeline.orient_ra_wj0002l_dial import fill, lighting, streaks

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-ra-aa0c02l19b-trace.json"
OUT = ROOT / "outputs/watches/orient-ra-aa0c02l19b/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
PERIOD_DEG = 6


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = boxes(t, shape, ("daydate", "logo", "print_wr", "print_6")).astype(np.uint8)
    ix = t["indices"]
    for hr in range(1, 13):
        q = ix["index_12_mm"] if hr == 12 else ix["bar_mm"]
        a = math.radians(hr * 30)
        for r0, r1, hw in ((q["inner"] - 0.4, q["outer"] + 0.4, q["half"] + 0.4), (15.7, 16.8, 0.6)):  # bar, printed lume square
            p0 = (int(px0 + r0 * S * math.sin(a)), int(py0 - r0 * S * math.cos(a)))
            p1 = (int(px0 + r1 * S * math.sin(a)), int(py0 - r1 * S * math.cos(a)))
            cv2.line(m, p0, p1, 1, int(2 * hw * S))
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil((t["bezel_inner_mm"] + 0.1) * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    prints = boxes(t, shape, ("logo", "print_wr", "print_6", "daydate"), pad=0)[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.1)[sl], hand_mask(t, shape)[sl])  # print the hand only grazes stays
    bad = mask | feature_mask(t, shape)[sl]
    todo = mask.copy()
    low = lighting(win, bad, (R, R))
    used = fill(win, todo, bad, low, [(sgn * k * PERIOD_DEG, 1.0) for k in range(1, 30) for sgn in (1, -1)], (R, R))
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo] + streaks(win, ~bad, (R, R))[todo], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
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
