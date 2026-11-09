"""Cut a clean dial map for the SNXG47K1 from the straightened photo, with the hands removed.

    python3 -B -m pipeline.seiko_snxg47_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snxg47k1/dial_photo.jpg

The dial has a fine woven pattern that repeats every 30 px across and down. Each pixel under a hand or its shadow is copied
from the nearest spot a whole number of periods away that is neither under a hand nor on a baton, the logo, a minute tick or
print (gold or dark); the copied pixels take the broad shade of the dial around them. Where the seconds hand crosses SEIKO and
the 5 shield, the strip is blended straight across from both edges instead. Square map centred on the hand pivot, out to the
crystal ring, at the photo's own resolution, light unsharp mask, JPEG. Hand zones come from config/watches/seiko-snxg47k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snxg47k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snxg47k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.35  # past each hand's outline: its bright edge, soft glow and up to 0.3 mm of trace offset near the hub
PERIOD_PX = 30  # woven dial pattern, measured by autocorrelation on the straightened photo (0.48 mm)
SHIFTS = sorted({(i * PERIOD_PX, j * PERIOD_PX) for i in range(-12, 13) for j in range(-12, 13) if i or j}, key=lambda v: v[0] ** 2 + v[1] ** 2)
PRINT_SAT, PRINT_DARK = 45, 150  # a source this saturated (gold) or this dark (print, ticks) is not plain dial
PIVOT_MM = 1.5  # hub ring and the hand roots
SHADOW_MM = (0.45, -0.45)
LOGO_R_MM = (3.0, 8.5)  # SEIKO and the 5 shield: the seconds hand crosses them here
WORD_Y_MM = (6.4, 8.8)  # SEIKO band: the hand cuts the K, which is redrawn from the same applied logo on the SNKL50K1 dial
DONOR = ROOT / "outputs/watches/seiko-snkl50k1/dial_photo.jpg"  # regenerate with pipeline.seiko_snkl50_dial if missing
DONOR_WORD_PX = (600, 435, 980, 530)  # x0, y0, x1, y1 around SEIKO in the donor map, clear of the shield
SHADE_SIGMA_PX = 5  # copied pixels keep their fine pattern but take the shade of the dial around them


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.hypot(mx, my) < PIVOT_MM
    for ox, oy in ((0.0, 0.0), SHADOW_MM):  # each hand and its shadow (light from the upper left)
        sx, sy = mx - ox, my - oy
        for name, h in t["hands"].items():
            if name == "seconds" and ox:  # the needle casts no shadow worth removing; its zone would cut the logo
                continue
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = sx * ux + sy * uy, np.abs(-sx * uy + sy * ux)
            m |= (along > 0) & (along < h["length_mm"] + MARGIN_MM) & (across < h["half_width_mm"] + MARGIN_MM)
            m |= (along > -h.get("tail_mm", 0.5) - MARGIN_MM) & (along <= 0) & (across < h.get("tail_half_width_mm", h["half_width_mm"]) + MARGIN_MM)
    return m


def redraw_word(out_img, win, letters, todo):
    """Inside `todo`, draw the SEIKO letters of the donor dial: its gold mask, stretched onto this photo's word box, as alpha;
    the colour is this photo's own letter gold, shaded by the donor's light."""
    sat = cv2.cvtColor(win, cv2.COLOR_BGR2HSV)[..., 1]
    ys, xs = np.nonzero(letters & (sat > PRINT_SAT))
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    d = cv2.imread(str(DONOR))
    x0, y0, x1, y1 = DONOR_WORD_PX
    dh = cv2.cvtColor(d[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    gm = ((dh[..., 1] > 60) & (dh[..., 2] > 90)).astype(np.uint8)
    gy, gx = np.nonzero(gm)
    gm = gm[gy.min():gy.max() + 1, gx.min():gx.max() + 1].astype(np.float32)
    lum = dh[gy.min():gy.max() + 1, gx.min():gx.max() + 1, 2].astype(np.float32)
    alpha = cv2.GaussianBlur(cv2.resize(gm, (bx1 - bx0, by1 - by0), interpolation=cv2.INTER_AREA), (0, 0), 1.0)
    lum = cv2.resize(lum, (bx1 - bx0, by1 - by0), interpolation=cv2.INTER_AREA)
    gold = win[by0:by1, bx0:bx1][(letters & (sat > PRINT_SAT))[by0:by1, bx0:bx1]].astype(np.float32)
    lo, hi = np.percentile(gold, 10, axis=0), np.percentile(gold, 90, axis=0)
    shade = np.clip((lum - 90) / 165, 0, 1)[..., None]
    colour = lo + shade * (hi - lo)
    reg = out_img[by0:by1, bx0:bx1].astype(np.float32)
    a = alpha[..., None]
    t = todo[by0:by1, bx0:bx1]
    reg[t] = (a * colour + (1 - a) * reg)[t]
    out_img[by0:by1, bx0:bx1] = np.clip(reg, 0, 255).astype(np.uint8)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    y0, x0 = py0 - R, px0 - R
    win = img[y0:py0 + R, x0:px0 + R].copy()
    mask = hand_mask(t, img.shape[:2])[y0:py0 + R, x0:px0 + R]
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    mx, my = (xx - R) / S, -(yy - R) / S
    r, a = np.hypot(mx, my), np.degrees(np.arctan2(mx, my))
    centre = r < t["dial_edge_radius_mm"]
    sat = cv2.cvtColor(win, cv2.COLOR_BGR2HSV)[..., 1]
    printed = cv2.dilate(((sat > PRINT_SAT) | (win.mean(2) < PRINT_DARK)).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & centre
    out_img, todo = win.copy(), mask.copy()
    for dx, dy in SHIFTS:  # the woven pattern repeats every PERIOD_PX across and down: copy whole periods over
        sx, sy = (xx + dx).astype(np.float32), (yy + dy).astype(np.float32)
        bad = cv2.remap((mask | printed).astype(np.uint8), sx, sy, cv2.INTER_NEAREST, borderValue=1).astype(bool)
        ok = todo & ~bad
        out_img[ok] = cv2.remap(win, sx, sy, cv2.INTER_NEAREST)[ok]
        todo &= ~ok
    if todo.any():  # a few pixels right at the pivot
        out_img = cv2.inpaint(out_img, todo.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)
    # the dial's light changes with angle: keep the copied fine pattern, take the broad shade from the unmasked dial around it
    f = out_img.astype(np.float32)
    fine = f - cv2.GaussianBlur(f, (0, 0), SHADE_SIGMA_PX)
    valid, shade, left = (~mask & ~printed).astype(np.float32), f.copy(), mask.copy()
    for sigma in (SHADE_SIGMA_PX, 2 * SHADE_SIGMA_PX, 4 * SHADE_SIGMA_PX, 8 * SHADE_SIGMA_PX):
        num = cv2.GaussianBlur(f * valid[..., None], (0, 0), sigma)
        den = cv2.GaussianBlur(valid, (0, 0), sigma)[..., None]
        ok = left & (den[..., 0] > 0.1)
        shade[ok] = (num / np.maximum(den, 1e-6))[ok]
        left &= ~ok
    f[mask] = (shade + fine)[mask]
    out_img = np.clip(f, 0, 255).astype(np.uint8)
    # across the logo the seconds hand leaves a thin strip: blend straight across it from both edges, so the letter and shield
    # outlines carry on through it
    sh = t["hands"]["seconds"]
    ux, uy = math.sin(math.radians(sh["angle_deg"])), math.cos(math.radians(sh["angle_deg"]))
    along, across = mx * ux + my * uy, -mx * uy + my * ux
    half = sh["half_width_mm"] + MARGIN_MM
    near_logo = cv2.dilate(printed.astype(np.uint8), np.ones((61, 61), np.uint8)).astype(bool)  # only where the strip cuts print
    strip = (np.abs(across) < half) & (along > LOGO_R_MM[0]) & (along < LOGO_R_MM[1]) & near_logo
    nx, ny = -uy, ux  # across direction, mm (y up)
    edge = half + 0.05
    take = lambda sgn: cv2.remap(win, (R + (mx + (sgn * edge - across) * nx) * S).astype(np.float32),
                                 (R - (my + (sgn * edge - across) * ny) * S).astype(np.float32), cv2.INTER_LINEAR).astype(np.float32)
    wgt = ((across + edge) / (2 * edge))[..., None]
    blend = (1 - wgt) * take(-1) + wgt * take(1)
    word = strip & (my > WORD_Y_MM[0]) & (my < WORD_Y_MM[1])
    out_img[strip & ~word] = np.clip(blend[strip & ~word], 0, 255).astype(np.uint8)
    redraw_word(out_img, win, printed & ~mask & (my > WORD_Y_MM[0]) & (my < WORD_Y_MM[1]) & (np.abs(mx) < 4), word)
    soft = cv2.GaussianBlur(out_img, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(out_img, 1 + SHARPEN[1], soft, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "inpainted_px": int(todo.sum())}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = win.copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, crop]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
