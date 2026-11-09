"""Straighten the SNKE61K1 front photo (Irsyad's, turned toward the crown) into a front view of the dial plane.

    python3 -B -m pipeline.seiko_snke61_rectify [out.png]     # default outputs/watches/seiko-snke61k1/front_rectified.png

Same method as pipeline/seiko_snkl41_rectify.py, for a navy dial: the 60 white minute-track marks (48 dashes, and the small
dots at the 5-minute numerals) go to one circle at 6 deg steps. The numerals (60, 5, 10 ...) are larger blobs and are skipped.
The photo's dark dial ellipse is 1.4 % out of round.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/seiko-snke61k1/front_turned_2048.png"
OUT = ROOT / "outputs/watches/seiko-snke61k1/front_rectified.png"
NEAR = ROOT / "references/seiko-snke61k1/front_near_2772.png"  # second photo, other hand positions: patches for the dial map
NEAR_OUT = ROOT / "outputs/watches/seiko-snke61k1/front_near_registered.png"
SIZE = (2100, 2100)
CENTRE_PX = (1050, 1050)
RHO = (0.83, 0.97)  # minute track in radii of the dark dial ellipse
MARK_AREA = (20, 135)  # px: dashes and dots (the 15-minute dash beside the date frame is 129 px); numerals are 139 px and more
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
    blobs = [cen[k] for k in range(1, n) if RHO[0] < rho[k] < RHO[1] and MARK_AREA[0] < st[k, cv2.CC_STAT_AREA] < MARK_AREA[1]]
    assert len(blobs) == 60, "found %d track marks" % len(blobs)
    (cx, cy), (w, h), _ = cv2.fitEllipse(np.float32(blobs))
    ang = sorted((math.degrees(math.atan2(x - cx, cy - y)) % 360, float(x), float(y)) for x, y in blobs)
    i0 = min(range(60), key=lambda k: min(ang[k][0], 360 - ang[k][0]))
    pts = [(x, y, k) for k, (_, x, y) in enumerate(ang[i0:] + ang[:i0])]
    assert all(abs(((math.degrees(math.atan2(x - cx, cy - y)) - 6 * k + 180) % 360) - 180) < 4.0 for x, y, k in pts)  # 3/4 view: up to 2.6 deg off before straightening
    return pts, (w / 2, h / 2)


def register_near(rectified, dial_r_px):
    """Map the second photo onto the straightened one: SIFT matches on the dial, RANSAC homography (its hands are elsewhere)."""
    near = cv2.imread(str(NEAR))
    ga, gb = (cv2.cvtColor(x, cv2.COLOR_BGR2GRAY) for x in (rectified, near))
    ma = np.zeros_like(ga)
    cv2.circle(ma, CENTRE_PX, int(dial_r_px), 255, -1)
    n, lab, st, _ = cv2.connectedComponentsWithStats((gb < DARK).astype(np.uint8))
    mb = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8) * 255
    mb = cv2.morphologyEx(mb, cv2.MORPH_CLOSE, np.ones((61, 61), np.uint8))
    sift = cv2.SIFT_create(8000)
    ka, da = sift.detectAndCompute(ga, ma)
    kb, db = sift.detectAndCompute(gb, mb)
    good = [m for m, m2 in cv2.BFMatcher().knnMatch(db, da, k=2) if m.distance < 0.75 * m2.distance]
    src = np.float32([kb[m.queryIdx].pt for m in good])
    dst = np.float32([ka[m.trainIdx].pt for m in good])
    H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 2.0)
    res = np.hypot(*(cv2.perspectiveTransform(src[None], H)[0] - dst).T)[inl.ravel() > 0]
    assert inl.sum() >= 30 and np.median(res) < 1.5, "near photo registration: %d inliers, %.2f px" % (inl.sum(), np.median(res))
    cv2.imwrite(str(NEAR_OUT), cv2.warpPerspective(near, H, SIZE, flags=cv2.INTER_LANCZOS4, borderValue=(255, 255, 255)))
    return {"source": str(NEAR.relative_to(ROOT)), "homography": H.tolist(), "inliers": int(inl.sum()),
            "residual_px": {"median": round(float(np.median(res)), 2), "max": round(float(res.max()), 2)}}


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
    meta["near"] = register_near(warped, 0.97 * R)
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("ticks_used", "residual_px", "tick_radius_px")}, "near:", {k: m["near"][k] for k in ("inliers", "residual_px")}, "->", dest)
