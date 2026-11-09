"""Cut a clean dial map for the SNXS75K1 from the straightened front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_snxs75_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snxs75k1/dial_photo.jpg

Same method as pipeline/seiko_snkl50_dial.py. The dial is a grey sunburst with 60 printed black minute ticks, so each hand
pixel is copied from the same radius 6, 12, 18 ... deg away (first source that is neither a hand nor a printed or applied part).
Square map centred on the dial centre (the trace origin; the hand pivot sits 0.4 mm off it by parallax), out to the crystal
ring, at the straightened photo's resolution, light unsharp mask, JPEG. Hand zones come from config/watches/seiko-snxs75k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snxs75k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snxs75k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.3  # past each hand's traced outline: its bright edge and soft glow
SHADOWS_MM = ((0.45, -0.45), (-0.2, 0.2))  # light from the upper left; a faint rim on the other side
PERIOD_DEG = 6
HUB_FEATHER_PX = 15
# dial grey in the map so that model-viewer shows the grey of references/seiko-snxs75k1/turned_crown_2000x3358.png (Irsyad's
# photo, about sRGB 109/108/117); the Ashford photo is lit brighter and warmer
DIAL_RGB = (82, 82, 90)  # set in model-viewer 4.1.0 (the tracker's viewer), which lifts the dial by about 30
SUNBURST_CONTRAST = 1.4
# SEIKO and the 5 shield come from Irsyad's photo (Irsyad: "harus persis"); the Ashford logo is a different finish.
# Matching points read from gridded crops (+-3 px): SEIKO corners, then the shield's top corners, lower corners and tip.
LOGO_SRC = ROOT / "references/seiko-snxs75k1/turned_crown_2000x3358.png"
LOGO_SRC_PX = [(822, 1222), (1100, 1222), (822, 1262), (1100, 1262),
               (877, 1295), (1032, 1295), (877, 1355), (1030, 1355), (952, 1380)]
LOGO_DST_PX = [(1284, 1124), (1514, 1124), (1284, 1167), (1514, 1167),  # in the straightened front photo
               (1329, 1187), (1460, 1187), (1331, 1233), (1458, 1233), (1397, 1258)]
SECONDS_IN_SRC = ((1049, 1180), (971, 1440))  # the seconds hand crosses the logo in Irsyad's photo: inpainted first
PATTERN_OFFSET_PX = (0, 0)  # the straightened ticks are centred on the origin


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S - t["hand_pivot_mm"][0], -(yy - py0) / S - t["hand_pivot_mm"][1]  # hand frame
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + shadows:
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + margin  # the wide tails are covered by each hand's own zone below
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            hw = h.get("half_width_root_mm", h.get("half_width_mm"))  # lit facet; the dark facet sits beside it
            m |= (along > 0) & (along < h["length_mm"] + margin) & (across < hw + margin)
            tw = h.get("tail_half_width_mm", hw)
            m |= (along > -h["tail_mm"] - margin) & (along <= 0) & (across < tw + margin)
    return m


def feature_mask(t, shape, prints_only=False):
    """Printed or applied parts that must not be copied into a hand zone (prints_only: logo, date, print at 6)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    pad = 0 if prints_only else 15  # the tight-mask zone is the print itself; sources keep clear of it by 15 px
    to_px = lambda b: (int(px0 + b[0] * S) - pad, int(py0 - b[1] * S) - pad, int(px0 + b[2] * S) + pad, int(py0 - b[3] * S) + pad)
    for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic", "print_6"):
        x0, y0, x1, y1 = to_px(t[k]["x0_y0_x1_y1_mm"])
        cv2.rectangle(m, (x0, y0), (x1, y1), 1, -1)
    if prints_only:
        return m.astype(bool)
    ix = t["indices"]
    for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        a = math.radians(hr * 30)
        r0, r1 = ix["inner_mm"], ix["outer_mm"]
        p0 = (int(px0 + (r0 - 0.3) * S * math.sin(a)), int(py0 - (r0 - 0.3) * S * math.cos(a)))
        p1 = (int(px0 + (r1 + 0.3) * S * math.sin(a)), int(py0 - (r1 + 0.3) * S * math.cos(a)))
        wd = ix["width_12_mm"] if hr == 12 else ix["width_wide_mm"] if hr in (6, 9) else ix["width_mm"]
        cv2.line(m, p0, p1, 1, int((wd + 0.8) * S))
    return m.astype(bool)


def polar_low(win, hands, parts, c, R, n=3600, sig_deg=1.5, sig_px=4):
    """Lighting of the sunburst: its brightness follows the angle, so work in polar coordinates. Applied and printed parts
    are bridged along the radius first (same angle, same brightness); then each hand zone is bridged along the angle from
    its two ends (a round blur mixes in the wrong angles and leaves light and dark patches)."""
    flags = cv2.WARP_POLAR_LINEAR
    P = cv2.warpPolar(win.astype(np.float32), (R, n), c, R, flags)  # rows: angle, columns: radius
    to_polar = lambda m: cv2.warpPolar(m.astype(np.float32), (R, n), c, R, flags | cv2.INTER_NEAREST) > 0.5
    H, F = to_polar(hands), to_polar(parts & ~hands)
    cols = np.arange(R)
    for i in np.nonzero(F.any(1))[0]:
        good = cols[~F[i] & ~H[i]]
        if len(good) > 1:
            for ch in range(3):
                P[i, F[i], ch] = np.interp(cols[F[i]], good, P[i, good, ch])
    V = ~H
    pad = int(4 * sig_deg * n / 360)
    wrap = lambda a: np.concatenate([a[-pad:], a, a[:pad]])
    k = (0, 0)
    wgt = cv2.GaussianBlur(wrap(V.astype(np.float32)), k, sigmaX=sig_px, sigmaY=sig_deg * n / 360)[pad:-pad]
    est = cv2.GaussianBlur(wrap(P * V[..., None]), k, sigmaX=sig_px, sigmaY=sig_deg * n / 360)[pad:-pad] / np.maximum(wgt, 1e-4)[..., None]
    ok = wgt > 0.3
    rows = np.arange(n)
    for j in range(R):  # periodic linear bridge over the masked angles at each radius
        good = rows[ok[:, j]]
        if 0 < len(good) < n:
            for ch in range(3):
                est[~ok[:, j], j, ch] = np.interp(rows[~ok[:, j]], good, est[good, j, ch], period=n)
    have = [j for j in range(R) if ok[:, j].any()]
    for j in range(have[0]):  # round the hub nothing is clean: take the first radius that has clean pixels
        est[:, j] = est[:, have[0]]
    return cv2.warpPolar(est, win.shape[1::-1], c, R, flags | cv2.WARP_INVERSE_MAP)


def daydate_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    x0, y0, x1, y1 = t["daydate_frame"]["x0_y0_x1_y1_mm"]
    m = np.zeros(shape, bool)
    m[int(py0 - y0 * S):int(py0 - y1 * S), int(px0 + x0 * S):int(px0 + x1 * S)] = True
    return m


def paste_logo(win, origin):
    """Warp SEIKO and the 5 shield from Irsyad's photo onto the map, shifted so that photo's dial grey lands on the map's."""
    src = cv2.imread(str(LOGO_SRC))
    line = np.zeros(src.shape[:2], np.uint8)
    cv2.line(line, *SECONDS_IN_SRC, 255, 17)  # the hand and its shadow beside it
    sh = LOGO_SRC_PX[4:]
    shield = np.zeros_like(line)
    cv2.fillPoly(shield, [np.int32([sh[0], sh[1], sh[3], sh[4], sh[2]])], 255)
    shield = cv2.dilate(shield, np.ones((7, 7), np.uint8))
    face = cv2.erode(shield, np.ones((19, 19), np.uint8))
    # the shield's dark rim is symmetric: rim pixels under the hand come from the mirror side
    axis2 = sh[0][0] + sh[1][0]
    ys, xs = np.nonzero(line & shield & ~face)
    src[ys, xs] = src[ys, np.clip(axis2 - xs, 0, src.shape[1] - 1)]
    rest = line & ~(shield & ~face)
    src = cv2.inpaint(src, rest, 3, cv2.INPAINT_TELEA)
    dst = [(x - origin[0], y - origin[1]) for x, y in LOGO_DST_PX]
    H, _ = cv2.findHomography(np.float32(LOGO_SRC_PX), np.float32(dst), 0)
    warped = cv2.warpPerspective(src, H, win.shape[1::-1], flags=cv2.INTER_CUBIC).astype(np.float32)
    foot = np.zeros(win.shape[:2], np.uint8)  # SEIKO box and shield outline, 6 px wider for the dark rims
    (a, b, c, d), sh = dst[:4], dst[4:]
    cv2.rectangle(foot, (int(a[0]) - 6, int(a[1]) - 6), (int(d[0]) + 6, int(d[1]) + 6), 255, -1)
    cv2.fillPoly(foot, [np.int32([sh[0], sh[1], sh[3], sh[4], sh[2]])], 255)
    foot = cv2.dilate(foot, np.ones((13, 13), np.uint8))
    ring = cv2.dilate(foot, np.ones((31, 31), np.uint8)) & ~foot  # dial just outside the logo, in both images
    shift = np.median(win[ring > 0].astype(np.float32), axis=0) - np.median(warped[ring > 0], axis=0)
    w = cv2.GaussianBlur((foot > 0).astype(np.float32), (0, 0), 2.0)[..., None]
    return np.clip(win * (1 - w) + w * (warped + shift), 0, 255).astype(np.uint8)


def dial_tone(win, keep):
    """Scale the grey dial and its black print to DIAL_RGB and lift the sunburst's contrast (model-viewer flattens it);
    the day-date discs (keep) stay as they are."""
    f = win.astype(np.float32)
    b_, g_, r_ = f[..., 0], f[..., 1], f[..., 2]
    grey = (np.abs(r_ - b_) < 22) & ~keep
    gain = np.array(DIAL_RGB[::-1], np.float32) / np.median(f[grey & (g_ > 70)], axis=0)  # BGR, from the dial, not the print
    low = cv2.GaussianBlur(f, (0, 0), 12)
    toned = (low + (f - low) * SUNBURST_CONTRAST) * gain
    w = cv2.GaussianBlur(grey.astype(np.float32), (0, 0), 1.0)[..., None]
    return np.clip(f * (1 - w) + w * toned, 0, 255).astype(np.uint8)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    prints = feature_mask(t, img.shape[:2], prints_only=True)
    mask = np.where(prints, hand_mask(t, img.shape[:2], (), 0.25), hand_mask(t, img.shape[:2]))[sl]  # print the hand only grazes stays
    bad = mask | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    c = (R + PATTERN_OFFSET_PX[0], R + PATTERN_OFFSET_PX[1])
    low = polar_low(win, mask, bad & ~mask, c, R)
    detail = win.astype(np.float32) - low
    used = {}
    # near the pivot every rotation lands on another hand: the plain black dial there takes the local lighting only
    moves = [(sgn * k * PERIOD_DEG, sc) for sc in (1.0,) for k in range(0 if sc < 1 else 1, 15) for sgn in (1, -1)]
    for deg, sc in moves:
            rot = cv2.getRotationMatrix2D(c, deg, sc)  # output pixel p takes the source pixel deg away, 1/sc further out
            src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            used["%d deg x%.0f" % (deg, 1 / sc)] = int(take.sum())
            if not todo.any():
                break
    unfilled = int(todo.sum())
    # round the hub no rotation finds clean dial and rotated copies bring in the hub's shadow: plain dial tone from just
    # outside as a fallback; first the dial itself copied in from further out along the same angle (the sunburst's tone and
    # streaks follow the angle), feathered into the rotation fill
    if unfilled:
        yy, xx = np.mgrid[0:win.shape[0], 0:win.shape[1]]
        d = np.hypot(xx - c[0], yy - c[1])
        r_hub = d[todo].max() + HUB_FEATHER_PX
        ring = (d > r_hub + HUB_FEATHER_PX) & (d < r_hub + 2 * HUB_FEATHER_PX) & ~bad
        tone = np.median(win[ring], axis=0).astype(np.float32)
        hub = np.broadcast_to(tone, win.shape).copy()
        left = mask & (d < r_hub + HUB_FEATHER_PX)
        for sc in (0.5, 0.4, 0.3, 0.25):
            m_ = cv2.getRotationMatrix2D(c, 0, sc)
            det = cv2.warpAffine(img[sl].astype(np.float32), m_, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~bad).astype(np.uint8), m_, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = left & ok
            hub[take] = det[take]
            left &= ~take
        f = np.clip((d - r_hub) / HUB_FEATHER_PX, 0, 1)[..., None]
        win = (f * win + (1 - f) * np.clip(hub, 0, 255)).astype(np.uint8)
    # soften the seam: blend a 3 px band around the filled zone
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    win = dial_tone(win, daydate_mask(t, img.shape[:2])[sl])  # the indices' lume is covered by the 3D indices
    win = paste_logo(win, (px0 - R, py0 - R))
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
