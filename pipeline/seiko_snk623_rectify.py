"""Straighten the SNK623K1 front photo (Irsyad's, turned slightly toward the crown) into a front view of the dial plane.

    python3 -B -m pipeline.seiko_snk623_rectify [out.png]     # default outputs/watches/seiko-snk623k1/front_rectified.png

Same method as pipeline/seiko_snkl41_rectify.py, for a black dial: the 60 white minute-track marks (dashes, and squares at
the hours) go to one circle at 6 deg steps. The photo's crystal ellipse is 1.5 % out of round along a diagonal.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/seiko-snk623k1/front_turned_2924.png"
OUT = ROOT / "outputs/watches/seiko-snk623k1/front_rectified.png"
SIZE = (2900, 2900)
CENTRE_PX = (1450, 1450)
RHO = (0.85, 0.99)  # minute track in radii of the dark dial ellipse
DARK, BRIGHT = 60, 150


def ticks(gray):
    """Track mark centroids numbered by minute (0 = the square at 12), and the semi axes of their ellipse."""
    n, lab, st, _ = cv2.connectedComponentsWithStats((gray < DARK).astype(np.uint8))
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    cnt, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    (cx, cy), (w, h), a = cv2.fitEllipse(max(cnt, key=len))
    inside = np.zeros_like(gray, np.uint8)
    cv2.ellipse(inside, ((cx, cy), (w, h), a), 1, -1)
    n, _, st, cen = cv2.connectedComponentsWithStats(((gray > BRIGHT) & (inside > 0)).astype(np.uint8))
    rho = np.hypot((cen[:, 0] - cx) / (w / 2), (cen[:, 1] - cy) / (h / 2))
    blobs = [cen[k] for k in range(1, n) if RHO[0] < rho[k] < RHO[1] and 30 < st[k, cv2.CC_STAT_AREA] < 2500]
    assert len(blobs) == 60, "found %d track marks" % len(blobs)
    (cx, cy), (w, h), _ = cv2.fitEllipse(np.float32(blobs))
    ang = sorted((math.degrees(math.atan2(x - cx, cy - y)) % 360, float(x), float(y)) for x, y in blobs)
    i0 = min(range(60), key=lambda k: min(ang[k][0], 360 - ang[k][0]))
    pts = [(x, y, k) for k, (_, x, y) in enumerate(ang[i0:] + ang[:i0])]
    assert all(abs(((math.degrees(math.atan2(x - cx, cy - y)) - 6 * k + 180) % 360) - 180) < 2.5 for x, y, k in pts)
    return pts, (w / 2, h / 2)


def build(out=OUT):
    im = cv2.imread(str(SRC))
    pts, axes = ticks(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY))
    R = max(axes)  # the turn foreshortens one axis only: keep the long one (the photo's own scale)
    src = np.float32([p[:2] for p in pts])
    dst = np.float32([(CENTRE_PX[0] + R * math.sin(math.radians(6 * k)), CENTRE_PX[1] - R * math.cos(math.radians(6 * k))) for _, _, k in pts])
    H, _ = cv2.findHomography(src, dst, 0)
    res = np.hypot(*(cv2.perspectiveTransform(src[None], H)[0] - dst).T)
    warped = cv2.warpPerspective(im, H, SIZE, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), warped)
    meta = {"source": str(SRC.relative_to(ROOT)), "homography": H.tolist(), "ticks_used": len(pts),
            "residual_px": {"median": round(float(np.median(res)), 2), "max": round(float(res.max()), 2)},
            "dial_centre_px": list(CENTRE_PX), "tick_radius_px": round(R, 1)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("ticks_used", "residual_px", "tick_radius_px")}, "->", dest)
