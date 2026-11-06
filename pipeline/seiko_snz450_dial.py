"""Cut a clean dial map for the SNZ450J1 from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_snz450_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snz450j1/dial_photo.jpg

Same method as pipeline/seiko_snkl50_dial.py: each hand pixel is copied from the same radius 6, 12, 18 ... deg away (60 printed
minute ticks), with the lighting of the gold sunburst taken from around the hand. Differences: the map is centred on the circle
through the indices (the dial plane), the hands on the visible hub, which sits about 10 px higher (tilt); the photo is turned
by photo_rot_deg, which the build undoes in the dial UV, not by resampling here. Hand zones come from
config/watches/seiko-snz450j1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snz450j1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snz450j1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.25  # past each hand's traced outline: its bright edge and soft glow
SHADOWS_MM = ((0.45, -0.45),)  # light from the upper left
LOW_SIGMA_PX = 25
PERIOD_DEG = 6
NEAR_HUB_MM = 3.0  # inside this the sunburst lines converge: plain lighting, no copied detail
FEATURES = ("daydate_frame", "marker_12", "logo_seiko", "logo_5_shield", "print_sports", "print_water_automatic_jewels", "print_6")


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (hx, hy) = t["scale_px_per_mm"], t["hub_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - hx) / S, -(yy - hy) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + shadows:
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + margin
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_photo_deg"])), math.cos(math.radians(h["angle_photo_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            m |= (along > 0) & (along < h["length_mm"] + margin) & (across < h["half_width_mm"] + margin)
            tw = h.get("tail_half_width_mm", h["half_width_mm"] * 1.15)  # hour and minute tails are wider blocks
            m |= (along > -h["tail_mm"] - margin) & (along <= 0) & (across < tw + margin)
    return m


def feature_mask(t, shape, prints_only=False):
    """Printed or applied parts that must not be copied into a hand zone (prints_only: the boxes themselves)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    pad = 0 if prints_only else 12
    to_px = lambda b: (int(px0 + b[0] * S) - pad, int(py0 - b[1] * S) - pad, int(px0 + b[2] * S) + pad, int(py0 - b[3] * S) + pad)
    for k in FEATURES:
        x0, y0, x1, y1 = to_px(t[k]["x0_y0_x1_y1_mm"])
        cv2.rectangle(m, (x0, y0), (x1, y1), 1, -1)
    if prints_only:
        return m.astype(bool)
    ix, rot = t["indices"], t["photo_rot_deg"]
    for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11):
        a = math.radians(hr * 30 + rot)
        p = lambda r: (int(px0 + r * S * math.sin(a)), int(py0 - r * S * math.cos(a)))
        cv2.line(m, p(ix["lume_inner_mm"] - 0.4), p(ix["lume_outer_mm"] + 0.4), 1, int((ix["lume_width_mm"] + 0.9) * S))
        cv2.circle(m, p(ix["lume_inner_mm"] - 1.3), int(0.9 * S), 1, -1)  # minute numeral inside each index
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S)) + 4
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    prints = feature_mask(t, img.shape[:2], prints_only=True)
    mask = np.where(prints, hand_mask(t, img.shape[:2], (), 0.2), hand_mask(t, img.shape[:2]))[sl]  # print a hand only grazes stays
    bad = mask | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    yy, xx = np.mgrid[0:2 * R, 0:2 * R]
    near_hub = np.hypot(xx - (t["hub_px"][0] - px0 + R), yy - (t["hub_px"][1] - py0 + R)) < NEAR_HUB_MM * S
    c = (R, R)  # minute track centred on the map centre (the index circle)
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):  # wide pass first: the middle of the hub zone is far from any clean pixel
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    win[todo & near_hub] = np.clip(low[todo & near_hub], 0, 255).astype(np.uint8)  # turned copies draw a fan round the hub
    todo &= ~near_hub
    used = {}
    for deg in [sgn * k * PERIOD_DEG for k in range(1, 6) for sgn in (1, -1)]:
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
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]  # soften the seam
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
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 900, 900), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
