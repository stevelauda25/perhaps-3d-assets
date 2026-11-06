"""Cut the SNZG11J1 dial map (hands removed) and the NATO strap atlas from the front photo.

    python3 -B -m pipeline.seiko_snzg11_dial [out_dir] [review.png]     # default outputs/watches/seiko-snzg11j1/

dial_photo.jpg: square crop centred on the hand pivot out to the bezel's inner edge, native resolution, light unsharp mask,
JPEG. The dial is plain navy, so each hand zone is filled with the local navy (normalised blur of clean dial pixels, print
excluded) plus grain of the same strength. Inside the traced hand outline (+0.1 mm) everything is filled; in the halo and
shadow band around it only dark pixels, so print beside a hand keeps its edge (print under a hand is hidden by the 3D hand).

strap_photo.jpg: the two strap ends straightened into one atlas, from the case edge to where each end folds into its
keeper, each row's own strap edges (between the lugs: the lug inner edges) mapped to the full width. Top half = 12 o'clock end (far end at the top row), bottom half = 6 o'clock end
(far end at the bottom row). The build mirrors the texture outside this stretch. Layout in strap_photo.json.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-snzg11j1-trace.json"
OUT = ROOT / "outputs/watches/seiko-snzg11j1"
SHARPEN = (1.2, 0.6)  # unsharp mask: blur sigma px, amount
JPEG_QUALITY = 93
CORE_MM, HALO_MM = 0.1, 0.4
SHADOW_MM = (0.25, -0.25)  # light from the upper left
PRINT_GRAY = 95  # print and hands are brighter than this; the navy dial is about 30-60
STRAP_FROM_CASE_MM = 0.5  # the strap shows between the lugs from the case edge
LUG_CLEAR_MM = 0.8  # past the slanted lug ends the row edges are the strap's own
STRAP_TO_MM = {"top": 30.0, "bottom": 33.5}  # where each end turns into its keeper fold
EDGE_INSET_MM = (0.15, 0.9)  # left, right: past the edge fibres; the right side wall shows (watch turned slightly)


def hand_polys(t):
    """Hand outlines in mm (sword hour/minute, seconds needle with its arrowhead and a 2.5 mm tail)."""
    out = []
    for name, h in t["hands"].items():
        a = math.radians(h["angle_deg"])
        ux, uy = math.sin(a), math.cos(a)
        L, hw = h["length_mm"], h["half_width_mm"]
        if name == "seconds":
            a0, a1 = h["arrow_from_to_mm"]
            local = [(-hw, -2.5), (hw, -2.5), (hw, a0), (0.42, a0), (hw, a1), (hw, L), (-hw, L), (-hw, a1), (-0.42, a0), (-hw, a0)]
        else:
            local = [(-hw, 0), (hw, 0), (hw, L - 1.1), (0, L), (-hw, L - 1.1)]
        out.append([(x * uy + y * ux, -x * ux + y * uy) for x, y in local])
    return out


def mask_mm(t, shape, grow, offset=(0, 0)):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    P = lambda p: (int(round((px0 + (p[0] + offset[0]) * S) * 4)), int(round((py0 - (p[1] + offset[1]) * S) * 4)))
    for poly in hand_polys(t):
        cv2.fillPoly(m, [np.array([P(p) for p in poly], np.int32)], 1, cv2.LINE_8, 2)
    cv2.circle(m, P((0, 0)), int(t["hub_radius_mm"][0] * S * 4), 1, -1, cv2.LINE_8, 2)
    r = max(1, int(round(grow * S)))
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))).astype(bool)


def dial_map(t, img):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    R = int(round(t["crystal_ring"]["radius_mm"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].astype(np.float32)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[sl]
    core = mask_mm(t, img.shape[:2], CORE_MM)[sl]
    halo = (mask_mm(t, img.shape[:2], HALO_MM) | mask_mm(t, img.shape[:2], HALO_MM, SHADOW_MM))[sl]
    bright = gray > PRINT_GRAY
    fill = core | (halo & ~bright)
    printed = cv2.dilate(bright.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    valid = (~(halo | printed)).astype(np.float32)[..., None]
    low = None
    for sig in (60, 20, 7):  # wide pass first: the hub zone is far from clean dial
        wgt = cv2.GaussianBlur(valid, (0, 0), sig)[..., None]
        est = cv2.GaussianBlur(win * valid, (0, 0), sig) / np.maximum(wgt, 1e-4)
        low = est if low is None else np.where(wgt > 0.2, est, low)
    clean = (valid[..., 0] > 0) & (np.hypot(*np.mgrid[-R:R, -R:R]) < 0.75 * R)
    grain = float(np.std((win - cv2.GaussianBlur(win, (0, 0), 3))[clean]))
    noise = cv2.GaussianBlur(np.random.default_rng(11).normal(0, 1, win.shape).astype(np.float32), (0, 0), 0.8)
    noise *= grain / max(float(np.std(noise)), 1e-6)
    filled = np.where(fill[..., None], low + noise, win)
    soft = cv2.GaussianBlur(fill.astype(np.float32), (0, 0), 1.2)[..., None]
    win = np.clip(soft * filled + (1 - soft) * win, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(win, (0, 0), SHARPEN[0])
    return cv2.addWeighted(win, 1 + SHARPEN[1], blur, -SHARPEN[1], 0), fill, sl, round(grain, 2)


def strap_atlas(t, img):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    body = img.mean(2) < 150  # strap body; the lugs, its lit side edge, the keepers and the background are brighter
    W = int(round(np.mean([s["x_px"][1] - s["x_px"][0] for s in t["strap"].values()])))
    s0 = t["case"]["radius_mm"] + STRAP_FROM_CASE_MM
    halves, layout = [], {}
    for side, sy in (("top", 1), ("bottom", -1)):
        n = int(round((STRAP_TO_MM[side] - s0) * S))
        s = STRAP_TO_MM[side] - np.arange(n) / S if sy > 0 else s0 + np.arange(n) / S  # far end at the atlas edge
        rows = np.round(py0 - sy * s * S).astype(int)
        gap = [p[0] for p in t["manual_px"]["lug_inner_px"][side]]  # lug inner edges: the strap shows between them
        past = t["lug_tip_mm"][side] + LUG_CLEAR_MM
        edges = np.array([gap if abs(py0 - r) / S < past else [np.nonzero(body[r])[0].min(), np.nonzero(body[r])[0].max()]
                          for r in rows], float)
        edges = np.array([np.median(edges[max(0, k - 15):k + 16], 0) for k in range(n)])  # white stars at the edge, stray fibres
        edges += [EDGE_INSET_MM[0] * S, -EDGE_INSET_MM[1] * S]
        j = (np.arange(W) + 0.5) / W
        mx = (edges[:, :1] + j[None] * (edges[:, 1:] - edges[:, :1])).astype(np.float32)
        my = np.repeat((py0 - sy * s * S)[:, None], W, 1).astype(np.float32)
        halves.append(cv2.remap(img, mx, my, cv2.INTER_CUBIC))
        layout[side] = {"s_from_mm": round(s0, 3), "s_to_mm": STRAP_TO_MM[side], "rows": n}
    f_top = layout["top"]["rows"] / (layout["top"]["rows"] + layout["bottom"]["rows"])
    return np.vstack(halves), {"size_px": [W, sum(h.shape[0] for h in halves)], "top_fraction": round(f_top, 5), **layout,
                               "v": "top: 1 - top_fraction * (s_to - s) / (s_to - s_from); "
                                    "bottom: (1 - top_fraction) * (1 - (s - s_from) / (s_to - s_from))"}


def build(out_dir=OUT, review=None):
    t = json.loads(TRACE.read_text())
    img = cv2.imread(str(ROOT / t["source"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    crop, fill, sl, grain = dial_map(t, img)
    cv2.imwrite(str(out_dir / "dial_photo.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    atlas, layout = strap_atlas(t, img)
    cv2.imwrite(str(out_dir / "strap_photo.jpg"), atlas, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    (out_dir / "strap_photo.json").write_text(json.dumps(layout, indent=1) + "\n")
    meta = {"source": t["source"], "dial_size_px": crop.shape[0], "filled_px": int(fill.sum()), "grain_std": grain, "strap": layout}
    (out_dir / "dial_photo.json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[fill] = (0.5 * shown[fill] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), np.hstack([shown, crop]))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
