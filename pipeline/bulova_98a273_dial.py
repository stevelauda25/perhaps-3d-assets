"""Cut a clean dial map for the Bulova 98A273 (Marine Star Automatic 44 mm) from the official front render, the hour and
minute hands removed.

    python3 -B -m pipeline.bulova_98a273_dial [out.jpg] [review.png]   # default outputs/watches/bulova-98a273/dial_photo.jpg

Square crop about the hand pivot out to the gold bezel's inner edge (chapter ring included). The open heart is transparent in
the render: it is laid on a dark movement shadow. Each hand pixel is copied from the same radius 6, 12 ... deg away about the
pivot (the sunray grooves and the chapter ring repeat), with every print and applied numeral protected as a copy source; the
applied gold numerals are geometry in the build. Native resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h82405130_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/bulova-98a273-trace.json"
OUT = ROOT / "outputs/watches/bulova-98a273/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.35
SHADOWS_MM = ((-0.2, -0.2),)  # the render's light comes from the upper right: thin shadows fall left and down
HEART_SHADOW = (38, 38, 40)
FIELD_R_MM = 12.0  # the flat octagon field ends inside this radius; outside it the sunray grooves  # BGR: what the open heart shows where the render is transparent


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + tuple(shadows):
        P = lambda p: [px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S]
        cv2.circle(m, (int(px0 + dx * S), int(py0 - dy * S)), int((t["hub_mm"]["collar"] + margin) * S), 1, -1)
        for h in t["hands"].values():
            cv2.fillPoly(m, [np.array([P(p) for p in h["outline_mm"]], np.int32)], 1)
    k = int(2 * margin * S) | 1
    return cv2.dilate(m, np.ones((k, k), np.uint8)).astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    raw = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)
    a = raw[..., 3:4].astype(np.float32) / 255
    img = (raw[..., :3] * a + np.array(HEART_SHADOW, np.float32) * (1 - a) + 0.5).astype(np.uint8)
    R = int(math.ceil(t["rings_mm"]["bezel_in"] * S)) + 2
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    mask = hand_mask(t, shape)[sl]
    hsv = cv2.cvtColor(win, cv2.COLOR_BGR2HSV)
    gray = hsv[..., 2]
    yy, xx = np.mgrid[-R:R, -R:R]
    rr = np.hypot(xx, yy)
    # prints (white) and applied gold are never a copy source inside the chapter ring; the chapter ring repeats every 6 deg
    feats = cv2.dilate(((gray > 120) & ~mask & (rr < t["rings_mm"]["chapter_in"] * S - 4)).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    sub = t["subdial"]["centre_mm"]
    feats |= np.hypot(xx - sub[0] * S, yy + sub[1] * S) < (t["subdial"]["ring_mm"][1] + 0.3) * S
    hc = t["heart"]["centre_mm"]
    feats |= np.hypot(xx - hc[0] * S, yy + hc[1] * S) < (t["heart"]["ring_out_mm"] + 0.3) * S
    black = np.median(win[~mask & ~feats & (rr < 0.6 * R)].reshape(-1, 3), 0)
    todo = mask.copy()
    # local lighting (masked blur): a copy keeps the rotated detail but takes the brightness of where it lands
    ok = (~mask & ~feats).astype(np.float32)
    den = cv2.GaussianBlur(ok, (0, 0), 18)[..., None]
    low = cv2.GaussianBlur(win.astype(np.float32) * ok[..., None], (0, 0), 18) / np.maximum(den, 1e-3)
    den2 = cv2.GaussianBlur(ok, (0, 0), 60)[..., None]
    low2 = cv2.GaussianBlur(win.astype(np.float32) * ok[..., None], (0, 0), 60) / np.maximum(den2, 1e-3)
    low = np.where(den > 0.05, low, low2).astype(np.float32)
    # the flat centre field is an octagon and the chapter ring repeats every 6 deg: quarter turns keep both, then 45 deg, then 6 deg
    octagon = [(90, 1.0), (-90, 1.0), (180, 1.0), (45, 1.0), (-45, 1.0), (135, 1.0), (-135, 1.0)]
    small = [(sgn * k * 6, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    outside = todo & (rr > FIELD_R_MM * S)  # sunray and chapter ring: nearest 6 deg steps first
    used = fill(win, outside, mask | feats, low, small, (R, R))
    todo &= ~(mask & (rr > FIELD_R_MM * S)) | outside
    used.update({"field " + k: v for k, v in fill(win, todo, mask | feats, low, octagon + small, (R, R)).items()})
    unfilled = int(todo.sum())
    ring = ~mask & ~feats & (rr > 60) & (rr < 110)
    win[todo] = np.median(win[ring].reshape(-1, 3), 0)  # the hub zone (rotation cannot reach it): the field colour around it
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    sharpen = lambda im: cv2.addWeighted(im, 1 + SHARPEN[1], cv2.GaussianBlur(im, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
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
