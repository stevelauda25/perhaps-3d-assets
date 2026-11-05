"""Cut a clean dial map for the SNK607K1 from the front photo: the hands are removed and filled from the woven pattern itself.

    python3 -B -m pipeline.seiko_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snk607k1/dial_photo.jpg

The woven dial repeats every 43.5 px (0.60 mm) across, so each pixel under a hand is copied from the nearest unmasked pixel
a whole number of periods to the left or right on the same row. Indices, logo, print and the day-date stay in the map (the
build may cover indices and logo with geometry). The map is square, centred on the hand pivot, out to the crystal ring, and
keeps the photo's lighting. It stays at the photo's own resolution (no resampling), gets a light unsharp mask and is saved as
JPEG so the GLB stays small. Hand zones come from config/watches/seiko-snk607k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snk607k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snk607k1/dial_photo.jpg"
PERIOD_PX = 43.5
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
# hand: (half width mm, tail mm); wide enough to take the edge highlights and the shadow each hand casts on the dial
HAND_ZONE = {"hour": (0.95, 0.0), "minute": (0.9, 0.0), "seconds": (0.22, None)}
PIVOT_MM = 1.3
REFLECTION = (220.0, 3.0, 0.5)  # crystal reflection wedge toward 7 o'clock: angle, length, half width (mm)
SHADOW_MM = (0.45, -0.45)  # light comes from the upper left, so each hand's shadow lies down and to the right


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.hypot(mx, my) < PIVOT_MM
    zones = [(h["angle_deg"], h["length_mm"] + 0.3, *HAND_ZONE[n]) for n, h in t["hands"].items()]
    zones = [(a, l, half, t["hands"]["seconds"]["tail_mm"] + 0.3 if tail is None else tail) for a, l, half, tail in zones]
    zones.append((REFLECTION[0], REFLECTION[1], REFLECTION[2], 0.0))
    for ang, length, half, tail in zones:
        ux, uy = math.sin(math.radians(ang)), math.cos(math.radians(ang))
        for ox, oy in ((0.0, 0.0), SHADOW_MM):
            sx, sy = mx - ox, my - oy
            along, across = sx * ux + sy * uy, -sx * uy + sy * ux
            m |= (along > -tail) & (along < length) & (np.abs(across) < half)
    tip = t["hands"]["seconds"]  # white lume tip of the seconds hand
    a = math.radians(tip["angle_deg"])
    m |= np.hypot(mx - tip["length_mm"] * math.sin(a), my - tip["length_mm"] * math.cos(a)) < 0.35
    return m


def fill_by_period(img, mask):
    out, todo = img.copy(), mask.copy()
    for k in range(1, 12):
        for sign in (1, -1):
            shift = int(round(sign * k * PERIOD_PX))
            src_ok = np.roll(~mask, -shift, axis=1)  # source pixel at x + shift is not under a hand
            take = todo & src_ok
            out[take] = np.roll(img, -shift, axis=1)[take]
            todo &= ~take
        if not todo.any():
            break
    return out, int(todo.sum())


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    clean, left = fill_by_period(img, mask)
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    crop = clean[py0 - R:py0 + R, px0 - R:px0 + R]
    out.parent.mkdir(parents=True, exist_ok=True)
    soft = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], soft, -SHARPEN[1], 0)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "period_px": PERIOD_PX, "unfilled_px": left}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        before = img[py0 - R:py0 + R, px0 - R:px0 + R]
        m = mask[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = before.copy()
        shown[m] = (0.5 * shown[m] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1100, 1100), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
