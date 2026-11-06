"""Measure the Seiko Presage SPB467J1 front photo (transparent background, 2204 x 2204) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.seiko_spb467_trace [out.json] [overlay.png]     # default config/watches/seiko-spb467j1-trace.json

Anchor: case diameter 40.2 mm (Irsyad, 2026-11-06) from the case edge left of and below the pivot (the right side carries the
crown, the top meets the end link). The bracelet face then measures 20.3 mm (listed lug width 20 mm). mm, x right, y toward 12,
origin = hand pivot. The stucco dial defeats thresholding, so hands, date, print boxes, crown, rings and bracelet columns come
from gridded crops (MANUAL_PX, +-3 px = +-0.1 mm); index radii from the saturation profile (grey steel on the salmon dial);
silhouette from the alpha channel.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-spb467j1/front_2204.png"
OUT = ROOT / "config/watches/seiko-spb467j1-trace.json"
CASE_MM = 40.2  # Irsyad, 2026-11-06
LISTED = {"lug_width_mm": 20.0}

MANUAL_PX = {
    "hand_pivot": [1040, 1028],
    "case_edge_left_x": 422,  # silhouette on the pivot row
    "case_edge_bottom_y": 1650,  # case edge below the bezel at 6 (end link joint)
    "bezel_outer_y": [437, 1620],  # dark line at 12 and 6
    "bezel_inner_left_x": 497,  # crystal edge on the pivot row
    "flange_inner_left_x": 571,  # minute-track flange starts (dial r 15.2)
    # dauphine hour and minute: full width (grey on salmon), measured across at two points along each hand
    "hour_hand_tip": [788, 853],
    "minute_hand_tip": [1420, 742],
    "hour_half_width_px": [26, 2],  # at the root, near the tip (0.88 L)
    "minute_half_width_px": [26, 9],
    "hand_tail_mm": 1.0,  # hour and minute tails hide under the hub boss
    "seconds_hand_tip": [572, 1176],
    "seconds_hand_tail_end": [1215, 975],
    "seconds_half_width_px": [3, 5],  # needle, counterweight
    "hub_radius_px": [30, 12],  # boss, cap
    "date_frame": [1322, 984, 1446, 1080],
    "date_window": [1348, 1003, 1438, 1068],
    "index_3_x_px": [1475, 1520],
    "index_width_px": 21,
    "index_12_width_px": 19,
    "index_12_offset_px": 17,  # each bar from the centre line
    "logo_seiko": [921, 787, 1163, 845],
    "print_presage": [900, 1203, 1192, 1283],
    "print_6": [855, 1458, 1210, 1495],
    "crown_box": [1655, 935, 1775, 1140],
    # bracelet (6 o'clock side, the flatter one): columns outer | A | B | C | D | E | outer, A C E polished pills half a row
    # out of step with the brushed outer, B and D links
    "bracelet_face_x": [752, 1378],
    "bracelet_centre_x": [900, 1215],
    "outer_joints_y": [1760, 1915],
    "pill_joints_y": [1700, 1855],
}
ARTEFACTS = ["the watch is turned slightly: the right side walls of the bracelet and case show (silhouette 653 px vs face 626 px)",
             "the bracelet curls away in the photo, rows shrink toward the ends: pitch from the first row at 6",
             "bright arcs on the bezel and case are reflections, not shape"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    fg = im[..., 3] > 128
    sat = cv2.GaussianBlur(cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2HSV)[..., 1].astype(float), (0, 0), 1.5)
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    case_r = ((px0 - M["case_edge_left_x"]) + (M["case_edge_bottom_y"] - py0)) / 2
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case diameter {CASE_MM} mm (Irsyad) from the case edge left of and below the pivot",
           "case_radius_mm": round(case_r / S, 3),
           "bezel_outer_radius_mm": round((M["bezel_outer_y"][1] - M["bezel_outer_y"][0]) / 2 / S, 3),
           "crystal_radius_mm": round((px0 - M["bezel_inner_left_x"]) / S, 3),
           "dial_flat_radius_mm": round((px0 - M["flange_inner_left_x"]) / S, 3)}

    prof = []
    for y_mm in np.arange(-36, 36.01, 0.25):
        row = int(round(py0 - y_mm * S))
        xs = np.nonzero(fg[row])[0]
        if len(xs):
            prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    # lug tips: the silhouette steps in from the lugs to the bracelet (more than 1 mm between rows 0.25 mm apart)
    tips = [next(y for y in np.arange(18, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}

    # applied batons: low-saturation run along each hour ray
    idx = {}
    for hr in (1, 2, 5, 6, 7, 8, 9, 10, 11):
        a = math.radians(hr * 30)
        p = [sat[int(py0 - r * math.cos(a)), int(px0 + r * math.sin(a))] for r in range(250, 560)]
        low = [i for i, v in enumerate(p) if v < 45]
        runs, s = [], low[0]
        for a_, b_ in zip(low, low[1:] + [None]):
            if b_ != a_ + 1:
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t: t[1] - t[0])
        idx[str(hr)] = [round((250 + r0) / S, 3), round((250 + r1) / S, 3)]
    out["indices"] = {"per_hour_mm": idx,
                      "inner_mm": round(float(np.median([v[0] for v in idx.values()])), 3),
                      "outer_mm": round(float(np.median([v[1] for v in idx.values()])), 3),
                      "short_inner_mm": round((M["index_3_x_px"][0] - px0) / S, 3),
                      "short_outer_mm": round((M["index_3_x_px"][1] - px0) / S, 3),
                      "width_mm": round(M["index_width_px"] / S, 3),
                      "width_12_mm": round(M["index_12_width_px"] / S, 3), "offset_12_mm": round(M["index_12_offset_px"] / S, 3),
                      "layout": "applied polished batons at 1 2 4 5 6 7 8 9 10 11, double at 12, short at 3 beside the date (4 hidden by glare in the profile)"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        w0, w1 = M[f"{name}_half_width_px"]
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": M["hand_tail_mm"],
                       "half_width_root_mm": round(w0 / S, 3), "half_width_tip_mm": round(w1 / S, 3)}
    r, a = polar(M["seconds_hand_tip"])
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(M["seconds_half_width_px"][0] / S, 3),
                        "tail_half_width_mm": round(M["seconds_half_width_px"][1] / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("date_frame", "date_window", "logo_seiko", "print_presage", "print_6", "crown_box"):
        out[k] = box(M[k])

    fx = M["bracelet_face_x"]
    out["bracelet"] = {"half_width_mm": round((fx[1] - fx[0]) / 2 / S, 3),
                       "centre_half_mm": round((M["bracelet_centre_x"][1] - M["bracelet_centre_x"][0]) / 2 / S, 3),
                       "pitch_mm": round(float(np.mean([np.diff(M["outer_joints_y"])[0], np.diff(M["pill_joints_y"])[0]])) / S, 3),
                       "pill_shift_mm": round((M["outer_joints_y"][0] - M["pill_joints_y"][0]) / S, 3),
                       "outer_joint_mm": round((M["outer_joints_y"][0] - py0) / S, 3)}
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_face_mm": round(2 * out["bracelet"]["half_width_mm"], 2), "listed": LISTED}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = (im[..., :3] // 2).copy()
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r_ in (case_r, out["bezel_outer_radius_mm"] * S, out["crystal_radius_mm"] * S, out["dial_flat_radius_mm"] * S):
            cv2.circle(ov, (px0, py0), int(r_), (0, 0, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for hd in hands.values():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, P((-hd["tail_mm"] * math.sin(t), -hd["tail_mm"] * math.cos(t))),
                     P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr, (r0, r1) in idx.items():
            t = math.radians(int(hr) * 30)
            for r_ in (r0, r1):
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 6, (255, 0, 255), 2)
        for k in ("date_frame", "date_window", "logo_seiko", "print_presage", "print_6", "crown_box"):
            cv2.rectangle(ov, tuple(M[k][:2]), tuple(M[k][2:]), (0, 200, 255), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k not in ("silhouette_y_left_right_mm", "manual_px", "artefacts_not_traced")},
                     default=float), "->", dest)
