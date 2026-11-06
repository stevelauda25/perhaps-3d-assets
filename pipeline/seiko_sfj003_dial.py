"""Cut the SFJ003P1 photo map (dial, subdials, flange print, gasket ring) from the front photo, all five hands removed.

    python3 -B -m pipeline.seiko_sfj003_dial [out.jpg] [review.png]     # default outputs/watches/seiko-sfj003p1/dial_photo.jpg

The dial and subdials are plain black under the hands, so each hand zone (traced outline, small margin, short shadow
down-right) gets the local lighting: a masked Gaussian average of the dial around it that leaves out the hands and every
bright mark (numerals, indices, print) so they do not bleed. The 3D hands, hubs and the applied 3 index cover the zones.
Square crop centred on the dial centre out to the bezel edge, photo resolution, light unsharp mask, JPEG. Zones come from
config/watches/seiko-sfj003p1-trace.json.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-sfj003p1-trace.json"
OUT = ROOT / "outputs/watches/seiko-sfj003p1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_MM = 18.7  # bezel inner edge 18.58 mm
MARGIN_MM = 0.15
SHADOW_MM = (0.15, -0.15)  # soft light here: short shadow down-right
LIT = 90
LOW_SIGMA_PX = (20, 60)


def hand_mask(t, shape, margin=MARGIN_MM, shadow=True):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda x, y: (px0 + x * S, py0 - y * S)
    m = np.zeros(shape, np.uint8)
    tp = t["time_pivot_mm"]
    parts = [(h["outline_mm"], tp) for h in t["hands"].values()]
    parts += [(s["outline_mm"], s["pivot_mm"]) for s in t["subdials"].values() if "outline_mm" in s]
    for dx, dy in ((0, 0), SHADOW_MM) if shadow else ((0, 0),):
        for poly, (ox, oy) in parts:
            cv2.fillPoly(m, [np.round([P(x + ox + dx, y + oy + dy) for x, y in poly]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(round(v)) for v in P(tp[0] + dx, tp[1] + dy)), int(t["hub_radius_mm"][0] * S * 1.15), 1, -1)
    if margin:
        m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=max(1, int(margin * S)))
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    R = int(round(HALF_MM * S))
    pad = 200
    win = (slice(py0 - R - pad, py0 + R + pad), slice(px0 - R - pad, px0 + R + pad))
    f32, mw = img[win].astype(np.float32), mask[win]
    bright = cv2.dilate((cv2.cvtColor(img[win], cv2.COLOR_BGR2GRAY) > LIT).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    valid = (~mw & ~bright).astype(np.float32)[..., None]
    low = None
    for sig in LOW_SIGMA_PX[::-1]:  # wide estimate first, the narrow one where it has enough support
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(f32 * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    filled = img[win].copy()
    filled[mw] = np.clip(low[mw], 0, 255).astype(np.uint8)
    filled = (cv2.GaussianBlur(mw.astype(np.float32), (0, 0), 1.5)[..., None] * filled + (1 - cv2.GaussianBlur(mw.astype(np.float32), (0, 0), 1.5)[..., None]) * img[win]).astype(np.uint8)
    crop = filled[pad:-pad, pad:-pad]
    soft = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], soft, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = 0.5 + x / (2 half), v = 0.5 + y / (2 half)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_mm": round(R / S, 4), "size_px": list(crop.shape[1::-1]),
            "masked_px": int(mw.sum()), "kb": out.stat().st_size // 1024}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        before = img[py0 - R:py0 + R, px0 - R:px0 + R].copy()
        m = mask[py0 - R:py0 + R, px0 - R:px0 + R]
        before[m] = (0.5 * before[m] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([before, crop]), (2 * 1100, 1100), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
