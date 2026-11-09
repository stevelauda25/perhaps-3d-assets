"""Cut a clean dial map for the SNKE61K1 from the straightened front photo, with the hands removed.

    python3 -B -m pipeline.seiko_snke61_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snke61k1/dial_photo.jpg

Same method as pipeline/seiko_snk623_dial.py, for a plain navy dial with 60 white minute-track marks: each hand pixel is
copied from the same radius 6, 12, 18 ... deg away (first source that is neither a hand nor a printed or applied part). The
day-date window is clean in the photo and stays as photographed. The hands are masked around the photographed hub
(hand_hub_px, 17 px left of the dial centre in the 3/4 photo); the copies turn about the dial centre. Square map centred on the hand pivot, out to the
crystal ring, at the photo's own resolution, light unsharp mask, JPEG. Hand zones come from config/watches/seiko-snke61k1-trace.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snke61k1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snke61k1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
MARGIN_MM = 0.3  # past each hand's traced outline: its bright edge and glow
NEEDLE_MARGIN_MM = 0.14  # seconds needle and tail: thin, little glow; keeps the print letters it crosses
SHADOWS_MM = ((0.45, -0.45), (-0.45, -0.45))  # shadows and glow fall on both sides of the hands in this photo
LOW_SIGMA_PX = 20  # lighting taken from around each hand, detail from the rotated copy
PERIOD_DEG = 6
PATTERN_OFFSET_PX = (0, 0)  # the origin is the minute-track centre
NEAR = ROOT / "outputs/watches/seiko-snke61k1/front_near_registered.png"  # second photo on the same frame (rectify step)
# print letters under the seconds needle (needle-only mask in the print box), copied from the same letter earlier in the same
# word: photo px x0, y0, x1, y1 and a source dx guess, refined +-10 px on the letter's unmasked pixels (column runs: A 977, T 1010, E 1031). Second A and T of
# AUTOMATIC from the first ones, second E of JEWELS from the first
PRINT_BOX = "print_automatic_21_jewels"
LETTER_COPIES = ((1063, 1184, 1080, 1204, -88), (1080, 1184, 1096, 1204, -72), (1073, 1205, 1090, 1230, -44))
PATCHED = ("logo_seiko", "logo_5_shield", "print_automatic_21_jewels")  # the seconds hand crosses these in the main photo
FEATURES = ("date_window", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "numeral_12", "numeral_9", "numeral_6")


def hand_mask(t, shape, shadows=SHADOWS_MM, margin=MARGIN_MM):
    S, (px0, py0) = t["scale_px_per_mm"], t["hand_hub_px"]
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    mx, my = (xx - px0) / S, -(yy - py0) / S
    m = np.zeros(shape, bool)
    for dx, dy in ((0, 0),) + shadows:
        x, y = mx - dx, my - dy
        m |= np.hypot(x, y) < t["hub_radius_mm"][0] + 0.4 + margin
        for h in t["hands"].values():
            ux, uy = math.sin(math.radians(h["angle_deg"])), math.cos(math.radians(h["angle_deg"]))
            along, across = x * ux + y * uy, np.abs(-x * uy + y * ux)
            mg = NEEDLE_MARGIN_MM if "tail_mm" in h else margin
            m |= (along > 0) & (along < h["length_mm"] + mg) & (across < h["half_width_mm"] + mg)  # leaf: widest width all along
            if "tail_mm" in h:  # seconds: tail along its own angle, lume disc at the end
                ta = math.radians(h["tail_angle_deg"])
                vx, vy = math.sin(ta), math.cos(ta)
                al, ac = x * vx + y * vy, np.abs(-x * vy + y * vx)
                m |= (al > 0) & (al < h["tail_mm"]) & (ac < h["tail_half_width_mm"] + mg)
                m |= np.hypot(x - h["tail_mm"] * vx, y - h["tail_mm"] * vy) < h["tail_disc_radius_mm"][1] + margin
    return m


def feature_mask(t, shape):
    """Printed or applied parts that must not be copied into a hand zone (kept clear by 15 px)."""
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for k in FEATURES:
        b = t[k]["x0_y0_x1_y1_mm"]
        cv2.rectangle(m, (int(px0 + b[0] * S) - 15, int(py0 - b[1] * S) - 15), (int(px0 + b[2] * S) + 15, int(py0 - b[3] * S) + 15), 1, -1)
    ix = t["indices"]
    for hr in ix["hours"]:
        a = math.radians(hr * 30)
        p0 = (int(px0 + (ix["inner_mm"] - 0.4) * S * math.sin(a)), int(py0 - (ix["inner_mm"] - 0.4) * S * math.cos(a)))
        p1 = (int(px0 + (ix["outer_mm"] + 0.4) * S * math.sin(a)), int(py0 - (ix["outer_mm"] + 0.4) * S * math.cos(a)))
        cv2.line(m, p0, p1, 1, int((ix["width_mm"] + 1.2) * S))  # with the raised baton's grey side and shadow
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    R = int(math.ceil(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    mask = hand_mask(t, img.shape[:2])[sl]
    b = t[PRINT_BOX]["x0_y0_x1_y1_mm"]  # in the print the shadow is faint: mask the needle only, keep the letters beside it
    pb = np.s_[int(R - b[1] * S) - 6:int(R - b[3] * S) + 6, int(R + b[0] * S) - 6:int(R + b[2] * S) + 6]
    mask[pb] = hand_mask(t, img.shape[:2], shadows=())[sl][pb]
    glow = cv2.dilate(mask.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)  # hand glow is never a source
    bad = glow | feature_mask(t, img.shape[:2])[sl]
    todo = mask.copy()
    c = (R + PATTERN_OFFSET_PX[0], R + PATTERN_OFFSET_PX[1])
    valid = (~bad).astype(np.float32)[..., None]
    low = None
    for sig in (3 * LOW_SIGMA_PX, LOW_SIGMA_PX):  # wide pass first: the middle of the hub zone is far from any clean pixel
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.15, est, low)
    used = {}
    for k in range(1, 15):
        for deg in (k * PERIOD_DEG, -k * PERIOD_DEG):
            rot = cv2.getRotationMatrix2D(c, deg, 1.0)
            src = cv2.warpAffine(win, rot, win.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)  # plain navy dial: copy as is
            ok = cv2.warpAffine((~bad).astype(np.uint8), rot, win.shape[1::-1], flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
            take = todo & ok
            win[take] = np.clip(src[take], 0, 255).astype(np.uint8)
            todo &= ~take
            used["%d deg" % deg] = int(take.sum())
    unfilled = int(todo.sum())  # near the pivot every rotation lands on another hand: the plain navy dial takes the local lighting
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    near = cv2.imread(str(NEAR))[sl].astype(np.float32)
    patched = 0
    for k in PATCHED:  # print and logo under a hand: take them from the second photo, matched per channel to this one
        b = t[k]["x0_y0_x1_y1_mm"]
        x0, y0 = int(R + b[0] * S) - 12, int(R - b[1] * S) - 12
        x1, y1 = int(R + b[2] * S) + 12, int(R - b[3] * S) + 12
        box = np.zeros(mask.shape, bool)
        box[y0:y1, x0:x1] = True
        ref = box & ~glow
        sel = box & mask
        if sel.any() and ref.sum() > 200:
            a_, n_ = img[sl][ref].astype(np.float32), near[ref]
            fit = (near[sel] - n_.mean(0)) / np.maximum(n_.std(0), 1) * a_.std(0) + a_.mean(0)
            win[sel] = np.clip(fit, 0, 255).astype(np.uint8)
            patched += int(sel.sum())
    copied = []
    for x0, y0, x1, y1, dx in LETTER_COPIES:
        x0, x1, y0, y1 = x0 - px0 + R, x1 - px0 + R, y0 - py0 + R, y1 - py0 + R  # photo px -> map px
        tgt, m_ = img[sl][y0:y1, x0:x1].astype(np.float32), mask[y0:y1, x0:x1]
        err = lambda d: float(np.abs(img[sl][y0:y1, x0 + d:x1 + d].astype(np.float32) - tgt)[~m_].mean())
        best = min(range(dx - 10, dx + 11), key=err)
        assert abs(best - dx) < 10, "letter copy at the search edge: %d" % best
        win[y0:y1, x0:x1][m_] = img[sl][y0:y1, x0 + best:x1 + best][m_]
        copied.append(best)
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "lighting_only_px": unfilled, "patched_from_near_px": patched, "letter_copy_dx": copied, "filled_from_deg": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2 * 1000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
