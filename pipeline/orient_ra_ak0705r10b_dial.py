"""Cut the Orient RA-AK0705R10B photo map (dial and leather strap) from the front photo, hands and their shadows removed.

    python3 -B -m pipeline.orient_ra_ak0705r10b_dial [out.jpg] [review.png]   # default outputs/watches/orient-ra-ak0705r10b/photo.jpg

Hands (main and sub-dial): the traced outlines grown by HAND_MARGIN_MM plus their shadow (light from the left: shadows fall to
the right) are filled along circles about the pivot (polar_fill); the modelled hands
cover them from the front. Only the dial and the strap use this map. The strap in this photo is straight
and runs to the image edge at both ends, so no fill is needed there. Crop: the watch width, rows to the strap's curled end
plus a margin, native resolution (no resampling), light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-ra-ak0705r10b-trace.json"
SPEC = ROOT / "config/watches/orient-ra-ak0705r10b.json"
OUT = ROOT / "outputs/watches/orient-ra-ak0705r10b/photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 2.0  # rows kept past the strap's front-visible end (tip + bend radius)
HAND_MARGIN_MM = {"hour": 0.3, "minute": 0.3}  # thin needles (seconds, sub-dial hands) keep a narrow zone: their shadow is short
THIN_MARGIN_MM = 0.1
SHADOWS_MM = {"hour": ((0.25, 0.0), (0.5, -0.05)), "minute": ((0.25, 0.0), (0.5, -0.05))}  # to the right (light from the left)
THIN_SHADOWS_MM = ((0.12, 0.0),)


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    m = np.zeros(shape, np.uint8)
    for name, h in t["hands"].items():
        one = np.zeros(shape, np.uint8)
        for dx, dy in ((0, 0),) + SHADOWS_MM.get(name, THIN_SHADOWS_MM):
            cv2.fillPoly(one, [np.round([P(p, dx, dy) for p in h["outline_mm"]]).astype(np.int32)], 1)
        k = 2 * int(HAND_MARGIN_MM.get(name, THIN_MARGIN_MM) * S) + 1
        m |= cv2.dilate(one, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    for dx, dy in ((0, 0),) + SHADOWS_MM["hour"]:
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_mm"]["black_r"] * S * 1.2), 1, -1)
    return m


def polar_fill(img, mask, centre, r_max, smooth_px=0):
    """Fill masked pixels from the dial at the same radius about the pivot: linear between the nearest clean pixels on
    either side in angle. Hands run along radii, so the gap is short and the sunburst's light and the rings stay continuous.
    smooth_px: clean pixels averaged over this many px along the radius first, so a brushed (sunburst) dial gives no arcs."""
    n_ang = 4096
    size = (int(r_max), n_ang)
    flags = cv2.WARP_POLAR_LINEAR + cv2.INTER_LINEAR
    P = cv2.warpPolar(img, size, centre, r_max, flags).astype(np.float32)
    Pm = cv2.warpPolar(mask * 255, size, centre, r_max, flags) > 20
    src = P
    if smooth_px:
        ok = (~Pm).astype(np.float32)[..., None]
        k = (2 * smooth_px + 1, 3)  # (along the radius, along the angle)
        src = cv2.blur(P * ok, k) / np.maximum(cv2.blur(ok, k), 1e-3)[..., None]
    out = P.copy()
    for c in range(P.shape[1]):
        col = Pm[:, c]
        if not col.any():
            continue
        if col.all():  # round the pivot every angle is covered: mean of the first ring with clean pixels
            c2 = next(k for k in range(c + 1, P.shape[1]) if not Pm[:, k].all())
            c2 = min(c2 + 15, P.shape[1] - 1)  # past the hub's dark shadow
            out[:, c] = P[~Pm[:, c2], c2].mean(0)
            continue
        good = np.nonzero(~col)[0]
        idx = np.arange(n_ang)
        gx = np.r_[good - n_ang, good, good + n_ang]  # circular in angle
        for ch in range(3):
            gv = np.r_[src[good, c, ch], src[good, c, ch], src[good, c, ch]]
            out[col, c, ch] = np.interp(idx[col], gx, gv)
    back = cv2.warpPolar(out, img.shape[1::-1], centre, r_max, flags + cv2.WARP_INVERSE_MAP)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)[..., None]
    return np.clip(soft * back + (1 - soft) * img, 0, 255).astype(np.uint8)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    st = json.loads(SPEC.read_text())["strap"]
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
    clean = polar_fill(img, mask, (float(px0), float(py0)), t["dial_edge_mm"] * S)
    keep = {k: t["strap_mm"][k]["tip_y"] + st["bend_radius"] + MARGIN_MM for k in ("top", "bottom")}
    y0 = max(0, int(py0 - keep["top"] * S))
    y1 = min(img.shape[0], int(py0 + keep["bottom"] * S))
    fg = np.nonzero((img[y0:y1].min(2) < 238).any(0))[0]
    x0c, x1c = max(0, fg.min() - 8), min(img.shape[1], fg.max() + 9)
    crop = clean[y0:y1, x0c:x1c]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = (px0 + x S - crop_x) k / w, v = 1 - (py0 - y S - crop_y) k / h
    meta = {"source": t["source"], "crop_px": [int(x0c), int(y0)], "scale": 1.0, "size_px": list(crop.shape[1::-1]),
            "strap_end_mm": {"top": round((py0 - y0) / S - 0.1, 2), "bottom": round((y1 - py0) / S - 0.1, 2)}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        R = int(17 * S)
        sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = img[sl].copy()
        shown[mask[sl].astype(bool)] = (0.5 * shown[mask[sl].astype(bool)] + [0, 127, 0]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[sl]]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
