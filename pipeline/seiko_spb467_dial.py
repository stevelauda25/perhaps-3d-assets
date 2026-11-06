"""Cut a clean dial map for the SPB467J1 from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_spb467_dial [out.jpg] [review.png]     # default outputs/watches/seiko-spb467j1/dial_photo.jpg

Same method as pipeline/seiko_sur419_dial.py: each hand pixel takes the lighting from around the hand and the detail from the
same radius 6, 12, 18 ... deg away (60 minute ticks on the flange; the stucco texture is random, so any rotated patch looks
like it). Sources that land on an index, the date or print are skipped. Square map centred on the hand pivot, out to the
crystal ring, at the photo's own resolution, light unsharp mask, JPEG. Zones from config/watches/seiko-spb467j1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-spb467j1-trace.json"
OUT = ROOT / "outputs/watches/seiko-spb467j1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.35
SHADOWS_MM = ((0.15, -0.25), (0.3, -0.45), (0.45, -0.7))  # soft shadows fall down-right in this render
CENTRE_MM = 2.6  # around the hub every rotation lands on a hand: copy the stucco from a clean patch instead
CENTRE_SOURCE_MM = (5.2, -3.0)  # between the minute hand and the date, clear of hands and print
LOW_SIGMA_PX = 20
PERIOD_DEG = 6


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + shadows:
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + margin
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            hw = h.get("half_width_root_mm", h.get("half_width_mm"))
            m |= (along > 0) & (along < h["length_mm"] + margin) & (across < hw + margin)
            tw = h.get("tail_half_width_mm", hw)
            m |= (along > -h["tail_mm"] - margin) & (along <= 0) & (across < tw + margin)
    return m


def feature_mask(t, shape):
    """Applied and printed parts: never copied into a hand zone, never overwritten (geometry or print stays)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    to_px = lambda b: (int(px0 + b[0] * S) - 8, int(py0 - b[1] * S) - 8, int(px0 + b[2] * S) + 8, int(py0 - b[3] * S) + 8)
    for k in ("date_frame", "logo_seiko", "print_presage", "print_6"):
        x0, y0, x1, y1 = to_px(t[k]["x0_y0_x1_y1_mm"])
        cv2.rectangle(m, (x0, y0), (x1, y1), 1, -1)
    ix = t["indices"]
    w = int((ix["width_mm"] + 0.5) * S)
    seg = lambda a, r0, r1, off=0.0: cv2.line(m, *[(int(px0 + (r * math.sin(a) + off * math.cos(a)) * S),
                                                    int(py0 - (r * math.cos(a) - off * math.sin(a)) * S)) for r in (r0 - 0.25, r1 + 0.25)], 1, w)
    for hr in range(1, 12):
        r0, r1 = (ix["short_inner_mm"], ix["short_outer_mm"]) if hr == 3 else (ix["inner_mm"], ix["outer_mm"])
        seg(math.radians(hr * 30), r0, r1)
    for off in (-ix["offset_12_mm"], ix["offset_12_mm"]):
        seg(0.0, ix["inner_mm"], ix["outer_mm"], off)
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    feat = feature_mask(t, img.shape[:2])[sl]
    mask = hand_mask(t, img.shape[:2])[sl] & ~feat
    bad = mask | feat
    todo = mask.copy()
    c = (float(R), float(R))
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):  # wide pass first: the middle of the hub zone is far from any clean pixel
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    used = {}
    yy, xx = np.mgrid[0:win.shape[0], 0:win.shape[1]]
    centre = todo & (np.hypot(xx - R, yy - R) < CENTRE_MM * S)
    shift = np.float32([[1, 0, CENTRE_SOURCE_MM[0] * S], [0, 1, -CENTRE_SOURCE_MM[1] * S]])  # output p takes p + shift
    src = low + cv2.warpAffine(detail, shift, win.shape[1::-1], flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    win[centre] = np.clip(src[centre], 0, 255).astype(np.uint8)
    todo &= ~centre
    used["centre patch"] = int(centre.sum())
    for k in range(1, 30):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D(c, deg, 1.0)
            src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            used["%d deg" % deg] = int(take.sum())
        if not todo.any():
            break
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
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
