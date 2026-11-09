"""Measure the Seiko 5 SNXG47K1 into mm from two photos. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snxg47_rectify                   # first: straightened sharp photo
    python3 -B -m pipeline.seiko_snxg47_trace [out.json] [overlay.png]   # default config/watches/seiko-snxg47k1-trace.json

Dial parts (indices, hands, day-date, hub, crystal ring) come from the straightened 3000 px photo
(outputs/watches/seiko-snxg47k1/front_rectified.png, about 62 px/mm). Case, lug and bracelet outline come from the small
straight-on photo (front_straight_2000x2000.jpg, about 25 px/mm), where the case and bracelet have no turn. Both are scaled
to the 38 mm case (Irsyad, from the listing) through the left case flank of the straight photo; the sharp photo is tied to
it by the baton tips (case flank / baton tip = 1.319 in the straight photo). mm, x right, y toward 12, origin = hand pivot.
Parts read from gridded crops sit in MANUAL_PX (+-3 px).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHARP = ROOT / "outputs/watches/seiko-snxg47k1/front_rectified.png"
STRAIGHT = ROOT / "references/seiko-snxg47k1/front_straight_2000x2000.jpg"
OUT = ROOT / "config/watches/seiko-snxg47k1-trace.json"
CASE_MM = 38.0  # Irsyad, listing 2026-11-09
LUG_WIDTH_MM = 16.0  # same listing

STRAIGHT_PX = {
    "hand_pivot": [979, 909],
    "baton_tip_r_px": 354,  # outer end of the 12 baton
    "lug_tip_y_px": [345, 1470],  # case ends (top, bottom) where the bracelet comes out
    "end_link_x_px": [733, 1233],  # between the lug corners at 6
    "bracelet_row_1600": {"edges": [755, 1203], "centre": [875, 1104]},  # right edge mirrored from the left (side face shows)
    "bracelet_joints_y": {"outer": [1471, 1567, 1667, 1767], "centre": [1517, 1617, 1717]},
}
SHARP_PX = {
    "hand_pivot": [1480, 2184],  # hub pin
    "baton_tip_r_px": 900,
    "index_r_px": [632, 893],
    "index_width_px": 34,
    "index_12_px": [35, 15],  # each bar of the double baton, gap
    "hour_hand_tip": [1083, 1905],
    "hour_hand_width_px": 56,
    "hour_lume_r_px": [170, 450],
    "minute_hand_tip": [2157, 1738],
    "minute_hand_width_px": 42,
    "minute_lume_r_px": [330, 780],
    "hand_outline_px": 9,
    "seconds_hand_tip": [1583, 1360],
    "seconds_hand_tail_end": [1440, 2447],
    "seconds_hand_width_px": [6, 17],
    "hub_radius_px": [60, 18],  # outer gold collar, pin cap
    "daydate_frame": [1790, 2085, 2335, 2310],
    "daydate_window": [1855, 2130, 2290, 2268],
    "crystal_r_px": 1058,  # inner edge of the dark gasket
    "dial_edge_r_px": 1000,
}
ARTEFACTS = ["the sharp photo is straightened on the dial plane: raised parts (batons, case, gasket) keep about 0.4 mm of parallax",
             "the straight photo shows the right case and bracelet side faces: outline mirrored from the left edge",
             "listed lug width 16 mm; the bracelet measures about 18 mm next to the case"]


def trace(overlay=None):
    st = cv2.imread(str(STRAIGHT))
    fg = (765 - st.astype(int).sum(2)) > 25
    M, N = STRAIGHT_PX, SHARP_PX
    qx, qy = M["hand_pivot"]
    rows = [np.nonzero(fg[y])[0] for y in range(qy - 15, qy + 16)]
    flank = qx - float(np.median([r.min() for r in rows]))
    Ss = flank / (CASE_MM / 2)  # straight photo px per mm
    tip_mm = M["baton_tip_r_px"] / Ss
    S = N["baton_tip_r_px"] / tip_mm  # sharp photo px per mm
    px0, py0 = N["hand_pivot"]
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(SHARP.relative_to(ROOT)), "outline_source": str(STRAIGHT.relative_to(ROOT)),
           "scale_px_per_mm": round(S, 4), "outline_scale_px_per_mm": round(Ss, 4), "origin_px": [px0, py0],
           "anchor": f"case diameter {CASE_MM} mm from the left flank of the straight photo; sharp photo tied by the baton tips ({round(tip_mm, 3)} mm)",
           "case": {"radius_mm": CASE_MM / 2},
           "crystal_ring": {"radius_mm": round(N["crystal_r_px"] / S, 3)},
           "dial_edge_radius_mm": round(N["dial_edge_r_px"] / S, 3)}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(qy - y_mm * Ss))
        if 0 <= row < st.shape[0]:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                l = round((xs.min() - qx) / Ss, 3)
                prof.append([round(float(y_mm), 2), l, -l])
    out["silhouette_y_left_right_mm"] = prof
    tips = [round(abs(qy - y) / Ss, 3) for y in M["lug_tip_y_px"]]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    gap = (M["end_link_x_px"][1] - M["end_link_x_px"][0]) / Ss
    br = M["bracelet_row_1600"]
    bw = 2 * (qx - br["edges"][0]) / Ss
    out["end_link_half_width_mm"] = round(gap / 2, 3)
    out["checks"] = {"lug_gap_mm": round(gap, 2), "bracelet_width_mm": round(bw, 2), "listed_lug_width_mm": LUG_WIDTH_MM}
    out["bracelet_centre_fraction"] = round((br["centre"][1] - br["centre"][0]) / (2 * (qx - br["edges"][0])), 3)
    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.median([(b - a) / Ss for js in j.values() for a, b in zip(js[:-1], js[1:])])), 3)
    out["bracelet_centre_joint_shift_mm"] = round((j["centre"][0] - j["outer"][1]) / Ss, 3)  # centre joints this far nearer the case than the next outer joint

    r0, r1 = N["index_r_px"]
    out["indices"] = {"inner_mm": round(r0 / S, 3), "outer_mm": round(r1 / S, 3), "width_mm": round(N["index_width_px"] / S, 3),
                      "bar_12_mm": round(N["index_12_px"][0] / S, 3), "gap_12_mm": round(N["index_12_px"][1] / S, 3),
                      "layout": "faceted gold batons, double at 12, none at 3 (day-date)"}
    hands = {}
    for name in ("hour", "minute", "seconds"):
        r, a = polar(N[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r}
    for name in ("hour", "minute"):
        hands[name]["half_width_mm"] = round(N[f"{name}_hand_width_px"] / 2 / S, 3)
        hands[name]["lume_from_to_mm"] = [round(v / S, 3) for v in N[f"{name}_lume_r_px"]]
        hands[name]["outline_mm"] = round(N["hand_outline_px"] / S, 3)
    hs = hands["seconds"]
    hs["tail_mm"] = polar(N["seconds_hand_tail_end"])[0]
    hs["half_width_mm"], hs["tail_half_width_mm"] = (round(v / 2 / S, 3) for v in N["seconds_hand_width_px"])
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in N["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "daydate_window"):
        out[k] = box(N[k])
    out["manual_px"] = {"straight": M, "sharp": N}
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        im = cv2.imread(str(SHARP))
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r_ in (CASE_MM / 2 * S, N["crystal_r_px"], N["dial_edge_r_px"]):
            cv2.circle(ov, (px0, py0), int(r_), (0, 0, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            tl = hd.get("tail_mm", 0)
            cv2.line(ov, P((-tl * math.sin(t), -tl * math.cos(t))), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            for k in ("inner_mm", "outer_mm"):
                r_ = out["indices"][k]
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 8, (255, 0, 255), 2)
        for k in ("daydate_frame", "daydate_window"):
            b = N[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        for y in (tips[0], -tips[1]):
            cv2.line(ov, P((-12, y)), P((12, y)), (255, 128, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "outline_scale_px_per_mm", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm",
                                           "checks", "indices", "hands", "bracelet_pitch_mm", "bracelet_centre_fraction", "bracelet_centre_joint_shift_mm")}), "->", dest)
