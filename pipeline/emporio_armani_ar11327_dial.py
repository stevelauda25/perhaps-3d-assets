"""Cut the Emporio Armani AR11327 dial map (hands removed) and a repeating mesh-bracelet tile from the front photo.

    python3 -B -m pipeline.emporio_armani_ar11327_dial [out.jpg] [review.png]   # default outputs/watches/emporio-armani-ar11327/dial_photo.jpg

Dial: hand needles and the hub (from config/watches/emporio-armani-ar11327-trace.json) filled with a normalised blur of
the pixels around them, coarse to fine; the 3D hands cover them. Crop to the bezel groove at native resolution, light
unsharp mask, JPEG. The photo is turned ~13 deg, so the map is narrower than tall; the build stretches it back with
half_w_mm.
Mesh: the weave repeats every two rows with a sideways step; rows are sheared by that step so the tile repeats straight
along the bracelet (wrap in v), one repeat measured by template matching on the flat band below the 6 o'clock end cap.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/emporio-armani-ar11327-trace.json"
OUT = ROOT / "outputs/watches/emporio-armani-ar11327/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_MM = 19.3  # map reaches the bezel groove (19.24 mm)
MARGIN_PX = 10
SHADOWS_MM = ((0.15, -0.15), (0.3, -0.3))  # soft shadow down-right of the hands (light from the upper left)
FILL_SIGMAS_PX = (30, 6)
REPEATS = 2  # mesh tile height in weave periods


def hand_mask(t, shape):
    S, ct, (px0, py0) = t["scale_px_per_mm"], t["cos_tilt"], t["origin_px"]
    P = lambda x, y: (int(round(px0 + x * S * ct)), int(round(py0 - y * S)))
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        for h in t["hands"].values():
            w = int(round(2 * h["half_width_mm"] * S)) + 2 * MARGIN_PX
            cv2.line(m, P(dx, dy), P(h["tip_mm"][0] + dx, h["tip_mm"][1] + dy), 1, w)
        cv2.circle(m, P(dx, dy), int(t["hub_mm"]["radius"] * S) + MARGIN_PX, 1, -1)
    return m


def mesh_tile(img, t):
    S, ct, M = t["scale_px_per_mm"], t["cos_tilt"], t["manual_px"]
    (r0, r1), (x0, x1) = M["mesh_rows"], M["mesh_x"]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    tpl = g[r0:r0 + 60, x0 + 60:x1 - 60]
    # one weave period sits ~70 rows down with a sideways step; find REPEATS periods exactly
    lo = r0 + 55 * REPEATS
    res = cv2.matchTemplate(g[lo:lo + 60 * REPEATS, x0:x1], tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, (bx, by) = cv2.minMaxLoc(res)
    period, step = lo + by - r0, bx - 60
    assert r0 + period < r1 and score > 0.8, (period, step, score)
    rows = np.arange(period, dtype=np.float32)
    mx = np.tile(np.arange(x0, x1, dtype=np.float32), (period, 1)) + (rows * step / period)[:, None] - min(step, 0)
    my = np.repeat((r0 + rows)[:, None], x1 - x0, 1)
    tile = cv2.remap(img, mx, my, cv2.INTER_LINEAR)
    return tile, {"period_px": int(period), "step_px": int(step), "match": round(float(score), 3),
                  "tile_mm": round(period / S, 4), "photo_half_width_mm": round((x1 - x0) / 2 / (S * ct), 4)}


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, ct, (px0, py0) = t["scale_px_per_mm"], t["cos_tilt"], t["origin_px"]
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
    H, W = int(round(HALF_MM * S)), int(round(HALF_MM * S * ct))
    crop = clean[py0 - H:py0 + H, px0 - W:px0 + W]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    tile, tm = mesh_tile(img, t)
    tile_path = out.with_name("mesh_tile.jpg")
    cv2.imwrite(str(tile_path), tile, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # build: u = 0.5 + x / (2 half_w), v = 0.5 + y / (2 half_h); mesh: u across the band, v = s / tile_mm (repeat)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_w_mm": round(W / (S * ct), 4), "half_h_mm": round(H / S, 4),
            "size_px": list(crop.shape[1::-1]), "masked_px": int(mask.sum()), "mesh": {"file": tile_path.name, **tm}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[py0 - H:py0 + H, px0 - W:px0 + W].copy()
        mk = mask[py0 - H:py0 + H, px0 - W:px0 + W].astype(bool)
        shown[mk] = (0.5 * shown[mk] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[py0 - H:py0 + H, px0 - W:px0 + W]]))
        cv2.imwrite(str(review.with_name("mesh_tile_x3.jpg")), np.vstack([tile] * 3))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
