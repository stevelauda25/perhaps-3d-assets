"""Cut a clean dial map for the SNK381K1 from the front photo: hands and hub removed, filled by inpainting the plain black dial.

    python3 -B -m pipeline.seiko_snk381_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snk381k1/dial_photo.jpg

The dial is plain black, so OpenCV inpainting fills the hand zones cleanly. Where the seconds hand crosses the 0 of 10, the
masked pixels inside that numeral are copied from its mirror image top-to-bottom (the 0 is symmetric) before inpainting.
Numerals, logo, print, dots and the day-date stay in the map. Square, centred on the hand pivot, out to the crystal ring,
photo resolution, light unsharp mask, JPEG. Zones come from config/watches/seiko-snk381k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snk381k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snk381k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HAND_ZONE = {"hour": (1.0, 1.0), "minute": (0.85, 1.0), "seconds": (0.3, 0)}  # half width mm (with edge glints), tail mm (seconds tail: below)
MARGIN_MM = 0.15
CORE_MM = {"hour": 0.82, "minute": 0.6, "seconds": 0.14}  # the hand body itself; bright pixels outside it are numerals
SHADOW_MM = (0.45, -0.45)  # light from the upper left: each hand's shadow lies down and to the right


def hand_mask(t, shape, core=False):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    h = t["hands"]
    m = np.hypot(mx, my) < h["hub_radius_mm"][1] + MARGIN_MM
    for name, (half, tail) in HAND_ZONE.items():
        half = CORE_MM[name] if core else half
        a, L = math.radians(h[name]["angle_deg"]), h[name]["length_mm"]
        ux, uy = math.sin(a), math.cos(a)
        for ox, oy in ((0.0, 0.0), SHADOW_MM) if name != "seconds" and not core else ((0.0, 0.0),):
            al, ac = (mx - ox) * ux + (my - oy) * uy, -(mx - ox) * uy + (my - oy) * ux
            tp = np.clip((L + 0.3 - al) / (0.4 * L), 0.3 / half, 1.0) * half  # pointed tips: keep the zone off nearby numerals
            end = L + 0.3 if ox == 0 else L - 1.5  # shadow zone stops short of the tip, which sits next to a numeral
            m |= (al > (-tail if tail else 0)) & (al < end) & (np.abs(ac) < tp)
    cx, cy = (np.array(t["manual_px"]["seconds_hand_tail_end"]) - [px0, py0]) / S * [1, -1]  # tail drawn to its disc, not straight through
    Lt = math.hypot(cx, cy)
    along, across = (mx * cx + my * cy) / Lt, (-mx * cy + my * cx) / Lt
    m |= (along > 0) & (along < Lt) & (np.abs(across) < HAND_ZONE["seconds"][0])
    m |= np.hypot(mx - cx, my - cy) < h["seconds"]["tail_disc_radius_mm"][1] + MARGIN_MM
    return m


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    x0, y0, x1, y1 = t["manual_px"]["numeral_10"]
    x1 += 40
    zx0 = x0 + (x1 - x0) // 2 - 60  # the 0 of 10 (right half of the box): flip it about its own centre row
    lit = cv2.cvtColor(img[y0:y1, zx0:x1], cv2.COLOR_BGR2GRAY) > 120
    n, lab, st, _ = cv2.connectedComponentsWithStats(lit.astype(np.uint8))
    k = 1 + int(np.argmax(st[1:, 4]))
    ya, yb = y0 + st[k, 1] - 15, y0 + st[k, 1] + st[k, 3] + 15
    sub, msub = img[ya:yb, zx0:x1], mask[ya:yb, zx0:x1].copy()
    sub[msub] = sub[::-1][msub]
    mask[ya:yb, zx0:x1] &= msub[::-1]  # still masked only where the mirror source was also under the hand
    # bright shapes outside the hand body that reach beyond the hand zone are numerals: keep them; glints stay inside the zone
    lit = (cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) > 90) & ~hand_mask(t, img.shape[:2], core=True)
    n, lab = cv2.connectedComponents(lit.astype(np.uint8))
    keep = np.zeros(n, bool)
    keep[np.unique(lab[lit & ~mask])] = True
    keep[0] = False
    mask &= ~keep[lab]
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    pad = 20
    win = (slice(py0 - R - pad, py0 + R + pad), slice(px0 - R - pad, px0 + R + pad))
    src, mw = img[win].copy(), mask[win]
    bright = (cv2.cvtColor(src, cv2.COLOR_BGR2GRAY) > 90) & ~mw  # numerals, dots, print: hidden from the fill so they do not bleed
    src[bright] = np.median(src[~mw & ~bright], axis=0)
    filled = img[win].copy()
    filled[mw] = cv2.inpaint(src, (mw * 255).astype(np.uint8), 9, cv2.INPAINT_TELEA)[mw]
    crop = filled[pad:-pad, pad:-pad]
    soft = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], soft, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask[win].sum()), "kb": out.stat().st_size // 1024}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        before = img[py0 - R:py0 + R, px0 - R:px0 + R].copy()
        m = hand_mask(t, img.shape[:2])[py0 - R:py0 + R, px0 - R:px0 + R]
        before[m] = (0.5 * before[m] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([before, crop]), (2 * 1100, 1100), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
