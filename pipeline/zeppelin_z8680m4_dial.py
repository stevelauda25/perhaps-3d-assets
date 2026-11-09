"""Cut the Z8680M4 dial map (dial, flange and telemeter ring) and mesh map from the straightened front photo.

    python3 -B -m pipeline.zeppelin_z8680m4_dial [out.jpg] [review.png]   # default outputs/watches/zeppelin-z8680m4/dial_photo.jpg

Same fill as pipeline/zeppelin_z70363_dial.py: the hand zones (posed outlines from config/watches/zeppelin-z8680m4-trace.json)
are filled with a normalised blur of the pixels around them; the 3D hands cover the zones from the front. Square map to the
polished bezel's inner edge, centred on the hand pivot, at the photo's own resolution, light unsharp mask, JPEG.

mesh_photo.jpg: a band of the 6 o'clock Milanese mesh (seen almost face-on) between its edges, MESH_PERIODS repeats long. The
pattern repeats every MESH_REPEAT_PX = (138 down, 22 across); each row is shifted back by its share of the 22 px so the band
tiles end to end. Row brightness is evened out and the first rows fade in from one band later, so the repeats show no seam.
The build tiles it along the bracelet.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/zeppelin-z8680m4-trace.json"
OUT = ROOT / "outputs/watches/zeppelin-z8680m4/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.2
SHADOWS_MM = ((0.15, -0.15),)
FILL_SIGMAS_PX = (40, 12, 4)
MESH_REPEAT_PX = (138, 22)  # (rows, sideways shift): best autocorrelation of the mesh band, r = 0.89
MESH_PERIODS = 2


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    hs, subs = t["hands"], t["subdials"]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        for poly in [h["outline_mm"] for h in hs.values()] + [s["outline_mm"] for s in subs.values()]:
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in poly]).astype(np.int32)], 1)
        circles = [(hs[n]["disc_centre_mm"], hs[n]["disc_ring_r_mm"]) for n in ("hour", "minute")]
        circles += [((0, 0), hs["chrono"]["hub_r_mm"] * 1.9)] + [(s["centre_mm"], s["hub_r_mm"]) for s in subs.values() if s["hub_r_mm"]]
        circles += [(s["tail_disc_mm"][:2], s["tail_disc_mm"][2]) for s in subs.values() if "tail_disc_mm" in s]
        for c, r in circles:
            cv2.circle(m, tuple(int(v) for v in P(c, dx, dy)), int(r * S * 1.1), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=max(1, int(MARGIN_MM * S / 1.5)))


def mesh_map(img, t):
    (x0, x1), y0 = t["manual_px"]["mesh_x"], t["manual_px"]["mesh_rows_y"][0]
    dy, dx = MESH_REPEAT_PX
    h, fade = dy * MESH_PERIODS, dy // 3
    xs = np.arange(x0, x1 - dx * MESH_PERIODS, dtype=np.float32)
    mx = np.tile(xs, (h + fade, 1)) + (np.arange(h + fade, dtype=np.float32)[:, None] * dx / dy)
    my = np.tile(np.arange(y0, y0 + h + fade, dtype=np.float32)[:, None], (1, len(xs)))
    band = cv2.remap(img, mx, my, cv2.INTER_LANCZOS4).astype(np.float32)
    row = cv2.GaussianBlur(band.mean(axis=(1, 2)).reshape(-1, 1), (0, 0), 25).ravel()  # smooth light falloff along the band
    band *= (row.mean() / row)[:, None, None]
    w = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None]  # first rows fade in from the same rows one band later: no seam
    band[:fade] = w * band[:fade] + (1 - w) * band[h:h + fade]
    band = band[:h]
    return np.clip(band, 0, 255).astype(np.uint8)


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
    R = int(round((t["rings_mm"]["bezel_inner"] + 0.3) * S))
    crop = clean[py0 - R:py0 + R, px0 - R:px0 + R]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = 0.5 + x / (2 half), v = 0.5 + y / (2 half)
    mesh = mesh_map(img, t)
    cv2.imwrite(str(out.parent / "mesh_photo.jpg"), mesh, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # mesh: u = 0.5 + x / (2 half_w), v = (s - start) / length, repeated
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_mm": round(R / S, 4), "size_px": list(crop.shape[1::-1]), "masked_px": int(mask.sum()),
            "mesh_repeat_mm": round(mesh.shape[0] / S, 4), "mesh_size_px": list(mesh.shape[1::-1])}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = img[sl].copy()
        mk = mask[sl].astype(bool)
        shown[mk] = (0.5 * shown[mk] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[sl]]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
