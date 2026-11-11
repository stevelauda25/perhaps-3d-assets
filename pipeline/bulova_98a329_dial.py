"""Cut a clean dial map for the Bulova 98A329 (Lunar Pilot Timascus) from the straightened front photo, hands removed.

    python3 -B -m pipeline.bulova_98a329_dial [out.jpg] [review.png]   # default outputs/watches/bulova-98a329/dial_photo.jpg

The Timascus dial has no rotational period, but its waves run left to right: each masked run of a row (hand, shadow, applied
index or numeral footprint) is copied from the same row shifted left or right, the shift chosen per run so the pixels next to
both ends of the run match best, with a small penalty for changing the shift from the row above (keeps the waves continuous).
The minute track flange repeats every 6 deg and is filled by rotation; the white subdials are inpainted under their needles.
Square map centred on the hand pivot, out to the black groove outside the tachymeter ring, native resolution, light unsharp
mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/bulova-98a329-trace.json"
OUT = ROOT / "outputs/watches/bulova-98a329/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.2
SHADOWS_MM = ((0.2, -0.2),)  # soft light from the upper left
PERIOD_DEG = 6
EDGE = 3  # px compared at each end of a run
COHERENCE = 4.0  # cost per px of shift change from the row above


def poly_mask(shape, polys):
    m = np.zeros(shape, np.uint8)
    for p in polys:  # one call per polygon: a single call fills overlaps even-odd
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    return m.astype(bool)


def masks(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda x, y: [px0 + x * S, py0 - y * S]
    rot = lambda x, y, deg: (x * math.cos(math.radians(deg)) + y * math.sin(math.radians(deg)), -x * math.sin(math.radians(deg)) + y * math.cos(math.radians(deg)))
    hands, sub = [], []
    k = MARGIN_MM
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        for name in ("hour", "minute"):
            h = t["hands"][name]
            L, (w0, w1) = h["length_mm"], h["half_mm"]
            poly = [(-w0 - k, -k), (w0 + k, -k), (w1 + k, L - h["point_mm"]), (0, L + k), (-w1 - k, L - h["point_mm"])]
            hands.append([P(*(np.add(rot(x, y, h["angle_deg"]), (dx, dy)))) for x, y in poly])
        h = t["hands"]["chrono"]
        tl, tw = h["tail_mm"]
        l0, lm, lw, l1 = h["lozenge_mm"]
        nw, pw = h["half_mm"] + k, h["pointer_half_mm"] + k
        poly = [(-tw - k, -tl - k), (tw + k, -tl - k), (nw, 0), (nw, l0), (lw + k, lm), (pw, l1), (pw, h["length_mm"] + k),
                (-pw, h["length_mm"] + k), (-pw, l1), (-lw - k, lm), (-nw, l0), (-nw, 0)]
        hands.append([P(*(np.add(rot(x, y, h["angle_deg"]), (dx, dy)))) for x, y in poly])
        for sd in t["subdials"].values():  # thin black needles on white: no shadow, a tight margin (the 3D needle covers it)
            if (dx, dy) != (0, 0):
                continue
            (cx, cy), L, (w0, w1), ks = sd["centre_mm"], sd["length_mm"], sd["half_mm"], 0.12
            poly = [(-w0 - ks, -ks), (w0 + ks, -ks), (w1 + ks, L + ks), (-w1 - ks, L + ks)]
            sub.append([P(*(np.add(rot(x, y, sd["angle_deg"]), (cx + dx, cy + dy)))) for x, y in poly])
    m_hand0 = poly_mask(shape, hands[:3])  # without the shadow copies: used inside the white subdials
    m_hand = poly_mask(shape, hands)
    m_sub = poly_mask(shape, sub)
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    m_hand |= np.hypot(xx - px0, yy - py0) < (t["hub_radius_mm"][0] + k) * S
    for sd in t["subdials"].values():
        cx, cy = P(*sd["centre_mm"])
        m_sub |= np.hypot(xx - cx, yy - cy) < (sd["hub_mm"] + 0.07) * S
    # applied indices and numerals: geometry, so their footprint becomes dial
    ix = t["indices"]
    bars = []
    for hr in range(12):
        r0, r1, hw = ix["twelve_mm"] if hr == 0 else ix["wide_bar_mm"] if hr % 3 == 0 else ix["bar_mm"]
        bars.append([P(*rot(x, y, hr * 30)) for x, y in ((-hw - k, r0 - k), (hw + k, r0 - k), (hw + k, r1 + k), (-hw - k, r1 + k))])
    m_app = poly_mask(shape, bars)
    num = np.zeros(shape, np.uint8)
    for shapes in t["numerals"].values():
        for sh in shapes:
            cv2.fillPoly(num, [np.array([P(*p) for p in sh["outer"]], np.int32)], 1)
    m_app |= cv2.dilate(num, np.ones((5, 5), np.uint8)).astype(bool)
    return m_hand, m_hand0, m_sub, m_app


def fill_rows(win, todo, bad, prefer):
    """Row-wise horizontal copy for the wave dial; returns the number of runs filled."""
    h, w = todo.shape
    src = win.astype(np.float32)
    prev, runs = {}, 0
    for y in range(h):
        row = todo[y]
        if not row.any():
            prev = {}
            continue
        xs = np.nonzero(row)[0]
        splits = np.nonzero(np.diff(xs) > 1)[0]
        cur = {}
        for a, b in zip(np.r_[xs[0], xs[splits + 1]], np.r_[xs[splits], xs[-1]]):
            n = b - a + 1
            best = None
            for dx in [s * d for d in range(n + 2, n + 260) for s in (1, -1)]:
                lo, hi = a + dx - EDGE, b + dx + EDGE + 1
                if lo < 0 or hi > w or bad[y, lo:hi].any():
                    continue
                cost = 0.0
                if a - EDGE >= 0 and not todo[y, a - EDGE:a].any():
                    cost += float(((src[y, a - EDGE:a] - src[y, a - EDGE + dx:a + dx]) ** 2).sum())
                if b + EDGE + 1 <= w and not todo[y, b + 1:b + EDGE + 1].any():
                    cost += float(((src[y, b + 1:b + EDGE + 1] - src[y, b + 1 + dx:b + EDGE + 1 + dx]) ** 2).sum())
                p = min((abs(dx - v) for v in prev.values()), default=0)
                cost += COHERENCE * p * p + prefer * abs(dx)
                if best is None or cost < best[0]:
                    best = (cost, dx)
            if best:
                win[y, a:b + 1] = win[y, a + best[1]:b + 1 + best[1]]
                todo[y, a:b + 1] = False
                cur[a] = best[1]
                runs += 1
        prev = cur
    return runs


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    px0, py0 = int(round(px0)), int(round(py0))
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["bezel_rings_mm"]["groove_out"] * S)) + 4
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    m_hand, m_hand0, m_sub, m_app = (m[sl] for m in masks(t, img.shape[:2]))
    yy, xx = np.mgrid[-R:R, -R:R]
    r = np.hypot(xx + (px0 - t["origin_px"][0]), yy + (py0 - t["origin_px"][1]))
    dial_out = t["bezel_rings_mm"]["dial_out"] * S
    discs = np.zeros(win.shape[:2], bool)
    for sd in t["subdials"].values():
        cx, cy = sd["disc_centre_mm"]
        discs |= np.hypot(xx - cx * S, yy + cy * S) < sd["disc_r_mm"] * S + 3
    m_logo = np.zeros(win.shape[:2], bool)
    b = t["logo"]["x0_y0_x1_y1_mm"]
    m_logo[int(R - b[1] * S):int(R - b[3] * S), int(R + b[0] * S):int(R + b[2] * S)] = True

    # subdials: inpaint under the needles and hubs
    sub_todo = cv2.dilate(((m_sub | m_hand0) & discs).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & discs
    win = cv2.inpaint(win, sub_todo.astype(np.uint8), 3, cv2.INPAINT_TELEA)
    # minute track flange: rotation by whole 6 deg periods
    fl = (m_hand | m_app) & (r >= dial_out - 1) & ~discs
    bad = m_hand | m_app
    for k in range(1, 30):
        for sgn in (1, -1):
            if not fl.any():
                break
            M = cv2.getRotationMatrix2D((R + t["origin_px"][0] - px0, R + t["origin_px"][1] - py0), sgn * k * PERIOD_DEG, 1.0)
            src = cv2.warpAffine(win, M, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~bad).astype(np.uint8), M, win.shape[1::-1], flags=cv2.INTER_NEAREST).astype(bool)
            take = fl & ok
            win[take] = src[take]
            fl &= ~take
    # wave dial: row-wise copies from clean dial on the same row
    todo = (m_hand | m_app) & (r < dial_out - 1) & ~discs & ~m_logo  # the needle over the logo stays: the 3D chrono needle covers it
    bad = m_hand | m_app | discs | m_logo | (r >= dial_out - 3)
    runs = 0
    for _ in range(4):  # rows boxed in by other hands and subdials take filled pixels from the pass before
        left = todo.copy()
        runs += fill_rows(win, left, bad | todo, 0.5)
        bad &= ~(todo & ~left)
        todo = left
        if not todo.any():
            break
    left = todo.copy()  # boxed in on every row (around the hub): copy along the columns instead, the waves stack there too
    runs += fill_rows(win.transpose(1, 0, 2), left.T, (bad | todo).T, 0.5)
    todo = left
    win = cv2.inpaint(win, todo.astype(np.uint8), 3, cv2.INPAINT_TELEA)  # what is left
    soft = cv2.GaussianBlur(((m_hand & ~discs) | m_hand0 | m_app | m_sub).astype(np.float32), (0, 0), 1.0)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the map is centred on the integer pivot pixel; the step offsets the UVs by the sub-pixel rest
    meta = {"inpainted_px": int(todo.sum()), "source": t["source"], "centre_px": [px0, py0], "centre_offset_mm": [round((px0 - t["origin_px"][0]) / S, 4), round(-(py0 - t["origin_px"][1]) / S, 4)],
            "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "masked_px": int((m_hand | m_app | m_sub).sum()), "row_runs": runs}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        mk = m_hand | m_app | m_sub
        shown[mk] = (0.5 * shown[mk] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, crop]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
