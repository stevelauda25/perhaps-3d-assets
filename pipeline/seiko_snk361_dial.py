"""Cut a clean dial map for the SNK361K1 from the front photo, with the hands removed.

    python3 -B -m pipeline.seiko_snk361_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snk361k1/dial_photo.jpg

The dial is plain black, so the hand zones are filled with OpenCV inpainting (pipeline/seiko_dial.py copies a woven pattern
instead). Indices, logo, 5 shield, print and the day-date stay in the map. Square map centred on the hand pivot, out to the
crystal ring, at the photo's own resolution, light unsharp mask, JPEG. Hand zones come from config/watches/seiko-snk361k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snk361k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snk361k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.3  # past each hand's traced outline: its bright edge and soft glow
TAIL_EXTRA_MM = (0.5, 0.3)  # tails: the traced end point is the paddle centre, the paddle reaches further and wider


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.hypot(mx, my) < t["hub_radius_mm"][0] + MARGIN_MM
    for h in t["hands"].values():
        ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
        along, across = mx * ux + my * uy, np.abs(-mx * uy + my * ux)
        # blade from the pivot to the tip, wider tail behind the pivot
        m |= (along > 0) & (along < h["length_mm"] + MARGIN_MM) & (across < h["half_width_mm"] + MARGIN_MM)
        m |= (along > -h["tail_mm"] - TAIL_EXTRA_MM[0]) & (along <= 0) & (across < h["tail_half_width_mm"] + TAIL_EXTRA_MM[1])
    return m


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    pad = 20  # inpainting looks past the crop edge
    win = img[py0 - R - pad:py0 + R + pad, px0 - R - pad:px0 + R + pad]
    mask = hand_mask(t, img.shape[:2])[py0 - R - pad:py0 + R + pad, px0 - R - pad:px0 + R + pad]
    clean = cv2.inpaint(win, mask.astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA)[pad:-pad, pad:-pad]
    soft = cv2.GaussianBlur(clean, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(clean, 1 + SHARPEN[1], soft, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum())}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = win[pad:-pad, pad:-pad].copy()
        m = mask[pad:-pad, pad:-pad]
        shown[m] = (0.5 * shown[m] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
