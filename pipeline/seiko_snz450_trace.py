"""Measure the Seiko 5 SNZ450J1 front photo (white background, 2510 x 2492) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snz450_trace [out.json] [overlay.png]     # default config/watches/seiko-snz450j1-trace.json

Same frame as pipeline/seiko_snkl50_trace.py: mm, x right, y toward 12. Anchor: case width on the flanks = 38.0 mm (Irsyad).
The gold-on-gold dial defeats threshold tracing, so hands, day-date, logo and crown come from gridded crops (MANUAL_PX, +-3 px =
+-0.1 mm). The photo is turned about 2 deg and slightly tilted: the dial origin is the circle through the lume of the indices,
the hands are read from the visible hub, and every photo angle is turned back by PHOTO_ROT_DEG. The case is not round: its
outline is r(angle) from the silhouette, averaged over the four quadrants (top/bottom differ by the tilt).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_print import UP, shapes_from_mask

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snz450j1/front_2510.png"
OUT = ROOT / "config/watches/seiko-snz450j1-trace.json"
CASE_MM = 38.0  # Irsyad, 2026-11-06 (listings: 38 mm)
# The applied SEIKO and 5 shield are gold on gold and too soft here to trace: SEIKO is traced from the SNKL50K1 photo (gold on
# black, same applied logo) and the shield is the SNK607K1 trace, each fitted to this photo's logo box by width.
LOGO_SEIKO_FROM = (ROOT / "references/seiko-snkl50k1/front_4520.png", (2068, 1760, 2432, 1850), 120)  # photo, crop, gray threshold
SHIELD_FROM = ROOT / "config/watches/seiko-snk607k1-trace.json"
PHOTO_ROT_DEG = -2.0  # photo angle = true angle + this (indices 4, 5, 7, 8, 9, 11 sit 1.1-2.8 deg short)

MANUAL_PX = {
    "case_flanks_x": [578, 1876],  # left flank, right flank under the crown (y 1180-1240)
    "case_edge_y": [548, 1700],  # flat top and bottom edges, shoulder to shoulder, where the flared first links leave the case
    "hub": [1230, 1106],  # visible hand pivot (sits higher than the dial: about 10 px above the index circle centre)
    "hour_hand_tip": [1005, 955],
    "hour_hand_tail_end": [1298, 1168],
    "hour_hand_half_width_px": 20,
    "hour_hand_black_px": [[35, 98], [205, 268]],  # black inlays along the hand, px from the hub
    "minute_hand_tip": [1596, 951],
    "minute_hand_tail_end": [1158, 1140],
    "minute_hand_half_width_px": 18,
    "minute_hand_black_px": [[80, 125], [320, 390]],
    "seconds_photo_deg": 111.5,  # thin gold needle through the hub, read along (1300, 1140)-(1490, 1215); its shadow runs 20 px lower
    "seconds_hand_length_px": 395,
    "seconds_hand_tail_px": 205,  # long counterweight end at (1060, 1000)
    "seconds_hand_half_width_px": [9, 9],  # needle with its bright edges; its shadow runs close below
    "hub_radius_px": [22, 6],
    "daydate_frame": [1395, 1072, 1632, 1160],  # gold frame round both white windows
    "marker_12": [1198, 712, 1264, 836],  # pentagon pointing to the centre, lume inside
    "logo_seiko": [1125, 878, 1335, 925],
    "logo_5_shield": [1185, 925, 1285, 990],
    "print_sports": [1140, 995, 1330, 1035],
    "print_water_automatic_jewels": [1030, 1235, 1450, 1340],
    "print_6": [1050, 1500, 1400, 1530],
    "crown_box": [1855, 1045, 1960, 1210],
    "crystal_r_px": 421,  # inner edge of the polished bezel (dial edge), from the index circle centre
    "bezel_r_px": 458,  # outer edge of the polished bezel ring
    # sculpted case top: pointed claws (centre of the claw) and teardrop scoops (centre of the dip)
    "claws": [[930, 640], [1530, 645], [1530, 1565], [930, 1565], [690, 1105], [1740, 1105]],
    "scoops": [[1231, 610], [1231, 1640], [700, 850], [700, 1350], [1760, 850], [1760, 1350]],
    # bracelet: outer edges in the narrow part, centre column edges, joints (rows at 12 and at 6)
    "bracelet_row_200": {"edges": [945, 1500], "centre": [1100, 1350]},
    "bracelet_joints_y": {"outer_top": [495, 245], "outer_bottom": [1845, 2100, 2350],
                          "centre_top": [400, 155], "centre_bottom": [1950, 2190]},
}
ARTEFACTS = ["white glare on the left flank and the bezel: reflections, not shape",
             "the photo is soft (upscaled): small print and minute numerals are blurred",
             "the case top sits higher than the bracelet: the 12 side end link is mostly hidden, the 6 side shows 4 mm; joints averaged"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    fg = cv2.morphologyEx(((765 - im.astype(int).sum(2)) > 45).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)).astype(bool)
    lume = (hsv[..., 1] < 70) & (hsv[..., 2] > 200)
    h, w = fg.shape
    M = MANUAL_PX
    S = (M["case_flanks_x"][1] - M["case_flanks_x"][0]) / CASE_MM
    yy, xx = np.mgrid[0:h, 0:w]

    # dial origin: circle through the lume centroids of the clean indices (4, 5, 7, 8, 9, 11; the others are under hands or glare)
    hx, hy = M["hub"]
    r_hub, a_hub = np.hypot(xx - hx, hy - yy), np.degrees(np.arctan2(xx - hx, hy - yy)) % 360
    cen = []
    for hr in (4, 5, 7, 8, 9, 11):
        m = lume & (np.abs((a_hub - hr * 30 + 180) % 360 - 180) < 9) & (r_hub > 320) & (r_hub < 420)
        cen.append((xx[m].mean(), yy[m].mean()))
    C = np.array(cen)
    cx, cy, c = np.linalg.lstsq(np.c_[2 * C, np.ones(len(C))], (C ** 2).sum(1), rcond=None)[0]
    ring_r = math.sqrt(c + cx * cx + cy * cy)
    px0, py0 = int(round(cx)), int(round(cy))
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    true = lambda deg: round((deg - PHOTO_ROT_DEG) % 360, 2)
    pol = lambda p, o=(px0, py0): (round(math.hypot(p[0] - o[0], p[1] - o[1]) / S, 3),
                                   true(math.degrees(math.atan2(p[0] - o[0], o[1] - p[1])) % 360))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0], "hub_px": M["hub"],
           "photo_rot_deg": PHOTO_ROT_DEG,
           "anchor": f"case width on the flanks = {CASE_MM} mm (Irsyad); origin = circle through the index lume",
           "index_circle_mm": round(ring_r / S, 3),
           "crystal_ring": {"radius_mm": round(M["crystal_r_px"] / S, 3)}, "bezel_outer_mm": round(M["bezel_r_px"] / S, 3)}

    # case outline r(true angle): last case pixel along each ray, bridged across the crown (75-110 deg). The bracelet goes on
    # past the case, so rays are capped at 12 and 6 by the flat edge (the flared first link's corners reach down beside the
    # shoulders: they are bracelet, not case). Top and bottom differ by the tilt (the 6 side shows more end link), so the cap is
    # the mean of both sides and only the upper half is traced, mirrored left/right and to the 6 side; 7 deg running mean.
    flat = (np.mean([py0 - M["case_edge_y"][0], M["case_edge_y"][1] - py0])) / S
    r_raw = []
    for deg in range(360):
        a = math.radians(deg + PHOTO_ROT_DEG)
        sx, sy = math.sin(a), -math.cos(a)
        rs = np.arange(300, 760, 0.5)
        X, Y = (px0 + rs * sx).astype(int), (py0 + rs * sy).astype(int)
        ok = (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
        hit = np.nonzero(fg[Y[ok], X[ok]])[0]
        r = rs[ok][hit[-1]] / S if len(hit) else np.nan
        c = abs(math.cos(math.radians(deg)))
        if c > 1e-3:
            r = min(r, flat / c)
        r_raw.append(r)
    r_raw = np.array(r_raw)
    crown = (np.arange(360) > 75) & (np.arange(360) < 110)
    r_raw[crown] = np.interp(np.arange(360)[crown], [75, 110], r_raw[[75, 110]])
    k = np.arange(360)
    top = (r_raw + r_raw[(360 - k) % 360]) / 2  # valid for 0-90 deg (upper right) after mirroring the upper left in
    r_sym = np.where(k <= 90, top, np.where(k <= 180, top[(180 - k) % 360], np.where(k <= 270, top[(k - 180) % 360], top[(360 - k) % 360])))
    flat_part = np.abs(np.cos(np.radians(k))) * r_sym >= flat - 1e-6  # keep the straight edge straight
    r_smooth = np.convolve(np.r_[r_sym[-3:], r_sym, r_sym[:3]], np.ones(7) / 7, "valid")
    r_sym = np.where(flat_part, r_sym, np.minimum(r_smooth, flat / np.maximum(np.abs(np.cos(np.radians(k))), 1e-3)))
    out["case_outline_r_mm"] = [round(float(v), 3) for v in r_sym]
    out["case"] = {"width_flanks_mm": CASE_MM, "flat_edge_y_mm": round(flat, 3), "r_at_12_mm": round(float(r_sym[0]), 3), "r_at_3_mm": round(float(r_sym[90]), 3),
                   "max_r_mm": round(float(r_sym.max()), 3), "max_at_deg": int(r_sym.argmax())}
    out["claws_r_deg"] = [pol(p) for p in M["claws"]]
    out["scoops_r_deg"] = [pol(p) for p in M["scoops"]]

    # indices: lume run along each hour ray (from the dial origin, photo angle), outer and inner radius and width
    r_o, a_o = np.hypot(xx - px0, py0 - yy), np.degrees(np.arctan2(xx - px0, py0 - yy)) % 360
    idx = {}
    for hr in (4, 5, 7, 8, 9, 11):
        m = lume & (np.abs((a_o - (hr * 30 + PHOTO_ROT_DEG) + 180) % 360 - 180) < 9) & (r_o > 280) & (r_o < 450)
        rr, across = r_o[m], r_o[m] * np.radians((a_o[m] - (hr * 30 + PHOTO_ROT_DEG) + 180) % 360 - 180)
        idx[str(hr)] = {"inner": round(float(np.percentile(rr, 2)) / S, 3), "outer": round(float(np.percentile(rr, 98)) / S, 3),
                        "width": round(float(np.percentile(across, 98) - np.percentile(across, 2)) / S, 3)}
    med = lambda key: round(float(np.median([v[key] for v in idx.values()])), 3)
    b12 = M["marker_12"]
    out["indices"] = {"per_hour_lume_mm": idx, "lume_inner_mm": med("inner"), "lume_outer_mm": med("outer"), "lume_width_mm": med("width"),
                      "marker_12": {"inner_mm": round((py0 - b12[3]) / S, 3), "outer_mm": round((py0 - b12[1]) / S, 3),
                                    "width_mm": round((b12[2] - b12[0]) / S, 3)},
                      "layout": "applied gold batons with white lume (none at 3: day-date); pentagon marker at 12 pointing to the centre"}

    hub = M["hub"]
    hands = {}
    for name in ("hour", "minute"):
        r, a = pol(M[f"{name}_hand_tip"], hub)
        hands[name] = {"angle_deg": a, "angle_photo_deg": round((a + PHOTO_ROT_DEG) % 360, 2), "length_mm": r,
                       "tail_mm": pol(M[f"{name}_hand_tail_end"], hub)[0], "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3),
                       "black_from_to_mm": [[round(v / S, 3) for v in seg] for seg in M[f"{name}_hand_black_px"]]}
    wn, wc = M["seconds_hand_half_width_px"]
    hands["seconds"] = {"angle_deg": true(M["seconds_photo_deg"]), "angle_photo_deg": M["seconds_photo_deg"],
                        "length_mm": round(M["seconds_hand_length_px"] / S, 3), "tail_mm": round(M["seconds_hand_tail_px"] / S, 3),
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k_ in ("daydate_frame", "marker_12", "logo_seiko", "logo_5_shield", "print_sports", "print_water_automatic_jewels", "print_6", "crown_box"):
        out[k_] = box(M[k_])

    def fit(shapes, b):
        """Scale and move shapes (mm, any frame) so their bounding box fills b's width, centred in b."""
        pts = np.array([p for sh in shapes for p in sh["outer"]])
        lo, hi = pts.min(0), pts.max(0)
        (x0, y1), (x1, y0) = mm(b[:2]), mm(b[2:])
        k = (x1 - x0) / (hi[0] - lo[0])
        cxy = ((lo + hi) / 2)
        tx = lambda p: [round((p[0] - cxy[0]) * k + (x0 + x1) / 2, 3), round((p[1] - cxy[1]) * k + (y0 + y1) / 2, 3)]
        return [{"outer": [tx(p) for p in sh["outer"]], "holes": [[tx(p) for p in hl] for hl in sh["holes"]]} for sh in shapes]

    src, (cx0, cy0, cx1, cy1), thr = LOGO_SEIKO_FROM
    g_ = cv2.cvtColor(cv2.imread(str(src))[cy0:cy1, cx0:cx1], cv2.COLOR_BGR2GRAY)
    up = cv2.resize(cv2.GaussianBlur(g_, (0, 0), 0.8), None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    letters = shapes_from_mask((up > thr).astype(np.uint8) * 255, lambda p: [p[0] / UP, -p[1] / UP], 40)
    out["logo_seiko_shapes"] = fit(letters, M["logo_seiko"])
    out["logo_5_shield_shapes"] = fit(json.loads(SHIELD_FROM.read_text())["logo_5_shield_shapes"], M["logo_5_shield"])

    row = M["bracelet_row_200"]
    out["bracelet_columns"] = {"centre_half": round((row["centre"][1] - row["centre"][0]) / (row["edges"][1] - row["edges"][0]), 3),
                               "width_mm": round((row["edges"][1] - row["edges"][0]) / S, 3), "basis": "row at y = 200 px"}
    j = M["bracelet_joints_y"]
    r_top = lambda ys: sorted((py0 - y) / S for y in ys)
    r_bot = lambda ys: sorted((y - py0) / S for y in ys)
    ot, ob, ct, cb = r_top(j["outer_top"]), r_bot(j["outer_bottom"]), r_top(j["centre_top"]), r_bot(j["centre_bottom"])
    shift = (ob[0] - ot[0]) / 2  # the case hides more of the 12 side: average the two sides
    outer = [round(v, 3) for v in sorted([v + shift for v in ot] + [v - shift for v in ob])]
    centre = [round(v, 3) for v in sorted([v + shift for v in ct] + [v - shift for v in cb])]
    pitch = float(np.median(np.diff(sorted(ob))))
    out["bracelet_joints_mm"] = {"outer": outer, "centre": centre, "side_shift_mm": round(shift, 3)}
    out["bracelet_pitch_mm"] = round(pitch, 3)
    out["lug_tip_mm"] = {"mean": round((ot[0] + ob[0]) / 2, 3), "top": round(ot[0], 3), "bottom": round(ob[0], 3),
                         "basis": "first outer-link joint: the end link ends here, the bend starts here"}
    out["bracelet_centre_phase"] = round(float(np.mean([((c_ - outer[0]) / pitch) % 1 for c_ in centre])), 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = im.copy() // 2 + 64
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        Pa = lambda r, deg, o=(px0, py0): (int(round(o[0] + r * S * math.sin(math.radians(deg + PHOTO_ROT_DEG)))),
                                           int(round(o[1] - r * S * math.cos(math.radians(deg + PHOTO_ROT_DEG)))))
        pts = np.array([Pa(r_sym[d], d) for d in range(360)], np.int32)
        cv2.polylines(ov, [pts], True, (0, 0, 255), 3)
        for r_ in (out["crystal_ring"]["radius_mm"], out["bezel_outer_mm"]):
            cv2.circle(ov, (px0, py0), int(r_ * S), (255, 128, 0), 2)
        for name, hd in hands.items():
            cv2.line(ov, Pa(-hd["tail_mm"], hd["angle_deg"], hub), Pa(hd["length_mm"], hd["angle_deg"], hub), (0, 255, 255), 2)
        for hr in range(1, 13):
            if hr != 3 and hr != 12:
                cv2.line(ov, Pa(out["indices"]["lume_inner_mm"], hr * 30), Pa(out["indices"]["lume_outer_mm"], hr * 30), (255, 0, 255), 3)
        for k_ in ("daydate_frame", "marker_12", "logo_seiko", "logo_5_shield", "print_sports", "print_water_automatic_jewels", "print_6", "crown_box"):
            b = M[k_]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        for p in M["claws"]:
            cv2.drawMarker(ov, tuple(p), (0, 255, 0), cv2.MARKER_TRIANGLE_UP, 40, 3)
        for p in M["scoops"]:
            cv2.drawMarker(ov, tuple(p), (255, 255, 0), cv2.MARKER_CROSS, 40, 3)
        for v in outer:
            for sy in (1, -1):
                cv2.line(ov, P((-9, sy * v)), P((-5, sy * v)), (0, 255, 0), 3)
        for v in centre:
            for sy in (1, -1):
                cv2.line(ov, P((-3, sy * v)), P((3, sy * v)), (255, 0, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "origin_px", "index_circle_mm", "crystal_ring", "case", "lug_tip_mm",
                                           "indices", "hands", "bracelet_columns", "bracelet_joints_mm", "bracelet_pitch_mm",
                                           "bracelet_centre_phase")}, default=float), "->", dest)
