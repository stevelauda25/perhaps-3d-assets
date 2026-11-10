"""Cut the Z86621 dial map and strap map from the straightened photo, with the hands and hubs removed from the dial.

    python3 -B -m pipeline.zeppelin_z86621_dial [out_dir] [review.png]   # default outputs/watches/zeppelin-z86621/

dial_photo.jpg: square, centred on the dial centre, out past the bezel's inner edge, photo resolution. The hand and hub zones
(posed outlines from config/watches/zeppelin-z86621-trace.json, at the positions seen in the photo, plus their shadows) are
filled with a normalised blur of the dial around them (coarse to fine); the 3D hands and hubs cover them.
strap_photo.jpg: the 12 o'clock strap (the 6 o'clock one carries an embossed logo), each row straightened between its leather
edges to the strap width; rows run from the case outward and stop where the strap turns away at the photo's top.
Light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.zeppelin_z96645_dial import sharpen

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/zeppelin-z86621-trace.json"
OUT_DIR = ROOT / "outputs/watches/zeppelin-z86621"
JPEG_QUALITY = 93
MAP_HALF_MM = 20.1
MARGIN_MM = 0.15
SHADOWS_MM = ((0.12, -0.12),)  # soft front light: only a thin shadow down and right (the 60 beside the minute hand stays clean)
FILL_SIGMAS_PX = (40, 12, 4)
FILL_CLEAR_MM = 0.3
STRAP_FROM_MM = 22.2  # rows above the dial centre: from the case edge to the photo's top
STRAP_BROWN = 10  # the upper strap turns away from the light and reads dark brown
STRAP_MIN_MM = 14.0  # a row with less leather than this is past the photo's strap
STRAP_SEARCH_MM = 1.0  # search this far past the lug gap: the keeper loop sticks out on the right at 580-660 px


def hand_mask(t, shape, core=False):
    S = t["scale_px_per_mm"]
    M = t["manual_px"]
    m = np.zeros(shape, np.uint8)
    parts = [(M["pivot"], h["outline_mm"]) for h in t["hands"].values()]
    parts += [(M[k]["centre"], sd["outline_mm"]) for k, sd in t["subdials"].items()]
    hubs = [(M["pivot"], t["hub_mm"]["collet"])] + [(M[k]["centre"], sd["hub_radius_mm"]) for k, sd in t["subdials"].items()]
    for dx, dy in ((0, 0),) + (() if core else SHADOWS_MM):
        P = lambda o, q: (o[0] + (q[0] + dx) * S, o[1] - (q[1] + dy) * S)
        for o, poly in parts:
            cv2.fillPoly(m, [np.round([P(o, q) for q in poly]).astype(np.int32)], 1)
        for o, r in hubs:
            cv2.circle(m, tuple(int(v) for v in P(o, (0, 0))), int(r * S * 1.1), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2 if core else max(1, int(MARGIN_MM * S / 1.5)))


def strap_map(img, S, mid_x, cy, width_mm):
    """The 12 o'clock strap, rows from the case upward; both edges where the brown leather meets the background."""
    f = img.astype(np.float32)
    brown = cv2.GaussianBlur(((f[..., 2] - f[..., 0]) > STRAP_BROWN).astype(np.float32), (0, 0), 2) > 0.5
    W = int(round(width_mm * S))
    rows, y = [], int(cy - STRAP_FROM_MM * S)
    lo, hi = int(mid_x - (width_mm / 2 + STRAP_SEARCH_MM) * S), int(mid_x + (width_mm / 2 + STRAP_SEARCH_MM) * S)
    while y > 2:
        xs = np.nonzero(brown[y, lo:hi])[0] + lo
        if len(xs) >= STRAP_MIN_MM * S:
            rows.append((y, float(xs.min()), float(xs.max())))
        elif rows:
            break
        y -= 1
    rows = rows[int(0.6 * S):]  # the first 0.6 mm: shadow under the case edge
    ys = np.array([q[0] for q in rows], np.float32)
    fit = lambda k: np.polyval(np.polyfit(ys, np.array([q[k] for q in rows]), 1), ys)
    out = []
    for yy, x0, x1 in zip(ys, fit(1), fit(2)):
        mx = np.linspace(x0, x1, W, dtype=np.float32)[None]
        out.append(cv2.remap(img, mx, np.full_like(mx, float(yy)), cv2.INTER_LINEAR)[0])
    s0 = (cy - ys[0]) / S
    return np.stack(out), round(float(s0), 3), round(float(s0 + len(rows) / S), 3)


def build(out_dir=OUT_DIR, review=None):
    t = json.loads(TRACE.read_text())
    S, (cx, cy) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))[..., :3]
    mask = hand_mask(t, img.shape[:2])
    # the estimate samples the dial a little away from the zones: the hands carry a pale halo at their edges
    valid = (1 - cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=int(FILL_CLEAR_MM * S / 1.5))).astype(np.float32)[..., None]
    est = None
    for sig in FILL_SIGMAS_PX:
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        e = cv2.GaussianBlur(img * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        est = e if est is None else np.where(wgt > 0.2, e, est)
    # dark print the hands only graze (the 60 beside the minute hand root): keep the photo's own pixels outside the bare hand outlines
    core = hand_mask(t, img.shape[:2], core=True)
    pc, R6 = t["manual_px"]["pivot"], 1.5 * t["hub_mm"]["collet"] * S
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    keep = (img.max(2) < 110) & (core == 0) & (np.hypot(xx - pc[0], yy - pc[1]) > R6)
    mask = mask * (1 - cv2.dilate(keep.astype(np.uint8), np.ones((3, 3), np.uint8)))
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = np.clip(soft * est + (1 - soft) * img, 0, 255).astype(np.uint8)
    R = int(round(MAP_HALF_MM * S))
    dial = sharpen(clean[cy - R:cy + R, cx - R:cx + R])
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / "dial_photo.jpg"), dial, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    hw = t["lug"]["inner_x_mm"]
    strap, s0, s1 = strap_map(img, S, sum(t["manual_px"]["lug_px"]["inner_x"]) / 2, cy, 2 * hw)
    cv2.imwrite(str(out_dir / "strap_photo.jpg"), sharpen(strap), [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # build: dial u = 0.5 + x / (2 half), v = 0.5 + y / (2 half); strap u = 0.5 + x / (2 half_w), v = 1 - (s - s0) / (s1 - s0)
    meta = {"source": t["source"], "centre_px": [cx, cy], "dial_half_mm": round(R / S, 4), "dial_size_px": list(dial.shape[1::-1]),
            "strap_half_w_mm": hw, "strap_s_from_to_mm": [s0, s1], "strap_size_px": list(strap.shape[1::-1]), "masked_px": int(mask.sum())}
    (out_dir / "dial_photo.json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[cy - R:cy + R, cx - R:cx + R].copy()
        mk = mask[cy - R:cy + R, cx - R:cx + R].astype(bool)
        shown[mk] = (0.5 * shown[mk] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, dial]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DIR
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
