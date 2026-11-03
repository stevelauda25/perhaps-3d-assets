"""Trace the printed layers (dial text/logo/subdial numerals+scales, minute track, bezel numerals/dots/TACHYMETRE) of the Speedmaster
from Omega's straight-on front render into vector outlines in mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.watch_print [out.json] [overlay.png]

Uses the scale/centre from config/watches/speedmaster-trace.json. Excluded on purpose: lume bars/dots and their frames (modelled as geometry),
hands and sub-hands (modelled). Everything else bright on the dial or bezel is kept as printed shapes, so glyph shapes, kerning, the Omega
symbol and tick marks come from the real watch instead of a font. Output groups: `dial` (inner dial), `subdials`, `track` (minute-track ring),
`bezel`; each shape = {"outer": [[x, y]...], "holes": [[[x, y]...]]}.
Limit: where a hand overlaps print in the source image, that part of the print is absent here (the 3D hands cover the same spot).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/omega-speedmaster-310-30-42-50-01-001/hires/official_main_2000.png"
TRACE = ROOT / "config/watches/speedmaster-trace.json"
OUT = ROOT / "config/watches/speedmaster-print.json"
UP = 4  # upsampling for smooth sub-pixel contours


def shapes_from_mask(mask, to_mm, min_area_px):
    """mask (uint8 0/255, at UP scale) -> list of {"outer", "holes"} in mm using the contour hierarchy."""
    contours, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    if hier is None:
        return out
    hier = hier[0]
    for i, c in enumerate(contours):
        if hier[i][3] != -1 or cv2.contourArea(c) < min_area_px * UP * UP:
            continue
        outer = cv2.approxPolyDP(c, 0.5, True)[:, 0, :]
        holes, j = [], hier[i][2]
        while j != -1:
            if cv2.contourArea(contours[j]) >= 2 * UP * UP:
                holes.append([to_mm(p) for p in cv2.approxPolyDP(contours[j], 0.5, True)[:, 0, :]])
            j = hier[j][0]
        if len(outer) >= 3:
            out.append({"outer": [to_mm(p) for p in outer], "holes": holes})
    return out


def trace(path=FRONT, overlay=None):
    t = json.loads(TRACE.read_text())
    S, (cx, cy) = t["scale_px_per_mm"], t["centre_px"]
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    bgr = im[..., :3].astype(int)
    gray = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    yy, xx = np.mgrid[0:h, 0:w]
    rad = np.hypot(xx - cx, yy - cy) / S
    ang = np.degrees(np.arctan2(xx - cx, -(yy - cy))) % 360
    lume = ((bgr[..., 1] > bgr[..., 2] + 6) & (bgr[..., 1] > bgr[..., 0] + 10) & (gray > 120))
    lume = cv2.dilate(lume.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0  # also removes the bright rim of lume bars
    # index zones (bars + their frames): radius 12.2..15.2 mm, +-3 degrees around each hour
    near_hour = np.minimum(ang % 30, 30 - ang % 30) < 3.2
    index_zone = (rad > 12.0) & (rad < 14.9) & near_hour
    sub = [(h_[0], h_[1]) for h_ in t["subdial_hubs_xy_r_mm"]]
    sub_r = t["subdial_radius_mm"]["value"]
    in_sub = np.zeros_like(rad, dtype=bool)
    for sx, sy in sub:
        in_sub |= np.hypot((xx - cx) / S - sx, -(yy - cy) / S - sy) < sub_r + 0.2
    bright = gray > 150
    # hand zones (analytic from the traced angles/lengths): hand pixels are cut out of the print masks (the 3D hands cover the spot)
    hand_zone = np.zeros_like(rad, dtype=bool)
    for deg, length, half, tail in ((304.5, 10.6, 0.7, 2.4), (49.0, 16.2, 0.6, 2.4), (222.0, 17.0, 0.4, 5.2)):
        ux, uy = math.sin(math.radians(deg)), math.cos(math.radians(deg))
        px, py = (xx - cx) / S, -(yy - cy) / S
        along, perp = px * ux + py * uy, -px * uy + py * ux
        hand_zone |= (along > -tail) & (along < length) & (np.abs(perp) < half)
    px_, py_ = (xx - cx) / S, -(yy - cy) / S
    for hx, hy in sub:  # sub-hands all point straight up from their hubs
        hand_zone |= (np.abs(px_ - hx) < 0.16) & (py_ > hy - 0.95) & (py_ < hy + sub_r - 0.4)
    hand_core = cv2.dilate(hand_zone.astype(np.uint8), np.ones((int(0.6 * S) | 1,) * 2, np.uint8)) > 0  # slivers of hand edges
    masks = {
        "dial": bright & (rad < 14.9) & ~in_sub & ~lume & ~index_zone & ~hand_zone,
        "subdials": bright & in_sub & ~lume & ~hand_zone,
        "track": bright & (rad >= 14.9) & (rad < 16.7) & ~lume & ~hand_zone,
        "bezel": (gray > 105) & (rad >= 18.0) & (rad < 20.65),
    }
    # remove hands / sub-hands / hub: components that are long, or touch a hub, or sit at the centre
    keep = {}
    for name, m in masks.items():
        m8 = m.astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m8, connectivity=8)
        ok = np.zeros(n, dtype=bool)
        for i in range(1, n):
            x0, y0, bw, bh, area = st[i]
            length = max(bw, bh) / S
            mid = ((x0 + bw / 2 - cx) / S, -(y0 + bh / 2 - cy) / S)
            at_hub = any(math.hypot(mid[0] - sx, mid[1] - sy) < 1.2 for sx, sy in sub) or math.hypot(*mid) < 2.0
            long_thin = name in ("bezel", "track") and length > {"bezel": 5.5, "track": 3.2}[name] and (area / (bw * bh) < 0.2 or (area / (bw * bh) < 0.5 and length > 3 * min(bw, bh) / S))
            sparse_arc = name == "dial" and length > 3.5 and area / (bw * bh) < 0.14  # crystal-edge reflection arc
            in_hand = hand_core[lab == i].mean() > 0.92  # a sliver lying entirely along a hand
            big = area > (2000 if name == "track" else 15000)  # the cursive Speedmaster script is one connected shape; hands are excluded by their zones
            if area < 6 or at_hub or long_thin or big or in_hand or sparse_arc:
                continue
            ok[i] = True
        keep[name] = ok[lab]
    result = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": S, "groups": {}}
    big_view = cv2.resize(gray, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    to_mm = lambda p: [round((p[0] / UP - cx) / S, 3), round(-(p[1] / UP - cy) / S, 3)]
    ov = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR) // 3 if overlay else None
    for name, k in keep.items():
        up = cv2.resize(k.astype(np.uint8) * 255, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR)
        up = cv2.GaussianBlur(up, (0, 0), UP * 0.45)
        thr = 128
        mask = (up > thr).astype(np.uint8) * 255
        shapes = shapes_from_mask(mask, to_mm, 5)
        result["groups"][name] = shapes
        if ov is not None:
            for sh in shapes:
                pts = (np.array(sh["outer"]) * S + [cx, 0]).copy()
                pts = np.c_[np.array(sh["outer"])[:, 0] * S + cx, -np.array(sh["outer"])[:, 1] * S + cy].astype(np.int32)
                cv2.polylines(ov, [pts], True, (0, 255, 255), 1)
    if overlay:
        cv2.imwrite(str(overlay), ov[int(cy - 22 * S):int(cy + 22 * S), int(cx - 22 * S):int(cx + 22 * S)])
    return result


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, separators=(",", ":"), default=float) + "\n")
    print({k: (len(v), sum(len(s["outer"]) for s in v)) for k, v in data["groups"].items()}, "->", dest, dest.stat().st_size, "bytes")
