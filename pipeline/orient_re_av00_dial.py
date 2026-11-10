"""Cut the Orient Star Modern Skeleton photo maps (RE-AV0004N00B, RE-AV0005L00B) from the front render: the dial with the hour
and minute hands removed, and (leather strap only) the strap resampled to a straight strip.

    python3 -B -m pipeline.orient_re_av00_dial <sku> [review.png]   # -> outputs/watches/orient-<sku>/dial_photo.jpg (+ strap_photo.jpg)

The dial is not rotationally even (open heart, power reserve, small seconds, skeleton window), so the period copy of
pipeline/orient_ra_wj0002l_dial.py does not apply: the hand zones (traced outlines incl. the counterweight tails, grown by
MARGIN_MM, plus the hub) are filled by OpenCV inpainting from their edges, as the blur fill of
pipeline/orient_re_at0007n00b_dial.py; the modelled hands cover them from the front. The official renders have no hand shadows.
The square map is centred on the hand pivot and reaches the polished bezel's inner edge. Strap: each photo row of leather is
resampled between its own edges to the strap width, from the lug tip outward (bottom strap, the longer one).
Native resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.25  # the hands' soft edges and rose reflections must not feed the inpaint
HUB_ZONE_MM = 1.0  # collar 0.89 mm
INPAINT_PX = 6


def hand_mask(t, shape, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["hand_pivot_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    x, y = (xx - px0) / S, -(yy - py0) / S
    m = np.hypot(x, y) < HUB_ZONE_MM + margin
    for h in t["hands"].values():
        ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
        al, ac = x * ux + y * uy, np.abs(-x * uy + y * ux)
        rs, ws = zip(*h["outline_mm"])
        m |= (al > rs[0] - margin) & (al < rs[-1] + margin) & (ac < np.interp(al, rs, ws) + margin)
    return m


def strap_strip(img, rows, centre_x, width):
    """Each photo row's strap run (not white) through the strap centre, resampled to `width`; ends at the first row without leather."""
    fg = (765 - img.astype(int).sum(2)) > 30  # past the lug tips the strap is the only thing on the white background
    out, used = [], []
    for y in rows:
        dark = fg[y]
        x0 = x1 = centre_x
        if dark[centre_x]:
            while x0 > 0 and dark[x0 - 1]:
                x0 -= 1
            while x1 < len(dark) - 1 and dark[x1 + 1]:
                x1 += 1
        if x1 - x0 < 0.8 * width:  # rows next to the case are skipped until the leather spans the lugs
            if out:
                break
            continue
        out.append(cv2.resize(img[y:y + 1, x0:x1 + 1], (width, 1), interpolation=cv2.INTER_AREA))
        used.append(int(y))
        centre_x = (x0 + x1) // 2
    return np.vstack(out), used


def build(sku, review=None):
    t = json.loads((ROOT / f"config/watches/orient-{sku}-trace.json").read_text())
    out = ROOT / f"outputs/watches/orient-{sku}/dial_photo.jpg"
    S, (px0, py0) = t["scale_px_per_mm"], t["hand_pivot_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil((t["bezel_inner_mm"] + 0.1) * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    mask = hand_mask(t, img.shape[:2])[sl]
    win = cv2.inpaint(img[sl].copy(), mask.astype(np.uint8) * 255, INPAINT_PX, cv2.INPAINT_TELEA)
    sharpen = lambda a: cv2.addWeighted(a, 1 + SHARPEN[1], cv2.GaussianBlur(a, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    crop = sharpen(win)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum())}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if "strap" in t:
        t1 = t["strap"]["lug_tips_px"][1]
        width = int(round(2 * t["strap"]["half_mm"] * S))
        strip, rows = strap_strip(img, range(t1 + 5, img.shape[0]), t["strap"]["centre_x_px"], width)
        sp = out.with_name("strap_photo.jpg")
        cv2.imwrite(str(sp), sharpen(strip), [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        sp.with_suffix(".json").write_text(json.dumps({"size_px": [strip.shape[1], strip.shape[0]], "rows_px": rows,
                                                       "scale_px_per_mm": S, "lug_tip_px": t1}) + "\n")
        meta["strap_rows"] = len(rows)
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    print(build(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else None))
