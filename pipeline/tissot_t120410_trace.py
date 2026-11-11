"""Measure the Tissot T120.410.11.051.00 (Seastar 1000 Quartz, 40 mm, black dial, black insert, steel bracelet) official
front render (1680 x 1680, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.tissot_t120410_trace [out.json] [overlay.png]   # default config/watches/tissot-t120.410.11.051.00-trace.json

Same method as pipeline/tissot_t120407_trace.py (bracelet joints as pipeline/tissot_t120607_trace.py). Anchor: 40 mm case width (Tissot official) from a circle fitted to the coin-edge
bezel on the flanks (alpha > 250: the render's drop shadow is semi-transparent). mm, x right, y toward 12, origin = hand pivot.
The dial centre sits 0.7 px right of and 6.7 px below the pivot in the render: indices and bezel are placed about the dial
centre, hands about the pivot. Hands, indices, crown and crown guard come from gridded crops and axis profiles (MANUAL_PX,
+-2 px = +-0.1 mm). The insert's white prints are traced by threshold and become inlays; the dial, its prints, the date, the
grey flange and its minute track stay in the dial map.
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
FRONT = ROOT / "references/tissot-t120.410.11.051.00/front_official_1680x1680.png"
OUT = ROOT / "config/watches/tissot-t120.410.11.051.00-trace.json"
CASE_MM = 40.0  # Tissot official case width: the coin-edge bezel is the widest part at 3 and 9
LISTED = {"lug_width_mm": 20.0, "thickness_mm": 9.97, "case_length_mm": 40.0}

MANUAL_PX = {
    "hand_pivot": [840, 840],
    "dial_centre": [840.7, 846.7],  # circle through the eight lume dot frames (r 252.6 px)
    # hour: broad baton, polished frame round a lume panel, short pointed tip
    "hour_hand": {"angle_deg": 303.5, "tip": 170, "shoulder": 150, "half": 19.5, "lume": [45, 158, 11]},
    # minute: long baton, polished frame round a lume panel, pointed tip
    "minute_hand": {"angle_deg": 50.8, "tip": 258, "shoulder": 240, "half": 15.5, "lume": [90, 248, 9]},
    # seconds: polished needle, lume dot in a polished ring, short tip past it; T-shaped counterweight
    "seconds_hand": {"angle_deg": 218.3, "half": 3.5, "ring_r": 252, "ring": [6, 12], "tip": 292,
                     "counterweight": [[-6.5, 0], [-6.5, 63], [-21, 63], [-21, 80], [34, 80], [28, 63], [5.5, 63], [5.5, 0]]},
    # the hour and minute tails below the hub, read as one polished outline (image px)
    "tails": [[812, 848], [795, 872], [802, 882], [822, 866], [840, 867], [880, 883], [888, 870], [872, 845], [858, 852], [840, 848]],
    "hub_radius_px": [15, 6],
    "outline_px": 5,
    # applied indices about the dial centre: polished frame round lume. Dots, triangle at 12, bars at 3 and 9; date frame at 6
    "dot_ring_r": 252.6, "dot_turn_deg": -0.26, "dot_lume_r": 13.0, "frame_px": 6.5,
    "triangle_px": {"r": [225, 264], "half": 29},
    "bar_px": {"r": [219, 267], "half": 11},
    "date_frame": {"outer": [811, 1020, 871, 1085], "inner": [822, 1030, 860, 1077]},  # polished frame round the date (8)
    "date_window": [811, 1020, 871, 1085],
    "logo": [770, 655, 912, 718],  # TISSOT 1853
    "print_seastar": [745, 955, 935, 1000],  # SEASTAR, 30 bar (300m / 1000 ft)
    "print_swiss_made": [775, 1112, 910, 1140],
    "crown_box": [1238, 785, 1300, 900],  # guard edge to the end of the crown
    "crown_teeth": 20,
    "guard": [[1180, 725], [1225, 728], [1250, 745], [1265, 770], [1268, 795], [1245, 805], [1245, 885], [1268, 895], [1265, 925],
              [1250, 945], [1225, 958], [1180, 960]],
    "bezel_rings_px": {"dial_out": 285, "lip_in": 302, "insert_in": 306, "insert_out": 370},  # about the dial centre
    "bezel_notch_count": 90,
    # bracelet: three columns, brushed outer links, polished centre links of a shorter pitch
    "bracelet_joints_y": {"top_outer": [392, 280], "top_centre": [430, 338, 236],
                          "bottom_outer": [1310, 1425], "bottom_centre": [1270, 1368, 1458]},
    "bracelet_centre_px": [742, 935],
    "end_link_x_px": [640, 1040],
}
ARTEFACTS = ["the render is 19.6 px/mm: hand and index edges are +-2 px (+-0.1 mm)",
             "the hands are rendered with a visible side wall on one side; the top face width is used",
             "the bracelet ends turn away in the render: the last joints are closer; the first pitches are used",
             "the date (8) stays in the dial map; its polished frame is geometry"]


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

    # coin-edge bezel on the flanks: the lugs leave it above 316 / below 224 deg (and 44 / 136), the crown guard at 62-120
    edge = []
    for a in list(np.arange(226, 314.1, 1.0)) + list(np.arange(46, 60.1, 1.0)) + list(np.arange(122, 134.1, 1.0)):
        rs = np.arange(360, 420, 0.5)
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
    white = (hsv[..., 1] < 60) & (hsv[..., 2] > 110)  # glare on the insert reaches V 70
    out["insert_srgb"] = [round(float(v) / 255, 3) for v in np.median(im[band & ~white & (gray < 60)][:, ::-1], 0)]

    # ---- silhouette per y (alpha), lug tips, bracelet joints ----
    prof = []
    for y_mm in np.arange(-43, 43.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    xl, xr = M["end_link_x_px"]
    tip_rows = []
    for sy in (1, -1):  # first row past the case where the outline drops to the bracelet (lug tip chamfer included)
        row = int(round(py0 - sy * 20 * S))
        while True:
            xs = np.nonzero(fg[row])[0]
            if xs.max() - xs.min() <= M["end_link_x_px"][1] - M["end_link_x_px"][0] + 12:
                break
            row -= sy
        tip_rows.append(row + sy)
    t0, t1 = tip_rows
    tips = [(py0 - t0) / S, (t1 - py0) / S]
    out["lug_tip_mm"] = {"top": round(tips[0], 3), "bottom": round(tips[1], 3), "mean": round(sum(tips) / 2, 3)}
    out["lug"] = {"tip_rows": tip_rows}
    j = M["bracelet_joints_y"]
    diffs = lambda v: [abs(a - b) for a, b in zip(v[1:], v[:-1])]
    out["bracelet_pitch_mm"] = {"outer": f(np.mean(diffs(j["top_outer"]) + diffs(j["bottom_outer"]))),
                                "centre": f(np.mean(diffs(j["top_centre"]) + diffs(j["bottom_centre"])))}
    out["bracelet_joints_mm"] = {k: [f(abs(y - py0)) for y in v] for k, v in j.items()}
    shift = [abs(j["top_outer"][0] - py0) - abs(j["top_centre"][0] - py0), abs(j["bottom_outer"][0] - py0) - abs(j["bottom_centre"][0] - py0)]
    out["bracelet_centre_joint_shift_mm"] = f(np.mean(shift))
    c0, c1 = M["bracelet_centre_px"]
    out["bracelet_centre_half_mm"] = f((c1 - c0) / 2)
    out["end_link_half_mm"] = f((xr - xl) / 2)
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "end_link_width_mm": f(xr - xl), "listed": LISTED,
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
                      "layout": "applied polished frames with lume: triangle at 12, bars at 3 and 9, dots elsewhere; a polished date frame at 6"}

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
    out["date_frame_mm"] = {k: mm(v[:2]) + mm(v[2:]) for k, v in M["date_frame"].items()}
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
          len(data["insert_prints"]), "insert prints")
