"""Cut the FS6012 photo map (dial and strap) from the front photo, with the hands, hub and their shadows removed.

    python3 -B -m pipeline.fossil_fs6012_dial [out.jpg] [review.png]   # default outputs/watches/fossil-fs6012/dial_photo.jpg

Same fill as pipeline/zeppelin_z96903_dial.py: the hand zones (posed outlines from config/watches/fossil-fs6012-trace.json)
are filled with a normalised blur of the pixels around them, coarse to fine; the 3D hands cover them from the front.
One map: full photo height (strap) by the strap width, centred on the hand pivot, working-copy resolution, light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/fossil-fs6012-trace.json"
OUT = ROOT / "outputs/watches/fossil-fs6012/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_WIDTH_MM = 11.4  # map x range: the dial opening (10.45 mm) and the strap (11.17 mm)
STRAP_HALF_MM = 11.17  # model strap half width (spec strap: brancard gap minus edge_inset)
MARGIN_MM = 0.2
SHADOWS_MM = ((0.0, -0.3), (-0.1, -0.6))  # cast shadows fall below the hands (light from above)
FILL_SIGMAS_PX = (40, 12, 4)


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    hs = t["hands"]
    polys = [h["outline_mm"] for h in hs.values()] + [hs["seconds"]["tail_mm"]]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        for poly in polys:
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in poly]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_mm"]["radius"] * S * 1.08), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=max(1, int(MARGIN_MM * S / 1.5)))


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    valid = (1 - mask).astype(np.float32)[..., None]
    est = None
    for sig in FILL_SIGMAS_PX:  # normalised blur of the unmasked pixels: smooth dial colour, no streaks from the hand edges
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        e = cv2.GaussianBlur(img * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        est = e if est is None else np.where(wgt > 0.2, e, est)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = np.clip(soft * est + (1 - soft) * img, 0, 255).astype(np.uint8)
    # strap past the horn tips: the photo's strap narrows where it runs away, so each row's leather is stretched to the
    # model's strap width (no white background on the strap edges); rows with under half the width are past the end
    tips = t["case"]["horn_tip_mm"]
    hw = int(round(STRAP_HALF_MM * S))
    reach = int(round((STRAP_HALF_MM + 0.8) * S))
    ends = {}
    for key, rows in (("top", range(int(py0 - (tips["top"] + 0.3) * S), -1, -1)), ("bottom", range(int(py0 + (tips["bottom"] + 0.3) * S), img.shape[0]))):
        for row in rows:
            dark = np.nonzero(img[row, px0 - reach:px0 + reach].min(1) < 215)[0]
            if len(dark) < hw:
                break
            seg = clean[row:row + 1, px0 - reach + dark.min():px0 - reach + dark.max() + 1]
            clean[row, px0 - hw:px0 + hw] = cv2.resize(seg, (2 * hw, 1), interpolation=cv2.INTER_LINEAR)[0]
            ends[key] = round(abs(py0 - row) / S - 0.2, 2)
    W = int(round(HALF_WIDTH_MM * S))
    crop = clean[:, px0 - W:px0 + W]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = 0.5 + x / (2 half_w), v = 0.5 + (y - centre_y) / (2 half_h)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_w_mm": round(W / S, 4), "half_h_mm": round(crop.shape[0] / 2 / S, 4),
            "centre_y_mm": round((py0 - crop.shape[0] / 2) / S, 4), "size_px": list(crop.shape[1::-1]), "masked_px": int(mask.sum()), "strap_end_mm": ends}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        R = int(11.4 * S)
        sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = img[sl].copy()
        shown[mask[sl].astype(bool)] = (0.5 * shown[mask[sl].astype(bool)] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[sl]]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
