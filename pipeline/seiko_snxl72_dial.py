"""Cut a clean dial map for the SNXL72K1 from the straightened front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_snxl72_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snxl72k1/dial_photo.jpg

Same frame as pipeline/seiko_snkk22_dial.py (lighting from around each hand, detail from a copy), but the gold dial carries a
square grid of light lines every 90 px (3.1 mm), so inside the minute track each hand pixel takes the detail from
one or more whole grid periods away (nearest first); on the minute track (beyond 12.2 mm) it takes the same radius 6, 12 ...
deg away (60 ticks). Square map centred on the hand pivot, out to the crystal ring, at the photo's own resolution, light
unsharp mask, JPEG. Hand zones come from config/watches/seiko-snxl72k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snxl72k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snxl72k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.45  # past each hand's traced outline: its bright edge and soft glow
SHADOWS_MM = ((0.35, -0.35), (-0.35, 0.35))  # both sides to be safe
LOW_SIGMA_PX = 30  # lighting taken from around each hand, detail from the shifted copy
PERIOD_DEG = 6
PATTERN_OFFSET_PX = (6, 0)  # minute-track centre relative to the hand pivot (crystal ring fit; the hands stand above the dial)
GRID_PX = (90.0, 90.0)  # grid period across, down (line positions 776, 866 ... 1136 both ways)
TRACK_MM = 12.2  # minute track starts here


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + shadows:
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + margin  # the broad tails get their own boxes below
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            hw = h.get("half_width_root_mm", h.get("half_width_mm"))  # lit facet; the dark facet sits beside it
            m |= (along > 0) & (along < h["length_mm"] + margin) & (across < hw + margin)
            tw = h.get("tail_half_width_mm", h.get("broad_tail_half_width_mm", hw))
            m |= (along > -h["tail_mm"] - margin) & (along <= 0) & (across < tw + margin)
    return m


def feature_mask(t, shape, prints_only=False):
    """Printed or applied parts that must not be copied into a hand zone (prints_only: logo, date, print at 6)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    pad = 0 if prints_only else 15  # the tight-mask zone is the print itself; sources keep clear of it by 15 px
    to_px = lambda b: (int(px0 + b[0] * S) - pad, int(py0 - b[1] * S) - pad, int(px0 + b[2] * S) + pad, int(py0 - b[3] * S) + pad)
    for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6"):
        x0, y0, x1, y1 = to_px(t[k]["x0_y0_x1_y1_mm"])
        cv2.rectangle(m, (x0, y0), (x1, y1), 1, -1)
    if prints_only:
        return m.astype(bool)
    ix = t["indices"]
    for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12):  # no index at 3 (day-date); lume dots sit beyond the track edge
        a = math.radians(hr * 30)
        r0, r1 = ix["inner_mm"], ix["outer_mm"]
        p0 = (int(px0 + (r0 - 0.3) * S * math.sin(a)), int(py0 - (r0 - 0.3) * S * math.cos(a)))
        p1 = (int(px0 + (r1 + 0.3) * S * math.sin(a)), int(py0 - (r1 + 0.3) * S * math.cos(a)))
        cv2.line(m, p0, p1, 1, int((ix["wide_mm"].get(str(hr), ix["width_mm"]) + 0.8) * S))
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    prints = feature_mask(t, img.shape[:2], prints_only=True)
    mask = np.where(prints, hand_mask(t, img.shape[:2], (), 0.25), hand_mask(t, img.shape[:2]))[sl]  # print the hand only grazes stays
    glow = cv2.dilate(mask.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)  # hand glow is never a source
    bad = glow | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    c = (R + PATTERN_OFFSET_PX[0], R + PATTERN_OFFSET_PX[1])
    yy, xx = np.mgrid[-R:R, -R:R]
    on_dial = np.hypot(xx, yy) < TRACK_MM * S  # minute ticks, gold rehaut and bezel would brighten the lighting estimate
    valid = (~bad & on_dial).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):  # wide pass first: the middle of the hub zone is far from any clean pixel
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    used = {}
    track = np.hypot(xx - PATTERN_OFFSET_PX[0], yy - PATTERN_OFFSET_PX[1]) >= TRACK_MM * S
    shifts = sorted(((i, j) for i in range(-4, 5) for j in range(-4, 5) if i or j), key=lambda ij: math.hypot(*ij))
    moves = [("%+d,%+d grid" % ij, np.float32([[1, 0, ij[0] * GRID_PX[0]], [0, 1, ij[1] * GRID_PX[1]]]), ~track) for ij in shifts]
    moves += [("%+d deg" % (sgn * k * PERIOD_DEG), cv2.getRotationMatrix2D(c, sgn * k * PERIOD_DEG, 1.0), track)
              for k in range(1, 15) for sgn in (1, -1)]
    for name, M, where in moves:  # output pixel p takes the detail of the source pixel M maps it to
        src = low + cv2.warpAffine(detail, M, win.shape[1::-1], flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
        ok = cv2.warpAffine((~bad).astype(np.uint8), M, win.shape[1::-1], flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP, borderValue=0).astype(bool)
        take = todo & ok & where
        win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
        todo &= ~take
        used[name] = int(take.sum())
        if not todo.any():
            break
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    # soften the seam: blend a 3 px band around the filled zone
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
