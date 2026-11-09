"""Measure the Seiko 5 SNKE61K1 front photo, straightened by pipeline/seiko_snke61_rectify.py, into mm. Host-side, numpy +
OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snke61_rectify          # first: outputs/watches/seiko-snke61k1/front_rectified.png
    python3 -B -m pipeline.seiko_snke61_trace [out.json] [overlay.png]     # default config/watches/seiko-snke61k1-trace.json

Same method as pipeline/seiko_snk623_trace.py. Anchor: case width on the left flank = 38 mm (owner's spec sheet); the case is
taken as concentric with the crystal ring (the right flank shows the case side and crown). The spec sheet's 18 mm lug width
is reported as a check against the bracelet between the lugs. mm, x right, y toward 12. Origin = the minute-track centre
(the dial plane): the raised hands sit 17 px left of it in the 3/4 photo, so their angles and lengths are measured from the
photographed hub (hand_hub_px). Hands, windows, logo, numerals, crown and bracelet come from gridded crops (MANUAL_PX,
+-3 px = +-0.11 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "outputs/watches/seiko-snke61k1/front_rectified.png"
OUT = ROOT / "config/watches/seiko-snke61k1-trace.json"
CASE_MM = 38.0  # owner's spec sheet, 2026-11-09
LUG_WIDTH_MM = 18.0  # spec sheet: reported as a check against the bracelet between the lugs

MANUAL_PX = {
    "dial_centre": [1050, 1050],  # minute-track centre from the rectify step
    "hand_hub_px": [1033, 1045],  # hole in the hub cap as photographed (raised: parallax)
    # hour and minute: steel leaf hands with a lume insert, widest near the middle; seconds: needle, lume disc on the tail
    "hour_hand_tip": [860, 931],
    "hour_hand_half_width_px": 19,
    "hour_hand_root_half_width_px": 8,
    "hour_hand_widest_at": 0.4,
    "hour_hand_lume_from_to": [0.2, 0.85],
    "minute_hand_tip": [1292, 859],
    "minute_hand_half_width_px": 17,
    "minute_hand_root_half_width_px": 7,
    "minute_hand_widest_at": 0.42,
    "minute_hand_lume_from_to": [0.2, 0.87],
    "seconds_hand_tip": [1125, 1349],
    "seconds_hand_tail_disc": [979, 883],
    "seconds_hand_half_width_px": [3, 4.5],  # needle, tail
    "seconds_tail_disc_radius_px": [12, 16],  # lume, steel rim
    "seconds_red_tip_from": 0.62,  # orange-yellow tip as photographed
    "hub_radius_px": [16, 4],  # cap, hole
    "date_window": [1177, 1014, 1382, 1084],  # day-date window with a steel frame at 3: stays in the dial map
    "logo_seiko": [965, 856, 1129, 886],
    "logo_5_shield": [1001, 899, 1095, 949],
    "print_automatic_21_jewels": [975, 1182, 1125, 1229],
    "numeral_12": [982, 732, 1121, 829],  # printed lume numerals
    "numeral_9": [746, 1003, 821, 1100],
    "numeral_6": [1013, 1271, 1089, 1368],
    "crown_box": [1493, 1183, 1610, 1310],  # fluted steel crown at about 3:40
    "index_inner_outer_px": [226.5, 312],  # radial ends from the dial centre (10, 11, 4 and 5 agree within 4 px)
    "index_width_px": 17,  # applied steel batons with a lume insert at 1, 2, 4, 5, 7, 8, 10, 11
    "ring_radii_px": {"dial_edge": 372, "gasket": 415},  # navy dial ends; grey rehaut to 406; dark gasket; grey bezel slope
    # bracelet: three columns between the lugs; an end link fills the gap between the case and the lug tips
    "bracelet_centre_x": [1046, 1083],  # top, bottom (the lower bracelet leans toward the camera)
    "bracelet_edges_x": {"top": [787, 1305], "bottom": [822, 1344]},  # inner edges of the lugs
    "bracelet_column_gaps_x": {"top": [960, 1200], "bottom": [950, 1206]},
    "lug_tip_y": [462, 1644],  # top, bottom
    "bracelet_joints_y": {"top_centre": [340, 170], "bottom_centre": [1791, 1972], "top_outer": [440, 240], "bottom_outer": [1672, 1889]},
}
ARTEFACTS = ["bright arcs on the polished bezel, case and bracelet: reflections, not shape",
             "straightened from a 3/4 photo turned toward the crown: case, bracelet and hands stand off the dial plane and keep some parallax (hub 17 px left of the dial centre, lower bracelet 37 px right)",
             "bracelet rows past the first joint lean away from the camera: pitch from the first rows only"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 1)
    fg = (765 - im.astype(int).sum(2)) > 45
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["dial_centre"]
    hx, hy = M["hand_hub_px"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    edge = []  # case outline on the left flank
    for a in np.arange(250, 290.1, 1.0):
        rs = np.arange(440, 700, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ring = []  # crystal ring: dark gasket line, skipping the crown side
    for a in np.arange(0, 360, 2.0):
        if 60 <= a <= 150:
            continue
        r0 = M["ring_radii_px"]["gasket"] - 12
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(r0, r0 + 24, 0.5)]
        ring.append(at(r0 + 0.5 * int(np.argmin(prof)), a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    ccx, ccy = rcx, rcy
    case_r = float(np.median(np.hypot(*(np.array(edge) - (ccx, ccy)).T)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "hand_hub_px": [hx, hy],
           "anchor": f"case width on the left flank = {CASE_MM} mm (spec sheet); bracelet between the lugs vs the listed {LUG_WIDTH_MM} mm lug width as a check",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "dark gasket line outside the grey rehaut"},
           "dial_edge_mm": round(M["ring_radii_px"]["dial_edge"] / S, 3)}

    # silhouette per y: left side mirrored, from the case centre on the case, blending to the bracelet centre at the lugs
    bxs = M["bracelet_centre_x"]
    tips = [(py0 - M["lug_tip_y"][0]) / S, (M["lug_tip_y"][1] - py0) / S]
    R = case_r / S
    prof = []
    for y_mm in np.arange(-26, 26.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                k = min(max((abs(y_mm) - 0.5 * R) / (0.5 * R), 0.0), 1.0)
                cx_ = ccx + k * ((bxs[0] if y_mm > 0 else bxs[1]) - ccx)
                l_ = round((xs.min() - cx_) / S, 3)
                prof.append([round(float(y_mm), 2), l_, -l_])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    circ = lambda y: 2 * math.sqrt(max(R * R - y * y, 0))
    lug_from = [next(y for y in np.arange(5, 20, 0.25) if width[round(sy * y, 2)] > circ(y) + 0.3) for sy in (1, -1)]
    out["lug_from_y_mm"] = round(sum(lug_from) / 2, 3)
    out["lug_tip_mm"] = {"top": round(tips[0], 3), "bottom": round(tips[1], 3), "mean": round(sum(tips) / 2, 3)}
    halves = [(e[1] - e[0]) / 2 / S for e in M["bracelet_edges_x"].values()]
    half = sum(halves) / 2
    centre = [(gp[1] - gp[0]) / S for gp in M["bracelet_column_gaps_x"].values()]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_width_mm": round(2 * half, 2),
                     "listed_lug_width_mm": LUG_WIDTH_MM, "centre_link_mm": round(sum(centre) / 2, 2)}
    out["bracelet_half_width_mm"] = round(half, 3)

    r0, r1 = (v / S for v in M["index_inner_outer_px"])
    out["indices"] = {"inner_mm": round(r0, 3), "outer_mm": round(r1, 3), "width_mm": round(M["index_width_px"] / S, 3),
                      "hours": [1, 2, 4, 5, 7, 8, 10, 11],
                      "layout": "applied steel batons with a lume insert at 1, 2, 4, 5, 7, 8, 10, 11; printed lume 12, 9, 6; day-date at 3"}

    polar = lambda p: (round(math.hypot(p[0] - hx, p[1] - hy) / S, 3), round(math.degrees(math.atan2(p[0] - hx, hy - p[1])) % 360, 2))
    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r, "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3),
                       "root_half_width_mm": round(M[f"{name}_hand_root_half_width_px"] / S, 3),
                       "widest_at": M[f"{name}_hand_widest_at"],
                       "lume_from_to_mm": [round(f * r, 3) for f in M[f"{name}_hand_lume_from_to"]]}
    r, a = polar(M["seconds_hand_tip"])
    tr_, ta = polar(M["seconds_hand_tail_disc"])
    wn, wt = M["seconds_hand_half_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": tr_, "tail_angle_deg": ta,
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wt / S, 3),
                        "tail_disc_radius_mm": [round(v / S, 3) for v in M["seconds_tail_disc_radius_px"]],
                        "tip_colour_from_mm": round(M["seconds_red_tip_from"] * r, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    out["hand_hub_offset_mm"] = mm((hx, hy))
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    boxes = ("date_window", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "numeral_12", "numeral_9", "numeral_6", "crown_box")
    for k in boxes:
        out[k] = box(M[k])

    j = M["bracelet_joints_y"]
    dist = lambda y: abs(py0 - y) / S
    cj = [dist(j["top_centre"][0]), dist(j["bottom_centre"][0])]
    out["bracelet_pitch_mm"] = round(float(np.mean([abs(b - a) / S for a, b in j.values()])), 3)
    out["bracelet_centre_first_joint_mm"] = round(sum(cj) / 2, 3)
    out["bracelet_centre_half"] = round(out["checks"]["centre_link_mm"] / 2 / half, 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 0, 255), 3)
        cv2.circle(ov, (int(rcx), int(rcy)), int(rr), (255, 128, 0), 3)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for hd in hands.values():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, (hx, hy), (int(hx + hd["length_mm"] * S * math.sin(t)), int(hy - hd["length_mm"] * S * math.cos(t))), (0, 255, 255), 2)
        for hr in out["indices"]["hours"]:
            t = math.radians(hr * 30)
            cv2.line(ov, P((r0 * math.sin(t), r0 * math.cos(t))), P((r1 * math.sin(t), r1 * math.cos(t))), (255, 0, 255), 2)
        for k in boxes:
            cv2.rectangle(ov, tuple(M[k][:2]), tuple(M[k][2:]), (0, 200, 255), 2)
        for y in (tips[0], -tips[1], out["lug_from_y_mm"], -out["lug_from_y_mm"]):
            cv2.line(ov, P((-14, y)), P((14, y)), (255, 255, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_mm", "lug_from_y_mm", "lug_tip_mm",
                                           "checks", "indices", "hands", "bracelet_pitch_mm", "bracelet_centre_first_joint_mm",
                                           "bracelet_centre_half")}, default=float), "->", dest)
