"""Cut the Orient RA-WJ0004Y photo map (dial, rehaut and bezel insert) from the front photo, hands and their shadows removed.

    python3 -B -m pipeline.orient_ra_wj0004y_dial [out.jpg] [review.png]   # default outputs/watches/orient-ra-wj0004y/photo.jpg

Hand zones (traced outlines grown by a margin, plus their shadow down-right: light from the upper left) are filled along
circles about the pivot (polar_fill from pipeline/orient_ra_ak0705r10b_dial.py): the sunburst's light and the minute track
stay continuous; the modelled hands cover the zones from the front. One square map centred on the pivot, wide enough for the
bezel insert, at the photo's own resolution, light unsharp mask, JPEG. The bracelet and case are modelled (no photo).
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.orient_ra_ak0705r10b_dial import polar_fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-ra-wj0004y-trace.json"
OUT = ROOT / "outputs/watches/orient-ra-wj0004y/photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_MM = 19.3  # insert outer edge (18.77 mm) plus margin
MARGIN_MM = {"hour": 0.25, "minute": 0.25, "seconds": 0.2}
SHADOWS_MM = {"hour": ((0.15, -0.15), (0.3, -0.3)), "minute": ((0.15, -0.15), (0.3, -0.3)), "seconds": ((0.1, -0.1),)}


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    m = np.zeros(shape, np.uint8)
    for name, h in t["hands"].items():
        one = np.zeros(shape, np.uint8)
        for dx, dy in ((0, 0),) + SHADOWS_MM[name]:
            cv2.fillPoly(one, [np.round([P(p, dx, dy) for p in h["outline_mm"]]).astype(np.int32)], 1)
        k = 2 * int(MARGIN_MM[name] * S) + 1
        m |= cv2.dilate(one, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    cv2.circle(m, (px0, py0), int(t["hub_mm"][0] * S * 1.8), 1, -1)
    return m


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    clean = polar_fill(img, mask, (float(px0), float(py0)), t["rings_mm"]["dial_edge"] * S, smooth_px=8)
    W = int(round(HALF_MM * S))
    crop = clean[py0 - W:py0 + W, px0 - W:px0 + W]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm (about the pivot) to this image: u = 0.5 + x / (2 half), v = 0.5 + y / (2 half)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_mm": round(W / S, 4), "size_px": list(crop.shape[1::-1])}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        R = int(15 * S)
        sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = img[sl].copy()
        shown[mask[sl].astype(bool)] = (0.5 * shown[mask[sl].astype(bool)] + [0, 127, 0]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[sl]]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
