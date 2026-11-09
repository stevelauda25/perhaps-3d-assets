"""Cut a clean dial map for the SNK623K1 from the straightened front photo, with the hands removed.

    python3 -B -m pipeline.seiko_snk623_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snk623k1/dial_photo.jpg

Same method as pipeline/seiko_snkl41_dial.py, for a plain black dial with 60 white minute-track marks: each hand pixel is
copied from the same radius 6, 12, 18 ... deg away (first source that is neither a hand nor a printed or applied part). The
day and date windows are clean in the photo and stay as photographed. Square map centred on the hand pivot, out to the
crystal ring, at the photo's own resolution, light unsharp mask, JPEG. Hand zones come from config/watches/seiko-snk623k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snk623k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snk623k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.3  # past each hand's traced outline: its bright edge and glow
SHADOWS_MM = ((0.45, -0.45),)  # light from the upper left
LOW_SIGMA_PX = 20  # lighting taken from around each hand, detail from the rotated copy
PERIOD_DEG = 6
PATTERN_OFFSET_PX = (7, 12)  # minute-track centre (rectify output, 1450, 1450) relative to the hand pivot
FEATURES = ("date_window", "day_window", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "numeral_12", "numeral_9", "numeral_6")


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + shadows:
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + 0.4 + margin
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            hw = h["half_width_mm"]
            taper = np.clip((h["length_mm"] - along) / (0.75 * h["length_mm"]), 0.15, 1.0) if "tail_half_width_mm" not in h else 1.0
            m |= (along > 0) & (along < h["length_mm"] + margin) & (across < hw * taper + margin)  # dauphine: widest at the root
            tw = h.get("tail_half_width_mm", hw)
            m |= (along > -h["tail_mm"] - margin) & (along <= 0) & (across < tw + margin)
    return m


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone (kept clear by 15 px)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in FEATURES:
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S) - 15, int(py0 - b[1] * S) - 15), (int(px0 + b[2] * S) + 15, int(py0 - b[3] * S) + 15), 1, -1)
    ix = t["indices"]
    for hr in ix["hours"]:
        a = math.radians(hr * 30)
        p0 = (int(px0 + (ix["inner_mm"] - 0.4) * S * math.sin(a)), int(py0 - (ix["inner_mm"] - 0.4) * S * math.cos(a)))
        p1 = (int(px0 + (ix["outer_mm"] + 0.4) * S * math.sin(a)), int(py0 - (ix["outer_mm"] + 0.4) * S * math.cos(a)))
        cv2.line(m, p0, p1, 1, int((ix["width_mm"] + 1.6) * S))  # with the raised baton's grey side and shadow
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    mask = hand_mask(t, img.shape[:2])[sl]
    glow = cv2.dilate(mask.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)  # hand glow is never a source
    bad = glow | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    c = (R + PATTERN_OFFSET_PX[0], R + PATTERN_OFFSET_PX[1])
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):  # wide pass first: the middle of the hub zone is far from any clean pixel
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    used = {}
    for k in range(1, 15):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D(c, deg, 1.0)
            src = cv2.warpAffine(win, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)  # plain black dial: copy as is
            ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            used["%d deg" % deg] = int(take.sum())
    unfilled = int(todo.sum())  # near the pivot every rotation lands on another hand: the plain black dial takes the local lighting
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
