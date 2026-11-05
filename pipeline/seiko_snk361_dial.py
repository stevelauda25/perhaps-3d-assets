"""Cut a clean dial map for the SNK361K1 from the front photo, with the hands removed.

    python3 -B -m pipeline.seiko_snk361_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snk361k1/dial_photo.jpg

The dial is plain black, so the hand zones are filled with OpenCV inpainting (pipeline/seiko_dial.py copies a woven pattern
instead). The seconds hand crosses SEIKO and the 5 shield in this photo, so that block is replaced by the same applied logo
from the SNK381K1 front photo (no hand over it): grey, matched in scale and position by template matching, levels mapped to
this photo's black and white, feathered edges. Indices, print and the day-date stay as photographed. Square map centred on the hand pivot, out to the
crystal ring, at the photo's own resolution, light unsharp mask, JPEG. Hand zones come from config/watches/seiko-snk361k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snk361k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snk361k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.3  # past each hand's traced outline: its bright edge and soft glow
TAIL_EXTRA_MM = (0.5, 0.3)  # tails: the traced end point is the paddle centre, the paddle reaches further and wider
LOGO_DONOR = ROOT / "references/seiko-snk381k1/front_4698x9372.png"
DONOR_BOX = (1945, 3884, 2643, 4315)  # SEIKO + 5 shield in the donor, 15 px clear of both
DONOR_LEVELS, TARGET_LEVELS = (30, 195), (16, 239)  # median dial black and letter white, donor -> this photo
FEATHER_PX = 10


def paste_logo(img, t):
    """Replace this photo's SEIKO + 5 shield block with the donor's, in place. Returns where and how well it matched."""
    a, b = t["logo_seiko"]["x0_y0_x1_y1_mm"], t["logo_5_shield"]["x0_y0_x1_y1_mm"]
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    xs = [px0 + v * S for v in (a[0], a[2], b[0], b[2])]
    ys = [py0 - v * S for v in (a[1], a[3], b[1], b[3])]
    sx0, sy0, sx1, sy1 = int(min(xs)) - 60, int(min(ys)) - 60, int(max(xs)) + 60, int(max(ys)) + 60
    target = cv2.cvtColor(img[sy0:sy1, sx0:sx1], cv2.COLOR_BGR2GRAY)
    x0, y0, x1, y1 = DONOR_BOX
    donor = cv2.cvtColor(cv2.imread(str(LOGO_DONOR))[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(float)
    (d0, d1), (t0, t1) = DONOR_LEVELS, TARGET_LEVELS
    donor = np.clip((donor - d0) * (t1 - t0) / (d1 - d0) + t0, 0, 255).astype(np.uint8)
    best = None
    for k in np.arange(0.60, 0.80, 0.0025):
        d = cv2.resize(donor, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
        if d.shape[0] >= target.shape[0] or d.shape[1] >= target.shape[1]:
            continue
        _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(target, d, cv2.TM_CCOEFF_NORMED))
        if best is None or score > best[0]:
            best = (score, k, loc, d)
    score, k, (lx, ly), d = best
    m = np.zeros(d.shape, np.float32)
    m[FEATHER_PX:-FEATHER_PX, FEATHER_PX:-FEATHER_PX] = 1
    m = cv2.GaussianBlur(m, (0, 0), FEATHER_PX / 2)[..., None]
    region = img[sy0 + ly:sy0 + ly + d.shape[0], sx0 + lx:sx0 + lx + d.shape[1]]
    region[:] = (m * d[..., None] + (1 - m) * region).astype(np.uint8)
    return {"donor": str(LOGO_DONOR.relative_to(ROOT)), "scale": round(float(k), 4), "match": round(float(score), 3),
            "at_px": [sx0 + lx, sy0 + ly, d.shape[1], d.shape[0]]}


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.hypot(mx, my) < t["hub_radius_mm"][0] + MARGIN_MM
    for h in t["hands"].values():
        ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
        along, across = mx * ux + my * uy, np.abs(-mx * uy + my * ux)
        # blade from the pivot to the tip, wider tail behind the pivot
        m |= (along > 0) & (along < h["length_mm"] + MARGIN_MM) & (across < h["half_width_mm"] + MARGIN_MM)
        m |= (along > -h["tail_mm"] - TAIL_EXTRA_MM[0]) & (along <= 0) & (across < h["tail_half_width_mm"] + TAIL_EXTRA_MM[1])
    return m


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    pad = 20  # inpainting looks past the crop edge
    win = img[py0 - R - pad:py0 + R + pad, px0 - R - pad:px0 + R + pad]
    mask = hand_mask(t, img.shape[:2])[py0 - R - pad:py0 + R + pad, px0 - R - pad:px0 + R + pad]
    full = img.copy()
    full[py0 - R - pad:py0 + R + pad, px0 - R - pad:px0 + R + pad] = cv2.inpaint(win, mask.astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA)
    logo = paste_logo(full, t)
    clean = full[py0 - R:py0 + R, px0 - R:px0 + R]
    soft = cv2.GaussianBlur(clean, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(clean, 1 + SHARPEN[1], soft, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "logo": logo}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = win[pad:-pad, pad:-pad].copy()
        m = mask[pad:-pad, pad:-pad]
        shown[m] = (0.5 * shown[m] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
