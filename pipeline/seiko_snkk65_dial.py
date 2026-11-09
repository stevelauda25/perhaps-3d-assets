"""Cut a clean dial map for the SNKK65K1 from the straight front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_snkk65_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snkk65k1/dial_photo.jpg

Same method as pipeline/seiko_snkl41_dial.py. Silver sunburst dial: each hand pixel is copied from the same radius 6, 12, 18 ...
deg away (first source that is neither a hand nor a printed or applied part). Square map centred on the hand pivot, out to
the crystal ring (the green gasket stays in the map), at the photo's own resolution, light unsharp mask, JPEG. The day-date
keeps the photo's SUN 5. Hand zones come from config/watches/seiko-snkk65k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snkk65k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snkk65k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.3  # past each hand's traced outline: its bright edge and soft glow
SHADOWS_MM = ((0.35, -0.35), (-0.35, 0.35))  # soft grey on the white dial; both sides to be safe
LOW_SIGMA_PX = 20  # lighting taken from around each hand, detail from the rotated copy
PERIOD_DEG = 6
PATTERN_OFFSET_PX = (0, 0)  # minute track centred on the hand pivot


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + shadows:
        x, y = mx - dx, my - dy
        star = max(h["tail_mm"] for h in t["hands"].values() if "tail_half_width_mm" not in h) if shadows else 0  # hub and the star of tails
        m |= np.hypot(x, y) < max(t["hub_radius_mm"][0], star) + margin
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            hw = h.get("half_width_root_mm", h.get("half_width_mm"))  # lit facet; the dark facet sits beside it
            m |= (along > 0) & (along < h["length_mm"] + margin) & (across < hw + margin)
            tw = h.get("tail_half_width_mm", hw)
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
    for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        a = math.radians(hr * 30)
        r0, r1 = ix["inner_mm"], ix["outer_mm"]
        p0 = (int(px0 + (r0 - 0.3) * S * math.sin(a)), int(py0 - (r0 - 0.3) * S * math.cos(a)))
        p1 = (int(px0 + (r1 + 0.3) * S * math.sin(a)), int(py0 - (r1 + 0.3) * S * math.cos(a)))
        cv2.line(m, p0, p1, 1, int(((ix["width_12_mm"] if hr == 12 else ix["width_mm"]) + 0.8) * S))
    return m.astype(bool)


def frame_ring(t, shape, grow_px=4):
    """Dark band of the day-date frame (outer edge grown by grow_px, inner edge = the 3D frame's inner wall)."""
    S, (px0, py0), f = t["scale_px_per_mm"], t["origin_px"], t["daydate_frame"]
    (left, top, right, bottom), c = f["x0_y0_x1_y1_mm"], f["corner_mm"]

    def rr(inset):
        r, pts = c - inset, []
        for cx, cy, a0 in ((right - c, top - c, 0), (left + c, top - c, 90), (left + c, bottom + c, 180), (right - c, bottom + c, 270)):
            pts += [(px0 + (cx + r * math.cos(math.radians(a0 + 9 * k))) * S, py0 - (cy + r * math.sin(math.radians(a0 + 9 * k))) * S) for k in range(11)]
        return np.round(pts).astype(np.int32)

    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [rr(-grow_px / S)], 1)
    cv2.fillPoly(m, [rr(f["wall_mm"])], 0)
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    prints = feature_mask(t, img.shape[:2], prints_only=True)
    mask = np.where(prints, hand_mask(t, img.shape[:2], (), 0.05), hand_mask(t, img.shape[:2]))[sl]  # print the hand only grazes stays
    ring = frame_ring(t, img.shape[:2])[sl]  # the 3D frame replaces the photo's dark band; left in, it shows twice at an angle
    mask |= ring
    glow = cv2.dilate(mask.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)  # hand glow is never a source
    bad = glow | feature_mask(t, img.shape[:2])[sl]
    todo = mask & ~ring  # rotated copies would drag minute marks into the band: it takes the plain lighting below
    # the seconds needle crosses SEIKO and the 5 shield: inpaint that narrow strip from both sides so the logo stays whole
    logo = np.zeros(img.shape[:2], np.uint8)
    for k in ("logo_seiko", "logo_5_shield"):
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(logo, (int(px0 + b[0] * S) - 4, int(py0 - b[1] * S) - 4), (int(px0 + b[2] * S) + 4, int(py0 - b[3] * S) + 4), 1, -1)
    needle = hand_mask(t, img.shape[:2], (), 0.1)[sl]
    strip = needle & logo.astype(bool)[sl]
    filled = cv2.inpaint(win, needle.astype(np.uint8), 4, cv2.INPAINT_TELEA)  # whole needle: no gold left at the strip ends
    win[strip] = filled[strip]
    todo &= ~strip
    c = (R + PATTERN_OFFSET_PX[0], R + PATTERN_OFFSET_PX[1])
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):  # wide pass first: the middle of the hub zone is far from any clean pixel
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    used = {}
    # near the pivot every rotation lands on another hand: the plain black dial there takes the local lighting only
    moves = [(sgn * k * PERIOD_DEG, sc) for sc in (1.0,) for k in range(0 if sc < 1 else 1, 15) for sgn in (1, -1)]
    for deg, sc in moves:
            rot = cv2.getRotationMatrix2D(c, deg, sc)  # output pixel p takes the source pixel deg away, 1/sc further out
            src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            used["%d deg x%.0f" % (deg, 1 / sc)] = int(take.sum())
            if not todo.any():
                break
    unfilled = int(todo.sum())
    win[ring] = np.clip(low[ring], 0, 255).astype(np.uint8)
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    # soften the seam: blend a 3 px band around the filled zone
    soft = cv2.GaussianBlur((mask | cv2.dilate(strip.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)).astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from_deg": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
