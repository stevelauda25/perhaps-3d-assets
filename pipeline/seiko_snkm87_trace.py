"""Measure the Seiko 5 SNKM87K1 front photo (white background, 1081 x 1500) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snkm87_trace [out.json] [overlay.png]     # default config/watches/seiko-snkm87k1-trace.json

Same method as pipeline/seiko_snk369_trace.py. Anchor: case diameter 43 mm (listings), from the LEFT flank only: the photo
shows a little of the right case side and bracelet side, so the silhouette is mirrored from the left edge. mm, x right, y
toward 12, origin = hand pivot. The dial has a fine concentric pattern, so hands, indices, day-date and bracelet joints are
read from gridded crops (MANUAL_PX, +-3 px = +-0.15 mm at this resolution).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snkm87k1/front_1081x1500.jpg"
OUT = ROOT / "config/watches/seiko-snkm87k1-trace.json"
CASE_MM = 43.0  # listings
BAND_MM = 21.0  # listings (one says 22)

MANUAL_PX = {
    "hand_pivot": [500, 690],
    # hour and minute: polished dauphine blades, widest near the hub, pointed counterweight tails
    "hour_hand_tip": [351.5, 577.7],
    "hour_hand_tail_end": [557.7, 733.8],
    "hour_hand_widest_px": [60, 35],  # along the hand, full width
    "minute_hand_tip": [730.8, 512.3],
    "minute_hand_tail_end": [446, 737.7],
    "minute_hand_widest_px": [60, 32],
    "tail_root_width_px": 27,
    # seconds: thin polished needle with a paddle tail
    "seconds_hand_tip": [211.5, 789.2],
    "seconds_hand_tail_end": [603.8, 659],
    "seconds_hand_width_px": [4, 14],
    "hub_radius_px": [13, 6],
    "daydate_frame": [604, 657, 781, 724],
    "crown_box": [993, 630, 1058, 757],  # knurled crown and its cap; the case flank here is 0.5 mm wide (side face)
    "index_r_px": [207, 300],  # batons
    "index_width_px": 24,
    "index_12_px": [22, 6],  # each bar of the double baton, gap between them
    "block_r_px": [312, 325],  # white blocks at the inner edge of the chapter ring
    "block_width_px": 32,
    "dial_edge_r_px": 304,  # edge of the patterned centre; the chapter ring starts here
    "crystal_r_px": 400,
    "end_link_x_px": [260, 725],
    "lug_tip_y_px": [145, 1255],  # top, bottom: where the lugs end beside the first bracelet row
    # bracelet at 6 (clearer than 12): outer joints at the lug tip and one row on, centre joints a little further out
    "bracelet_joints_y": {"outer": [1255, 1410], "centre": [1295, 1440]},
    "bracelet_centre_fraction": 0.5,  # centre column / bracelet width (front photo 0.59, 3/4 photo 0.48)
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "the photo shows a little of the right case and bracelet sides; scale and silhouette use the left side",
             "the bracelet columns look shifted left of the pivot in the front photo (perspective); the build centres them",
             "watermark across the lower bracelet: geometry only, not in the dial map"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    edge = []
    for a in np.arange(260, 280.1, 1.0):
        rs = np.arange(400, 520, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), np.clip(xs.astype(int), 0, w - 1)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    edge = np.array(edge)
    case_r = float(np.median(np.hypot(edge[:, 0] - px0, edge[:, 1] - py0)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case diameter {CASE_MM} mm (listings) from the left flank",
           "case": {"radius_mm": round(case_r / S, 3)},
           "crystal_ring": {"radius_mm": round(M["crystal_r_px"] / S, 3), "basis": "inner edge of the polished bezel (radial profiles)"},
           "dial_edge_radius_mm": round(M["dial_edge_r_px"] / S, 3)}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                l = round((xs.min() - px0) / S, 3)
                prof.append([round(float(y_mm), 2), l, -l])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [round(abs(py0 - y) / S, 3) for y in M["lug_tip_y_px"]]  # the silhouette step is too soft to find them
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (26, 28, 30, -26, -28, -30) if y in width}
    lug_gap = (M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S
    out["checks"] = {"lug_gap_mm": round(lug_gap, 2), "listed_band_mm": BAND_MM}

    r0, r1 = M["index_r_px"]
    b0, b1 = M["block_r_px"]
    out["indices"] = {"inner_mm": round(r0 / S, 3), "outer_mm": round(r1 / S, 3), "width_mm": round(M["index_width_px"] / S, 3),
                      "bar_12_mm": round(M["index_12_px"][0] / S, 3), "gap_12_mm": round(M["index_12_px"][1] / S, 3),
                      "block_inner_mm": round(b0 / S, 3), "block_outer_mm": round(b1 / S, 3), "block_width_mm": round(M["block_width_px"] / S, 3),
                      "layout": "faceted polished batons, double at 12, none at 3 (day-date); a white block at every hour on the chapter ring edge"}

    hands = {}
    for name in ("hour", "minute", "seconds"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0]}
    for name in ("hour", "minute"):
        at_px, wd = M[f"{name}_hand_widest_px"]
        hands[name]["widest_at_mm"], hands[name]["half_width_mm"] = round(at_px / S, 3), round(wd / 2 / S, 3)
        hands[name]["tail_half_width_mm"] = round(M["tail_root_width_px"] / 2 / S, 3)
    hands["seconds"]["half_width_mm"], hands["seconds"]["tail_half_width_mm"] = (round(v / 2 / S, 3) for v in M["seconds_hand_width_px"])
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "crown_box"):
        out[k] = box(M[k])
    out["end_link_half_width_mm"] = round(lug_gap / 2, 3)
    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.median([(b - a) / S for js in j.values() for a, b in zip(js[:-1], js[1:])])), 3)
    out["bracelet_centre_joint_shift_mm"] = round((j["outer"][0] - j["centre"][0]) / S, 3)  # negative: centre joints further out
    out["bracelet_centre_fraction"] = M["bracelet_centre_fraction"]

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r_ in (case_r, M["crystal_r_px"], M["dial_edge_r_px"]):
            cv2.circle(ov, (px0, py0), int(r_), (0, 0, 255), 1)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 1, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 1, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, P((-hd["tail_mm"] * math.sin(t), -hd["tail_mm"] * math.cos(t))), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            for k in ("inner_mm", "outer_mm", "block_outer_mm"):
                r_ = out["indices"][k]
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 3, (255, 0, 255), 1)
        for k in ("daydate_frame", "crown_box"):
            b = [int(v) for v in M[k]]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for ys in j.values():
            for y in ys:
                cv2.line(ov, (200, y), (800, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "checks",
                                           "bracelet_width_mm", "indices", "hands", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm")}), "->", dest)
