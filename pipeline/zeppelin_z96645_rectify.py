"""Straighten the Zeppelin Z96645 front photo (taken slightly from below and right) into a front view of the dial plane.

    python3 -B -m pipeline.zeppelin_z96645_rectify [out.png]     # default outputs/watches/zeppelin-z96645/front_rectified.png

The 12 black hour bars on the minute track (dark blobs of 820-940 px at r 900-1015 px around the hub) go to one circle at 30 deg steps with a
homography. The radius keeps the photo's own scale (longest semi axis of their ellipse). The whole photo is warped, strap included.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/zeppelin-z96645/front_3218x4988.png"
OUT = ROOT / "outputs/watches/zeppelin-z96645/front_rectified.png"
SIZE = (3218, 4988)
CENTRE_PX = (1609, 2420)
# black hour bars at 12, 1, 2 ... 11 (centroids, px in the source photo)
DOTS_PX = [(1510, 1420), (1989, 1551), (2337, 1904), (2461, 2384), (2329, 2863), (1975, 3214),
           (1493, 3340), (1013, 3208), (665, 2854), (541, 2372), (675, 1894), (1030, 1545)]


def build(out=OUT):
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    src = np.float32(DOTS_PX)
    _, axes, _ = cv2.fitEllipse(src)
    R = max(axes) / 2
    dst = np.float32([(CENTRE_PX[0] + R * math.sin(math.radians(30 * k)), CENTRE_PX[1] - R * math.cos(math.radians(30 * k))) for k in range(12)])
    H, _ = cv2.findHomography(src, dst, 0)
    res = np.hypot(*(cv2.perspectiveTransform(src[None], H)[0] - dst).T)
    assert res.max() < 2.0, "bar residual %.2f px" % res.max()
    warped = cv2.warpPerspective(im, H, SIZE, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), warped)
    meta = {"source": str(SRC.relative_to(ROOT)), "homography": H.tolist(), "dots_used": len(DOTS_PX),
            "residual_px": {"median": round(float(np.median(res)), 2), "max": round(float(res.max()), 2)},
            "dial_centre_px": list(CENTRE_PX), "dot_radius_px": round(float(R), 1)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("dots_used", "residual_px", "dot_radius_px")}, "->", dest)
