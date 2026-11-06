"""Cut the SSA425J1 photo map (dial, sub-dial, open-heart aperture, crystal wall and bezel insert) with the hands removed.

    python3 -B -m pipeline.seiko_ssa425_dial [out.jpg] [review.png]     # default outputs/watches/seiko-ssa425j1/dial_photo.jpg

Hand pixels are filled per zone (same method as pipeline/seiko_spb467_dial.py: lighting from around the hand, detail from a
rotated copy that lands on clean dial):
  main dial    plain black inside TRACK_MM: lighting only; the minute track rotated about the pivot in 6 deg steps;
  24-h sub-dial rotated about its own pivot in 45 deg steps, ring included (8 ticks; the 24 and 12 numerals are never a source);
  aperture     left as photographed: the seconds needle there lies under the 3D needle (inpainting smeared the movement).
Square map centred on the hand pivot out to the bezel insert, at the photo's own resolution, light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-ssa425j1-trace.json"
OUT = ROOT / "outputs/watches/seiko-ssa425j1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_MM = 0.3
SHADOWS_MM = ((0.12, -0.2),)  # the black studio render shows almost no hand shadow
CORRIDOR_MM = 0.5  # around each hand: never a source; bright pixels in it are hand (gunmetal edges reach past the traced width)
TRACK_MM = 12.8  # minute-track ticks start here; inside it the dial is plain black
LOW_SIGMA_PX = 20


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + shadows:
        for h in t["hands"].values():
            ox, oy = h.get("pivot_mm", (0, 0))
            x, y = mx - dx - ox, my - dy - oy
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            L = h["length_mm"]
            if "half_width_mid_mm" in h:  # sword hands taper from the root to the tip
                hw = np.interp(along / L, [0.25, 0.75, 0.95, 1.0], [h["half_width_root_mm"], h["half_width_mid_mm"], h["half_width_tip_mm"], 0.1])
            else:
                hw = h.get("arrow_half_width_mm", h.get("half_width_mm"))
            m |= (along > 0) & (along < L + margin) & (across < hw + margin)
            tw = h.get("tail_half_width_mm", h.get("half_width_root_mm", h.get("half_width_mm")))
            m |= (along > -h.get("tail_mm", 0) - margin) & (along <= 0) & (across < tw + margin)
            m |= np.hypot(x, y) < h.get("cap_radius_mm", 0) + margin
        m |= np.hypot(mx - dx, my - dy) < t["hub_radius_mm"][0] + margin
    return m


def feature_mask(t, shape):
    """Applied and printed parts: never copied into a hand zone (geometry or print stays)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    to_px = lambda b: (int(px0 + b[0] * S) - 8, int(py0 - b[1] * S) - 8, int(px0 + b[2] * S) + 8, int(py0 - b[3] * S) + 8)
    for b in [t[k]["x0_y0_x1_y1_mm"] for k in ("logo_seiko", "print_presage", "print_6")] + t["sub24"]["numerals_mm"]:
        x0, y0, x1, y1 = to_px(b)
        cv2.rectangle(m, (x0, y0), (x1, y1), 1, -1)
    ix = t["indices"]
    w = int((ix["width_mm"] + 0.6) * S)
    for hr in range(1, 13):
        a = math.radians(hr * 30)
        ends = [(int(px0 + r * math.sin(a) * S), int(py0 - r * math.cos(a) * S)) for r in (9.0, ix["outer_mm"] + 0.3)]  # with the lume pad
        cv2.line(m, *ends, 1, w if hr != 12 else int(2.6 * S))
    return m.astype(bool)


def disc(t, shape, centre_mm, r_mm):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    return np.hypot((xx - px0) / S - centre_mm[0], -(yy - py0) / S - centre_mm[1]) < r_mm


def rotate_fill(win, low, detail, todo, ok_src, centre, step, n):
    used = {}
    for k in range(1, n):
        for deg in (k * step, -k * step):
            rot = cv2.getRotationMatrix2D(centre, deg, 1.0)
            src = low + cv2.warpAffine(detail, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            ok = cv2.warpAffine(ok_src.astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            if take.any():
                used["%d deg" % deg] = int(take.sum())
        if not todo.any():
            break
    return used


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    shape = img.shape[:2]
    R = int(math.ceil((t["rings_mm"]["insert_outer"] + 0.2) * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    feat = feature_mask(t, shape)[sl]
    corridor = hand_mask(t, shape, margin=CORRIDOR_MM)[sl]
    lit = cv2.dilate((win.max(axis=2) > 30).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    sub = disc(t, shape, t["sub24"]["centre_mm"], t["sub24"]["radius_mm"] + 0.3)[sl]  # with its ring
    ap = disc(t, shape, t["aperture"]["centre_mm"], t["aperture"]["radius_mm"] + 0.1)[sl] & ~sub
    hands = hand_mask(t, shape)[sl] | (corridor & lit)
    dial = disc(t, shape, (0, 0), t["rings_mm"]["crystal_edge"])[sl]  # the crystal wall is round too
    mask = hands & ~feat & ~ap  # over the movement the photo's needle stays: the 3D needle covers it, inpainting smeared the movement
    bad = corridor | feat
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    detail = win.astype(np.float32) - low
    used = {}

    # 24-hour sub-dial
    sc = ((t["sub24"]["centre_mm"][0] * S + R), (-t["sub24"]["centre_mm"][1] * S + R))
    todo_sub = mask & sub
    used.update({"sub " + k: v for k, v in rotate_fill(win, low, detail, todo_sub, sub & ~bad & ~ap, sc, 45, 8).items()})

    # main dial: 6 deg rotations about the pivot on the minute track, lighting only inside it
    inner = disc(t, shape, (0, 0), TRACK_MM)[sl]
    todo = mask & ~sub & ~ap & ~inner
    ok_main = ~bad & ~sub & ~ap & dial
    used.update(rotate_fill(win, low, detail, todo, ok_main, (float(R), float(R)), 6, 30))
    rest = todo | todo_sub | (mask & ~sub & ~ap & inner)
    unfilled = int(rest.sum())
    win[rest] = np.clip(low[rest], 0, 255).astype(np.uint8)

    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "filled": used}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
