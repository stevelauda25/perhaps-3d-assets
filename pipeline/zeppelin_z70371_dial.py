"""Cut the Z70371 dial map and strap map from the straightened photo, with the hands and hubs removed from the dial.

    python3 -B -m pipeline.zeppelin_z70371_dial [out_dir] [review.png]   # default outputs/watches/zeppelin-z70371/

dial_photo.jpg: square, centred on the dial centre, out to the bezel's inner edge, photo resolution. The hand zones (posed
outlines from config/watches/zeppelin-z70371-trace.json, at the positions seen in the photo) are filled with a normalised blur
of the pixels around them, coarse to fine (same fill as pipeline/zeppelin_z70363_dial.py); the 3D hands cover them.
strap_photo.jpg: the 6 o'clock strap (the 12 o'clock one curls away), each row straightened between its leather edges to the
20 mm strap width; rows run from the case outward. Light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/zeppelin-z70371-trace.json"
OUT_DIR = ROOT / "outputs/watches/zeppelin-z70371"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MAP_HALF_MM = 18.6
MARGIN_MM = 0.15
SHADOWS_MM = ((0.1, -0.1),)
FILL_SIGMAS_PX = (40, 12, 4)
STRAP_FROM_MM = 19.0  # rows below the dial centre: under the case edge to the photo's end
STRAP_DARK = 120
STRAP_MIN_MM = 15.0  # a row with less dark leather than this is past the photo's end


def hand_mask(t, shape):
    S, (cx, cy) = t["scale_px_per_mm"], t["origin_px"]
    pc = t["manual_px"]["pivot_central"]
    P = lambda q, o, dx=0, dy=0: (o[0] + (q[0] + dx) * S, o[1] - (q[1] + dy) * S)
    hs = t["hands"]
    central = [h["outline_mm"] for h in hs.values()] + [hs["seconds"]["tail_mm"], hs["week"]["crescent_mm"]]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        for poly in central:
            cv2.fillPoly(m, [np.round([P(q, pc, dx, dy) for q in poly]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), pc, dx, dy)), int(t["hub_radius_mm"][0] * S * 1.08), 1, -1)
        for sd in t["subdials"].values():
            seen = (cx + sd["pivot_seen_mm"][0] * S, cy - sd["pivot_seen_mm"][1] * S)
            o = (seen[0] - sd["centre_mm"][0] * S, seen[1] + sd["centre_mm"][1] * S)  # hand_mm is posed about the true centre
            cv2.fillPoly(m, [np.round([P(q, o, dx, dy) for q in sd["hand_mm"]]).astype(np.int32)], 1)
            cv2.circle(m, tuple(int(v) for v in P((0, 0), seen, dx, dy)), int(t["sub_hub_radius_mm"] * S * 1.15), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=max(1, int(MARGIN_MM * S / 1.5)))


def sharpen(im):
    blur = cv2.GaussianBlur(im, (0, 0), SHARPEN[0])
    return cv2.addWeighted(im, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)


def strap_map(img, S, cx, cy, width_mm):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    W = int(round(width_mm * S))
    rows, y, y0 = [], int(cy + STRAP_FROM_MM * S), None
    while y < img.shape[0] - 3:
        dark = cv2.GaussianBlur(g[y - 2:y + 3], (0, 0), 1.5).mean(0) < STRAP_DARK
        xs = np.nonzero(dark[int(cx - 14 * S):int(cx + 14 * S)])[0] + int(cx - 14 * S)
        if len(xs) < STRAP_MIN_MM * S:
            if y0 is None:  # still on the case: the leather starts below its edge
                y += 1
                continue
            break
        if y0 is None:  # skip the first 0.6 mm: the case edge glints on the leather there
            y = y + int(0.6 * S)
            y0 = y
            continue
        rows.append((y, float(xs.min()), float(xs.max())))
        y += 1
    # right edge: where the warm tan side of the strap (or the white background) starts; both edges as straight-line fits
    f = img.astype(np.float32)
    b, r = (cv2.GaussianBlur(f[..., k], (0, 0), 2) for k in (0, 2))
    lum = cv2.GaussianBlur(f.mean(2), (0, 0), 2)
    ys = np.array([q[0] for q in rows], np.float32)
    left = np.array([q[1] for q in rows])
    right = []
    for yy, x0 in zip(ys.astype(int), left.astype(int)):
        a = x0 + int(12 * S)
        stop = np.nonzero(((r[yy, a:] - b[yy, a:] > 18) & (lum[yy, a:] > 80)) | (lum[yy, a:] > 205))[0]
        right.append(a + stop[0] if len(stop) else np.nan)
    right = np.array(right, np.float32)
    fit = lambda v: np.polyval(np.polyfit(ys[np.isfinite(v)], v[np.isfinite(v)], 1), ys)
    left, right = fit(left), fit(right)
    out = []
    for yy, x0, x1 in zip(ys, left, right):
        mx = np.linspace(x0, x1, W, dtype=np.float32)[None]
        out.append(cv2.remap(img, mx, np.full_like(mx, float(yy)), cv2.INTER_LINEAR)[0])
    strap = np.stack(out)
    s0 = (y0 - cy) / S
    return strap, round(s0, 3), round(s0 + len(rows) / S, 3)


def build(out_dir=OUT_DIR, review=None):
    t = json.loads(TRACE.read_text())
    S, (cx, cy) = t["scale_px_per_mm"], t["origin_px"]
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
