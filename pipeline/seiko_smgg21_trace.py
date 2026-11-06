"""Measure the Seiko SMGG21P1 front image (official cut-out on transparency, 6432 x 6432) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.seiko_smgg21_trace [out.json] [overlay.png]     # default config/watches/seiko-smgg21p1-trace.json

Digital watch, no hands. Anchor: bezel width across the flanks (tooth tips) = 37 mm (listing, Irsyad 2026-11-06); the
listed lug to lug 43.5 mm and lug width 20 mm are reported as checks. mm, x right, y toward 12, origin = centre of the
octagon (flank width centre, insert top and bottom centre). The octagon bezel and the printed insert are described by
their support distances at 0, 45, 90 ... deg (the insert's outer edge from the blue print, the bezel's tooth tips from the
silhouette and gridded crops). The case outline is the silhouette above and below the bezel joined to the bezel octagon
inset by the notch depth, so the bezel notches on the flanks stay open. Bracelet joints and columns from gridded crops
(MANUAL_PX, +-5 px = +-0.05 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-smgg21p1/front_6432_transparent.png"
OUT = ROOT / "config/watches/seiko-smgg21p1-trace.json"
WIDTH_MM = 37.0  # listing, Irsyad 2026-11-06
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 43.5, "thickness_mm": 10.64}

MANUAL_PX = {
    # bezel tooth tips: top and bottom edges, diagonals (distance from the centre along 45 deg), from gridded crops
    "bezel_top_bottom_y": [1326, 4604],
    "bezel_diag_point": [1755, 2000],  # tooth tip on the upper left diagonal (silhouette)
    "notch": {"pitch_px": 190, "width_px": 80, "depth_px": 72},  # U slots between flat teeth (top edge and flanks, 20 px grid)
    "case_split_dy_px": 1100,
    "groove_px": 24,  # dark line between the tooth tips and the case (top edge, 20 px grid)
    "dial_radius_px": 1268,  # white dial disc inside the insert (the blue LCD frame defeats the ray search)  # above / below this the silhouette is the case block, not the bezel
    "case_ends_y": [998, 4946],
    "pusher_rows_y": [3550, 3920],
    # bracelet: brushed outer and centre links share joints at the case; the polished links' joints sit nearer the case
    "bracelet_joints_y": {"top_wide": [998, 592], "top_polished": [769, 456],
                          "bottom_wide": [4946, 5352, 5748], "bottom_polished": [5196, 5602, 5977]},
    "bracelet_columns_x": {"y5500": [2325, 2867, 2887, 3127, 3137, 3346, 3356, 3637, 3648, 4106]},
}
ARTEFACTS = ["the source is an upscaled product image (soft edges, JPEG blocks at full size); the photo map keeps its resolution",
             "the bezel's top and bottom notches lie over the case block: their spacing is taken from the flanks",
             "LCD segments, print, the insert colours and the window frame stay in the photo map"]


def octagon(d, inset=0.0):
    """Convex octagon from support distances d[k] at k * 45 deg (0 = 12 o'clock, clockwise), moved in by inset."""
    pts = []
    for k in range(8):
        a1, a2 = math.radians(45 * k), math.radians(45 * (k + 1))
        d1, d2 = d[k] - inset, d[(k + 1) % 8] - inset
        # intersection of x sin a + y cos a = d for both edges
        det = math.sin(a1) * math.cos(a2) - math.cos(a1) * math.sin(a2)
        pts.append(((d1 * math.cos(a2) - d2 * math.cos(a1)) / det, (d2 * math.sin(a1) - d1 * math.sin(a2)) / det))
    return pts


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    alpha = im[..., 3] > 128
    a = im[..., 3:4] / 255.0
    rgb = (im[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    h, w = alpha.shape
    M = MANUAL_PX
    pr0, pr1 = M["pusher_rows_y"]
    flank = [(np.nonzero(alpha[y])[0].min(), np.nonzero(alpha[y])[0].max()) for y in range(2400, 3400, 10)]
    x_left, x_right = float(min(f[0] for f in flank)), float(max(f[1] for f in flank))  # tooth tips
    S = (x_right - x_left) / WIDTH_MM
    px0 = int(round((x_left + x_right) / 2))

    # insert outer edge: blue print, rays from the centre; top/bottom fix the centre height
    b_, r_ = rgb[..., 0].astype(int), rgb[..., 2].astype(int)
    blue = (b_ - r_) > 60
    col = np.nonzero(blue[:, px0])[0]
    top, bottom = col.min(), col.max()
    py0 = int(round((top + bottom) / 2))
    out_pts = {}
    for adeg in np.arange(0, 360, 1.0):
        t = math.radians(adeg)
        rs = np.arange(900, 1900, 1.0)
        xs, ys = (px0 + rs * math.sin(t)).astype(int), (py0 - rs * math.cos(t)).astype(int)
        k = np.nonzero(blue[ys, xs])[0]
        if len(k) > 50 and k[0] < 500:
            out_pts[adeg] = (xs[k[-1]], ys[k[-1]])
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]

    def support(adeg):
        """Insert edge distance along the normal at adeg: max projection of the blue edge points within +-12 deg."""
        n = (math.sin(math.radians(adeg)), math.cos(math.radians(adeg)))
        proj = [(x - px0) * n[0] - (y - py0) * n[1] for a_, (x, y) in out_pts.items() if abs((a_ - adeg + 180) % 360 - 180) <= 12]
        return float(np.median(sorted(proj)[-8:])) / S if proj else None

    ins = [support(45 * k) for k in range(8)]
    # the left half is partly grey print (no blue edge): mirror the right half, average top and bottom
    tb = (ins[0] + ins[4]) / 2
    ins = [tb, ins[1], ins[2], ins[3], tb, ins[3], ins[2], ins[1]]
    dial_r = M["dial_radius_px"] / S

    ty, by = M["bezel_top_bottom_y"]
    dx, dy = M["bezel_diag_point"]
    diag = ((px0 - dx) + (py0 - dy)) / math.sqrt(2) / S
    side = (x_right - x_left) / 2 / S
    bez = [(py0 - ty) / S, diag, side, diag, (by - py0) / S, diag, side, diag]
    tb = (bez[0] + bez[4]) / 2  # top and bottom averaged (the photo is about 0.3 mm taller toward 12)
    bez[0] = bez[4] = tb
    nt = M["notch"]
    notch = {"pitch_mm": round(nt["pitch_px"] / S, 3), "width_mm": round(nt["width_px"] / S, 3), "depth_mm": round(nt["depth_px"] / S, 3)}

    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"bezel width across the flanks (tooth tips) = {WIDTH_MM} mm (listing)",
           "bezel_support_mm": [round(v, 3) for v in bez], "insert_support_mm": [round(v, 3) for v in ins],
           "dial_radius_mm": round(dial_r, 3), "notch": notch}

    # case outline: silhouette beyond the split rows, joined to the bezel octagon inset by the notch depth
    c0, c1 = M["case_ends_y"]
    sp = M["case_split_dy_px"]
    mask = np.zeros((h, w), np.uint8)
    rows = np.zeros((h, w), bool)
    rows[c0:py0 - sp] = True
    rows[py0 + sp:c1 + 1] = True
    mask[alpha & rows] = 1
    oct_px = [(px0 + x * S, py0 - y * S) for x, y in octagon(bez, notch["depth_mm"] + 0.05)]
    cv2.fillPoly(mask, [np.round(oct_px).astype(np.int32)], 1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cmax = max(cs, key=cv2.contourArea)
    cmax = cv2.approxPolyDP(cmax, 2.0, True)[:, 0]
    out["case_outline_mm"] = [mm(p) for p in cmax]
    # dark gap between the case and the bezel: a line just outside the tooth tips, and the floor seen in the notches;
    # clipped to the case so it never shows past the silhouette on the flanks
    gm = np.zeros((h, w), np.uint8)
    cv2.fillPoly(gm, [np.round([(px0 + x * S, py0 - y * S) for x, y in octagon(bez, -M["groove_px"] / S)]).astype(np.int32)], 1)
    gm &= mask
    gs, _ = cv2.findContours(gm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out["groove_outline_mm"] = [mm(p) for p in cv2.approxPolyDP(max(gs, key=cv2.contourArea), 2.0, True)[:, 0]]
    tips = [(py0 - c0) / S, (c1 - py0) / S]
    out["case_end_mm"] = {"top": round(tips[0], 3), "bottom": round(tips[1], 3), "mean": round(sum(tips) / 2, 3)}

    # pushers: rows where the silhouette sticks out past the bezel flanks
    pl = [np.nonzero(alpha[y])[0].min() for y in range(pr0, pr1)]
    prr = [np.nonzero(alpha[y])[0].max() for y in range(pr0, pr1)]
    ys_l = [y for y, x in zip(range(pr0, pr1), pl) if x < x_left - 3]
    ys_r = [y for y, x in zip(range(pr0, pr1), prr) if x > x_right + 3]
    push = {}
    for name, ys_, ext in (("left", ys_l, (min(pl) - px0) / S), ("right", ys_r, (max(prr) - px0) / S)):
        yc = (min(ys_) + max(ys_)) / 2
        push[name] = {"centre_y_mm": round(-(yc - py0) / S, 3), "half_height_mm": round((max(ys_) - min(ys_)) / 2 / S, 3), "end_x_mm": round(ext, 3),
                      "angle_deg": round(math.degrees(math.atan2(ext, -(yc - py0) / S)) % 360, 2)}
    out["pushers"] = push

    prof = []
    for y_mm in np.arange(-36, 36.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(alpha[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    t = out["case_end_mm"]["mean"]
    near = [width[y] for y in width if t + 0.5 <= abs(y) <= t + 2]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_case_mm": round(float(np.median(near)), 2), "listed": LISTED}

    j = M["bracelet_joints_y"]
    pitch = [abs(a_ - b2) / S for js in j.values() for a_, b2 in zip(js[1:], js[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.median(pitch)), 3)
    jm = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    out["bracelet_joints_mm"] = jm
    shift = [jm["top_wide"][1] - jm["top_polished"][0], jm["bottom_wide"][1] - jm["bottom_polished"][0], jm["bottom_wide"][2] - jm["bottom_polished"][1]]
    out["bracelet_polished_joint_shift_mm"] = round(float(np.mean(shift)), 3)
    xs = M["bracelet_columns_x"]["y5500"]
    hw = (xs[-1] - xs[0]) / 2
    # symmetric: centre column half width, outer edge of the polished columns, as fractions of the half width
    out["bracelet_column_fractions"] = {"centre_half": round((xs[5] - xs[4]) / 2 / hw, 3),
                                        "polished_outer": round(1 - ((xs[1] - xs[0]) + (xs[-1] - xs[-2])) / 2 / hw, 3)}

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for d, col_ in ((bez, (0, 0, 255)), (ins, (255, 255, 0))):
            cv2.polylines(ov, [np.array([P(p) for p in octagon(d)], np.int32)], True, col_, 4)
        cv2.circle(ov, (px0, py0), int(dial_r * S), (0, 255, 255), 4)
        cv2.polylines(ov, [np.array([P(p) for p in out["case_outline_mm"]], np.int32)], True, (0, 255, 0), 4)
        cv2.polylines(ov, [np.array([P(p) for p in out["groove_outline_mm"]], np.int32)], True, (255, 0, 255), 3)
        for k, v in push.items():
            cv2.circle(ov, P((v["end_x_mm"], v["centre_y_mm"])), 20, (255, 0, 255), 6)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "origin_px", "bezel_support_mm", "insert_support_mm", "dial_radius_mm", "notch",
                                           "case_end_mm", "pushers", "checks", "bracelet_pitch_mm", "bracelet_joints_mm",
                                           "bracelet_polished_joint_shift_mm", "bracelet_column_fractions")}, default=float), "->", dest)
