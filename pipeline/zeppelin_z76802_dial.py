"""Cut the Z76802 photo map (dial, telemeter ring and strap) from the front photo, with the hands, hubs and their shadows removed.

    python3 -B -m pipeline.zeppelin_z76802_dial [out.jpg] [review.png]   # default outputs/watches/zeppelin-z76802/dial_photo.jpg

Same fill as pipeline/zeppelin_z7680mb2_dial.py and the strap straightening of pipeline/zeppelin_z96905_dial.py: the hand zones (posed outlines from config/watches/zeppelin-z76802-trace.json)
are filled with a normalised blur of the pixels around them, coarse to fine; the 3D hands cover them from the front.
One map: full photo height (strap) by the bezel width, centred on the hand pivot, photo resolution, light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/zeppelin-z76802-trace.json"
OUT = ROOT / "outputs/watches/zeppelin-z76802/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_WIDTH_MM = 19.8  # map x range: dial and telemeter ring to the bezel; the strap is narrower
MARGIN_MM = 0.35  # soft photo: the hands bleed about 10 px into the dial
SHADOWS_MM = ((0.15, -0.15),)  # soft halo, light from the upper left
FILL_SIGMAS_PX = (40, 12, 4)
DIAL_MAX_GREY = 110


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


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    # fill only from the dark dial: white print and the hands' bright halo would grey the black dial
    valid = ((1 - mask) * (cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) < DIAL_MAX_GREY)).astype(np.float32)[..., None]
    est = None
    for sig in FILL_SIGMAS_PX:  # normalised blur of the unmasked pixels: smooth dial colour, no streaks from the hand edges
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        e = cv2.GaussianBlur(img * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        est = e if est is None else np.where(wgt > 0.2, e, est)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = np.clip(soft * est + (1 - soft) * img, 0, 255).astype(np.uint8)
    # strap past the lug tips: the photo's strap narrows where it curls away, so each row's leather is stretched to the
    # model's strap width (no white background on the strap edges); rows with under half the width are past the end
    lg = t["lug"]
    hw = int(round((lg["inner_x_mm"] - 0.05) * S))
    reach = int(round((lg["inner_x_mm"] + 0.5) * S))
    ends = {}
    for sy, rows in ((1, range(int(py0 - (lg["tip_mm"]["mean"] + 0.3) * S), -1, -1)), (-1, range(int(py0 + (lg["tip_mm"]["mean"] + 0.3) * S), img.shape[0]))):
        for row in rows:
            dark = np.nonzero(img[row, px0 - reach:px0 + reach].min(1) < 215)[0]
            if len(dark) < hw:
                break
            seg = clean[row:row + 1, px0 - reach + dark.min():px0 - reach + dark.max() + 1]
            clean[row, px0 - hw:px0 + hw] = cv2.resize(seg, (2 * hw, 1), interpolation=cv2.INTER_LINEAR)[0]
            ends["top" if sy > 0 else "bottom"] = round(abs(py0 - row) / S - 0.2, 2)
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
        R = int(19.8 * S)
        sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = img[sl].copy()
        shown[mask[sl].astype(bool)] = (0.5 * shown[mask[sl].astype(bool)] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[sl]]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
