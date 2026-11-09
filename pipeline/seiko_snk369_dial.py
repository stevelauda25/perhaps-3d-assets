"""Cut a clean dial map for the SNK369K1 from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_snk369_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snk369k1/dial_photo.jpg

The dial is white with a printed red and grey track from 12 to 4 o'clock. Hand pixels on the track are copied from the same
spot one hour (30 deg) round the pivot, so the track blocks and the edge of the 1/2 o'clock indices repeat exactly; the rest of
the dial is plain white and is filled with OpenCV inpainting. Square map centred on the hand pivot, out to the crystal ring, at
the photo's own resolution, light unsharp mask, JPEG. Hand zones come from config/watches/seiko-snk369k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snk369k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snk369k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.45  # past each hand's traced outline: its edge, soft glow and the soft edge of its shadow
SHADOWS_MM = ((0.45, -0.45), (0.9, -0.9))  # light from the upper left: each hand's soft shadow lies down and to the right
TRACK = (9.9, 0.0, 125.0)  # printed track: from this radius (mm, outside the minute numerals) between these angles (deg)
TRACK_SHIFTS = (-30, 30, -60, 60)  # deg, tried in order; whole hours so the indices on the track line up too
ZERO_OF_10 = (1342, 1633, 21)  # photo px: centre and radius of the 0 of the red 10, kept out of the mask
ONE_OF_10 = ((1313, 1616), (1342, 1598))  # photo px: ends of the 1 of 10, hidden under the seconds hand (radial, beside the 0)
ONE_STROKE_PX = 7
FIFTY = (665, 1615, 33)  # photo px: the 50 beside the hour hand's tip, kept out of the mask
GRAIN_BOX = (840, 2160, 940, 2260)  # photo px: plain white dial; its fine grain is tiled over the filled areas
KEEP_OUT = (ZERO_OF_10, FIFTY)  # print just clear of a hand: (x, y, r) photo px, never masked


def plain_dial(out):
    """Pixels of the plain dial (float BGR image) that may seed the fill: white here, no print, track, frame or bezel."""
    return (out.min(2) > 215) & (out.max(2) - out.min(2) < 25)


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.hypot(mx, my) < t["hub_radius_mm"][0] + MARGIN_MM
    hs = t["hands"]
    for ox, oy in ((0.0, 0.0),) + SHADOWS_MM:
        sx, sy = mx - ox, my - oy
        for name, h in hs.items():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = sx * ux + sy * uy, np.abs(-sx * uy + sy * ux)
            tail = h.get("tail_mm", 0.3)
            m |= (along > 0) & (along < h["length_mm"] + MARGIN_MM) & (across < h["half_width_mm"] + MARGIN_MM)
            if name == "hour":  # arrow head
                m |= (along > h["head_base_mm"] - MARGIN_MM) & (along < h["length_mm"] + MARGIN_MM) & (across < h["head_half_width_mm"] + MARGIN_MM)
            m |= (along > -tail - MARGIN_MM) & (along <= 0) & (across < h.get("tail_half_width_mm", h["half_width_mm"]) + MARGIN_MM)
    return m


def fill_track(img, mask, t):
    """Copy masked track pixels from the same radius one or two hours round. Returns the pixels still to fill."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    mx, my = (xx - px0) / S, -(yy - py0) / S
    r, a = np.hypot(mx, my), np.degrees(np.arctan2(mx, my)) % 360
    zone = mask & (r > TRACK[0]) & (a >= TRACK[1]) & (a <= TRACK[2])
    todo = zone.copy()
    for d in TRACK_SHIFTS:
        src_a = np.radians(a + d)
        sx, sy = (px0 + r * S * np.sin(src_a)).astype(np.float32), (py0 - r * S * np.cos(src_a)).astype(np.float32)
        src = cv2.remap(img, sx, sy, cv2.INTER_LINEAR)
        src_masked = cv2.remap(mask.astype(np.uint8), sx, sy, cv2.INTER_NEAREST).astype(bool)
        ok = todo & ~src_masked & ((a + d) % 360 >= TRACK[1]) & ((a + d) % 360 <= TRACK[2])
        img[ok] = src[ok]
        todo &= ~ok
    return (mask & ~zone) | todo


def smooth_fill(img, todo, grain):
    """Fill masked white-dial pixels with the broad dial shade (normalised blur) plus the dial's own grain; inpainting leaves grey smears."""
    out = img.astype(np.float32)
    valid = cv2.dilate(todo.astype(np.uint8), np.ones((9, 9), np.uint8)) == 0  # skip the grey fringe
    valid &= plain_dial(out)
    valid = valid.astype(np.float32)
    left = todo.copy()
    for sigma in (24, 48, 96, 192):
        num = cv2.GaussianBlur(out * valid[..., None], (0, 0), sigma)
        den = cv2.GaussianBlur(valid, (0, 0), sigma)[..., None]
        ok = left & (den[..., 0] > 0.05)
        out[ok] = (num / np.maximum(den, 1e-6))[ok]
        left &= ~ok
    g = grain.astype(np.float32)
    g -= cv2.GaussianBlur(g, (0, 0), 3)
    reps = (-(-img.shape[0] // g.shape[0]), -(-img.shape[1] // g.shape[1]), 1)
    out[todo] += np.tile(g, reps)[:img.shape[0], :img.shape[1]][todo]
    return np.clip(out, 0, 255).astype(np.uint8)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    pad = 20  # inpainting looks past the crop edge
    y0, y1, x0, x1 = py0 - R - pad, py0 + R + pad, px0 - R - pad, px0 + R + pad
    win = img[y0:y1, x0:x1].copy()
    mask = hand_mask(t, img.shape[:2])
    for cx, cy, cr in KEEP_OUT:
        cv2.circle(mask.view(np.uint8), (cx, cy), cr, 0, -1)
    bx0, by0, bx1, by1 = t["manual_px"]["daydate_frame"]  # the frame is never under a hand, only near the shadow zone
    mask[by0 - 4:by1 + 4, bx0 - 4:bx1 + 4] = False
    mask = mask[y0:y1, x0:x1]
    t_win = dict(t, origin_px=[px0 - x0, py0 - y0])
    filled = win.copy()
    rest = fill_track(filled, mask, t_win)
    gx0, gy0, gx1, gy1 = GRAIN_BOX
    filled = smooth_fill(filled, rest, img[gy0:gy1, gx0:gx1])
    if ONE_OF_10:  # the 1 of 10 lies under the seconds hand: redraw it as a stroke in the colour of the 0 beside it
        zx, zy, zr = ZERO_OF_10
        ring = win[zy - y0 - zr:zy - y0 + zr, zx - x0 - zr:zx - x0 + zr].reshape(-1, 3)
        red = np.median(ring[ring.astype(int).sum(1) < 450], axis=0)
        (ax, ay), (bx, by) = ONE_OF_10
        cv2.line(filled, (ax - x0, ay - y0), (bx - x0, by - y0), [int(v) for v in red], ONE_STROKE_PX, cv2.LINE_AA)
    clean = filled[pad:-pad, pad:-pad]
    soft = cv2.GaussianBlur(clean, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(clean, 1 + SHARPEN[1], soft, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "inpainted_px": int(rest.sum())}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = win[pad:-pad, pad:-pad].copy()
        m = mask[pad:-pad, pad:-pad]
        shown[m] = (0.5 * shown[m] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, crop]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
