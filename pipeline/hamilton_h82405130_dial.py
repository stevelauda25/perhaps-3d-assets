"""Cut a clean dial map for the Hamilton H82405130 (Khaki Navy Scuba Auto) from the front photo, hands and shadows removed.

    python3 -B -m pipeline.hamilton_h82405130_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h82405130/dial_photo.jpg

Same method as pipeline/orient_ra_aa0818l19b_dial.py: the matte black dial is even and the minute track repeats every
6 deg, so each hand pixel is copied from the same radius 6, 12, 18 ... deg away (no lighting estimate: the base is flat black);
the 13-24 numerals the hands touch are copied by translation from a numeral with the same digit. Square map centred on the
hand pivot, out to the bezel's inner lip, at the photo's resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/hamilton-h82405130-trace.json"
OUT = ROOT / "outputs/watches/hamilton-h82405130/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.45
SHADOWS_MM = ((0.45, -0.45), (0.25, -0.25))  # light from the upper left
HUB_ZONE_MM = 0.95  # hour-hand ring (0.85 mm)
PERIOD_DEG = 6
# photo px: digit boxes under a hand, filled from the same digit elsewhere (dst x0 y0 x1 y1, src x0 y0)
DIGIT_PATCHES = [([554, 1452, 590, 1499], (520, 1452)),   # second 2 of 22 (hour tip) from the first 2
                 ([1108, 1449, 1136, 1493], (1159, 1618)),  # 1 of 14 (minute hand) from the 1 of 15
                 ([1141, 1449, 1179, 1492], (845, 1267))]  # 4 of 14 from the 4 of 24
NUMERAL_BOXES = [[815, 1269, 880, 1308], [991, 1325, 1053, 1363], [643, 1327, 707, 1366], [1111, 1452, 1176, 1490],
                 [523, 1456, 590, 1498], [1162, 1621, 1224, 1659], [477, 1626, 533, 1664], [1114, 1796, 1174, 1834],
                 [532, 1800, 596, 1838], [999, 1924, 1059, 1962], [648, 1926, 710, 1964], [822, 1977, 884, 2016]]  # 13-24, photo px
KEEP_BOXES = [[562, 1797, 594, 1841]]  # the 0 of 20 sits next to the seconds arrow: photo kept


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
        m |= np.hypot(x, y) < HUB_ZONE_MM + margin
        for name in ("hour", "minute"):  # tapered baton and its tail
            h = h_ = hs[name]
            al, ac = axes(h, x, y)
            L, (r0, w0), w1 = h["length_mm"], h["root_mm"], h["tip_half_mm"]
            hw = w0 + (w1 - w0) * np.clip((al - r0) / (L - r0), 0, 1)
            m |= (al > -0.3) & (al < L + margin) & (ac < hw + margin)
            tl, t0, t1 = h_["tail_mm"]
            m |= (al > -tl - margin) & (al <= 0.3) & (ac < t0 + (t1 - t0) * np.clip(-al / tl, 0, 1) + margin)
        h = hs["seconds"]
        al, ac = axes(h, x, y)
        a0, aw0, a1, aw1 = h["arrow_mm"]
        m |= (al > -h["tail_mm"] - margin) & (al < h["length_mm"] + margin) & (ac < max(h["half_width_mm"], h["pointer_half_mm"]) + margin)
        m |= (al > a0 - margin) & (al < a1 + margin) & (ac < aw0 + (aw1 - aw0) * np.clip((al - a0) / (a1 - a0), 0, 1) + margin)
    return m


def boxes(t, shape, keys, pad=12):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in keys:
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S) - pad, int(py0 - b[1] * S) - pad), (int(px0 + b[2] * S) + pad, int(py0 - b[3] * S) + pad), 1, -1)
    return m.astype(bool)


def index_mask(t, shape, pad_mm=0.15):
    """Footprint of the applied indices (lume plus polished frame)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["indices"]
    m = np.zeros(shape, np.uint8)
    k = ix["frame_mm"] + pad_mm
    for hr in range(12):
        a = math.radians(hr * 30)
        if hr % 3 == 0:
            (r0, r1), (w0, w1) = ix["wedge_r_mm"], ix["wedge_half_mm"]
        else:
            (r0, r1), w0 = ix["bar_r_mm"], ix["bar_half_mm"]
            w1 = w0
        poly = [(-w0 - k, r0 - k), (w0 + k, r0 - k), (w1 + k, r1 + k), (-w1 - k, r1 + k)]
        pts = [[px0 + (x * math.cos(a) + y * math.sin(a)) * S, py0 - (-x * math.sin(a) + y * math.cos(a)) * S] for x, y in poly]
        cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m.astype(bool)


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone: logo, prints, indices, date window."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = boxes(t, shape, ("logo", "print_khaki", "print_swiss_made")).astype(np.uint8)
    ix = t["indices"]
    for hr in range(12):
        a = math.radians(hr * 30)
        r0, r1 = ix["wedge_r_mm"] if hr % 3 == 0 else ix["bar_r_mm"]
        wid = 2 * (ix["wedge_half_mm"][1] if hr % 3 == 0 else ix["bar_half_mm"]) + 2 * ix["frame_mm"] + 0.8
        p0 = (int(px0 + (r0 - 0.4) * S * math.sin(a)), int(py0 - (r0 - 0.4) * S * math.cos(a)))
        p1 = (int(px0 + (r1 + 0.4) * S * math.sin(a)), int(py0 - (r1 + 0.4) * S * math.cos(a)))
        cv2.line(m, p0, p1, 1, int(wid * S))
    win = np.array([[px0 + x * S, py0 - y * S] for x, y in t["date_window_mm"]], np.int32)
    cv2.fillPoly(m, [win], 1)
    for x0, y0, x1, y1 in NUMERAL_BOXES:
        cv2.rectangle(m, (x0, y0), (x1, y1), 1, -1)
    m = cv2.dilate(m, np.ones((25, 25), np.uint8))
    return m.astype(bool)


def fill(win, todo, bad, low, moves, centre):
    detail = win.astype(np.float32) - low
    used = {}
    good = cv2.erode((~bad).astype(np.uint8), np.ones((5, 5), np.uint8))  # linear sampling next to a hand would pull its dark edge in
    for deg, sc in moves:
        rot = cv2.getRotationMatrix2D(centre, deg, sc)
        src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        ok = cv2.warpAffine(good, rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
        take = todo & ok
        win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
        todo &= ~take
        used["%+.0f deg x%.0f" % (deg, 1 / sc)] = int(take.sum())
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
    prints = boxes(t, shape, ("logo", "print_khaki", "print_swiss_made"), pad=0)[sl]
    mask = np.where(prints, hand_mask(t, shape, (), 0.12)[sl], hand_mask(t, shape)[sl])  # print the hand only grazes stays
    for x0, y0, x1, y1 in KEEP_BOXES:
        mask[y0 - py0 + R:y1 - py0 + R, x0 - px0 + R:x1 - px0 + R] = False
    feats = feature_mask(t, shape)[sl]
    # applied indices are geometry: their footprint becomes plain dial so no white bleeds into the filled zones
    idx = index_mask(t, shape)[sl]
    black = np.median(win[~idx & ~mask & ~feats & (np.hypot(*np.mgrid[-R:R, -R:R]) < R * 0.9)].reshape(-1, 3), 0)
    win[idx] = black
    # the rest of the dial: whole minute-track periods about the hand pivot
    todo = mask.copy()
    bad = mask | feats
    # matte black dial: a flat black base, so the copies are the rotated photo itself (a lighting estimate or a
    # gradient-domain blend would carry the hands' glow into the filled zones)
    low = np.broadcast_to(black.astype(np.float32), win.shape).copy()
    moves = [(sgn * k * PERIOD_DEG, 1.0) for k in range(1, 30) for sgn in (1, -1)]
    used = fill(win, todo, bad, low, moves, (R, R))
    unfilled = int(todo.sum())
    win[todo] = black
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    for (dx0, dy0, dx1, dy1), (sx0, sy0) in DIGIT_PATCHES:  # whole digit boxes from a clean numeral
        ox, oy = px0 - R, py0 - R
        win[dy0 - oy:dy1 - oy, dx0 - ox:dx1 - ox] = img[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled,
            "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
