"""Cut the Bulova 96B431 photo maps from the official front render: dial + bezel insert (hands removed) and the rubber strap.

    python3 -B -m pipeline.bulova_96b431_dial [review.png]
    # -> outputs/watches/bulova-96b431/dial_photo.jpg (+ .json) and strap.jpg (+ .json)

Dial map: square crop about the pivot out to the bezel rim's corners, native resolution. The wave dial is not round, so hand
pixels inside the minute track are copied from the same place one or two wave rows (42 px) up or down, with the local lighting
kept (masked blur); the minute track and insert repeat every 6 deg, so pixels out there are copied from the same radius 6, 12
... deg away. Prints, indices and the date window are never a copy source. Light unsharp mask, JPEG 93.
Strap map: each photo row of the strap from the case edge outward, resampled to one width (the strap tapers in the render),
12 o'clock rows first, then 6 o'clock rows.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/bulova-96b431-trace.json"
OUT = ROOT / "outputs/watches/bulova-96b431"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.3
SHADOWS_MM = ((0.15, -0.2), (0.3, -0.35))  # the render's hands throw a thin shadow right and down
WAVE_ROW_PX = 42
HUB_ZONE_MM = 1.0
STRAP_W = 640


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        P = lambda p: [px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S]
        cv2.circle(m, (int(px0 + dx * S), int(py0 - dy * S)), int(HUB_ZONE_MM * S), 1, -1)  # hub, tail roots and their facets
        for h in t["hands"].values():
            for key in ("outline_mm", "needle_mm", "tail_mm", "triangle_mm", "stick_mm"):
                if key in h:
                    cv2.fillPoly(m, [np.array([P(p) for p in h[key]], np.int32)], 1)
    k = int(2 * MARGIN_MM * S) | 1
    return cv2.dilate(m, np.ones((k, k), np.uint8)).astype(bool)


def copy_fill(win, todo, bad, low, warps):
    """Fill todo pixels from warped copies (affine 2x3 matrices), detail over the local lighting `low`; sources never in bad."""
    detail = win.astype(np.float32) - low
    good = cv2.erode((~bad).astype(np.uint8), np.ones((5, 5), np.uint8))
    used = {}
    for name, A in warps:
        src = low + cv2.warpAffine(detail, A, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ok = cv2.warpAffine(good, A, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
        take = todo & ok
        win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
        todo &= ~take
        used[name] = int(take.sum())
        if not todo.any():
            break
    return used


def build(review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    img0 = img
    rg = t["rings_mm"]
    R = int(math.ceil(rg["rim_apothem"] / math.cos(math.pi / t["sides"]) * S)) + 4
    pad = 64  # the rim's corners at 9 o'clock reach the render's left edge
    img = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
    sl = np.s_[py0 + pad - R:py0 + pad + R, px0 + pad - R:px0 + pad + R]
    win = img[sl].copy()
    mask = cv2.copyMakeBorder(hand_mask(t, (img.shape[0] - 2 * pad, img.shape[1] - 2 * pad)).astype(np.uint8), pad, pad, pad, pad,
                              cv2.BORDER_CONSTANT, value=0)[sl].astype(bool)
    hsv = cv2.cvtColor(win, cv2.COLOR_BGR2HSV)
    yy, xx = np.mgrid[-R:R, -R:R]
    rr = np.hypot(xx, yy)
    yellow = (hsv[..., 1] > 100) & (hsv[..., 0] > 15) & (hsv[..., 0] < 40)
    # anything not plain yellow inside the track (prints, indices, date window) is never a copy source
    feats = cv2.dilate((~yellow & ~mask & (rr < 375)).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    ok = (~mask & ~feats).astype(np.float32)
    den = cv2.GaussianBlur(ok, (0, 0), 14)[..., None]
    low = cv2.GaussianBlur(win.astype(np.float32) * ok[..., None], (0, 0), 14) / np.maximum(den, 1e-3)
    den2 = cv2.GaussianBlur(ok, (0, 0), 50)[..., None]
    low2 = cv2.GaussianBlur(win.astype(np.float32) * ok[..., None], (0, 0), 50) / np.maximum(den2, 1e-3)
    low = np.where(den > 0.05, low, low2).astype(np.float32)
    track = rg["dial"] * S - 55  # the yellow minute track starts here
    inner = mask & (rr < track)
    outer = mask & (rr >= track)
    shifts = [("dy %+d" % (k * WAVE_ROW_PX), np.float32([[1, 0, 0], [0, 1, k * WAVE_ROW_PX]])) for k in (1, -1, 2, -2, 3, -3)]
    shifts += [("dx %+d" % dx, np.float32([[1, 0, dx], [0, 1, k * WAVE_ROW_PX]])) for k in (0, 1, -1) for dx in (-60, 60, -120, 120)]
    used = copy_fill(win, inner, mask | feats, low, shifts)
    rots = [("%+d deg" % (sg * k * 6), cv2.getRotationMatrix2D((float(R), float(R)), sg * k * 6, 1.0)) for k in range(1, 20) for sg in (1, -1)]
    used.update(copy_fill(win, outer, mask | feats, low, rots))
    todo = inner | outer
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)  # the hub zone: the local lighting (the hub disc covers it)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    OUT.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT / "dial_photo.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from": {k: v for k, v in used.items() if v}}
    (OUT / "dial_photo.json").write_text(json.dumps(meta, indent=1) + "\n")

    # ---- strap: rows from the case edge outward, each resampled to STRAP_W ----
    raw = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)
    fg = raw[..., 3] > 128
    M = t["manual_px"]
    xl, xr = M["lug_inner_x"]
    strips, rows_meta = [], []
    for sy, (n_row, tip_row) in ((1, (M["notch_rows"][0], M["lug_tip_rows"][0])), (-1, (M["notch_rows"][1], M["lug_tip_rows"][1]))):
        rows = range(n_row, -1, -1) if sy == 1 else range(n_row, img0.shape[0])
        out = []
        for y in rows:
            if (sy == 1 and y >= tip_row) or (sy == -1 and y <= tip_row):
                x0, x1 = xl, xr  # between the lugs
            else:
                xs = np.nonzero(fg[y])[0]
                if len(xs) < 10:
                    break
                x0, x1 = xs.min(), xs.max()
            out.append(cv2.resize(img0[y:y + 1, x0 + 2:x1 - 1], (STRAP_W, 1), interpolation=cv2.INTER_AREA))
        strips.append(np.vstack(out))
        rows_meta.append({"first_s_mm": round(sy * (py0 - n_row) / S, 3), "rows": len(out)})
    strap = np.vstack(strips)
    cv2.imwrite(str(OUT / "strap.jpg"), strap, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    smeta = {"source": t["source"], "width_px": STRAP_W, "rows_per_mm": round(S, 4), "top": rows_meta[0], "bottom": rows_meta[1],
             "size_px": [STRAP_W, strap.shape[0]]}
    (OUT / "strap.json").write_text(json.dumps(smeta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2000, 1000), interpolation=cv2.INTER_AREA))
    return meta, smeta


if __name__ == "__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else None))
