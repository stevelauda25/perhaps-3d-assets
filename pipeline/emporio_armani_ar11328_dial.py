"""Cut the Emporio Armani AR11328 dial map and mesh map from the front photo, with the hands, hub and their halos removed.

    python3 -B -m pipeline.emporio_armani_ar11328_dial [out.jpg] [review.png]   # default outputs/watches/emporio-armani-ar11328/dial_photo.jpg

dial_photo.jpg: square crop to the crystal opening (+0.3 mm), centred on the hand pivot, photo resolution, light unsharp
mask. Hand zones (posed outlines from config/watches/emporio-armani-ar11328-trace.json, plus their dark halos) are filled
with a normalised blur of the dial around them (smooth green-to-black gradient, one wide blur).
mesh_photo.jpg: a band of the 6 o'clock Milanese mesh just below the end cap, one pattern repeat long (MESH_REPEAT_PX rows,
no sideways shift), brightness evened along the band, seamless top to bottom (same method as pipeline/zeppelin_z8680m4_dial.py).
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/emporio-armani-ar11328-trace.json"
OUT = ROOT / "outputs/watches/emporio-armani-ar11328/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.35
SHADOWS_MM = ((-0.25, 0.25), (0.1, 0.3), (0.15, -0.15), (0.35, -0.35))  # dark halo around the hands, wider down-right (light from the upper left)
FILL_SIGMAS_PX = (60,)
MESH_REPEAT_PX = (133, -4)  # (rows, sideways shift): two weave rows, autocorrelation r = 0.9
MESH_PERIODS = 2
# EMPORIO [eagle] ARMANI: the upscaled photo smears the 1 mm letters, so they are redrawn in a sharp Didone serif over the
# filled dial, each word fitted to its box in the photo; the small eagle is the large dial eagle scaled down. Boxes in photo px.
WORDMARK = {"zone": (1860, 1755, 2455, 1850), "cap_y": (1774, 1832), "words": {"EMPORIO": (1879, 2158), "ARMANI": (2212, 2436)},
            "eagle_box": (2160, 1781, 2210, 1814), "eagle_src": (1940, 1405, 2350, 1615)}
FONT = ("/System/Library/Fonts/Supplemental/Didot.ttc", 2)  # Didot Bold: the printed strokes are heavy


def letters(g):
    """Text strength: brightness above the dial with the letters opened away."""
    bg = cv2.GaussianBlur(cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((41, 41))), (0, 0), 8)
    return np.clip(g - bg, 0, None)


def redraw_wordmark(clean, img):
    from PIL import Image, ImageDraw, ImageFont
    W = WORDMARK
    x0, y0, x1, y1 = W["zone"]
    zone = img[y0:y1, x0:x1].astype(np.float32)
    t = letters(zone.mean(2))
    ink = np.percentile(zone[t > 0.6 * t.max()], 85, axis=0)
    # dial under the letters: normalised blur of the pixels around them (smooth, no inpaint streaks)
    valid = 1 - cv2.dilate((t > 0.08 * t.max()).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
    pad = 60
    big = clean[y0 - pad:y1 + pad, x0 - pad:x1 + pad].astype(np.float32)
    vb = np.pad(valid, pad, constant_values=1)[..., None]
    base = (cv2.GaussianBlur(big * vb, (0, 0), 20) / np.maximum(cv2.GaussianBlur(vb, (0, 0), 20)[..., None], 1e-4))[pad:-pad, pad:-pad]
    base = valid[..., None] * clean[y0:y1, x0:x1] + (1 - valid[..., None]) * base
    k = 4  # supersampling
    alpha = Image.new("L", ((x1 - x0) * k, (y1 - y0) * k), 0)
    cap = (W["cap_y"][1] - W["cap_y"][0]) * k
    font = ImageFont.truetype(FONT[0], int(cap * 1.45), index=FONT[1])
    for word, (wx0, wx1) in W["words"].items():
        bb = font.getbbox(word)
        tile = Image.new("L", (bb[2] - bb[0], bb[3] - bb[1]), 0)
        ImageDraw.Draw(tile).text((-bb[0], -bb[1]), word, fill=255, font=font)
        tile = tile.resize(((wx1 - wx0) * k, cap), Image.LANCZOS)
        alpha.paste(tile, ((wx0 - x0) * k, (W["cap_y"][0] - y0) * k), tile)
    ex0, ey0, ex1, ey1 = W["eagle_src"]
    src = img[ey0:ey1, ex0:ex1].astype(np.float32).mean(2)
    te = letters(src)
    te = np.clip((te / np.percentile(te, 99) - 0.35) / 0.3, 0, 1)
    bx0, by0, bx1, by1 = W["eagle_box"]
    eg = Image.fromarray((te * 255).astype(np.uint8)).resize(((bx1 - bx0) * k, (by1 - by0) * k), Image.LANCZOS)
    alpha.paste(eg, ((bx0 - x0) * k, (by0 - y0) * k), eg)
    a = cv2.resize(np.asarray(alpha, np.float32) / 255, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)[..., None]
    clean[y0:y1, x0:x1] = np.clip(base * (1 - a) + ink * a, 0, 255).astype(np.uint8)


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        for h in t["hands"].values():
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in h["outline_mm"]]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_mm"]["radius"] * S * 1.15), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=max(1, int(MARGIN_MM * S / 1.5)))


def mesh_map(img, t):
    (x0, x1), y0 = t["manual_px"]["mesh_x"], t["manual_px"]["mesh_rows_y"][0]
    x0, x1 = x0 + 6, x1 - 6  # edge columns show the white background
    dy, dx = MESH_REPEAT_PX
    h, fade = dy * MESH_PERIODS, dy // 3
    xs = np.arange(x0 + max(-dx * MESH_PERIODS, 0), x1 - max(dx * MESH_PERIODS, 0), dtype=np.float32)
    mx = np.tile(xs, (h + fade, 1)) + (np.arange(h + fade, dtype=np.float32)[:, None] * dx / dy)
    my = np.tile(np.arange(y0, y0 + h + fade, dtype=np.float32)[:, None], (1, len(xs)))
    band = cv2.remap(img, mx, my, cv2.INTER_LANCZOS4).astype(np.float32)
    row = cv2.GaussianBlur(band.mean(axis=(1, 2)).reshape(-1, 1), (0, 0), 25).ravel()  # smooth light falloff along the band
    band *= (row.mean() / row)[:, None, None]
    w = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None]  # first rows fade in from the same rows one band later: no seam
    band[:fade] = w * band[:fade] + (1 - w) * band[h:h + fade]
    return np.clip(band[:h], 0, 255).astype(np.uint8)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    valid = (1 - mask).astype(np.float32)[..., None]
    est = None
    for sig in FILL_SIGMAS_PX:
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        e = cv2.GaussianBlur(img * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        est = e if est is None else np.where(wgt > 0.2, e, est)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = np.clip(soft * est + (1 - soft) * img, 0, 255).astype(np.uint8)
    R = int(round((t["rings_mm"]["bezel_inner"] + 0.3) * S))
    crop = clean[py0 - R:py0 + R, px0 - R:px0 + R]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    redraw_wordmark(clean, img)  # after the unsharp mask: the redrawn letters are already sharp
    x0, y0, x1, y1 = WORDMARK["zone"]
    crop[y0 - py0 + R:y1 - py0 + R, x0 - px0 + R:x1 - px0 + R] = clean[y0:y1, x0:x1]
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    mesh = mesh_map(img, t)
    cv2.imwrite(str(out.parent / "mesh_photo.jpg"), mesh, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # dial: u = 0.5 + x / (2 half), v = 0.5 + y / (2 half); mesh: u across the band, v = (s - start) / mesh_repeat_mm, repeated
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_mm": round(R / S, 4), "size_px": list(crop.shape[1::-1]), "masked_px": int(mask.sum()),
            "mesh_repeat_mm": round(mesh.shape[0] / S, 4), "mesh_size_px": list(mesh.shape[1::-1])}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = img[sl].copy()
        mk = mask[sl].astype(bool)
        shown[mk] = (0.5 * shown[mk] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[sl]]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
