"""Cut the photo maps for the Bulova 98A227 (Marine Star automatic) from the official front render: a clean dial (hands
removed) and the strap.

    python3 -B -m pipeline.bulova_98a227_dial [review.png]   # -> outputs/watches/bulova-98a227/dial_photo.jpg, strap_photo.jpg

Dial: square map to the bezel's inner edge. Each main-hand pixel gets a local lighting estimate (masked normalised blur)
plus detail copied from the same radius 30, 60 ... deg, then 6, 12 ... deg away about the pivot (the ridged dial and the
chapter ring repeat); the sub-seconds hand is removed the same way about the sub-dial centre (concentric track, 6 deg
ticks). White prints, red prints, the applied rose-gold parts and the open-heart aperture are never a copy source; inside
the aperture the photo stays as it is (no repeat; the modelled hands do not cross it). Strap: the photo column between the
strap edges, as taken. Native resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load
from pipeline.hamilton_h82405130_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/bulova-98a227-trace.json"
OUT = ROOT / "outputs/watches/bulova-98a227/dial_photo.jpg"
STRAP = ROOT / "outputs/watches/bulova-98a227/strap_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_PX = 8
SHADOW_PX = ((4, 4),)  # the render's hands throw a faint shadow down to the right
LIGHT_SIGMA_PX = 12
STRAP_X = (290, 975)


def poly(h, S, pad=0.0):
    t = math.radians(h["angle_deg"])
    pts = [(r * S, v * S + pad) for r, v in h["outline_mm"]]
    pts[0], pts[-1] = (pts[0][0] - pad, pts[0][1]), (pts[-1][0] + pad, pts[-1][1])
    loop = [(v, r) for r, v in pts] + [(-v, r) for r, v in pts[::-1]]
    return [(x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)) for x, y in loop]


def masks(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    main, sub = np.zeros(shape, np.uint8), np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOW_PX:
        for name in ("hour", "minute"):
            cv2.fillPoly(main, [np.array([(px0 + x + dx, py0 - y + dy) for x, y in poly(t["hands"][name], S, MARGIN_PX)], np.int32)], 1)
        cv2.circle(main, (px0 + dx, py0 + dy), int(t["hub_radius_mm"][0] * S + MARGIN_PX), 1, -1)
        sb = t["sub"]
        cx, cy = px0 + sb["centre_mm"][0] * S + dx, py0 - sb["centre_mm"][1] * S + dy
        a = math.radians(sb["angle_deg"])
        p = lambda r: (int(cx + r * S * math.sin(a)), int(cy - r * S * math.cos(a)))
        cv2.line(sub, p(-sb["tail_mm"]), p(sb["length_mm"]), 1, int(2 * sb["tail_half_mm"] * S + 2 * MARGIN_PX))
        cv2.circle(sub, (int(cx), int(cy)), int(sb["hub_mm"] * S + MARGIN_PX), 1, -1)
    return main.astype(bool), sub.astype(bool)


def build(review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    shape = img.shape[:2]
    R = int(math.ceil(t["rings_mm"]["bezel_in"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    main, sub = (m[sl] for m in masks(t, shape))
    bgr = win.astype(int)
    B, G, Rc = bgr[..., 0], bgr[..., 1], bgr[..., 2]
    gray = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY)
    feats = ((gray > 150) & ((B - Rc) < 70)) | ((Rc - B) > 40)  # white and red prints, rose-gold parts (not the blue ridge highlights)
    feats = cv2.dilate(feats.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    yy, xx = np.mgrid[-R:R, -R:R]
    ac, ar = t["aperture"]["centre_mm"], t["aperture"]["ring_mm"][1] * S + 4
    ap = np.hypot(xx - ac[0] * S, yy + ac[1] * S) < ar
    sc = t["sub"]["centre_mm"]
    sxc, syc = R + sc[0] * S, R - sc[1] * S

    def lighting(mask):
        clean = (~mask & ~feats & ~ap).astype(np.float32)
        num = cv2.GaussianBlur(win.astype(np.float32) * clean[..., None], (0, 0), LIGHT_SIGMA_PX)
        return num / np.maximum(cv2.GaussianBlur(clean, (0, 0), LIGHT_SIGMA_PX)[..., None], 1e-3)

    hand = main | sub
    low = lighting(hand)
    used = {}
    todo = main & ~ap & ~sub
    moves = [(sg * k * 30, 1.0) for k in range(1, 6) for sg in (1, -1)] + [(sg * k * 6, 1.0) for k in range(1, 30) for sg in (1, -1)]
    used.update(fill(win, todo, hand | feats | ap, low, moves, (R, R)))
    left_main = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    todo = sub.copy()
    used.update({"sub " + k: v for k, v in fill(win, todo, hand | feats | ap, low, [(sg * k * 6, 1.0) for k in range(1, 30) for sg in (1, -1)], (sxc, syc)).items()})
    left_sub = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur((hand & ~ap).astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    sharpen = lambda a: cv2.addWeighted(a, 1 + SHARPEN[1], cv2.GaussianBlur(a, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    crop = sharpen(win)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(hand.sum()), "lighting_only_px": [left_main, left_sub], "filled_from": {k: v for k, v in used.items() if v}}
    OUT.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")

    x0, x1 = STRAP_X
    strap = sharpen(img[:, x0:x1])
    cv2.imwrite(str(STRAP), strap, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    STRAP.with_suffix(".json").write_text(json.dumps({"source": t["source"], "crop_px": [x0, 0], "size_px": [x1 - x0, img.shape[0]]}, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[hand] = (0.5 * shown[hand] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else None), "->", OUT, STRAP)
