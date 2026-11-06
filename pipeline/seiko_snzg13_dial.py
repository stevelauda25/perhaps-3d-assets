"""Cut the SNZG13K1 dial map (hands removed) from the front photo.

    python3 -B -m pipeline.seiko_snzg13_dial [out_dir] [review.png]     # default outputs/watches/seiko-snzg13k1/

dial_photo.jpg: square crop centred on the hand pivot out to the bezel's inner edge, native resolution, light unsharp mask,
JPEG. Same method as pipeline/seiko_snzg11_dial.py (same dial layout, black instead of navy): each hand zone is filled with
the local black plus grain of the same strength; inside the traced hand outline (+0.1 mm) everything is filled, in the halo
and shadow band around it only dark pixels, so print beside a hand keeps its edge.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snzg13k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snzg13k1"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
CORE_MM, HALO_MM = 0.1, 0.4
SHADOW_MM = (0.25, -0.25)  # light from the upper left
PRINT_GRAY = 95  # print and hands are brighter than this; the black dial is about 20-35


def hand_polys(t):
    """Hand outlines in mm (sword hour/minute, seconds needle with its arrowhead and its paddle tail)."""
    out = []
    for name, h in t["hands"].items():
        a = math.radians(h["angle_deg"])
        ux, uy = math.sin(a), math.cos(a)
        L, hw = h["length_mm"], h["half_width_mm"]
        if name == "seconds":
            a0, a1 = h["arrow_from_to_mm"]
            tl, tw = h["tail_mm"], h["tail_half_width_mm"]
            local = [(-tw, -tl), (tw, -tl), (tw, -0.5), (hw, a0), (0.42, a0), (hw, a1), (hw, L), (-hw, L), (-hw, a1), (-0.42, a0), (-hw, a0), (-tw, -0.5)]
        else:
            local = [(-hw, 0), (hw, 0), (hw, L - 1.1), (0, L), (-hw, L - 1.1)]
        out.append([(x * uy + y * ux, -x * ux + y * uy) for x, y in local])
    return out


def mask_mm(t, shape, grow, offset=(0, 0)):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    P = lambda p: (int(round((px0 + (p[0] + offset[0]) * S) * 4)), int(round((py0 - (p[1] + offset[1]) * S) * 4)))
    for poly in hand_polys(t):
        cv2.fillPoly(m, [np.array([P(p) for p in poly], np.int32)], 1, cv2.LINE_8, 2)
    cv2.circle(m, P((0, 0)), int(t["hub_radius_mm"][0] * S * 4), 1, -1, cv2.LINE_8, 2)
    r = max(1, int(round(grow * S)))
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))).astype(bool)


def dial_map(t, img):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    R = int(round(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].astype(np.float32)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[sl]
    core = mask_mm(t, img.shape[:2], CORE_MM)[sl]
    halo = (mask_mm(t, img.shape[:2], HALO_MM) | mask_mm(t, img.shape[:2], HALO_MM, SHADOW_MM))[sl]
    bright = gray > PRINT_GRAY
    fill = core | (halo & ~bright)
    printed = cv2.dilate(bright.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    valid = (~(halo | printed)).astype(np.float32)[..., None]
    low = None
    for sig in (60, 20, 7):  # wide pass first: the hub zone is far from clean dial
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.2, est, low)
    clean = (valid[..., 0] > 0) & (np.hypot(*np.mgrid[-R:R, -R:R]) < 0.75 * R)
    grain = float(np.std((win - cv2.GaussianBlur(win, (0, 0), 3))[clean]))
    noise = cv2.GaussianBlur(np.random.default_rng(11).normal(0, 1, win.shape).astype(np.float32), (0, 0), 0.8)
    noise *= grain / max(float(np.std(noise)), 1e-6)
    filled = np.where(fill[..., None], low + noise, win)
    soft = cv2.GaussianBlur(fill.astype(np.float32), (0, 0), 1.2)[..., None]
    win = np.clip(soft * filled + (1 - soft) * win, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    return cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0), fill, sl, round(grain, 2)


def build(out_dir=OUT, review=None):
    t = json.loads(TRACE.read_text())
    img = cv2.imread(str(ROOT / t["source"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    crop, fill, sl, grain = dial_map(t, img)
    cv2.imwrite(str(out_dir / "dial_photo.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "dial_size_px": crop.shape[0], "filled_px": int(fill.sum()), "grain_std": grain}
    (out_dir / "dial_photo.json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[fill] = (0.5 * shown[fill] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, crop]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
