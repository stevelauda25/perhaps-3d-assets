"""Cut the SSB479P1 photo map (dial, crystal wall and tachymeter insert) from the front photo, main hands and shadows removed.

    python3 -B -m pipeline.seiko_ssb479_dial [out.jpg] [review.png]     # default outputs/watches/seiko-ssb479p1/dial_photo.jpg

Same fill as pipeline/seiko_spb335_dial.py on the black dial: the minute track has 60 ticks, so each hand pixel is copied
from the same radius 6, 12, 18 ... deg away about the dial centre (first source that is not a hand, index, subdial or print),
lighting from around the hand. The chronograph hand runs through the 6 o'clock subdial, which carries the same 60/10/20/30/
40/50 print as the 9 o'clock one: there the pixels come from the 9 o'clock subdial at the same offset from its centre
(except its own hand and the MIN. print); what is left gets the lighting only. Subdial hands stay in the map. No colour
grading. Square crop centred on the dial centre out to the case edge, photo's own resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-ssb479p1-trace.json"
OUT = ROOT / "outputs/watches/seiko-ssb479p1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_MM = 19.4  # map half size: the case edge
MARGIN_MM = 0.2
SHADOWS_MM = ((0.25, -0.25), (0.45, -0.45))  # light from the upper left (house value)
LOW_SIGMA_PX = 30
PERIOD_DEG = 6
HUB_LIGHTING_MM = 0.75
# pixels read from gridded crops of the photo
SUB_CENTRE_PX = {"9": (1140, 2337), "6": (1545, 2743)}
SUB_RADIUS_PX = 218
SUB9_HAND_PX = [(1134, 2335), (1146, 2335), (1146, 2185), (1134, 2185)]  # its own hand, pointing at 60
SUB9_HUB_PX = 28
MIN_PRINT_PX = (1055, 2385, 1225, 2440)
PRINT_BOXES_PX = [(1340, 1870, 1740, 1960), (1340, 2005, 1750, 2055),  # SEIKO, CHRONOGRAPH
                  (1870, 2730, 2050, 2830),  # date window
                  (1280, 3086, 1800, 3135)]  # MOV'T JAPAN and the calibre print below the track


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ox, oy = t["pivot_offset_mm"]
    P = lambda p, dx, dy: (px0 + (p[0] + ox + dx) * S, py0 - (p[1] + oy + dy) * S)
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + shadows:
        for h in t["hands"].values():
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in h["outline_mm"]]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_radius_mm"][0] * S * 1.3), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=max(1, int(margin * S / 1.5))).astype(bool)


def feature_mask(t, shape):
    """Never used as a fill source on the black dial: indices, subdials, prints."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda x, y: (px0 + x * S, py0 - y * S)
    m = np.zeros(shape, np.uint8)
    ix = t["indices"]
    for hr, v in ix["per_hour_mm"].items():
        w = (ix["width_12_mm"] if hr == "12" else ix["width_mm"]) / 2 + 0.25
        a = math.radians(int(hr) * 30)
        pts = [P(x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))
               for x, y in ((-w, v["inner"] - 0.25), (w, v["inner"] - 0.25), (w, v["outer"] + 0.25), (-w, v["outer"] + 0.25))]
        cv2.fillPoly(m, [np.round(pts).astype(np.int32)], 1)
    for c in SUB_CENTRE_PX.values():
        cv2.circle(m, c, SUB_RADIUS_PX + 15, 1, -1)
    cx, cy = P(*t["subdials"]["3"]["centre_mm"])
    cv2.circle(m, (int(cx), int(cy)), int((t["subdials"]["3"]["radius_mm"] + 0.3) * S), 1, -1)
    for x0, y0, x1, y1 in PRINT_BOXES_PX:
        cv2.rectangle(m, (x0, y0), (x1, y1), 1, -1)
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    H, W = img.shape[:2]
    mask = hand_mask(t, (H, W))
    bad = mask | feature_mask(t, (H, W))
    f32 = img.astype(np.float32)
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(f32 * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    out_img = img.copy()
    todo = mask.copy()
    used = {}
    yy, xx = np.mgrid[0:H, 0:W]

    # pivot: lighting only (hand roots, hub glints)
    piv = (px0 + t["pivot_offset_mm"][0] * S, py0 - t["pivot_offset_mm"][1] * S)
    hub = np.hypot(xx - piv[0], yy - piv[1]) <= HUB_LIGHTING_MM * S
    out_img[hub] = np.clip(low[hub], 0, 255).astype(np.uint8)
    todo &= ~hub
    mask |= hub

    # 6 o'clock subdial: copy from the 9 o'clock subdial at the same offset; light from the 6 itself
    (c9x, c9y), (c6x, c6y) = SUB_CENTRE_PX["9"], SUB_CENTRE_PX["6"]
    in6 = todo & (np.hypot(xx - c6x, yy - c6y) <= SUB_RADIUS_PX - 2)
    sub_bad = np.zeros((H, W), np.uint8)
    cv2.fillPoly(sub_bad, [np.array(SUB9_HAND_PX, np.int32)], 1)
    cv2.circle(sub_bad, (c9x, c9y), SUB9_HUB_PX, 1, -1)
    cv2.rectangle(sub_bad, MIN_PRINT_PX[:2], MIN_PRINT_PX[2:], 1, -1)
    sub_bad = cv2.dilate(sub_bad, np.ones((5, 5), np.uint8), iterations=2).astype(bool)
    # subdial lighting from the cream discs only (the dial-wide estimate excludes them and comes out black)
    disc = np.zeros((H, W), np.uint8)
    for cx_, cy_ in (c9x, c9y), (c6x, c6y):
        cv2.circle(disc, (cx_, cy_), SUB_RADIUS_PX - 40, 1, -1)
    vs = (disc.astype(bool) & ~mask & ~sub_bad).astype(np.float32)[..., None]
    lows = cv2.GaussianBlur(f32 * vs, (0, 0), LOW_SIGMA_PX) / np.maximum(cv2.GaussianBlur(vs, (0, 0), LOW_SIGMA_PX)[..., None], 1e-4)
    sy, sx = yy - (c6y - c9y), xx - (c6x - c9x)
    ok = in6 & (sy >= 0) & (sx >= 0)
    ok[ok] = ~sub_bad[sy[ok], sx[ok]] & ~mask[sy[ok], sx[ok]]
    src = f32[sy[ok], sx[ok]]
    # match the 9's local lighting to the 6's
    out_img[ok] = np.clip(src - lows[sy[ok], sx[ok]] + lows[ok], 0, 255).astype(np.uint8)
    used["from 9 subdial"] = int(ok.sum())
    rest6 = in6 & ~ok
    # left over (the 9's hand and MIN. print): the 6's own track and rim turned about its centre in 6 deg steps, else lighting
    r6 = SUB_RADIUS_PX + 40
    s6 = np.s_[c6y - r6:c6y + r6, c6x - r6:c6x + r6]
    w6, t6, m6 = f32[s6], rest6[s6].copy(), (~mask[s6]).astype(np.uint8)
    rim = np.hypot(*(np.mgrid[0:2 * r6, 0:2 * r6] - r6)) > SUB_RADIUS_PX - 45  # digits inside this are not periodic
    t6 &= rim
    for k in range(1, 10):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D((r6, r6), deg, 1.0)
            src6 = cv2.warpAffine(w6, rot, w6.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok6 = cv2.warpAffine(m6, rot, w6.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool) & t6
            out_img[s6][ok6] = np.clip(src6[ok6], 0, 255).astype(np.uint8)
            rest6[s6][ok6] = False
            t6 &= ~ok6
    out_img[rest6] = np.clip(lows[rest6], 0, 255).astype(np.uint8)
    used["6 subdial lighting only"] = int(rest6.sum())
    todo &= ~in6

    # black dial: rotate about the dial centre in 6 deg steps
    R = int(16 * S)
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win, lw, tw, bw = f32[sl], low[sl], todo[sl].copy(), bad[sl]
    detail = win - lw
    res = out_img[sl]
    c = (R, R)
    for k in range(1, 15):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D(c, deg, 1.0)
            srcr = lw + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            okr = cv2.warpAffine((~bw).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = tw & okr
            res[take] = np.clip(srcr[take], 0, 255).astype(np.uint8)
            tw &= ~take
            if take.sum():
                used["%d deg" % deg] = int(take.sum())
    res[tw] = np.clip(lw[tw], 0, 255).astype(np.uint8)
    used["dial lighting only"] = int(tw.sum())
    out_img[sl] = res

    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = (soft * out_img + (1 - soft) * img).astype(np.uint8)
    hw = int(round(HALF_MM * S))
    crop = clean[py0 - hw:py0 + hw, px0 - hw:px0 + hw]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = 0.5 + x / (2 half), v = 0.5 + y / (2 half)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_mm": round(hw / S, 4), "size_px": list(crop.shape[1::-1]),
            "masked_px": int(mask.sum()), "filled": used}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        r2 = int(15.5 * S)
        a = img[py0 - r2:py0 + r2, px0 - r2:px0 + r2].copy()
        a[mask[py0 - r2:py0 + r2, px0 - r2:px0 + r2]] = (0.5 * a[mask[py0 - r2:py0 + r2, px0 - r2:px0 + r2]] + [0, 0, 127]).astype(np.uint8)
        b = clean[py0 - r2:py0 + r2, px0 - r2:px0 + r2]
        cv2.imwrite(str(review), cv2.resize(np.hstack([a, b]), (2 * 1100, 1100), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
