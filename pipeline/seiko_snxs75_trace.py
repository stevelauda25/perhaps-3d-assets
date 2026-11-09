"""Measure the straightened Seiko 5 SNXS75K1 front photo into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snxs75_rectify                       # first: outputs/watches/seiko-snxs75k1/front_rectified.png
    python3 -B -m pipeline.seiko_snxs75_trace [out.json] [overlay.png]  # default config/watches/seiko-snxs75k1-trace.json

Same output as pipeline/seiko_snkl50_trace.py. The photo is turned about 11 deg toward the crown, so: origin = dial centre of the
straightened photo (the hand pivot stands 0.4 mm off it by parallax; hand angles and lengths are measured from the pivot);
anchor = case face from the left edge to the face/flank edge on the right = 36.8 mm (Irsyad); silhouette from the left side
only (the right side shows the case flank and the bracelet side). Hands, logo, day-date, crown and bracelet joints from gridded
crops (MANUAL_PX, +-5 px = +-0.13 mm); index radii and widths from gold/lume masks along each hour ray.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "outputs/watches/seiko-snxs75k1/front_rectified.png"
OUT = ROOT / "config/watches/seiko-snxs75k1-trace.json"
CASE_MM = 36.8  # Irsyad, 2026-11-09 (dealer listings: 37 mm)
LUG_WIDTH_MM = 19.0  # listing, reported as a check

MANUAL_PX = {
    "dial_centre": [1400, 1400],  # pipeline/seiko_snxs75_rectify.py CENTRE_PX
    "hand_pivot": [1383, 1393],
    "case_face_x": [707, 2080],  # row y 1400: left edge; right edge of the polished bezel where the flank starts
    "rings_r_px": {"dial_edge": 562, "gasket_outer": 590, "bezel_slope_outer": 630, "bezel_outer": 683},  # mean of 12 and 6
    # hands: gold frame with a lume inlay; hour and minute are batons with a pointed end and a short wide tail
    "hour_hand_tip": [1122, 1198],
    "hour_hand_tail_end": [1470, 1455],
    "hour_hand_lume": [[1300, 1330], [1190, 1250]],
    "hour_hand_half_width_px": 25,  # gold frame edge to edge, measured across the blade
    "minute_hand_tip": [1765, 1120],
    "minute_hand_tail_end": [1318, 1438],
    "minute_hand_lume": [[1520, 1290], [1740, 1150]],
    "minute_hand_half_width_px": 18,
    "seconds_hand_tip": [932, 1535],
    "seconds_hand_tail_end": [1530, 1347],
    "seconds_hand_half_width_px": [2, 9],  # needle, tapered tail at its root
    "hub_radius_px": [20, 5],  # gold cap, dark centre
    "daydate_frame": [1558, 1332, 1888, 1462],  # gold frame round both windows
    "logo_seiko": [1278, 1122, 1515, 1168],
    "logo_5_shield": [1328, 1185, 1465, 1260],
    "print_automatic": [1297, 1598, 1503, 1636],
    "print_6": [1245, 1845, 1565, 1885],
    "crown_box": [2059, 1617, 2119, 1727],  # recessed in the flank at about 4 o'clock
    # bracelet at 12, first rows next to the end link (further rows curve away and shorten)
    "bracelet_row_520": {"edges": [1050, 1789], "centre": [1250, 1606]},  # right outer edge without the visible side
    "bracelet_joints_y": {"outer": [600, 428], "centre": [628, 478]},
}
ARTEFACTS = ["straightened from a photo turned about 11 deg: case, bezel and bracelet keep some parallax (right flank and bracelet side visible)",
             "the left of the dial lies in the shadow of the inner wall; the right of the bezel looks wider",
             "bracelet rows curve away from the camera: only the first row is used for the pitch"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    b, g_, r = (im[..., i].astype(int) for i in range(3))
    fg = (765 - im.astype(int).sum(2)) > 45
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["dial_centre"]
    S = (M["case_face_x"][1] - M["case_face_x"][0]) / CASE_MM
    ccx = sum(M["case_face_x"]) / 2
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    at = lambda rr, a: (px0 + rr * math.sin(math.radians(a)), py0 - rr * math.cos(math.radians(a)))
    hx, hy = M["hand_pivot"]
    hand_polar = lambda p: (round(math.hypot(p[0] - hx, p[1] - hy) / S, 3), round(math.degrees(math.atan2(p[0] - hx, hy - p[1])) % 360, 2))

    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case face, left edge to the face/flank edge on the right, row y 1400 = {CASE_MM} mm (Irsyad); lug width {LUG_WIDTH_MM} mm (listing) as a check",
           "case": {"radius_mm": round(CASE_MM / 2, 3), "centre_mm": mm((ccx, py0))},
           "hand_pivot_mm": mm(M["hand_pivot"]),
           "rings_mm": {k: round(v / S, 3) for k, v in M["rings_r_px"].items()}}
    out["crystal_ring"] = {"radius_mm": out["rings_mm"]["gasket_outer"], "basis": "outer edge of the black gasket = inner edge of the steel bezel"}

    # silhouette from the left side, as a half width about the case centre
    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row, :int(ccx)])[0]
            if len(xs):
                half = (ccx - xs.min()) / S
                prof.append([round(float(y_mm), 2), round(-half + (ccx - px0) / S, 3), round(half + (ccx - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(15, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 3 or -tips[1] - 3 <= y <= -tips[1] - 0.5]
    row = M["bracelet_row_520"]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "end_link_width_mm": round((row["edges"][1] - row["edges"][0]) / S, 2), "listed_lug_width_mm": LUG_WIDTH_MM}

    # indices: extent of the gold frame (R well above B; the lume is as light as the shaded dial) in a band round each hour ray
    gold = ((r - b) > 30) & (r > 180)
    idx = {}
    for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        a = math.radians(hr * 30)
        hits = [(rr, k) for rr in range(300, 540) for k in range(-70, 71)
                if gold[int(py0 - rr * math.cos(a) + k * math.sin(a)), int(px0 + rr * math.sin(a) + k * math.cos(a))]]
        rs, ks = [p[0] for p in hits], [p[1] for p in hits]
        idx[str(hr)] = {"inner": round(min(rs) / S, 3), "outer": round(max(rs) / S, 3), "width": round((max(ks) - min(ks) + 1) / S, 3),
                        "offset": round((max(ks) + min(ks)) / 2 / S, 3)}
    # hours 10, 11 (hour hand) and 1, 2 (minute hand) carry gold from the hands: the singles' median ignores them
    singles = [v for k, v in idx.items() if k in ("4", "5", "7", "8")]
    out["indices"] = {"per_hour_mm": idx,
                      "inner_mm": round(float(np.median([v["inner"] for v in singles])), 3),
                      "outer_mm": round(float(np.median([v["outer"] for v in singles])), 3),
                      "width_mm": round(float(np.median([v["width"] for v in singles])), 3),
                      "width_wide_mm": round((idx["6"]["width"] + idx["9"]["width"]) / 2, 3), "width_12_mm": idx["12"]["width"],
                      "layout": "applied, gold frame with a lume inlay; two bars at 12, wide bars at 6 and 9, day-date at 3 with a gold marker outside it"}
    m3 = [rr for rr in range(495, M["rings_r_px"]["dial_edge"] + 1) if gold[int(at(rr, 90)[1]), int(at(rr, 90)[0])]]  # past the day-date frame
    out["marker_3_mm"] = {"inner": round(m3[0] / S, 3), "outer": round(m3[-1] / S, 3)} if m3 else None

    hands = {}
    for name in ("hour", "minute"):
        rr, a = hand_polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": rr, "tail_mm": hand_polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3),
                       "lume_from_to_mm": sorted(hand_polar(p)[0] for p in M[f"{name}_hand_lume"])}
    rr, a = hand_polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_half_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": rr, "tail_mm": hand_polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda bx: {"x0_y0_x1_y1_mm": mm(bx[:2]) + mm(bx[2:]), "size_mm": [round((bx[2] - bx[0]) / S, 3), round((bx[3] - bx[1]) / S, 3)],
                      "centre_mm": mm(((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2))}
    for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic", "print_6", "crown_box"):
        out[k] = box(M[k])
    c = (row["edges"][0] + row["edges"][1]) / 2
    hw = (row["edges"][1] - row["edges"][0]) / 2
    out["bracelet_columns"] = {"centre_half": round((abs(row["centre"][0] - c) + abs(row["centre"][1] - c)) / 2 / hw, 3),
                               "basis": "fraction of the bracelet half width, first row at 12"}
    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.mean([(a_ - b_) / S for js in j.values() for b_, a_ in zip(js[1:], js[:-1])])), 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = im // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), py0), int(CASE_MM / 2 * S), (0, 0, 255), 3)
        for v in M["rings_r_px"].values():
            cv2.circle(ov, (px0, py0), v, (255, 128, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, (int(hx - hd["tail_mm"] * S * math.sin(t)), int(hy + hd["tail_mm"] * S * math.cos(t))),
                     (int(hx + hd["length_mm"] * S * math.sin(t)), int(hy - hd["length_mm"] * S * math.cos(t))), (0, 255, 255), 2)
        for hr, v in idx.items():
            t = math.radians(int(hr) * 30)
            for r_ in (v["inner"], v["outer"]):
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 7, (255, 0, 255), 2)
        for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic", "print_6", "crown_box"):
            cv2.rectangle(ov, tuple(M[k][:2]), tuple(M[k][2:]), (0, 200, 255), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "hand_pivot_mm", "rings_mm", "lug_tip_mm", "checks", "indices", "marker_3_mm",
                                           "hands", "bracelet_columns", "bracelet_pitch_mm")}, default=float), "->", dest)
