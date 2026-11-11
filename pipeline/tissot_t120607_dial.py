"""Cut a clean dial map for the Tissot T120.607.11.041.00 (Seastar 2000 Professional) from the front photo, hands and shadows
removed.

    python3 -B -m pipeline.tissot_t120607_dial [out.jpg] [review.png]   # default outputs/watches/tissot-t120.607.11.041.00/dial_photo.jpg

Same method as pipeline/hamilton_h82405130_dial.py. The blue gradient is radial and the flange's minute track repeats every
6 deg, so each hand pixel is copied from the same radius 6, 12, 18 ... deg away (the wave relief turns with it, which reads
as the same pattern). Applied indices become plain dial (they are geometry). Square map centred on the hand pivot, out to the
bezel's inner lip, at the photo's resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/tissot-t120.607.11.041.00-trace.json"
OUT = ROOT / "outputs/watches/tissot-t120.607.11.041.00/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.3
SHADOWS_MM = ((0.3, -0.3),)  # light from the upper left; the shadows here are faint
PERIOD_DEG = 6


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    hs = t["hands"]
    m = np.zeros(shape, bool)

    def axes(h, x, y):
        ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
        return x * ux + y * uy, np.abs(-x * uy + y * ux)

    for dx, dy in ((0, 0),) + tuple(shadows):
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + margin
        h = hs["hour"]
        al, ac = axes(h, x, y)
        m |= (al > -0.8 - margin) & (al < h["tip"] + margin) & (ac < h["half"] + margin)
        m |= (al > h["guard"][0] - margin) & (al < h["guard"][1] + margin) & (ac < h["guard"][2] + margin)
        for name in ("hour", "minute"):  # stepped tails: wide, then narrow
            h = hs[name]
            al, ac = axes(h, x, y)
            r0, r1, w0, w1 = h["tail"]
            m |= (al < 0.3) & (al > -r0 - margin) & (ac < w0 + margin)
            m |= (al < 0.3) & (al > -r1 - margin) & (ac < w1 + margin)
        h = hs["minute"]
        al, ac = axes(h, x, y)
        m |= (al > -0.3) & (al < h["tip"] + margin) & (ac < h["half"] + margin)
        h = hs["seconds"]
        al, ac = axes(h, x, y)
        m |= (al > -h["tail"] - margin) & (al < h["tip"][0] + margin) & (ac < h["half"] + margin)
        m |= (al > h["dot_r"]) & (al < h["tip"][0] + margin) & (ac < h["tip"][1] + margin)
        dot = (al - h["dot_r"]) ** 2 + ac ** 2 < (h["dot"][1] + margin) ** 2
        m |= dot
    return m


def index_mask(t, shape, pad_mm=0.25):
    """Footprint of the applied indices (lume plus polished frame)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["indices"]
    k = ix["frame_mm"] + pad_mm
    m = np.zeros(shape, np.uint8)
    P = lambda x, y: [px0 + x * S, py0 - y * S]
    for x, y in ix["dots_mm"]:
        cv2.circle(m, tuple(int(v) for v in P(x, y)), int((ix["dot_lume_r_mm"] + k) * S), 1, -1)
    turn = ix["turn_deg"]
    kt = 1.5 * k  # slanted frame edges: a wider offset
    shapes = [(0, [(-ix["triangle_half_mm"] - kt, ix["triangle_r_mm"][1] + k), (ix["triangle_half_mm"] + kt, ix["triangle_r_mm"][1] + k),
                   (0, ix["triangle_r_mm"][0] - 3 * k)])]
    for hr in (3, 9):
        (r0, r1), w = ix["bar_r_mm"], ix["bar_half_mm"]
        shapes.append((hr, [(-w - k, r0 - k), (w + k, r0 - k), (w + k, r1 + k), (-w - k, r1 + k)]))
    (r0, r1), w = ix["bar6_r_mm"], ix["bar6_half_mm"]
    shapes.append((6, [(-w - k, r0 - k), (w + k, r0 - k), (w + k, r1 + k), (-w - k, r1 + k)]))
    for hr, poly in shapes:
        a = math.radians(hr * 30 + turn)
        pts = [P(x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)) for x, y in poly]
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
    m = cv2.dilate(m, np.ones((15, 15), np.uint8))
    return m.astype(bool)


def fill(win, todo, bad, moves, centre, low):
    """Copy each todo pixel from the first rotation (deg) whose source is good; `low` is taken out before the copy and put
    back at the destination."""
    used = {}
    good = cv2.erode((~bad).astype(np.uint8), np.ones((5, 5), np.uint8))  # linear sampling next to a hand would pull its dark edge in
    detail = win.astype(np.float32) - low
    for deg in moves:
        rot = cv2.getRotationMatrix2D(centre, deg, 1.0)
        src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ok = cv2.warpAffine(good, rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
        take = todo & ok
        win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
        todo &= ~take
        used[str(deg)] = int(take.sum())
        if not todo.any():
            break
    return used


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["bezel_rings_mm"]["lip_in"] * S))
    assert py0 - R >= 0 and px0 - R >= 0
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    shape = img.shape[:2]
    mask = hand_mask(t, shape)[sl]
    feats = feature_mask(t, shape)[sl]
    idx = index_mask(t, shape)[sl]
    # applied indices are geometry: fill their footprint like a hand zone so no white bleeds into the dial
    todo = mask | idx
    bad = todo | (feats & ~idx)
    yy, xx = np.mgrid[-R:R, -R:R]
    rr = np.hypot(xx, yy)
    flange = rr >= t["indices"]["bar_r_mm"][1] * S + 2
    # flange: whole minute-track periods about the pivot (copied as is: the flange is evenly lit black)
    left_f = todo & flange
    used = fill(win, left_f, bad, [sgn * k * PERIOD_DEG for k in range(1, 60) for sgn in (1, -1)], (R, R), np.zeros(win.shape, np.float32))
    # blue dial: the wave relief does not repeat, and every filled pixel lies under a 3D hand or index; a smooth inpaint
    # from the surrounding dial keeps the gradient without copied wave seams at the visible hand edges
    # (the flange ring is hidden from the inpaint so the black does not bleed in at the index ends)
    rest = (todo & ~flange) | left_f
    ring = flange & (rr < t["indices"]["bar_r_mm"][1] * S + 40)
    painted = cv2.inpaint(win, (rest | ring).astype(np.uint8), 9, cv2.INPAINT_TELEA)
    win[rest] = painted[rest]
    soft = cv2.GaussianBlur(todo.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(todo.sum()), "inpainted_px": int(rest.sum()), "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[todo] = (0.5 * shown[todo] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
