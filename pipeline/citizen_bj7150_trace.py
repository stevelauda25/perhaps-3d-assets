"""Measure the Citizen BJ7150-50W (Promaster Land GMT, 39.5 mm steel bezel, red textured dial, steel bracelet) official front
render (1295 x 2048, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.citizen_bj7150_trace [out.json] [overlay.png]   # default config/watches/citizen-bj7150-50w-trace.json

Anchor: the steel bezel's outer edge = 39.5 mm (Citizen's listed case width; the bracelet then measures 20.1 mm at the lug
tips against the listed 20 mm). mm, x right, y toward 12, origin = hand pivot. The case outline is centred 6 px below the pivot
in the render: bezel and case are placed about that centre, hands about the pivot. Hands are polygons read from axis profiles
and gridded crops (hand-local px: x across, + = clockwise side; y along the hand). The bezel's black 24-hour numerals and marks
are traced by threshold and become inlays. The textured dial, its printed lume numerals, the date and the flange stay in the
dial map.
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
FRONT = ROOT / "references/citizen-bj7150-50w/front_official_1295x2048.png"
OUT = ROOT / "config/watches/citizen-bj7150-50w-trace.json"
BEZEL_MM = 39.5  # Citizen: case width 39.5 mm = the steel bezel
LISTED = {"case_width_mm": 39.5, "lug_width_mm": 20.0, "thickness_mm": 13.5, "case_length_mm": 39.5}

MANUAL_PX = {
    "hand_pivot": [600, 899],
    "hands": {
        # hour: shaft with a lume panel, a barb, a pointed blade with a second lume panel
        "hour": {"angle_deg": 302.3, "body": [[-28.5, 30], [28.5, 30], [28.5, 102], [41, 120], [0, 243], [-41, 120], [-28.5, 102]],
                 "lume": [[[-20, 42], [20, 42], [20, 98], [-20, 98]], [[-30, 128], [30, 128], [0, 222]]]},
        # minute: long baton, pointed tip, lume panel
        "minute": {"angle_deg": 57.7, "body": [[-20, 30], [20, 30], [20, 335], [0, 358], [-20, 335]],
                   "lume": [[[-13, 62], [13, 62], [13, 328], [0, 344], [-13, 328]]]},
        # seconds: white needle with a tail and an oval counterweight
        "seconds": {"angle_deg": 211.3, "body": [[-4.5, -66], [4.5, -66], [4.5, 0], [2.0, 365], [-2.0, 365], [-4.5, 0]],
                    "counterweight": [[-6.5, 0], [-6.5, 66], [-10, 72], [-10, 144], [0, 152], [10, 144], [10, 72], [6.5, 66], [6.5, 0]]},
        # GMT: yellow stem and an outlined triangle with a lume fill
        "gmt": {"angle_deg": 150.8, "body": [[-4, 0], [4, 0], [4, 283], [40, 283], [0, 352], [-40, 283], [-4, 283]],
                "lume": [[[-27, 291], [27, 291], [0, 336]]]},
    },
    "hub_px": {"black": 34, "cap": 13},
    "crown_box": [1155, 840, 1257, 1000],  # knurled crown at 3
    "crown_teeth": 30,
    # the case flank bulges round the crown; inner points lie under the bezel
    "guard": [[1100, 760], [1170, 770], [1192, 800], [1198, 840], [1198, 1000], [1190, 1030], [1165, 1045], [1100, 1050]],
    "rings_px": {"dial_map": 438, "flange_in": 381, "bezel_in": 441, "bezel_out": 536},  # about the case centre
    "bezel_print_band": [452, 530],
    "lug_tip_rows": [276, 1519],
    # bracelet: three columns; brushed outer links, wide polished centre links, joints from the dark gaps
    "bracelet_joints_y": {"top_outer": [295, 145], "top_centre": [214, 95],
                          "bottom_outer": [1567, 1743, 1893], "bottom_centre": [1640, 1810, 1946]},
    "bracelet_centre_px": [447, 750],
    "end_link_x_px": [325, 871],
}
ARTEFACTS = ["the render is 27.1 px/mm: hand edges are +-2 px (+-0.07 mm)",
             "the bracelet ends turn away in the render: the far joints are closer; mean pitches are used",
             "the dial's lume numerals, triangle and bars are printed (not applied): they stay in the dial map"]


def trace(path=FRONT, overlay=None):
    raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    al = raw[..., 3:].astype(float) / 255
    im = (raw[..., :3] * al + 255 * (1 - al)).astype(np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = raw[..., 3] > 250
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * np.sin(np.radians(a)), c[1] - r * np.cos(np.radians(a)))

    # case outline on the flanks (lugs leave it above 306 / below 234 deg; the crown bulge at 64-116)
    edge = []
    for a in list(np.arange(235, 305.1, 1.0)) + list(np.arange(55, 64.1, 1.0)) + list(np.arange(116, 125.1, 1.0)):
        rs = np.arange(620, 450, -0.5)
        xs, ys = at(rs, a)
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[0]], ys[hit[0]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    rg = M["rings_px"]
    S = 2 * rg["bezel_out"] / BEZEL_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(float(v) / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"bezel outer edge = {BEZEL_MM} mm (Citizen case width)",
           "case": {"radius_mm": f(case_r), "centre_mm": mm((ccx, ccy))}, "rings_mm": {k: f(v) for k, v in rg.items()}}

    # ---- silhouette per y, lug tips ----
    prof = []
    for y_mm in np.arange(-36, 36.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    t0, t1 = M["lug_tip_rows"]
    tips = [(py0 - t0) / S, (t1 - py0) / S]
    out["lug_tip_mm"] = {"top": round(tips[0], 3), "bottom": round(tips[1], 3), "mean": round(sum(tips) / 2, 3)}

    # ---- bracelet ----
    j = M["bracelet_joints_y"]
    diffs = lambda v: [abs(a - b) for a, b in zip(v[1:], v[:-1])]
    out["bracelet_pitch_mm"] = {"outer": f(np.mean(diffs(j["top_outer"]) + diffs(j["bottom_outer"]))),
                                "centre": f(np.mean(diffs(j["top_centre"]) + diffs(j["bottom_centre"])))}
    out["bracelet_joints_mm"] = {k: [f(abs(y - py0)) for y in v] for k, v in j.items()}
    shift = [abs(j["top_outer"][0] - py0) - abs(j["top_centre"][0] - py0), abs(j["bottom_outer"][0] - py0) - abs(j["bottom_centre"][0] - py0)]
    out["bracelet_centre_joint_shift_mm"] = f(np.mean(shift))
    c0, c1 = M["bracelet_centre_px"]
    out["bracelet_centre_half_mm"] = f((c1 - c0) / 2)
    xl, xr = M["end_link_x_px"]
    out["end_link_half_mm"] = f((xr - xl) / 2)
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "end_link_width_mm": f(xr - xl), "case_outline_mm": f(2 * case_r),
                     "listed": LISTED, "case_centre_vs_pivot_px": [round(ccx - px0, 1), round(ccy - py0, 1)]}

    # ---- hands (hand-local px -> hand-local mm; the step rotates them) ----
    hands = {}
    for name, hd in M["hands"].items():
        hands[name] = {"angle_deg": hd["angle_deg"], "body_mm": [[f(a), f(b)] for a, b in hd["body"]],
                       "lume_mm": [[[f(a), f(b)] for a, b in lp] for lp in hd.get("lume", [])]}
        if "counterweight" in hd:
            hands[name]["counterweight_mm"] = [[f(a), f(b)] for a, b in hd["counterweight"]]
    out["hands"] = hands
    out["hub_mm"] = {k: f(v) for k, v in M["hub_px"].items()}
    b = M["crown_box"]
    out["crown"] = {"x_from_to_mm": [f(b[0] - px0), f(b[2] - px0)], "centre_y_mm": mm((0, (b[1] + b[3]) / 2))[1], "radius_mm": f((b[3] - b[1]) / 2),
                    "teeth": M["crown_teeth"]}
    out["crown_guard_mm"] = [mm(p) for p in M["guard"]]

    # ---- bezel prints: black on steel inside the print band ----
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - ccx, yy - ccy)
    b0, b1 = M["bezel_print_band"]
    pr = ((gray < 90) & (rr > b0) & (rr < b1)).astype(np.uint8) * 255
    pr = cv2.morphologyEx(pr, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)
    pr = np.isin(lab, [i for i in range(1, n) if st[i, 4] >= 30]).astype(np.uint8) * 255
    x0b, y0b = int(ccx - b1 - 4), int(ccy - b1 - 4)
    sz = int(2 * b1 + 8)
    crop = pr[y0b:y0b + sz, x0b:x0b + sz]
    up = cv2.GaussianBlur(cv2.resize(crop, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
    to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
    area = lambda lp: 0.5 * abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(lp, lp[1:] + lp[:1])))
    # the smallest marks are 0.43 mm2; a glint on the bezel edge near 10 traces as a 0.27 mm2 speck
    out["bezel_prints"] = [sh for sh in shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 20) if area(sh["outer"]) > 0.35]
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in rg.values():
            cv2.circle(ov, (int(ccx), int(ccy)), int(rk), (0, 0, 255), 1)
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 1, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 1, (0, 255, 0), -1)
        for name, hd in M["hands"].items():
            a = math.radians(hd["angle_deg"])
            loc = lambda q: (int(round(px0 + q[0] * math.cos(a) + q[1] * math.sin(a))), int(round(py0 + q[0] * math.sin(a) - q[1] * math.cos(a))))
            for lp in [hd["body"]] + hd.get("lume", []):
                cv2.polylines(ov, [np.array([loc(q) for q in lp], np.int32)], True, (0, 255, 255), 1)
            if "counterweight" in hd:
                a += math.pi
                cv2.polylines(ov, [np.array([loc(q) for q in hd["counterweight"]], np.int32)], True, (0, 255, 255), 1)
        cv2.rectangle(ov, tuple(M["crown_box"][:2]), tuple(M["crown_box"][2:]), (0, 200, 255), 1)
        cv2.polylines(ov, [np.array(M["guard"], np.int32)], True, (0, 200, 255), 1)
        for sh in out["bezel_prints"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (300, y), (900, y), (255, 128, 0), 1)
        for row in M["lug_tip_rows"]:
            cv2.line(ov, (150, row), (1100, row), (255, 0, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "rings_mm", "lug_tip_mm", "checks", "bracelet_pitch_mm",
                                           "bracelet_centre_joint_shift_mm", "bracelet_centre_half_mm", "end_link_half_mm")}, default=float),
          "->", dest, len(data["bezel_prints"]), "bezel prints")
