"""Cut a clean dial map for the SNKM87K1 from the front photo, with the hands removed.

    python3 -B -m pipeline.seiko_snkm87_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snkm87k1/dial_photo.jpg

The dial centre has a fine concentric pattern and the chapter ring has a tick every 6 deg, so each pixel under a hand is
copied from the same radius a whole number of minutes (6 deg) round the pivot, nearest first, from a spot that is neither
under a hand nor (inside the centre) on an index, the logo or print. What is left near the pivot is filled with the local
shade. Square map centred on the hand pivot, out to the crystal ring, at the photo's own resolution, light unsharp mask, JPEG.
Hand zones come from config/watches/seiko-snkm87k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snkm87k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snkm87k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.45  # past each hand's outline: its bright edge, soft glow and up to 0.3 mm of trace offset near the hub
SHIFTS = [s * 6 * k for k in range(1, 31) for s in (1, -1)]  # deg, 6 deg steps: the chapter ring ticks line up
PRINT_LEVEL = 110  # inside the centre, a source this bright is an index, logo or print, not dial pattern
PIVOT_MM = 1.5  # the blades are widest where they cross at the hub
SHADE_SIGMA_PX = 5  # copied pixels keep their fine pattern but take the shade of the dial around them


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.hypot(mx, my) < PIVOT_MM
    for name, h in t["hands"].items():
        ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
        along, across = mx * ux + my * uy, np.abs(-mx * uy + my * ux)
        m |= (along > 0) & (along < h["length_mm"] + MARGIN_MM) & (across < h["half_width_mm"] + MARGIN_MM)
        m |= (along > -h["tail_mm"] - MARGIN_MM) & (along <= 0) & (across < h["tail_half_width_mm"] + MARGIN_MM)
    return m


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    y0, x0 = py0 - R, px0 - R
    win = img[y0:py0 + R, x0:px0 + R].copy()
    mask = hand_mask(t, img.shape[:2])[y0:py0 + R, x0:px0 + R]
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    mx, my = (xx - R) / S, -(yy - R) / S
    r, a = np.hypot(mx, my), np.degrees(np.arctan2(mx, my))
    centre = r < t["dial_edge_radius_mm"]
    printed = cv2.dilate((win.mean(2) > PRINT_LEVEL).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & centre
    out_img, todo = win.copy(), mask.copy()
    for d in SHIFTS:
        src_a = np.radians(a + d)
        sx, sy = (R + r * S * np.sin(src_a)).astype(np.float32), (R - r * S * np.cos(src_a)).astype(np.float32)
        bad = cv2.remap((mask | printed).astype(np.uint8), sx, sy, cv2.INTER_NEAREST).astype(bool)
        ok = todo & ~bad
        out_img[ok] = cv2.remap(win, sx, sy, cv2.INTER_LINEAR)[ok]
        todo &= ~ok
    if todo.any():  # a few pixels right at the pivot
        out_img = cv2.inpaint(out_img, todo.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)
    # the dial's light changes with angle: keep the copied fine pattern, take the broad shade from the unmasked dial around it
    f = out_img.astype(np.float32)
    fine = f - cv2.GaussianBlur(f, (0, 0), SHADE_SIGMA_PX)
    valid, shade, left = (~mask & ~printed).astype(np.float32), f.copy(), mask.copy()
    for sigma in (SHADE_SIGMA_PX, 2 * SHADE_SIGMA_PX, 4 * SHADE_SIGMA_PX, 8 * SHADE_SIGMA_PX):
        num = cv2.GaussianBlur(f * valid[..., None], (0, 0), sigma)
        den = cv2.GaussianBlur(valid, (0, 0), sigma)[..., None]
        ok = left & (den[..., 0] > 0.1)
        shade[ok] = (num / np.maximum(den, 1e-6))[ok]
        left &= ~ok
    f[mask] = (shade + fine)[mask]
    out_img = np.clip(f, 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(out_img, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(out_img, 1 + SHARPEN[1], soft, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "inpainted_px": int(todo.sum())}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = win.copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, crop]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
