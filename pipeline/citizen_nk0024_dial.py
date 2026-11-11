"""Cut a clean dial map for the Citizen NK0024-54X (Tsuyosa 60, green patterned dial) from the front photo, hands, applied
indices and their shadows removed.

    python3 -B -m pipeline.citizen_nk0024_dial [out.jpg] [review.png]   # default outputs/watches/citizen-nk0024-54x/dial_photo.jpg

Same method as pipeline/seiko_sur419_dial.py. The dial pattern repeats every 3 deg about the dial centre and the printed
minute track every 6 deg, so each hidden pixel takes the pattern detail from the same radius 6, 12, 18 ... deg away (first
source that is neither a hand, an index nor a print) on top of the local lighting (weighted blur round the hidden zone).
Square map centred on the dial centre, out to the gold rehaut, at the photo's resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/citizen-nk0024-54x-trace.json"
OUT = ROOT / "outputs/watches/citizen-nk0024-54x/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.25
SHADOWS_MM = ((0.25, -0.25), (0.0, -0.35), (0.05, -0.6))  # light from above: the seconds needle's shadow lies 0.6 mm below it
LOW_SIGMA_PX = 20
PERIOD_DEG = 6


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["hand_pivot_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + tuple(shadows):
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + margin
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            al, ac = x * ux + y * uy, np.abs(-x * uy + y * ux)
            m |= (al > 0) & (al < h["tip"] + margin) & (ac < h["half"] + margin)
            m |= (al <= 0) & (al > -h["tail"][0] - margin) & (ac < h["tail"][1] + margin)
    return m


def index_mask(t, shape, pad_mm):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["indices"]
    m = np.zeros(shape, np.uint8)
    for b in ix["bars"]:
        a = math.radians(b["angle_deg"])
        u, v = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
        L, W = b["half_len_mm"] + ix["frame_mm"] + pad_mm, b["half_w_mm"] + ix["frame_mm"] + pad_mm
        cx, cy = b["centre_mm"]
        pts = [(px0 + (cx + su * L * u[0] + sv * W * v[0]) * S, py0 - (cy + su * L * u[1] + sv * W * v[1]) * S) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m.astype(bool)


def feature_mask(t, shape):
    """Prints and applied parts that must not be copied into a hidden zone."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in ("logo", "print_automatic", "cyclops"):
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S) - 6, int(py0 - b[1] * S) - 6), (int(px0 + b[2] * S) + 6, int(py0 - b[3] * S) + 6), 1, -1)
    return m.astype(bool) | index_mask(t, shape, 0.35)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["rings_mm"]["dial_out"] * S)) + 2
    cx, cy = int(round(px0)), int(round(py0))
    sl = np.s_[cy - R:cy + R, cx - R:cx + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    feats = feature_mask(t, shape)[sl]
    prints = feature_mask(t, shape)[sl] & ~index_mask(t, shape, 0.35)[sl]
    todo = (hand_mask(t, shape)[sl] & ~prints) | index_mask(t, shape, 0.15)[sl]
    todo |= hand_mask(t, shape, (), 0.05)[sl]  # a hand over a print: only its own outline
    bad = todo | feats
    c = (px0 - (cx - R), py0 - (cy - R))
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):  # wide pass first: the hub zone is far from any clean pixel
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    used, left = {}, todo.copy()
    for deg in [sgn * k * PERIOD_DEG for k in range(1, 30) for sgn in (1, -1)]:
        rot = cv2.getRotationMatrix2D(c, deg, 1.0)
        src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ok = cv2.warpAffine(cv2.erode((~bad).astype(np.uint8), np.ones((3, 3), np.uint8)), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST,
                            borderValue=0).astype(bool)
        take = left & ok
        win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
        left &= ~take
        used[str(deg)] = int(take.sum())
        if not left.any():
            break
    # the hub zone: every rotation lands on it; mirror the concentric rings just outside it radially inward (r -> 2 R0 - r)
    yy, xx = np.mgrid[0:win.shape[0], 0:win.shape[1]].astype(np.float32)
    rr = np.hypot(xx - c[0], yy - c[1])
    r0 = float(rr[left].max()) + 1 if left.any() else 0.0
    k = (2 * r0 - rr) / np.maximum(rr, 1e-3)
    mirrored = cv2.remap(win, (c[0] + (xx - c[0]) * k).astype(np.float32), (c[1] + (yy - c[1]) * k).astype(np.float32), cv2.INTER_LINEAR)
    win[left] = mirrored[left]
    soft = cv2.GaussianBlur(todo.astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [cx, cy], "centre_offset_px": [round(px0 - cx, 2), round(py0 - cy, 2)],
            "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "masked_px": int(todo.sum()), "mirrored_px": int(left.sum()), "mirror_radius_px": round(r0, 1),
            "filled_from_deg": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[todo] = (0.5 * shown[todo] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
