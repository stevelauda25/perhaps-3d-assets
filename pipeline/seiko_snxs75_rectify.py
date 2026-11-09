"""Straighten the SNXS75K1 front photo (turned about 11 deg toward the crown) into a front view of the dial plane.

    python3 -B -m pipeline.seiko_snxs75_rectify [out.png]     # default outputs/watches/seiko-snxs75k1/front_rectified.png

No straight front photo exists. Same idea as pipeline/seiko_sna411_rectify.py, but the points are found automatically: the
printed black minute ticks (dark blobs in a ring round the first-guess ellipse) go to one circle at 6 deg steps, homography by
RANSAC. Output keeps the photo's vertical scale, dial centre at CENTRE_PX, Lanczos, white background. Parts above the dial
plane (hands, bezel, case, bracelet) keep some parallax; the trace fits them on their own.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/seiko-snxs75k1/front_ashford_2800x2800.jpg"
OUT = ROOT / "outputs/watches/seiko-snxs75k1/front_rectified.png"
SIZE = (2800, 2800)
CENTRE_PX = (1400, 1400)
GUESS = ((1370, 1327), (512, 522))  # Phase 0 ellipse through the outer tick ends: centre, semi axes (gridded crops)
RHO = (0.94, 1.0)  # tick ring in first-guess radii: keeps out the index shadows (0.87-0.92) and the gasket (> 1.03)
DARK = 80


def ticks(gray):
    """Tick centroids with their minute; the ellipse they lie on (semi axes in px)."""
    (cx, cy), (ax, ay) = GUESS
    yy, xx = np.mgrid[0:gray.shape[0], 0:gray.shape[1]]
    rho = np.hypot((xx - cx) / ax, (yy - cy) / ay)
    m = ((gray < DARK) & (rho > RHO[0]) & (rho < RHO[1])).astype(np.uint8)
    n, _, st, cen = cv2.connectedComponentsWithStats(m)
    # single ticks; the shadowed upper left (inner wall) merges into one large blob and is left out
    blobs = [cen[i] for i in range(1, n) if 50 <= st[i, cv2.CC_STAT_AREA] <= 260]
    (cx, cy), (w, h), _ = cv2.fitEllipse(np.float32(blobs))
    # perspective makes the ellipse angle drift up to 0.4 tick from the true minute, so number the ticks in order round the
    # dial (steps of about 1 tick, larger over gaps) starting from the tick nearest 12
    ang = sorted(((math.degrees(math.atan2((x - cx) / (w / 2), -(y - cy) / (h / 2))) % 360) / 6, float(x), float(y)) for x, y in blobs)
    i0 = min(range(len(ang)), key=lambda i: min(ang[i][0], 60 - ang[i][0]))
    ang = ang[i0:] + [(a + 60, x, y) for a, x, y in ang[:i0]]
    pts, k = [], 0
    for j, (a, x, y) in enumerate(ang):
        if j:
            step = a - ang[j - 1][0]
            assert abs(step - round(step)) < 0.25, "tick spacing %.2f at %.1f" % (step, a)
            k += round(step)
        pts.append((x, y, k % 60))
    return pts, (w / 2, h / 2)


def build(out=OUT):
    im = cv2.imread(str(SRC))
    pts, axes = ticks(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY))
    assert len(pts) >= 30, "only %d ticks found" % len(pts)
    R = max(axes)  # the turn foreshortens across the turn axis only: keep the long axis (the photo's own scale)
    src = np.float32([p[:2] for p in pts])
    dst = np.float32([(CENTRE_PX[0] + R * math.sin(math.radians(6 * p[2])), CENTRE_PX[1] - R * math.cos(math.radians(6 * p[2]))) for p in pts])
    H, _ = cv2.findHomography(src, dst, 0)  # all ticks: the top three sit 3-4 px out (centroid bias), RANSAC would drop them
    res = np.hypot(*(cv2.perspectiveTransform(src[None], H)[0] - dst).T)
    warped = cv2.warpPerspective(im, H, SIZE, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), warped)
    meta = {"source": str(SRC.relative_to(ROOT)), "homography": H.tolist(), "ticks_used": len(pts),
            "minutes_used": sorted({p[2] for p in pts}),
            "residual_px": {"median": round(float(np.median(res)), 2), "max": round(float(res.max()), 2)},
            "dial_centre_px": list(CENTRE_PX), "tick_radius_px": round(R, 1)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("ticks_used", "residual_px", "tick_radius_px")}, "missing minutes:",
          sorted(set(range(60)) - set(m["minutes_used"])), "->", dest)
