"""Cut the Hamilton H82395331 / H76255810 photo maps from the front photo: dial + bezel insert (hands removed) and strap.

    python3 -B -m pipeline.hamilton_scuba_pioneer_dial <sku> [review.png]
    # -> outputs/watches/hamilton-<sku>/dial.jpg (+ .json) and strap.jpg (+ .json)

Dial map: square crop about the pivot to the bezel's polished rim, native photo resolution, from the photo as taken (the build
turns model mm into photo px with the trace's photo_rot_deg, so nothing is resampled). Hand zones (the traced outlines, grown
by HAND_MARGIN_MM, plus a short shadow down-right) are filled: inside each period band (minute track) from the same radius one
period over, elsewhere by inpainting from the edges; the modelled hands cover them from the front. Unsharp mask 1.2 / 0.6,
JPEG 93. Strap map: the columns of the photo's strap, all rows (the strap runs off the top and bottom of the photo), long side
capped at 2048 px.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
STRAP_MAX_PX = 2048
HAND_MARGIN_MM = 0.12
SHADOWS_MM = ((0.15, -0.15), (0.3, -0.3))  # light from the upper left
CFG = {
    # period bands: [r0 mm, r1 mm, deg]; the minute track repeats every hour (30 deg) between the indices
    "h82395331": {"period": [[12.6, 15.2, 30.0]], "strap_pad_px": 30, "near_mm": 0.3, "bright": 80, "print_free_mm": 12.6},
    "h32515135": {"period": [[15.2, 17.1, 30.0]], "near_mm": 0.12, "margin_mm": 0.18, "shadows_mm": [[0.1, -0.1]], "bright": 150,
                  "print_free_mm": 9.5, "rim_key": "bezel_in"},
    "h64455523": {"period": [], "strap_pad_px": 20, "near_mm": 0.15, "margin_mm": 0.25, "shadows_mm": [[0.15, -0.15]], "bright": 225,
                  "print_free_mm": 8.0, "rim_key": "bezel_in"},
    "h76419941": {"period": [[11.0, 12.5, 30.0]], "strap_pad_px": 20, "near_mm": 0.15, "margin_mm": 0.15, "shadows_mm": [[0.1, -0.1]],
                  "bright": 150, "print_free_mm": 8.0, "rim_key": "bezel_in"},
    "h36205130": {"period": [[14.7, 15.6, 30.0]], "near_mm": 0.12, "margin_mm": 0.15, "shadows_mm": [[0.1, -0.1]], "bright": 120,
                  "print_free_mm": 10.5, "rim_key": "insert_out"},
    "h70215880": {"period": [], "strap_pad_px": 20, "near_mm": 0.15, "margin_mm": 0.12, "shadows_mm": [[0.1, -0.1]], "dark_hands": True,
                  "dark": 60, "print_free_mm": 9.5, "rim_key": "bezel_in"},
    "h76255810": {"period": [[12.6, 15.15, 30.0]], "strap_pad_px": 20, "near_mm": 0.12, "margin_mm": 0.08, "shadows_mm": [[0.08, -0.08]], "dark_hands": True, "dark": 140, "print_free_mm": 9.8},
}


def rot(x, y, deg):
    t = math.radians(deg)
    return (x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))


def build(sku, review=None):
    t = json.loads((ROOT / ("config/watches/hamilton-%s-trace.json" % sku)).read_text())
    c = CFG[sku]
    S, (px0, py0), pr = t["scale_px_per_mm"], t["origin_px"], t["photo_rot_deg"]
    P = lambda x, y: (lambda q: (px0 + q[0] * S, py0 - q[1] * S))(rot(x, y, pr))
    img = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)
    if img.shape[2] == 4:  # official renders: transparent background -> white
        a = img[..., 3:4] / 255.0
        img = (img[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    out = ROOT / ("outputs/watches/hamilton-%s" % sku)
    out.mkdir(parents=True, exist_ok=True)

    # ---- hand mask in photo px ----
    mask = np.zeros(img.shape[:2], np.uint8)
    polys = []
    for h in t["hands"].values():
        polys += [part["poly_mm"] for part in h["parts"] if part["layer"] == "base"]
    for dx, dy in ((0, 0),) + tuple(c.get("shadows_mm", SHADOWS_MM)):
        for poly in polys:
            cv2.fillPoly(mask, [np.round([P(x + dx, y + dy) for x, y in poly]).astype(np.int32)], 1)
        cv2.circle(mask, tuple(int(v) for v in P(dx, dy)), int(t["hub_mm"]["disc"] * S * 1.1), 1, -1)
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(c.get("margin_mm", HAND_MARGIN_MM) * S) + 1,) * 2))
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    rr = np.hypot(xx - px0, yy - py0) / S
    # the photographed hands are a little wider than the traced outlines: add their bright / coloured pixels next to the mask,
    # inside the print-free radius (numerals and indices further out stay)
    near = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(c["near_mm"] * S) + 1,) * 2)) > 0
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    if c.get("dark_hands"):  # black hands on a light dial
        hand_px = (cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) < c["dark"]) & near & (rr < c["print_free_mm"])
    else:
        hand_px = ((img.min(2) > c["bright"]) | ((hsv[..., 1] > 110) & (hsv[..., 2] > 100))) & near & (rr < c["print_free_mm"])
    mask = (mask | cv2.dilate(hand_px.astype(np.uint8), np.ones((5, 5), np.uint8))).astype(np.uint8)
    clean = cv2.inpaint(img, mask * 255, 6, cv2.INPAINT_TELEA)
    for r0, r1, deg in c["period"]:  # same radius one period over (the source must be outside the mask)
        for sgn in (1, -1):
            Mr = cv2.getRotationMatrix2D((float(px0), float(py0)), -sgn * deg, 1.0)
            src = cv2.warpAffine(img, Mr, (img.shape[1], img.shape[0]), flags=cv2.INTER_CUBIC)
            src_ok = cv2.warpAffine(1 - mask, Mr, (img.shape[1], img.shape[0]), flags=cv2.INTER_NEAREST)
            sel = (mask > 0) & (rr >= r0) & (rr <= r1) & (src_ok > 0)
            clean[sel] = src[sel]
            mask = np.where(sel, 0, mask)

    # ---- dial map: square to the bezel rim, native resolution ----
    half = int(math.ceil(t["rings_mm"][c.get("rim_key", "rim_in")] * S)) + 12
    crop = clean[py0 - half:py0 + half, px0 - half:px0 + half]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    cv2.imwrite(str(out / "dial.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "crop_px": [px0 - half, py0 - half], "scale": 1.0, "size_px": [2 * half, 2 * half]}
    (out / "dial.json").write_text(json.dumps(meta, indent=1) + "\n")

    if "strap_mm" not in t:  # bracelet watch: no strap map
        return meta, None
    # ---- strap map: the strap's columns, all rows ----
    xs = [P(x, 0)[0] for s in t["strap_mm"].values() for x in s["x"]]
    x0, x1 = int(min(xs)) - c["strap_pad_px"], int(max(xs)) + c["strap_pad_px"]
    st = img[:, x0:x1]
    k = min(1.0, STRAP_MAX_PX / max(st.shape[:2]))
    if k < 1:
        st = cv2.resize(st, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(out / "strap.jpg"), st, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    smeta = {"source": t["source"], "crop_px": [x0, 0], "scale": round(k, 6), "size_px": list(st.shape[1::-1]),
             "photo_rows_mm": [round(py0 / S, 3), round((img.shape[0] - py0) / S, 3)]}
    (out / "strap.json").write_text(json.dumps(smeta, indent=1) + "\n")
    if review:
        R = int(16 * S)
        sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
        shown = img[sl].copy()
        m = cv2.dilate(mask, np.ones((3, 3), np.uint8))[sl] > 0
        shown[m] = (0.5 * shown[m] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, clean[sl]]))
    return meta, smeta


if __name__ == "__main__":
    print(build(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else None))
