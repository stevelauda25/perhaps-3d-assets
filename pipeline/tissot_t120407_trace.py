"""Measure the Tissot T120.407.17.041.00 (Seastar 1000 Powermatic 80, 43 mm, blue gradient dial, black ceramic insert, black
rubber strap) official front render (1680 x 1680, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.tissot_t120407_trace [out.json] [overlay.png]   # default config/watches/tissot-t120.407.17.041.00-trace.json

Same method as pipeline/tissot_t120607_trace.py. Anchor: 43 mm case width (Tissot official) from a circle fitted to the coin-edge
bezel on the flanks (alpha > 250: the render's drop shadow is semi-transparent). mm, x right, y toward 12, origin = hand pivot.
The dial centre sits 2.8 px right of and 2 px below the pivot in the render: indices and bezel are placed about the dial
centre, hands about the pivot. Hands, indices, crown and crown guard come from gridded crops and axis profiles (MANUAL_PX,
+-2 px = +-0.1 mm). The insert's prints (silver numerals, bars, minute marks, the triangle with its lume pip) are traced by
threshold and become inlays; the gradient dial, its prints, the date and the flange minute track stay in the dial map.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_print import UP, shapes_from_mask
from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/tissot-t120.407.17.041.00/front_official_1680x1680.png"
OUT = ROOT / "config/watches/tissot-t120.407.17.041.00-trace.json"
CASE_MM = 43.0  # Tissot official case width: the coin-edge bezel is the widest part at 3 and 9
LISTED = {"lug_width_mm": 21.0, "thickness_mm": 12.7, "case_length_mm": 43.0}

MANUAL_PX = {
    "hand_pivot": [840, 840],
    "dial_centre": [842.8, 842.0],  # circle through the seven clean lume dots (r 265.0 px)
    # hour: broad baton, polished frame round a lume panel, short pointed tip
    "hour_hand": {"angle_deg": 305.0, "tip": 178, "shoulder": 150, "half": 26, "lume": [64, 160, 15]},
    # minute: long baton, polished frame round a lume panel, pointed tip
    "minute_hand": {"angle_deg": 55.0, "tip": 270, "shoulder": 245, "half": 23.5, "lume": [105, 258, 12.5]},
    # seconds: polished needle, lume dot in a polished ring, short tip past it; T-shaped counterweight
    "seconds_hand": {"angle_deg": 215.3, "half": 2.5, "ring_r": 263, "ring": [7, 13], "tip": 307,
                     "counterweight": [[-9.5, 0], [-9.5, 82], [-34, 82], [-34, 98], [61, 98], [47, 57], [10.5, 57], [10.5, 0]]},
    # the hour and minute tails below the hub, read as one polished outline (image px)
    "tails": [[800, 845], [785, 867], [800, 888], [820, 879], [842, 877], [848, 882], [863, 881], [880, 890], [897, 862], [883, 848],
              [870, 835], [840, 825]],
    "hub_radius_px": [22, 8],
    "outline_px": 5,  # polished frame round the hand lume
    # applied indices about the dial centre: polished frame round lume. Dots, triangle at 12, bars at 3 and 9, short bar at 6
    "dot_ring_r": 265.0, "dot_turn_deg": 0.4, "dot_lume_r": 15.5, "frame_px": 6,
    "triangle_px": {"r": [227, 280], "half": 29.5},
    "bar_px": {"r": [221, 280], "half": 11.5},
    "bar6_px": {"r": [256, 282], "half": 11.5},
    "date_window": [810, 1020, 875, 1082],  # round window at 6 with the date (8): dial map
    "logo": [770, 652, 915, 718],  # TISSOT 1853
    "print_seastar": [735, 925, 955, 1005],  # SEASTAR, POWERMATIC 80, 30 bar (300m / 1000 ft)
    "print_swiss_made": [775, 1088, 910, 1122],
    "crown_box": [1250, 775, 1343, 915],  # guard edge to the end of the fluted crown
    "crown_teeth": 20,
    # one crown guard round the crown; the inner points lie under the bezel
    "guard": [[1180, 700], [1235, 700], [1262, 707], [1290, 722], [1300, 760], [1303, 800], [1303, 890], [1300, 930], [1290, 965],
              [1262, 980], [1235, 990], [1180, 990]],
    "bezel_rings_px": {"dial_out": 313, "lip_in": 323, "insert_in": 336, "insert_out": 405},  # about the dial centre
    "insert_pip": [841.5, 469, 18],  # lume pip inside the insert triangle at 12 (x, y, radius)
    "bezel_notch_count": 90,  # wide square teeth about 29 px apart at the rim
    "lug_inner_x": [642, 1043],
}
ARTEFACTS = ["the render is 19.4 px/mm: hand and index edges are +-2 px (+-0.1 mm)",
             "the hands are rendered with a visible side wall on one side; the top face width is used",
             "the minute tail lies under the seconds hand; its width is an estimate",
             "the date window (round, with 8) stays in the dial map"]


def trace(path=FRONT, overlay=None):
    raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    al = raw[..., 3:].astype(float) / 255
    im = (raw[..., :3] * al + 255 * (1 - al)).astype(np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
    fg = raw[..., 3] > 250  # the drop shadow is semi-transparent
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    dcx, dcy = M["dial_centre"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * np.sin(np.radians(a)), c[1] - r * np.cos(np.radians(a)))

    # coin-edge bezel on the flanks: the lugs leave it above 318 / below 222 deg (and 42 / 138), the crown guard at 62-118
    edge = []
    for a in list(np.arange(224, 316.1, 1.0)) + list(np.arange(44, 60.1, 1.0)) + list(np.arange(120, 136.1, 1.0)):
        rs = np.arange(380, 440, 0.5)
        xs, ys = at(rs, a, (dcx, dcy))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(float(v) / S, 3)
    rg = dict(M["bezel_rings_px"], rim_out=round(float(case_r), 1))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Tissot official), coin-edge circle on the flanks",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "dial_centre_mm": mm((dcx, dcy)), "bezel_rings_mm": {k: f(v) for k, v in rg.items()},
           "bezel_notches": {"count": M["bezel_notch_count"], "basis": "square teeth about 29 px apart at the rim"}}

    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - dcx, yy - dcy)
    band = (rr > rg["insert_in"] + 5) & (rr < rg["insert_out"] - 2)
    white = (hsv[..., 1] < 60) & (hsv[..., 2] > 70)  # raised prints: their shaded sides read V 70-110
    out["insert_srgb"] = [round(float(v) / 255, 3) for v in np.median(im[band & ~white & (gray < 60)][:, ::-1], 0)]

    # ---- silhouette per y (alpha), lug tips, strap width past the tips ----
    prof = []
    for y_mm in np.arange(-43, 43.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    xl, xr = M["lug_inner_x"]
    tip_rows = []
    for sy in (1, -1):  # first row past the case where the outline is no wider than the strap (+12 px: the strap is 7 px wider than the lug gap)
        row = int(round(py0 - sy * 20 * S))
        while True:
            xs = np.nonzero(fg[row])[0]
            if xs.max() - xs.min() <= xr - xl + 12:
                break
            row -= sy
        tip_rows.append(row + sy)
    t0, t1 = tip_rows
    tips = [(py0 - t0) / S, (t1 - py0) / S]
    out["lug_tip_mm"] = {"top": round(tips[0], 3), "bottom": round(tips[1], 3), "mean": round(sum(tips) / 2, 3)}
    out["lug"] = {"inner_x_mm": f(((px0 - xl) + (xr - px0)) / 2), "tip_rows": tip_rows,
                  "notch_rows": [int(round(dcy - case_r)), int(round(dcy + case_r))]}
    widths = []
    for k in range(0, 160):
        s_mm = k * 0.1
        ws = []
        for sy, row0 in ((1, t0), (-1, t1)):
            row = int(round(row0 - sy * s_mm * S))
            xs = np.nonzero(fg[row])[0] if 0 <= row < h else []
            if len(xs) > 10:
                ws.append((xs.max() - xs.min()) / 2 / S)
        if len(ws) == 2:
            widths.append([round(s_mm, 2), round(float(np.mean(ws)), 3)])
    out["strap"] = {"half_width_by_s_mm": widths}
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "lug_gap_mm": f(xr - xl), "listed": LISTED,
                     "dial_vs_pivot_px": [round(dcx - px0, 1), round(dcy - py0, 1)],
                     "coin_edge_centre_vs_dial_px": [round(ccx - dcx, 1), round(ccy - dcy, 1)]}

    # ---- applied indices (about the dial centre) ----
    turn, dr = M["dot_turn_deg"], M["dot_ring_r"]
    dx, dy = mm((dcx, dcy))
    dots = [[round(dx + f(dr) * math.sin(math.radians(hr * 30 + turn)), 3), round(dy + f(dr) * math.cos(math.radians(hr * 30 + turn)), 3)]
            for hr in (1, 2, 4, 5, 7, 8, 10, 11)]
    out["indices"] = {"dots_mm": dots, "dot_r_mm": f(dr), "turn_deg": turn, "centre_mm": [dx, dy],
                      "dot_lume_r_mm": f(M["dot_lume_r"]), "frame_mm": f(M["frame_px"]),
                      "triangle_r_mm": [f(v) for v in M["triangle_px"]["r"]], "triangle_half_mm": f(M["triangle_px"]["half"]),
                      "bar_r_mm": [f(v) for v in M["bar_px"]["r"]], "bar_half_mm": f(M["bar_px"]["half"]),
                      "bar6_r_mm": [f(v) for v in M["bar6_px"]["r"]], "bar6_half_mm": f(M["bar6_px"]["half"]),
                      "layout": "applied polished frames with lume: triangle at 12, bars at 3 and 9, short bar at 6, dots elsewhere"}

    # ---- hands (about the pivot) ----
    hands = {}
    for name in ("hour_hand", "minute_hand", "seconds_hand"):
        hd = {}
        for k, v in M[name].items():
            if k == "angle_deg":
                hd[k] = v
            elif k == "counterweight":
                hd[k] = [[f(a), f(b)] for a, b in v]
            else:
                hd[k] = [f(x) for x in v] if isinstance(v, list) else f(v)
        hands[name.split("_")[0]] = hd
    out["hands"] = hands
    out["tails_mm"] = [mm(p) for p in M["tails"]]
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_outline_mm"] = f(M["outline_px"])
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [f(b[2] - b[0]), f(b[3] - b[1])],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("date_window", "logo", "print_seastar", "print_swiss_made", "crown_box"):
        out[k] = box(M[k])
    out["crown_teeth"] = M["crown_teeth"]
    out["crown_guard_mm"] = [mm(p) for p in M["guard"]]

    # ---- insert prints: light on black between the insert edges ----
    pr = (white & band).astype(np.uint8) * 255
    pr = cv2.morphologyEx(pr, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)
    pr = np.isin(lab, [i for i in range(1, n) if st[i, 4] >= 25]).astype(np.uint8) * 255
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(255 - pr)  # fill specks inside the strokes
    pr[np.isin(lab2, [i for i in range(2, n2) if st2[i, 4] < 12])] = 255
    x0b, y0b = int(dcx - rg["insert_out"] - 10), int(dcy - rg["insert_out"] - 10)
    sz = int(2 * rg["insert_out"] + 20)
    crop = pr[y0b:y0b + sz, x0b:x0b + sz]
    up = cv2.GaussianBlur(cv2.resize(crop, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
    to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
    pc = M["insert_pip"]
    out["insert_pip_mm"] = {"centre": mm(pc[:2]), "radius": f(pc[2])}
    out["insert_prints"] = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 12)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in rg.values():
            cv2.circle(ov, (int(dcx), int(dcy)), int(rk), (0, 0, 255), 1)
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 1, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 1, (0, 255, 0), -1)
        for name, hd in M.items():
            if name.endswith("_hand"):
                t = math.radians(hd["angle_deg"])
                L = hd["tip"]
                cv2.line(ov, (px0, py0), (int(px0 + L * math.sin(t)), int(py0 - L * math.cos(t))), (0, 255, 255), 1)
        for p in dots:
            cv2.circle(ov, P(p), int(M["dot_lume_r"]), (255, 0, 255), 1)
            cv2.circle(ov, P(p), int(M["dot_lume_r"] + M["frame_px"]), (255, 0, 255), 1)
        for k in ("date_window", "logo", "print_seastar", "print_swiss_made", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        cv2.polylines(ov, [np.array(M["guard"], np.int32)], True, (0, 200, 255), 1)
        for sh in out["insert_prints"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        for row in tip_rows:
            cv2.line(ov, (500, row), (1200, row), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "dial_centre_mm", "bezel_rings_mm", "insert_srgb", "lug_tip_mm",
                                           "lug", "checks")}, default=float), "->", dest,
          len(data["insert_prints"]), "insert prints", "strap", data["strap"]["half_width_by_s_mm"][::20])
