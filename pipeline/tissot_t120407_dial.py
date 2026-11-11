"""Cut the Tissot T120.407.17.041.00 (Seastar 1000 Powermatic 80, 43 mm) photo maps from the official front render: the dial
(hands and applied indices removed) and the rubber strap.

    python3 -B -m pipeline.tissot_t120407_dial [review.png]
    # -> outputs/watches/tissot-t120.407.17.041.00/dial_photo.jpg (+ .json) and strap.jpg (+ .json)

Dial map: as pipeline/tissot_t120607_dial.py. Square crop centred on the hand pivot out to the bezel's inner lip, native
resolution. The flange's minute track repeats every 6 deg, so flange pixels under a hand are copied from the same radius 6, 12
... deg away; the blue gradient under the hands and indices is a smooth inpaint (every filled pixel lies under a 3D hand or
index). Light unsharp mask, JPEG 93.
Strap map: as pipeline/bulova_96b431_dial.py. Each render row of the strap from the case edge outward, resampled to one width
(the strap tapers), 12 o'clock rows first, then 6 o'clock rows.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.tissot_t120607_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/tissot-t120.407.17.041.00-trace.json"
OUT = ROOT / "outputs/watches/tissot-t120.407.17.041.00"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.3
SHADOWS_MM = ((0.25, -0.25),)  # the render's hands throw a faint shadow right and down
PERIOD_DEG = 6
STRAP_W = 420


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    hs = t["hands"]
    m = np.zeros(shape, bool)

    def axes(h, x, y):
        ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
        return x * ux + y * uy, -x * uy + y * ux  # along, across (+ = clockwise side)

    for dx, dy in ((0, 0),) + tuple(shadows):
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + margin
        for name in ("hour", "minute"):
            h = hs[name]
            al, ac = axes(h, x, y)
            m |= (al > -0.5) & (al < h["tip"] + margin) & (np.abs(ac) < h["half"] + margin)
        h = hs["seconds"]
        al, ac = axes(h, x, y)
        b = t["print_seastar"]["x0_y0_x1_y1_mm"]  # the needle crosses POWERMATIC and 30 bar: keep the photo there (its
        in_print = (mx > b[0]) & (mx < b[2]) & (my < b[1]) & (my > b[3])  # needle lies under the 3D one), so no letter is lost
        m |= (al > 0) & (al < h["tip"] + margin) & (np.abs(ac) < h["half"] + margin) & ~in_print
        m |= (al - h["ring_r"]) ** 2 + ac ** 2 < (h["ring"][1] + margin) ** 2
        tails = np.zeros(shape, np.uint8)
        cv2.fillPoly(tails, [np.array([[px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S] for p in t["tails_mm"]], np.int32)], 1)
        m |= cv2.dilate(tails, np.ones((9, 9), np.uint8)).astype(bool)
        cw = h["counterweight"]  # T-shaped, behind the pivot: along = -y_local
        poly = np.array([[a, b] for a, b in cw], np.float64)
        bx0, bx1 = poly[:, 0].min() - margin, poly[:, 0].max() + margin
        m |= (al < 0.3) & (al > -poly[:, 1].max() - margin) & (-ac > bx0) & (-ac < bx1)
    return m


def index_mask(t, shape, pad_mm=0.25):
    """Footprint of the applied indices (lume plus polished frame), about the dial centre."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["indices"]
    cx, cy = ix["centre_mm"]
    k = ix["frame_mm"] + pad_mm
    m = np.zeros(shape, np.uint8)
    P = lambda x, y: [px0 + x * S, py0 - y * S]
    for x, y in ix["dots_mm"]:
        cv2.circle(m, tuple(int(v) for v in P(x, y)), int((ix["dot_lume_r_mm"] + k) * S), 1, -1)
    kt = 2.0 * k  # slanted frame edges: a wider offset
    shapes = [(0, [(-ix["triangle_half_mm"] - kt, ix["triangle_r_mm"][1] + k), (ix["triangle_half_mm"] + kt, ix["triangle_r_mm"][1] + k),
                   (0, ix["triangle_r_mm"][0] - 2.5 * k)])]
    for hr in (3, 9):
        (r0, r1), w = ix["bar_r_mm"], ix["bar_half_mm"]
        shapes.append((hr, [(-w - k, r0 - k), (w + k, r0 - k), (w + k, r1 + k), (-w - k, r1 + k)]))
    (r0, r1), w = ix["bar6_r_mm"], ix["bar6_half_mm"]
    shapes.append((6, [(-w - k, r0 - k), (w + k, r0 - k), (w + k, r1 + k), (-w - k, r1 + k)]))
    for hr, poly in shapes:
        a = math.radians(hr * 30 + ix["turn_deg"])
        pts = [P(cx + x * math.cos(a) + y * math.sin(a), cy - x * math.sin(a) + y * math.cos(a)) for x, y in poly]
        cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m.astype(bool)


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone: logo, prints, indices, date window."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in ("logo", "print_seastar", "print_swiss_made", "date_window"):
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S), int(py0 - b[1] * S)), (int(px0 + b[2] * S), int(py0 - b[3] * S)), 1, -1)
    m |= index_mask(t, shape, 0.3).astype(np.uint8)
    return cv2.dilate(m, np.ones((15, 15), np.uint8)).astype(bool)


def build(review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    raw = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)
    al = raw[..., 3:].astype(np.float32) / 255
    img = (raw[..., :3] * al + 255 * (1 - al)).astype(np.uint8)
    R = int(math.ceil(t["bezel_rings_mm"]["lip_in"] * S)) + 4
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    mask = hand_mask(t, shape)[sl]
    feats = feature_mask(t, shape)[sl]
    idx = index_mask(t, shape)[sl]
    todo = mask | idx
    bad = todo | (feats & ~idx)
    yy, xx = np.mgrid[-R:R, -R:R]
    rr = np.hypot(xx, yy)
    flange = rr >= t["bezel_rings_mm"]["dial_out"] * S - 30  # minute track on the black flange
    left_f = todo & flange
    used = fill(win, left_f, bad, [sg * k * PERIOD_DEG for k in range(1, 60) for sg in (1, -1)], (R, R), np.zeros(win.shape, np.float32))
    rest = (todo & ~flange) | left_f
    ring = flange & (rr < t["bezel_rings_mm"]["dial_out"] * S)
    painted = cv2.inpaint(win, (rest | ring).astype(np.uint8), 9, cv2.INPAINT_TELEA)
    win[rest] = painted[rest]
    soft = cv2.GaussianBlur(todo.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    OUT.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT / "dial_photo.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(todo.sum()), "inpainted_px": int(rest.sum()), "filled_from": {k: v for k, v in used.items() if v}}
    (OUT / "dial_photo.json").write_text(json.dumps(meta, indent=1) + "\n")

    # ---- strap: rows from the case edge outward, each resampled to STRAP_W ----
    fg = raw[..., 3] > 250
    M = t["manual_px"]
    xl, xr = M["lug_inner_x"]
    strips, rows_meta = [], []
    for sy, n_row, tip_row in ((1, t["lug"]["notch_rows"][0], t["lug"]["tip_rows"][0]), (-1, t["lug"]["notch_rows"][1], t["lug"]["tip_rows"][1])):
        rows = range(n_row, -1, -1) if sy == 1 else range(n_row, img.shape[0])
        out = []
        for y in rows:
            if (sy == 1 and y >= tip_row) or (sy == -1 and y <= tip_row):
                x0, x1 = xl, xr  # between the lugs
            else:
                xs = np.nonzero(fg[y])[0]
                if len(xs) < 10:
                    break
                x0, x1 = xs.min(), xs.max()
            out.append(cv2.resize(img[y:y + 1, x0 + 2:x1 - 1], (STRAP_W, 1), interpolation=cv2.INTER_AREA))
        strips.append(np.vstack(out))
        rows_meta.append({"first_s_mm": round(sy * (py0 - n_row) / S, 3), "rows": len(out)})
    strap = np.vstack(strips)
    cv2.imwrite(str(OUT / "strap.jpg"), strap, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    smeta = {"source": t["source"], "width_px": STRAP_W, "rows_per_mm": round(S, 4), "top": rows_meta[0], "bottom": rows_meta[1],
             "size_px": [STRAP_W, strap.shape[0]]}
    (OUT / "strap.json").write_text(json.dumps(smeta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[todo] = (0.5 * shown[todo] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2000, 1000), interpolation=cv2.INTER_AREA))
    return meta, smeta


if __name__ == "__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else None))
