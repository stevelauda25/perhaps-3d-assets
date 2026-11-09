"""Cut a clean dial map for the SNZB26J1 from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_snzb26_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snzb26j1/dial_photo.jpg

Same gold sunburst dial and method as pipeline/seiko_snz450_dial.py (hand pixels copied from the same radius 6, 12 ... deg
away). The day-date is then redrawn as MON 15 to match the target photo (front_target_1000x1672.png, Irsyad 2026-11-09).
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline import seiko_snz450_dial as base

ROOT = base.ROOT
base.TRACE = ROOT / "config/watches/seiko-snzb26j1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snzb26j1/dial_photo.jpg"
# day-date in the traced photo (px): white area inside the frame, then the target's glyph boxes placed in it by proportion
DAYDATE_INNER_PX = (1113, 1017, 1310, 1080)
DAYDATE_TEXT_PX = {"MON": (1122, 1023, 1212, 1070), "15": (1234, 1023, 1297, 1070)}
DAYDATE_DIVIDER_PX = (1221, 1019, 1224, 1078)
# shortcut: macOS system font, the closest condensed sans to the Seiko day wheel; bundle a font if this runs elsewhere
MAP_GAIN = 1.12
TARGET = "references/seiko-snzb26j1/front_target_1000x1672.png"
TARGET_HUB_PX = (468, 784)  # target photo: hub, scale (traced px per target px, from the bezel pip radius) and turn
TARGET_SCALE = 26.3 / (369 / 18.2)
TARGET_TURN_DEG = 2.2
PAPER_RGB = (240, 241, 243)  # cool white wheel as in the target photo (the traced photo is pink-tinted by the red SUN)
FONT = "/System/Library/Fonts/Supplemental/Arial Narrow.ttf"
LOGO_BOX_MM = (-9.0, 12.0, 9.0, 0.9)  # x0, y0, x1, y1: SEIKO, 5 shield, SPORTS and the hand zones above the hub


def redraw_daydate(crop, origin, ss=4):
    """Paint the window white and set the target's day and date in black at 4x, then downsample into the map (in place)."""
    from PIL import Image, ImageDraw, ImageFont
    ox, oy = origin
    x0, y0, x1, y1 = (v - o for v, o in zip(DAYDATE_INNER_PX, (ox, oy) * 2))
    tile = Image.new("RGB", ((x1 - x0) * ss, (y1 - y0) * ss), PAPER_RGB)
    d = ImageDraw.Draw(tile)
    for text, box in DAYDATE_TEXT_PX.items():
        bx0, by0, bx1, by1 = ((v - o) * ss for v, o in zip(box, (DAYDATE_INNER_PX[0], DAYDATE_INNER_PX[1]) * 2))
        font = ImageFont.truetype(FONT, int((by1 - by0) * 1.36))  # cap height of Arial Narrow is about 0.72 em
        l, t_, r, b = d.textbbox((0, 0), text, font=font)
        glyph = Image.new("L", (r - l + 4, b - t_ + 4), 0)
        ImageDraw.Draw(glyph).text((2 - l, 2 - t_), text, font=font, fill=255, stroke_width=ss // 2, stroke_fill=255)
        glyph = glyph.resize((int(bx1 - bx0), int(by1 - by0)), Image.LANCZOS)
        tile.paste((25, 25, 30), (int(bx0), int(by0)), glyph)
    dx0, dy0, dx1, dy1 = ((v - o) * ss for v, o in zip(DAYDATE_DIVIDER_PX, (DAYDATE_INNER_PX[0], DAYDATE_INNER_PX[1]) * 2))
    d.rectangle((dx0, dy0, dx1, dy1), fill=(30, 30, 30))
    crop[y0:y1, x0:x1] = np.asarray(tile.resize((x1 - x0, y1 - y0), Image.LANCZOS))[..., ::-1]


def restore_print(crop, t, origin, half_px=11):
    """The target time moves the seconds hand off the WATER 100M RESIST / AUTOMATIC / 23 JEWELS print, so the letters the
    traced photo's needle hides (M, T, L) come back from the target photo, along the needle band only (in place)."""
    img = cv2.imread(str(ROOT / t["source"]))
    S, (hx, hy) = t["scale_px_per_mm"], t["hub_px"]
    a = np.radians(t["hands"]["seconds"]["angle_photo_deg"])
    L = t["hands"]["seconds"]["length_mm"] * S
    band = np.zeros(img.shape[:2], np.uint8)
    cv2.line(band, (hx, hy), (int(hx + L * np.sin(a)), int(hy - L * np.cos(a))), 255, 2 * half_px + 1)
    paste_from_target(crop, t, origin, img, t["print_water_automatic_jewels"]["x0_y0_x1_y1_mm"], band, pad=12)


def restore_logo(crop, t, origin):
    """The copied-over hand zones smear SEIKO, the 5 shield and SPORTS (the seconds tail crosses SEIKO and is not covered
    by any hand at the target time), so every hand zone above the hub comes back from the target photo (in place)."""
    img = cv2.imread(str(ROOT / t["source"]))
    band = base.hand_mask(t, img.shape[:2]).astype(np.uint8) * 255
    paste_from_target(crop, t, origin, img, LOGO_BOX_MM, band, pad=0, local=True)


def paste_from_target(crop, t, origin, img, box_mm, band, pad, local=False):
    """Target photo affine-aligned on box_mm (ECC, band masked out), colour-matched to the traced photo outside the band,
    pasted into the band with a soft edge."""
    tgt = cv2.imread(str(ROOT / TARGET))
    S, (hx, hy) = t["scale_px_per_mm"], t["hub_px"]
    (x0, y0), (x1, y1) = [(int(round(t["origin_px"][0] + v[0] * S)), int(round(t["origin_px"][1] - v[1] * S)))
                          for v in (box_mm[:2], box_mm[2:])]
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    # first guess: scale and turn about the hubs, then refine on the print
    k, th = TARGET_SCALE, np.radians(TARGET_TURN_DEG)
    (tx, ty) = TARGET_HUB_PX
    A = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]) / k  # traced px offset -> target px offset
    W = np.c_[A, np.array([tx, ty]) - A @ np.array([hx, hy])].astype(np.float32)  # traced px -> target px
    W[:, 2] += A @ np.array([x0, y0])  # map the crop's own (0, 0) to the target
    band = band[y0:y1, x0:x1]
    keep = (band == 0).astype(np.uint8)
    # hands inpainted out of the alignment reference so ECC locks on the print, not on hands the target lacks
    ref = cv2.cvtColor(cv2.inpaint(img[y0:y1, x0:x1], band, 5, cv2.INPAINT_TELEA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    _, W = cv2.findTransformECC(cv2.GaussianBlur(ref, (0, 0), 1.0),
                                cv2.GaussianBlur(cv2.cvtColor(tgt, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0),
                                W, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
    warped = cv2.warpAffine(tgt, W, (x1 - x0, y1 - y0), flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP).astype(np.float32)
    own = img[y0:y1, x0:x1].astype(np.float32)
    m = keep.astype(bool)
    for k in ("logo_seiko", "logo_5_shield"):  # applied logos: dark in the traced photo, pale in the target, so not fitted
        bx0, by0, bx1, by1 = t[k]["x0_y0_x1_y1_mm"]
        ox_, oy_ = t["origin_px"]
        m[max(0, int(oy_ - by0 * S) - 6 - y0):max(0, int(oy_ - by1 * S) + 6 - y0),
          max(0, int(ox_ + bx0 * S) - 6 - x0):max(0, int(ox_ + bx1 * S) + 6 - x0)] = False
    for c in range(3):  # match the traced photo's levels outside the band (print and dial)
        a_, b_ = np.polyfit(warped[..., c][m], own[..., c][m], 1)
        warped[..., c] = a_ * warped[..., c] + b_
    if local:  # remaining tone difference measured just outside the band, spread smoothly across it
        ring = (cv2.dilate(band, np.ones((31, 31), np.uint8)) > 0) & m
        wr = cv2.GaussianBlur(ring.astype(np.float32), (0, 0), 15) + 1e-4
        for c in range(3):
            warped[..., c] += cv2.GaussianBlur((own[..., c] - warped[..., c]) * ring, (0, 0), 15) / wr
    w = cv2.GaussianBlur((band > 0).astype(np.float32), (0, 0), 2.0)[..., None]
    patch = np.clip(w * warped + (1 - w) * own, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(patch, (0, 0), base.SHARPEN[0])
    patch = cv2.addWeighted(patch, 1 + base.SHARPEN[1], blur, -base.SHARPEN[1], 0)
    ox, oy = origin
    crop[y0 - oy:y1 - oy, x0 - ox:x1 - ox] = patch

def build(out=OUT, review=None):
    meta = base.build(out, review)
    t = json.loads(base.TRACE.read_text())
    R = meta["size_px"] // 2
    (px0, py0) = t["origin_px"]
    im = cv2.imread(str(out))
    restore_print(im, t, (px0 - R, py0 - R))
    restore_logo(im, t, (px0 - R, py0 - R))
    im = np.clip(im.astype(np.float32) * MAP_GAIN, 0, 255).astype(np.uint8)  # the target photo's dial is brighter
    redraw_daydate(im, (px0 - R, py0 - R))
    cv2.imwrite(str(out), im, [cv2.IMWRITE_JPEG_QUALITY, base.JPEG_QUALITY])
    meta["daydate"] = " ".join(DAYDATE_TEXT_PX)
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
