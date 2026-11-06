"""Cut the SFK001J1 photo map (wave dial, 24-hour flange and bezel insert) from the front photo, with the hands and their
shadows removed.

    python3 -B -m pipeline.seiko_sfk001_dial [out.jpg] [review.png]     # default outputs/watches/seiko-sfk001j1/dial_photo.jpg

Same fill as pipeline/seiko_spb335_dial.py: each hand pixel is copied from the same radius 7.5, 15, 22.5 ... deg away (the
flange's 24-hour tick pitch; first source that is neither a hand nor an index or print), lighting from around the hand. Hand masks grow to
every non-blue patch touching a traced hand (black frames, tails) and every orange patch (GMT hand over the SEIKO print).
Hand zones are the traced outlines about the hand pivot from config/watches/seiko-sfk001j1-trace.json; indices, prints and
the rotation centre use the dial centre. One square map centred on the dial centre, wide enough for the bezel insert, at
the photo's own resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-sfk001j1-trace.json"
OUT = ROOT / "outputs/watches/seiko-sfk001j1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_MM = 21.0  # map half size: insert outer edge (20.13 mm) plus the bezel centre offset
MARGIN_MM = 0.25
SHADOWS_MM = ((0.0, -0.5), (0.2, -0.9), (0.45, -0.45), (0.3, 0.35))  # mostly below the hands (up to 1 mm), a dark edge above the minute hand
LOW_SIGMA_PX = 30
PERIOD_DEG = 7.5
HUB_LIGHTING_MM = 1.8  # round the pivot: lighting only (rotated copies streak at small radii; the hands cover most of it)
HUB_FEATHER_MM = 1.5  # then fade from lighting only to the rotated copies
ORANGE = 60  # GMT hand: red this far above blue, removed even over the SEIKO print it crosses
NOT_BLUE = 45  # dial pixels have blue at least this far above red; hand frames, lume and orange do not
# date: the photo shows "10"; Irsyad asked for "6" (2026-11-06). Digits filled from the white window's lighting, the new date
# drawn in a geometric sans (the photo's round "0") at the photo's digit height, centred in the window
DATE_TEXT = "6"
DATE_WINDOW_PX = (1651, 2051, 1778, 2158)  # white window inside the frame (x0, y0, x1, y1)
DATE_DIGIT_PX = (2066, 2140, 10)  # digit top, bottom, stroke width in the photo
DATE_FONT = ("/System/Library/Fonts/Avenir Next.ttc", 5)  # Avenir Next Medium
DATE_INK = (28, 28, 30)  # BGR, the photo's digit colour


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["pivot_px"]
    P = lambda p, dx=0, dy=0: (px0 + (p[0] + dx) * S, py0 - (p[1] + dy) * S)
    m = np.zeros(shape, np.uint8)
    sec = t["hands"]["seconds"]
    for dx, dy in ((0, 0),) + shadows:
        for h in t["hands"].values():
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in h["outline_mm"]]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P(sec["disc_centre_mm"], dx, dy)), int(sec["disc_radius_mm"] * S), 1, -1)
        for poly in t["extra_hand_mask_mm"]:
            cv2.fillPoly(m, [np.round([P(p, dx, dy) for p in poly]).astype(np.int32)], 1)
        cv2.circle(m, tuple(int(v) for v in P((0, 0), dx, dy)), int(t["hub_radius_mm"][0] * S * 1.2), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=int(margin * S / 1.5)).astype(bool)


def feature_mask(t, shape, prints_only=False):
    """Indices and prints never used as a fill source (prints_only: the prints a hand may only graze)."""
    S, (dx0, dy0) = t["scale_px_per_mm"], t["origin_px"]
    P = lambda p: (dx0 + p[0] * S, dy0 - p[1] * S)
    m = np.zeros(shape, np.uint8)
    pad = 0 if prints_only else 12
    for k in ("logo_seiko", "logo_x", "print_gmt", "print_divers", "print_6", "date_window"):
        x0, y0, x1, y1 = t["manual_px"][k]
        cv2.rectangle(m, (x0 - pad, y0 - pad), (x1 + pad, y1 + pad), 1, -1)
    nu = t["numerals_24h"]
    for a in nu["angles_deg"]:  # small printed numerals just inside the flange
        pts = [P((r * math.sin(math.radians(a + s)), r * math.cos(math.radians(a + s)))) for r, s in
               ((nu["r_mm"][0], -nu["half_angle_deg"]), (nu["r_mm"][0], nu["half_angle_deg"]), (nu["r_mm"][1], nu["half_angle_deg"]), (nu["r_mm"][1], -nu["half_angle_deg"]))]
        cv2.fillPoly(m, [np.round(pts).astype(np.int32)], 1)
    if prints_only:
        return m.astype(bool)
    ix = t["indices"]
    for hr in range(1, 13):
        a = math.radians(hr * 30)
        if str(hr) in ix["shapes_mm"]:
            pts = [P((x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))) for x, y in ix["shapes_mm"][str(hr)]["outline"]]
            cv2.fillPoly(m, [np.round(pts).astype(np.int32)], 1)
        else:
            cv2.circle(m, tuple(int(v) for v in P((ix["dot_r_mm"] * math.sin(a), ix["dot_r_mm"] * math.cos(a)))), int(ix["dot_radius_mm"] * S), 1, -1)
    return cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=pad // 2 or 1).astype(bool)


def redate(img):
    """Replace the date digits in place: fill the dark digits from the window's own lighting, then darken a drawn DATE_TEXT."""
    x0, y0, x1, y1 = DATE_WINDOW_PX
    win = img[y0:y1, x0:x1]
    ink = cv2.dilate((win.max(2) < 140).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
    ink[:, :8] = 0  # keep the frame's shaded left wall
    ok = (1 - ink).astype(np.float32)[..., None]  # smooth white from the window's own lighting, not inpaint ghosts
    smooth = cv2.GaussianBlur(win * ok, (0, 0), 14) / np.maximum(cv2.GaussianBlur(ok, (0, 0), 14)[..., None], 1e-3)
    grow = cv2.dilate(ink, np.ones((3, 3), np.uint8), iterations=3)[..., None].astype(bool)
    win[:] = np.where(grow, smooth, win).clip(0, 255).astype(np.uint8)
    top, bottom, _ = DATE_DIGIT_PX
    k = 4  # supersampled for smooth edges
    font = ImageFont.truetype(DATE_FONT[0], 100 * k, index=DATE_FONT[1])
    bx = font.getbbox(DATE_TEXT)
    font = ImageFont.truetype(DATE_FONT[0], int(100 * k * (bottom - top) * k / (bx[3] - bx[1])), index=DATE_FONT[1])
    bx = font.getbbox(DATE_TEXT)
    W, H = (x1 - x0) * k, (y1 - y0) * k
    canvas = Image.new("L", (W, H), 0)
    cx, cy = W / 2 + 4 * k, ((top + bottom) / 2 - y0) * k  # +4 px: the window's left edge is the shaded wall
    ImageDraw.Draw(canvas).text((cx - (bx[0] + bx[2]) / 2, cy - (bx[1] + bx[3]) / 2), DATE_TEXT, fill=255, font=font)
    a = cv2.resize(np.asarray(canvas, np.float32) / 255, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)[..., None]
    win[:] = (win * (1 - a) + np.array(DATE_INK, np.float32) * a).astype(np.uint8)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["rings_mm"]["dial_edge"] * S + 0.6 * S))  # hand fill works inside the flange
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    prints = feature_mask(t, img.shape[:2], prints_only=True)
    mask = np.where(prints, hand_mask(t, img.shape[:2], (), 0.15), hand_mask(t, img.shape[:2]))[sl]
    # the photo's hands are a little larger than the traced outlines (black frames, tails): add every non-blue patch that
    # touches a traced hand, except over the prints; orange patches (GMT hand) also where it crosses the SEIKO print
    b_, r_ = win[..., 0].astype(int), win[..., 2].astype(int)
    traced = hand_mask(t, img.shape[:2], (), 0.0)[sl]
    touching = lambda m: (lambda lab: np.isin(lab, np.unique(lab[traced & (lab > 0)])))(cv2.connectedComponents(m.astype(np.uint8))[1])
    auto = touching(b_ - r_ < NOT_BLUE) & ~prints[sl] & ~feature_mask(t, img.shape[:2])[sl] | touching(r_ - b_ > ORANGE)
    mask |= cv2.dilate(auto.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=3).astype(bool)
    bad = mask | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    c = (R, R)
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    used = {}
    yy, xx = np.mgrid[0:win.shape[0], 0:win.shape[1]]
    ppx, ppy = t["pivot_px"]
    hub = np.hypot(xx - (R + ppx - px0), yy - (R + ppy - py0)) <= HUB_LIGHTING_MM * S  # disc round the pivot: lighting only
    win[hub] = np.clip(low[hub], 0, 255).astype(np.uint8)
    todo &= ~hub
    mask |= hub
    for k in range(1, 24):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D(c, deg, 1.0)
            src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            used["%g deg" % deg] = int(take.sum())
    unfilled = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    rr = np.hypot(xx - (R + ppx - px0), yy - (R + ppy - py0)) / S
    w = np.clip((rr - HUB_LIGHTING_MM) / HUB_FEATHER_MM, 0, 1)[..., None]
    win = np.where(mask[..., None], w * win + (1 - w) * low, win).clip(0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    clean = img.copy()
    clean[sl] = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    redate(clean)
    W = int(round(HALF_MM * S))
    crop = clean[py0 - W:py0 + W, px0 - W:px0 + W]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm (about the dial centre) to this image: u = 0.5 + x / (2 half), v = 0.5 + y / (2 half)
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_mm": round(W / S, 4), "size_px": list(crop.shape[1::-1]),
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled_from_deg": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, clean[sl]]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
