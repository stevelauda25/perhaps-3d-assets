"""Measure the Seiko 5 Sports SNZB26J1 front photo (white background, 2048 x 2048) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snzb26_trace [out.json] [overlay.png]     # default config/watches/seiko-snzb26j1-trace.json

Same frame as pipeline/seiko_snz450_trace.py: mm, x right, y toward 12. Anchor: case diameter 40 mm (spec sheet) across the
knurled bezel skirt. The origin is the middle of the crystal ring (the hub sits on it within 1 px). The gold-on-gold dial
defeats threshold tracing, so hands, indices, day-date, logo and crown come from gridded crops (MANUAL_PX, +-3 px = +-0.1 mm).
The bezel print is black on gold: numerals, triangles and the lume pip square are traced by threshold. The applied SEIKO and 5
shield are fitted from the SNZ450J1 trace (same applied logo, also too soft here).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_print import UP, shapes_from_mask

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snzb26j1/front_psb_2048.jpg"
OUT = ROOT / "config/watches/seiko-snzb26j1-trace.json"
CASE_MM = 40.0  # spec sheet (listings 39-42 mm); across the knurled bezel skirt
LOGO_FROM = ROOT / "config/watches/seiko-snz450j1-trace.json"
PHOTO_ROT_DEG = 0.0  # the bezel triangles sit 89.8-90.2 deg apart and the 12 marker is upright

MANUAL_PX = {
    "skirt_r_px": 526,  # knurled bezel skirt, left flank at y 1044 (x 457)
    "dial_centre": [983, 1044],  # middle of the crystal ring (x 610-1357, y 670-1418); the numeral blobs pull 5 px left
    "hub": [982, 1043],
    "hub_radius_px": [20, 6],
    "hour_hand_tip": [827, 926],
    "hour_hand_half_width_px": 20,
    "hour_hand_tail_px": 22,
    "hour_hand_black_px": [[24, 60], [108, 120]],  # black bar between the two lume windows, px from the hub
    "hour_hand_lume_px": [60, 182],
    "minute_hand_tip": [1207, 854],
    "minute_hand_half_width_px": 15,
    "minute_hand_tail_px": 22,
    "minute_hand_black_px": [[24, 55], [162, 172]],
    "minute_hand_lume_px": [55, 284],
    "seconds_hand_tip": [1052, 1340],
    "seconds_hand_half_width_px": 3,
    "seconds_disc": [942, 884, 14],  # lume disc on the counterweight end: centre x, y, radius
    "crystal_r_px": 374,  # thin gold ring round the dial
    "bezel_inner_r_px": 402,  # inner edge of the flat bezel top
    "bezel_top_r_px": 512,  # outer edge of the flat bezel top (the knurled skirt shows past it)
    "block_half_deg": 7.5,  # raised square pads under the triangles and the pip
    "block_r_px": [412, 522],
    "index_r_px": [244, 334],  # gold frame, inner and outer end
    "index_width_px": 22,
    "index_wide_px": 34,  # 6 and 9
    "marker_12": [960, 705, 1022, 815],  # double baton with a pointed outer end (tip at y 705, box from 735)
    "marker_12_tip_px": 30,
    "daydate_frame": [1102, 1003, 1308, 1095],
    "logo_seiko": [902, 857, 1070, 885],
    "logo_5_shield": [942, 900, 1027, 938],
    "print_sports": [915, 951, 1052, 975],
    "print_water_automatic_jewels": [820, 1145, 1145, 1225],
    "print_6": [820, 1375, 1145, 1410],
    "crown_box": [1503, 995, 1552, 1108],
    "case_edge_y": [455, 1636],  # lug ends at 12 and 6, outside the bracelet
    "lug_gap_mm": 0.3,  # case past the bezel skirt between the lugs
    "bracelet_edges_x": {"450": [700, 1261], "400": [719, 1257], "300": [736, 1236], "1700": [704, 1234], "1850": [723, 1201]},
    "bracelet_centre_x_300": [853, 1113],
    "bracelet_joints_y": {"outer_top": [440, 265, 90], "outer_bottom": [1650, 1810, 1985],
                          "centre_top": [290, 115], "centre_bottom": [1790, 1950]},
}
ARTEFACTS = ["bezel position as photographed: the lume pip (0) sits at 149 deg",
             "the centre bracelet links end in a shallow chevron; modelled square",
             "the knurled skirt is drawn as 120 teeth, not counted"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    fg = cv2.morphologyEx(((765 - im.astype(int).sum(2)) > 45).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)).astype(bool)
    h, w = g.shape
    M = MANUAL_PX
    yy, xx = np.mgrid[0:h, 0:w]

    # origin: circle through the bezel numeral centroids (dark blobs in the numeral band)
    hx, hy = M["hub"]
    rr0 = np.hypot(xx - hx, yy - hy)
    n, lab, st, cen = cv2.connectedComponentsWithStats(((g < 80) & (rr0 > 425) & (rr0 < 470)).astype(np.uint8))
    C = np.array([cen[i] for i in range(1, n) if st[i, 4] > 300])
    cx, cy, c = np.linalg.lstsq(np.c_[2 * C, np.ones(len(C))], (C ** 2).sum(1), rcond=None)[0]
    num_r = math.sqrt(c + cx * cx + cy * cy)
    px0, py0 = M["dial_centre"]
    S = M["skirt_r_px"] * 2 / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    pol = lambda p, o=(px0, py0): (round(math.hypot(p[0] - o[0], p[1] - o[1]) / S, 3),
                                   round(math.degrees(math.atan2(p[0] - o[0], o[1] - p[1])) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0], "hub_px": M["hub"],
           "photo_rot_deg": PHOTO_ROT_DEG, "anchor": f"knurled bezel skirt diameter = {CASE_MM} mm (spec sheet); origin = middle of the crystal ring",
           "bezel_numeral_circle_mm": round(num_r / S, 3), "crystal_ring": {"radius_mm": round(M["crystal_r_px"] / S, 3)},
           "bezel": {"inner_mm": round(M["bezel_inner_r_px"] / S, 3), "top_outer_mm": round(M["bezel_top_r_px"] / S, 3),
                     "skirt_mm": round(M["skirt_r_px"] / S, 3), "block_r_mm": [round(v / S, 3) for v in M["block_r_px"]],
                     "block_half_deg": M["block_half_deg"]}}

    # bezel print: black numerals, triangles and pip square; each shape tagged with whether it sits on a raised block
    band = (g < 80) & (rr0 > 410) & (rr0 < 505)
    n, lab, st, cen = cv2.connectedComponentsWithStats(band.astype(np.uint8))
    keep = np.zeros_like(g, np.uint8)
    blocks = []
    for i in range(1, n):
        r_, a_ = pol(cen[i])
        if st[i, 4] < 250:
            continue  # knurl shadows and specks
        keep[lab == i] = 255
        if r_ * S > 470:  # triangles and the pip square sit outside the numeral band, on the blocks
            blocks.append(a_)
    up = cv2.resize(cv2.GaussianBlur(keep, (0, 0), 0.8), None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    shapes = shapes_from_mask(((up > 127) * 255).astype(np.uint8), lambda p: mm((p[0] / UP, p[1] / UP)), 60)
    out["bezel_blocks_deg"] = sorted(round(a, 2) for a in blocks)
    out["bezel_print_shapes"] = shapes
    pip = [sh for sh in shapes if sh["holes"]]
    out["bezel_pip"] = {"centre_mm": [round(float(np.mean([p[0] for p in pip[0]["holes"][0]])), 3),
                                      round(float(np.mean([p[1] for p in pip[0]["holes"][0]])), 3)]} if pip else None

    # case outline r(angle): last foreground pixel along each ray, capped at the lug ends (12 and 6), bridged over the crown
    flat = np.mean([py0 - M["case_edge_y"][0], M["case_edge_y"][1] - py0]) / S
    r_raw = []
    for deg in range(360):
        a = math.radians(deg)
        rs = np.arange(300, 760, 0.5)
        X, Y = (px0 + rs * math.sin(a)).astype(int), (py0 - rs * math.cos(a)).astype(int)
        ok = (X >= 0) & (X < w) & (Y >= 0) & (Y < h)
        hit = np.nonzero(fg[Y[ok], X[ok]])[0]
        r = rs[ok][hit[-1]] / S if len(hit) else np.nan
        cc = abs(math.cos(a))
        if cc > 1e-3:
            r = min(r, flat / cc)
        r_raw.append(r)
    r_raw = np.array(r_raw)
    k = np.arange(360)
    crown = (k > 82) & (k < 100)
    r_raw[crown] = np.interp(k[crown], [82, 100], r_raw[[82, 100]])
    r_raw = np.maximum(r_raw, M["skirt_r_px"] / S)  # never inside the bezel skirt
    top = (r_raw + r_raw[(360 - k) % 360]) / 2  # left/right mean, then the 12 half mirrored to 6
    r_sym = np.where(k <= 90, top, np.where(k <= 180, top[(180 - k) % 360], np.where(k <= 270, top[(k - 180) % 360], top[(360 - k) % 360])))
    flat_part = np.abs(np.cos(np.radians(k))) * r_sym >= flat - 1e-6
    r_smooth = np.convolve(np.r_[r_sym[-3:], r_sym, r_sym[:3]], np.ones(7) / 7, "valid")
    r_sym = np.where(flat_part, r_sym, np.minimum(r_smooth, flat / np.maximum(np.abs(np.cos(np.radians(k))), 1e-3)))
    # between the lugs the bracelet runs up to the bezel: cut the case back to just past the skirt there
    e450 = M["bracelet_edges_x"]["450"]
    hw_case = (e450[1] - e450[0]) / 2 / S
    between = flat * np.abs(np.tan(np.radians(k))) < hw_case
    between &= np.abs(np.cos(np.radians(k))) > 0.5
    r_sym = np.where(between, M["skirt_r_px"] / S + M["lug_gap_mm"], r_sym)
    out["case_outline_r_mm"] = [round(float(v), 3) for v in r_sym]
    out["case"] = {"diameter_mm": CASE_MM, "flat_edge_y_mm": round(flat, 3), "r_at_3_mm": round(float(r_sym[90]), 3),
                   "max_r_mm": round(float(r_sym.max()), 3), "max_at_deg": int(r_sym.argmax())}

    ir = [round(v / S, 3) for v in M["index_r_px"]]
    b12 = M["marker_12"]
    out["indices"] = {"lume_inner_mm": ir[0], "lume_outer_mm": ir[1], "lume_width_mm": round(M["index_width_px"] / S, 3),
                      "wide_width_mm": round(M["index_wide_px"] / S, 3),
                      "marker_12": {"inner_mm": round((py0 - b12[3]) / S, 3), "outer_mm": round((py0 - b12[1] - M["marker_12_tip_px"]) / S, 3),
                                    "tip_mm": round((py0 - b12[1]) / S, 3), "width_mm": round((b12[2] - b12[0]) / S, 3)},
                      "layout": "gold frames with cream lume; 6 and 9 wider; double baton with a pointed end at 12; none at 3 (day-date)"}

    hub = M["hub"]
    hands = {}
    for name in ("hour", "minute"):
        r, a = pol(M[f"{name}_hand_tip"], hub)
        hands[name] = {"angle_deg": a, "angle_photo_deg": a, "length_mm": r, "tail_mm": round(M[f"{name}_hand_tail_px"] / S, 3),
                       "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3),
                       "black_from_to_mm": [[round(v / S, 3) for v in seg] for seg in M[f"{name}_hand_black_px"]],
                       "lume_from_to_mm": [round(v / S, 3) for v in M[f"{name}_hand_lume_px"]]}
    r, a = pol(M["seconds_hand_tip"], hub)
    sd = M["seconds_disc"]
    tail = pol(sd[:2], hub)[0]
    hands["seconds"] = {"angle_deg": a, "angle_photo_deg": a, "length_mm": r, "tail_mm": round(tail + sd[2] / S, 3),
                        "disc_at_mm": tail, "disc_r_mm": round(sd[2] / S, 3),
                        "half_width_mm": round(M["seconds_hand_half_width_px"] / S, 3), "tail_half_width_mm": round(sd[2] / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k_ in ("daydate_frame", "marker_12", "logo_seiko", "logo_5_shield", "print_sports", "print_water_automatic_jewels", "print_6", "crown_box"):
        out[k_] = box(M[k_])

    def fit(shapes_, b):
        """Scale and move shapes (mm) so their bounding box fills b's width, centred in b."""
        pts = np.array([p for sh in shapes_ for p in sh["outer"]])
        lo, hi = pts.min(0), pts.max(0)
        (x0, y1), (x1, y0) = mm(b[:2]), mm(b[2:])
        kk = (x1 - x0) / (hi[0] - lo[0])
        cxy = (lo + hi) / 2
        tx = lambda p: [round((p[0] - cxy[0]) * kk + (x0 + x1) / 2, 3), round((p[1] - cxy[1]) * kk + (y0 + y1) / 2, 3)]
        return [{"outer": [tx(p) for p in sh["outer"]], "holes": [[tx(p) for p in hl] for hl in sh["holes"]]} for sh in shapes_]

    src = json.loads(LOGO_FROM.read_text())
    out["logo_seiko_shapes"] = fit(src["logo_seiko_shapes"], M["logo_seiko"])
    out["logo_5_shield_shapes"] = fit(src["logo_5_shield_shapes"], M["logo_5_shield"])

    e = M["bracelet_edges_x"]
    cx3 = M["bracelet_centre_x_300"]
    out["bracelet_columns"] = {"centre_half": round((cx3[1] - cx3[0]) / (e["300"][1] - e["300"][0]), 3)}
    out["bracelet_half_width_mm"] = sorted([round(abs(int(y) - py0) / S, 3), round((x1 - x0) / 2 / S, 3)] for y, (x0, x1) in e.items())
    j = M["bracelet_joints_y"]
    r_top = lambda ys: sorted((py0 - y) / S for y in ys)
    r_bot = lambda ys: sorted((y - py0) / S for y in ys)
    ot, ob, ct, cb = r_top(j["outer_top"]), r_bot(j["outer_bottom"]), r_top(j["centre_top"]), r_bot(j["centre_bottom"])
    outer = sorted((a + b) / 2 for a, b in zip(ot, ob))
    centre = sorted((a + b) / 2 for a, b in zip(ct, cb))
    pitch = float(np.mean(np.diff(outer)))
    out["bracelet_joints_mm"] = {"outer": [round(v, 3) for v in outer], "centre": [round(v, 3) for v in centre]}
    out["bracelet_pitch_mm"] = round(pitch, 3)
    out["lug_tip_mm"] = {"mean": round(outer[0], 3), "top": round(ot[0], 3), "bottom": round(ob[0], 3),
                         "basis": "first outer-link joint: the end link ends here, the bend starts here"}
    out["bracelet_centre_phase"] = round(float(np.mean([((c_ - outer[0]) / pitch) % 1 for c_ in centre])), 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = im.copy() // 2 + 64
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        Pa = lambda r, deg, o=(px0, py0): (int(round(o[0] + r * S * math.sin(math.radians(deg)))), int(round(o[1] - r * S * math.cos(math.radians(deg)))))
        cv2.polylines(ov, [np.array([Pa(r_sym[d], d) for d in range(360)], np.int32)], True, (0, 0, 255), 3)
        for r_ in (out["crystal_ring"]["radius_mm"], out["bezel"]["inner_mm"], out["bezel"]["top_outer_mm"], out["bezel"]["skirt_mm"]):
            cv2.circle(ov, (px0, py0), int(r_ * S), (255, 128, 0), 2)
        for a in out["bezel_blocks_deg"]:
            for s_ in (-1, 1):
                cv2.line(ov, Pa(out["bezel"]["block_r_mm"][0], a + s_ * M["block_half_deg"]), Pa(out["bezel"]["block_r_mm"][1], a + s_ * M["block_half_deg"]), (0, 255, 0), 2)
        for sh in shapes:
            cv2.polylines(ov, [np.array([P(p) for p in sh["outer"]], np.int32)], True, (0, 255, 255), 1)
        for name, hd in hands.items():
            cv2.line(ov, Pa(-hd["tail_mm"], hd["angle_deg"], hub), Pa(hd["length_mm"], hd["angle_deg"], hub), (0, 255, 255), 2)
        for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11):
            cv2.line(ov, Pa(ir[0], hr * 30), Pa(ir[1], hr * 30), (255, 0, 255), 3)
        for k_ in ("daydate_frame", "marker_12", "logo_seiko", "logo_5_shield", "print_sports", "print_water_automatic_jewels", "print_6", "crown_box"):
            b = M[k_]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
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
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "origin_px", "bezel_numeral_circle_mm", "crystal_ring", "bezel", "bezel_blocks_deg",
                                           "bezel_pip", "case", "lug_tip_mm", "indices", "hands", "bracelet_columns", "bracelet_half_width_mm",
                                           "bracelet_joints_mm", "bracelet_pitch_mm", "bracelet_centre_phase")}, default=float), "->", dest)
    print("bezel print shapes:", len(data["bezel_print_shapes"]))
