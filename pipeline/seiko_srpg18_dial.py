"""Cut the SRPG18J1 photo map (dial, bezel insert and strap) from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_srpg18_dial [out.jpg] [review.png]     # default outputs/watches/seiko-srpg18j1/dial_photo.jpg

Same fill as pipeline/seiko_snkl50_dial.py: the dial has 60 printed minute ticks, so each hand pixel is copied from the same
radius 6, 12, 18 ... deg away (first source that is neither a hand nor an index or print), lighting from around the hand.
Hand zones are the traced outlines from config/watches/seiko-srpg18j1-trace.json. One map for every photo part: the full
photo height (strap) by the case width, centred on the hand pivot, at the photo's own resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-srpg18j1-trace.json"
OUT = ROOT / "outputs/watches/seiko-srpg18j1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_WIDTH_MM = 21.7  # map x range: the case flanks
MARGIN_MM = 0.25
SHADOWS_MM = ((0.3, -0.3), (0.55, -0.55))  # light from the upper left
LOW_SIGMA_PX = 30
PERIOD_DEG = 6
HUB_LIGHTING_MM = 2.6
# colour reference: the turned SKU photo (darker, cooler brown, pinker rose gold; Irsyad 2026-11-06). Matching patches
# (x0, y0, x1, y1 px) per zone in the turned photo and in the front photo; per zone the Lab median: L gamma and a/b shift, turned over front.
COLOUR_REF = ROOT / "references/seiko-srpg18j1/front_turned_3000x4977.png"
COLOUR_PATCHES = {  # zone: (turned patches, front patches, keep pixels darker than this; None = all)
    "dial": ([(1205, 1938, 1255, 1988), (1604, 1915, 1654, 1965), (1006, 2580, 1056, 2630), (1692, 2602, 1742, 2652)],
             [(1460, 1260, 1520, 1320), (1500, 1950, 1560, 2000), (1880, 1700, 1950, 1780)], 90),
    "insert": ([(418, 2125, 448, 2155), (2278, 1815, 2308, 1845)], [(930, 1300, 980, 1400), (2300, 1750, 2350, 1850)], 160),
    "strap": ([(1236, 973, 1356, 1093)], [(1450, 250, 1800, 450)], None),
    "print": ([(1274, 1254, 1451, 1475)], [(1556, 907, 1725, 1003)], -120),  # bezel N, large rose print (negative: keep brighter)
}
# target L x, a +, b + per zone: the photo already holds glass haze and sheen, the GLB adds its own (checked in model-viewer)
COLOUR_TRIM = {"dial": (0.7, 0.0, 4.0), "insert": (0.65, 0.0, 0.0)}
ZONE_R_MM = (15.2, 19.3)  # dial (with flange and gasket) | insert | strap, by distance from the pivot


def polys_px(t):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    return S, P


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, P = polys_px(t)
    m = np.zeros(shape, np.uint8)
    sec = t["hands"]["seconds"]
    for dx, dy in ((0, 0),) + shadows:
        for h in t["hands"].values():
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in h["outline_mm"]]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P(sec["disc_centre_mm"], dx, dy)), int((sec["disc_radius_mm"]) * S), 1, -1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_radius_mm"][0] * S * 1.6), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=int(margin * S / 1.5)).astype(bool)


def feature_mask(t, shape, prints_only=False):
    """Indices and prints never used as a fill source (prints_only: the prints a hand may only graze)."""
    S, P = polys_px(t)
    m = np.zeros(shape, np.uint8)
    pad = 0 if prints_only else 12
    for k in ("logo_seiko", "logo_x", "print_automatic_20bar", "date_window", "print_6"):
        b = t[k]["x0_y0_x1_y1_mm"]
        (x0, y0), (x1, y1) = P(b[:2]), P(b[2:])
        cv2.rectangle(m, (int(x0) - pad, int(y0) - pad), (int(x1) + pad, int(y1) + pad), 1, -1)
    if prints_only:
        return m.astype(bool)
    ix = t["indices"]
    for hr in range(1, 13):
        sh = ix["shapes_mm"]["12" if hr == 12 else "cardinal" if hr % 3 == 0 else "bar"]["outline"]
        a = math.radians(hr * 30)
        pts = [P((x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))) for x, y in sh]
        cv2.fillPoly(m, [np.round(pts).astype(np.int32)], 1)
        if hr % 3 == 0:  # stick inward
            r0 = ix["stick_inner_mm"]
            cv2.line(m, tuple(int(v) for v in P((r0 * math.sin(a), r0 * math.cos(a)))),
                     tuple(int(v) for v in P((9 * math.sin(a), 9 * math.cos(a)))), 1, int(0.6 * S))
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=pad // 2 or 1).astype(bool)


def _lab(px):
    return cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.float32) / 255, cv2.COLOR_BGR2LAB).reshape(-1, 3)


def colour_shift(front):
    """Per zone: Lab medians of the matching patches -> (L gamma, a shift, b shift), turned photo over front photo."""
    ref = cv2.imread(str(COLOUR_REF), cv2.IMREAD_UNCHANGED)[..., :3]
    out = {}
    for zone, (tb, fb, cut) in COLOUR_PATCHES.items():
        med = []
        for im, boxes in ((ref, tb), (front, fb)):
            px = np.concatenate([im[y0:y1, x0:x1].reshape(-1, 3) for x0, y0, x1, y1 in boxes])
            lum = px.mean(1)
            px = px if cut is None else px[lum < cut] if cut > 0 else px[lum > -cut]
            med.append(np.median(_lab(px), 0))
        t, f = med
        if zone in COLOUR_TRIM:
            k = COLOUR_TRIM[zone]
            t = t * np.array([k[0], 1, 1], np.float32) + np.array([0, *k[1:]], np.float32)
        out[zone] = np.array([math.log(t[0] / 100) / math.log(f[0] / 100), t[1] - f[1], t[2] - f[2]], np.float32)  # L gamma maps f -> t
    return out


def grade(crop, shifts, S, px0_in_crop, py0):
    """Dark pixels take their zone's shift, bright print and stitching the print shift, blended by brightness."""
    yy, xx = np.mgrid[0:crop.shape[0], 0:crop.shape[1]]
    r = np.hypot(xx - px0_in_crop, yy - py0) / S
    zone = np.where(r <= ZONE_R_MM[0], 0, np.where(r <= ZONE_R_MM[1], 1, 2))
    dark = np.stack([shifts[z] for z in ("dial", "insert", "strap")])[zone]
    w = np.clip((crop.mean(2, keepdims=True) - 60) / 100, 0, 1)
    k = (1 - w) * dark + w * shifts["print"]
    lab = cv2.cvtColor(crop.astype(np.float32) / 255, cv2.COLOR_BGR2LAB)
    lab = np.dstack([100 * (lab[..., 0] / 100) ** k[..., 0], lab[..., 1] + k[..., 1], lab[..., 2] + k[..., 2]]).astype(np.float32)
    return np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR) * 255, 0, 255).astype(np.uint8)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)
    a = img[..., 3:4] / 255.0
    img = (img[..., :3] * a + 20 * (1 - a)).astype(np.uint8)  # outside the photo: near black, like the strap edge
    R = int(math.ceil(t["rings_mm"]["dial_edge"] * S + 0.6 * S))  # hand fill works inside the minute track
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    prints = feature_mask(t, img.shape[:2], prints_only=True)
    mask = np.where(prints, hand_mask(t, img.shape[:2], (), 0.15), hand_mask(t, img.shape[:2]))[sl]
    bad = mask | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    c = (R, R)
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    used = {}
    yy, xx = np.mgrid[0:win.shape[0], 0:win.shape[1]]
    hub = np.hypot(xx - R, yy - R) <= HUB_LIGHTING_MM * S  # whole disc round the pivot (hand glints, rotated tails): lighting only
    hub &= ~feature_mask(t, img.shape[:2], prints_only=True)[sl]  # the Prospex X sits just below
    win[hub] = np.clip(low[hub], 0, 255).astype(np.uint8)
    todo &= ~hub
    mask |= hub
    for k in range(1, 15):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D(c, deg, 1.0)
            src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            used["%d deg" % deg] = int(take.sum())
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = img.copy()
    clean[sl] = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    W = int(round(HALF_WIDTH_MM * S))
    shifts = colour_shift(img)
    crop = grade(clean[:, px0 - W:px0 + W], shifts, S, W, py0)
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = 0.5 + x / (2 half_w), v = 0.5 + (y - centre_y) / (2 half_h)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_w_mm": round(W / S, 4), "half_h_mm": round(crop.shape[0] / 2 / S, 4),
            "centre_y_mm": round((py0 - crop.shape[0] / 2) / S, 4), "size_px": list(crop.shape[1::-1]),
            "colour_shift_L_gamma_a_b": {k: [round(float(x), 3) for x in v] for k, v in shifts.items()}, "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from_deg": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, clean[sl]]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
