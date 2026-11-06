"""Measure the Seiko Presage Style60's SSA425J1 front photo (transparent background, 2204 x 2204) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.seiko_ssa425_trace [out.json] [overlay.png]     # default config/watches/seiko-ssa425j1-trace.json

Anchor: case diameter 40.8 mm (listing, Irsyad 2026-11-06) from the bezel edge left of the pivot (the right side carries the crown
and shows the turned side wall). Check: lug to lug 47.0 mm listed. mm, x right, y toward 12, origin = hand pivot. Hands, rings,
print boxes, crown and bracelet joints come from gridded crops (MANUAL_PX, +-3 px = +-0.1 mm); index radii and widths from the
brightness along each hour ray (polished batons on the black dial); silhouette from the alpha channel.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-ssa425j1/front_2204.png"
OUT = ROOT / "config/watches/seiko-ssa425j1-trace.json"
CASE_MM = 40.8  # listing (Irsyad, 2026-11-06)
LISTED = {"lug_to_lug_mm": 47.0, "lug_width_mm": 20.0, "thickness_mm": 12.8}

MANUAL_PX = {
    "hand_pivot": [1038, 1021],
    "case_edge_left_x": 412,  # silhouette on the pivot row (outer edge of the bezel)
    # radii along clean rays between the bezel marks (15, 75, 105, 165, 195, 345 deg)
    "rings_px": {"insert_outer": 618, "insert_inner": 546, "crystal_edge": 522, "dial_flat": 445},
    # sword hands: gunmetal frame, cream lume from lume_from to lume_to (fractions of the length); widest near the root
    "hour_hand_tip": [820, 866],  # polished white tip piece beyond the lume
    "minute_hand_tip": [1376, 772],
    "hour_half_width_px": [29, 14, 8],  # at 0.25 L, 0.75 L, 0.95 L
    "minute_half_width_px": [28, 17, 12],
    "hour_lume": [0.25, 0.76],
    "minute_lume": [0.22, 0.74],
    "lume_inset_px": 7,
    "hour_tail_end": [1132, 1083],  # broad triangular tail opposite the hour hand
    "hour_tail_half_width_px": 30,
    "minute_tail_mm": 1.0,
    "seconds_hand_tip": [630, 1166],
    "seconds_hand_tail_end": [1182, 972],  # long paddle counterweight
    "seconds_half_width_px": [2, 8],
    "hub_radius_px": [22, 10],  # boss, cap
    # 24-hour sub-dial at 10 o'clock: arrow hand, cap
    "sub24_pivot": [930, 880],
    "sub24_tip": [878, 790],
    "sub24_arrow_px": [0.38, 0.71, 13],  # base and point (fractions of the length), half width at the base
    "sub24_half_width_px": 4,
    "sub24_cap_px": 18,
    "sub24_ring_px": 137,
    "sub24_numerals": [[900, 745, 955, 792], [902, 1003, 955, 1050]],  # 24 and 12
    "aperture_centre_px": [826, 1068],
    "aperture_radius_px": 158,
    "index_12_px": [1013, 615, 1075, 707],  # three rounded ribs
    "logo_seiko": [1122, 1000, 1335, 1055],
    "print_presage": [940, 1195, 1155, 1275],
    "print_6": [855, 1458, 1210, 1505],
    "crown_box": [1690, 943, 1790, 1112],
    "crown_flutes_to_x": 1765,
    # bracelet (6 o'clock side): three columns, centre links half a row nearer the case than the outer links
    "bracelet_face_x": [752, 1372],
    "bracelet_centre_x": [900, 1207],
    "outer_joints_y": [1765, 1968],
    "centre_joints_y": [1718, 1910],
}
ARTEFACTS = ["the watch is turned slightly: the right side walls of the bracelet, lugs and case show (bracelet face centre 0.8 mm right of the pivot)",
             "the bracelet curls away in the photo, rows shrink toward the ends: pitch from the first outer row at 6",
             "grey band between the dial edge and the bezel is the box crystal's side wall, not a part",
             "the left half of the black bezel insert carries a soft grey reflection"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    fg = im[..., 3] > 128
    grey = cv2.GaussianBlur(cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY).astype(float), (0, 0), 1.0)
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    case_r = px0 - M["case_edge_left_x"]
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p, o=(px0, py0): (round(math.hypot(p[0] - o[0], p[1] - o[1]) / S, 3),
                                     round(math.degrees(math.atan2(p[0] - o[0], o[1] - p[1])) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case diameter {CASE_MM} mm (listing) from the bezel edge left of the pivot",
           "case_radius_mm": round(case_r / S, 3),
           "rings_mm": {k: round(v / S, 3) for k, v in M["rings_px"].items()}}

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

    # applied batons: longest bright run along each hour ray, width from the bright run across its middle
    ap_c, ap_r = M["aperture_centre_px"], M["aperture_radius_px"]
    idx = {}
    for hr in range(1, 12):
        a = math.radians(hr * 30)
        ray = lambda r, t=0.0: (px0 + r * math.sin(a) + t * math.cos(a), py0 - r * math.cos(a) + t * math.sin(a))
        p = [grey[int(round(ray(r)[1])), int(round(ray(r)[0]))] for r in range(280, 440)]
        hi = [i for i, v in enumerate(p) if v > 120]
        runs, s = [], hi[0]
        for a_, b_ in zip(hi, hi[1:] + [None]):
            if b_ != a_ + 1:
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t: t[1] - t[0])
        rm = 280 + (r0 + r1) / 2
        across = [t for t in range(-40, 41) if grey[int(round(ray(rm, t)[1])), int(round(ray(rm, t)[0]))] > 60]
        idx[str(hr)] = {"r_mm": [round((280 + r0) / S, 3), round((280 + r1) / S, 3)], "width_mm": round((max(across) - min(across) + 1) / S, 3),
                        "cut_by_aperture": bool(math.hypot(*np.subtract(ray(280 + r0), ap_c)) < ap_r + 3)}
    full = [v for k, v in idx.items() if not v["cut_by_aperture"] and k != "3"]
    b = M["index_12_px"]
    out["indices"] = {"per_hour": idx,
                      "inner_mm": round(float(np.median([v["r_mm"][0] for v in full])), 3),
                      "outer_mm": round(float(np.median([v["r_mm"][1] for v in full])), 3),
                      "width_mm": round(float(np.median([v["width_mm"] for v in full])), 3),
                      "index_12_mm": {"x": [mm(b[:2])[0], mm(b[2:])[0]], "r": [round((py0 - b[3]) / S, 3), round((py0 - b[1]) / S, 3)]},
                      "layout": "three-rib polished batons; wide triple at 12; 3 longer beside SEIKO; 9 cut short by the open-heart aperture; lume pads stay in the dial map"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        w0, wm, w1 = M[f"{name}_half_width_px"]
        hands[name] = {"angle_deg": a, "length_mm": r, "half_width_root_mm": round(w0 / S, 3), "half_width_mid_mm": round(wm / S, 3),
                       "half_width_tip_mm": round(w1 / S, 3),
                       "lume": M[f"{name}_lume"], "lume_inset_mm": round(M["lume_inset_px"] / S, 3)}
    hands["hour"]["tail_mm"] = polar(M["hour_tail_end"])[0]
    hands["hour"]["tail_half_width_mm"] = round(M["hour_tail_half_width_px"] / S, 3)
    hands["minute"]["tail_mm"] = M["minute_tail_mm"]
    r, a = polar(M["seconds_hand_tip"])
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(M["seconds_half_width_px"][0] / S, 3),
                        "tail_half_width_mm": round(M["seconds_half_width_px"][1] / S, 3)}
    r, a = polar(M["sub24_tip"], M["sub24_pivot"])
    f0, f1, aw = M["sub24_arrow_px"]
    hands["sub24"] = {"pivot_mm": mm(M["sub24_pivot"]), "angle_deg": a, "length_mm": r, "arrow": [f0, f1],
                      "arrow_half_width_mm": round(aw / S, 3), "half_width_mm": round(M["sub24_half_width_px"] / S, 3),
                      "cap_radius_mm": round(M["sub24_cap_px"] / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    out["sub24"] = {"centre_mm": mm(M["sub24_pivot"]), "radius_mm": round(M["sub24_ring_px"] / S, 3),
                    "numerals_mm": [mm(b[:2]) + mm(b[2:]) for b in M["sub24_numerals"]]}
    out["aperture"] = {"centre_mm": mm(ap_c), "radius_mm": round(ap_r / S, 3)}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("logo_seiko", "print_presage", "print_6", "crown_box"):
        out[k] = box(M[k])
    out["crown_box"]["flutes_to_mm"] = round((M["crown_flutes_to_x"] - px0) / S, 3)

    fx = M["bracelet_face_x"]
    out["bracelet"] = {"half_width_mm": round((fx[1] - fx[0]) / 2 / S, 3),
                       "centre_half_mm": round((M["bracelet_centre_x"][1] - M["bracelet_centre_x"][0]) / 2 / S, 3),
                       "pitch_mm": round(float(np.diff(M["outer_joints_y"])[0]) / S, 3),
                       "centre_shift_mm": round((M["outer_joints_y"][0] - M["centre_joints_y"][0]) / S, 3),
                       "outer_joint_mm": round((M["outer_joints_y"][0] - py0) / S, 3)}
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_face_mm": round(2 * out["bracelet"]["half_width_mm"], 2), "listed": LISTED}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = (im[..., :3] // 2).copy()
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r_ in [case_r] + list(M["rings_px"].values()):
            cv2.circle(ov, (px0, py0), int(r_), (0, 0, 255), 2)
        cv2.circle(ov, tuple(M["sub24_pivot"]), M["sub24_ring_px"], (0, 0, 255), 2)
        cv2.circle(ov, tuple(ap_c), ap_r, (0, 0, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for k, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            o = hd.get("pivot_mm", (0, 0))
            cv2.line(ov, P((o[0] - hd.get("tail_mm", 0) * math.sin(t), o[1] - hd.get("tail_mm", 0) * math.cos(t))),
                     P((o[0] + hd["length_mm"] * math.sin(t), o[1] + hd["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr, v in idx.items():
            t = math.radians(int(hr) * 30)
            for r_ in v["r_mm"]:
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 6, (255, 0, 255), 2)
        for k in ("logo_seiko", "print_presage", "print_6", "crown_box", "index_12_px"):
            cv2.rectangle(ov, tuple(M[k][:2]), tuple(M[k][2:]), (0, 200, 255), 2)
        for y in M["outer_joints_y"] + M["centre_joints_y"]:
            cv2.line(ov, (fx[0], y), (fx[1], y), (255, 255, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k not in ("silhouette_y_left_right_mm", "manual_px", "artefacts_not_traced")},
                     default=float), "->", dest)
