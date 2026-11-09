"""Cut the Z96645 dial map and strap map from the straightened photo, with the hands and hub removed from the dial.

    python3 -B -m pipeline.zeppelin_z96645_dial [out_dir] [review.png]   # default outputs/watches/zeppelin-z96645/

dial_photo.jpg: square, centred on the dial centre, out to the bezel's inner edge, photo resolution. The hand zones (posed
outlines from config/watches/zeppelin-z96645-trace.json, at the positions seen in the photo) are filled with the pattern
of a normalised blur of the plain cream dial around them (coarse to fine); the 3D hands cover them.
strap_photo.jpg: the 12 o'clock strap (the 6 o'clock one carries an embossed logo), each row straightened between its
leather edges to the strap width; rows run from the case outward. Light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/zeppelin-z96645-trace.json"
OUT_DIR = ROOT / "outputs/watches/zeppelin-z96645"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MAP_HALF_MM = 18.4
MARGIN_MM = 0.2
SHADOWS_MM = ((0.15, -0.15), (0.3, -0.3), (0.45, -0.45))  # light from the upper left: shadows fall down and right
FILL_SIGMAS_PX = (40, 12, 4)
ROT_STEP_DEG = 3
FILL_CLEAR_MM = 0.35
ROT_STEPS = 0  # plain cream dial: the blur estimate alone matches its shading; no pattern to copy round
STRAP_FROM_MM = 20.6  # rows above the dial centre: from the case edge to the photo's top
STRAP_BROWN = 25
STRAP_MIN_MM = 15.0  # a row with less dark leather than this is past the photo's end


def hand_mask(t, shape, core=False):
    S = t["scale_px_per_mm"]
    pc = t["manual_px"]["pivot"]
    P = lambda q, dx=0, dy=0: (pc[0] + (q[0] + dx) * S, pc[1] - (q[1] + dy) * S)
    hs = t["hands"]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + (() if core else SHADOWS_MM):
        for poly in [h["outline_mm"] for h in hs.values()] + [hs["seconds"]["tail_mm"]]:
            cv2.fillPoly(m, [np.round([P(q, dx, dy) for q in poly]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_radius_mm"][0] * S * 1.1), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=1 if core else max(1, int(MARGIN_MM * S / 1.5)))


def sharpen(im):
    blur = cv2.GaussianBlur(im, (0, 0), SHARPEN[0])
    return cv2.addWeighted(im, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)


def strap_map(img, S, cx, cy, width_mm):
    """The 12 o'clock strap, rows from the case upward; both edges where the brown leather meets the white background."""
    f = img.astype(np.float32)
    brown = cv2.GaussianBlur(((f[..., 2] - f[..., 0]) > STRAP_BROWN).astype(np.float32), (0, 0), 2) > 0.5
    W = int(round(width_mm * S))
    rows, y = [], int(cy - STRAP_FROM_MM * S)
    lo, hi = int(cx - 14 * S), int(cx + 14 * S)
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
    left, right = fit(1), fit(2)
    out = []
    for yy, x0, x1 in zip(ys, left, right):
        mx = np.linspace(x0, x1, W, dtype=np.float32)[None]
        out.append(cv2.remap(img, mx, np.full_like(mx, float(yy)), cv2.INTER_LINEAR)[0])
    s0 = (cy - ys[0]) / S
    return np.stack(out), round(float(s0), 3), round(float(s0 + len(rows) / S), 3)


def build(out_dir=OUT_DIR, review=None):
    t = json.loads(TRACE.read_text())
    S, (cx, cy) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    # the estimate samples the dial a little away from the zones: the hands carry a pale halo at their edges
    valid = (1 - cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=int(FILL_CLEAR_MM * S / 1.5))).astype(np.float32)[..., None]
    est = None
    for sig in FILL_SIGMAS_PX:
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        e = cv2.GaussianBlur(img * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        est = e if est is None else np.where(wgt > 0.2, e, est)
    # sunburst dial: copy each hand pixel from the same radius a few degrees round (never from a hand, numeral or print);
    # the blur estimate only fills what no rotation reaches
    f = img.astype(np.float32)
    plain = (f.min(2) > 160) & ((f[..., 2] - f[..., 0]) < 60)  # cream dial, not the gold numerals or black print
    ok = (plain & (mask == 0)).astype(np.uint8)
    fill, todo = est.copy(), mask.astype(bool)
    for k in range(1, ROT_STEPS + 1):
        for deg in (k * ROT_STEP_DEG, -k * ROT_STEP_DEG):
            rot = cv2.getRotationMatrix2D((float(cx), float(cy)), deg, 1.0)
            src = cv2.warpAffine(f, rot, img.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            good = cv2.warpAffine(ok, rot, img.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & good
            fill[take] = src[take]
            todo &= ~take
    # numerals the hands only graze (shadow and margin zone): keep the photo's own pixels
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    pc = t["manual_px"]["pivot"]
    cream = (f.max(2) > 95) & (f.min(2) < 130) & ((f[..., 2] - f[..., 0]) > 60) & (np.hypot(xx - pc[0], yy - pc[1]) > 6.0 * S)  # gold numerals, not the hub
    keep = cv2.dilate((cream & (hand_mask(t, img.shape[:2], core=True) == 0)).astype(np.uint8), np.ones((3, 3), np.uint8))
    mask = mask * (1 - keep)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = np.clip(soft * fill + (1 - soft) * img, 0, 255).astype(np.uint8)
    # where a hand crosses a numeral (the seconds needle over the 4), carry the numeral's strokes across by inpainting
    near_num = cv2.dilate(cream.astype(np.uint8), np.ones((15, 15), np.uint8)) & (mask > 0)
    near_num &= cv2.erode(cv2.dilate(cream.astype(np.uint8), np.ones((31, 31), np.uint8)), np.ones((15, 15), np.uint8))
    clean = cv2.inpaint(clean, near_num.astype(np.uint8), 5, cv2.INPAINT_TELEA)
    R = int(round(MAP_HALF_MM * S))
    dial = sharpen(clean[cy - R:cy + R, cx - R:cx + R])
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / "dial_photo.jpg"), dial, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    hw = t["lug"]["inner_x_mm"]
    strap, s0, s1 = strap_map(img, S, cx, cy, 2 * hw)
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
