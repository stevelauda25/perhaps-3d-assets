"""Cut the Z70363 photo map (dial and strap) from the front photo, with the hands, hubs and their shadows removed.

    python3 -B -m pipeline.zeppelin_z70363_dial [out.jpg] [review.png]   # default outputs/watches/zeppelin-z70363/dial_photo.jpg

The dial has no repeating pattern under the hands (numerals, sub-dial rings, week and minute scales), so the hand zones are
filled with a normalised blur of the pixels around them (coarse to fine); the 3D hands cover the zones from the front. Hand zones are the posed outlines from
config/watches/zeppelin-z70363-trace.json. One map: full photo height (strap) by the case width, centred on the hand pivot,
at the photo's own resolution, light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/zeppelin-z70363-trace.json"
OUT = ROOT / "outputs/watches/zeppelin-z70363/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_WIDTH_MM = 18.6  # map x range: the dial and a little bezel; the strap is narrower
MARGIN_MM = 0.2
SHADOWS_MM = ((0.15, -0.15),)  # faint, light from the upper left
FILL_SIGMAS_PX = (40, 12, 4)  # coarse to fine: each pass replaces the estimate where it has enough valid pixels
# The turned photo (other listing) has the seconds hand at 9 and the moon disc on the left (Irsyad 2026-11-09: the front
# photo's moon window reads as flipped). Registered onto the front photo by a homography on the dial and colour-matched,
# it supplies the moon window with its caption and the dial under the front photo's seconds needle.
TURNED = ROOT / "references/zeppelin-z70363/three_quarter_2000x3140.png"
MOON_BOX_PX = (1150, 1375, 1495, 1572)  # front photo: moon window and MOON PHASE caption (x0, y0, x1, y1)
DIAL_MATCH_MM = 17.0


def register_turned(img, t):
    """Turned photo warped onto the front photo frame: SIFT on the dial, RANSAC homography (moon disc and hands move)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    tb = cv2.imread(str(TURNED))
    ga, gb = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.cvtColor(tb, cv2.COLOR_BGR2GRAY)
    ma = np.zeros_like(ga)
    cv2.circle(ma, (px0, py0), int(DIAL_MATCH_MM * S), 255, -1)
    sift = cv2.SIFT_create(12000)
    ka, da = sift.detectAndCompute(ga, ma)
    kb, db = sift.detectAndCompute(gb, None)
    good = [m for m, m2 in cv2.BFMatcher().knnMatch(db, da, k=2) if m.distance < 0.75 * m2.distance]
    src = np.float32([kb[m.queryIdx].pt for m in good])
    dst = np.float32([ka[m.trainIdx].pt for m in good])
    H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    res = np.hypot(*(cv2.perspectiveTransform(src[None], H)[0] - dst).T)[inl.ravel() > 0]
    assert inl.sum() >= 30 and np.median(res) < 2.0, "turned photo registration: %d inliers, %.2f px" % (inl.sum(), np.median(res))
    warped = cv2.warpPerspective(tb, H, img.shape[1::-1], flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
    return warped, {"inliers": int(inl.sum()), "residual_px": round(float(np.median(res)), 2)}


def colour_match(src, ref, region):
    """Per-channel Lab mean/std of src mapped onto ref over the region (dial pixels clear of hands and the moon window)."""
    a, b = (cv2.cvtColor(x, cv2.COLOR_BGR2LAB).astype(np.float32) for x in (src, ref))
    ma, sa, mb, sb = a[region].mean(0), a[region].std(0), b[region].mean(0), b[region].std(0)
    return cv2.cvtColor(np.clip((a - ma) * (sb / sa) + mb, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    hs = t["hands"]
    polys = [h["outline_mm"] for h in hs.values()] + [hs["seconds"]["tail_mm"], hs["week"]["crescent_mm"]]
    polys += [s["hand_mm"] for s in t["subdials"].values()]
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        for poly in polys:
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in poly]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_radius_mm"][0] * S * 1.08), 1, -1)
        for s in t["subdials"].values():
            cv2.circle(m, tuple(int(v) for v in P(s["centre_mm"], dx, dy)), int(t["sub_hub_radius_mm"] * S * 1.15), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=max(1, int(MARGIN_MM * S / 1.5)))


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    mask = hand_mask(t, img.shape[:2])
    valid = (1 - mask).astype(np.float32)[..., None]
    est = None
    for sig in FILL_SIGMAS_PX:  # normalised blur of the unmasked pixels: smooth dial colour, no streaks from the hand edges
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        e = cv2.GaussianBlur(img * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        est = e if est is None else np.where(wgt > 0.2, e, est)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = np.clip(soft * est + (1 - soft) * img, 0, 255).astype(np.uint8)

    turned, reg = register_turned(img, t)
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    r = np.hypot(xx - px0, yy - py0) / S
    x0, y0, x1, y1 = MOON_BOX_PX
    moon = np.zeros(img.shape[:2], np.uint8)
    moon[y0:y1, x0:x1] = 1
    sec = np.zeros(img.shape[:2], np.uint8)  # seconds needle zone, past the centre hub
    for dx, dy in ((0, 0),) + SHADOWS_MM:
        poly = [(px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S) for p in t["hands"]["seconds"]["outline_mm"]]
        cv2.fillPoly(sec, [np.round(poly).astype(np.int32)], 1)
    sec = cv2.dilate(sec, np.ones((3, 3), np.uint8), iterations=max(1, int(MARGIN_MM * S / 1.5))).astype(bool)
    sec &= r > t["hub_radius_mm"][0] * 1.15
    region = (r < 13.5) & ~cv2.dilate(mask, np.ones((25, 25), np.uint8)).astype(bool) & ~moon.astype(bool) & (turned.min(2) < 250)
    turned = colour_match(turned, img, region)
    take = (moon.astype(bool) & ~mask.astype(bool)) | sec
    soft = cv2.GaussianBlur(take.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = np.clip(soft * turned + (1 - soft) * clean, 0, 255).astype(np.uint8)
    W = int(round(HALF_WIDTH_MM * S))
    crop = clean[:, px0 - W:px0 + W]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = 0.5 + x / (2 half_w), v = 0.5 + (y - centre_y) / (2 half_h)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_w_mm": round(W / S, 4), "half_h_mm": round(crop.shape[0] / 2 / S, 4),
            "centre_y_mm": round((py0 - crop.shape[0] / 2) / S, 4), "size_px": list(crop.shape[1::-1]), "masked_px": int(mask.sum()), "turned_photo": reg}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        R = int(18.2 * S)
        sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = img[sl].copy()
        shown[mask[sl].astype(bool)] = (0.5 * shown[mask[sl].astype(bool)] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[sl]]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
