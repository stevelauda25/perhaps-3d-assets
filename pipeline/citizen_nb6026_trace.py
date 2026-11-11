"""Measure the Citizen NB6026-56L (Promaster Fujitsubo, 41 mm titanium, blue dial, black insert in a blue coin-edge bezel,
titanium bracelet) official front render (1324 x 2048, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.citizen_nb6026_trace [out.json] [overlay.png]   # default config/watches/citizen-nb6026-56l-trace.json

Anchor: the bezel's coin edge = 41 mm (Citizen's listed case width; the bezel overhangs the case at 3 and 9). mm, x right, y
toward 12, origin = hand pivot. The bezel is centred 3.5 px below the pivot in the render: bezel and indices are placed about
that centre, hands about the pivot. Hands are polygons and circles read from axis profiles and gridded crops (hand-local px:
x across, + = clockwise side; y along the hand). Applied indices are rectangles (polished frame round lume) found by threshold.
The insert's silver numerals, bars, dots and triangle are traced by threshold and become inlays. The dial, its prints, the date
and the minute track stay in the dial map.
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
FRONT = ROOT / "references/citizen-nb6026-56l/front_official_1324x2048.png"
OUT = ROOT / "config/watches/citizen-nb6026-56l-trace.json"
BEZEL_MM = 41.0  # Citizen: case width 41 mm = the coin-edge bezel
LISTED = {"case_width_mm": 41.0, "lug_width_mm": 20.0, "thickness_mm": 12.2}

MANUAL_PX = {
    "hand_pivot": [620, 901],
    "bezel_centre": [620.7, 904.5],  # circle fitted to the coin edge on the flanks (r 585.2 px)
    "hands": {
        # hour: slotted shaft, a ring with a three-spoke lume disc, a pointed tip with a lume triangle
        "hour": {"angle_deg": 304.5, "body": [[[-9, 22], [9, 22], [9, 100], [-9, 100]], [[-24, 172], [24, 172], [0, 224]]],
                 "circles": [[137, 44]], "lume": [[[-12, 181], [12, 181], [0, 210]]], "lume_circles": [[137, 37]], "spokes": [60, 180, 300],
                 "spoke_half": 2.2},
        # minute: long baton with a pointed tip and a lume panel
        "minute": {"angle_deg": 62.5, "body": [[[-18, 22], [18, 22], [18, 312], [0, 340], [-18, 312]]],
                   "lume": [[[-11, 60], [11, 60], [11, 308], [0, 326], [-11, 308]]]},
        # seconds: needle with a short wide tail, lume dot in a ring near the tip
        "seconds": {"angle_deg": 213.6, "body": [[[-6, -72], [6, -72], [6, -20], [3.5, 0], [2, 345], [-2, 345], [-3.5, 0], [-6, -20]]],
                    "circles": [[246, 17]], "lume_circles": [[246, 12]]},
    },
    "hub_px": {"disc": 30, "pin": 8},
    # applied indices about the bezel centre: polished frame round lume; [hour, r0, r1, half, kind] of the lume, frame 10.5 px
    "indices": {"frame": 10.5, "normal": {"hours": [1, 2, 4, 5, 7, 8, 10, 11], "r": [270, 344], "half": 16.3},
                "wide": {"hours": [6, 9], "r": [262, 350], "half": 23.2}, "twelve": {"hours": [0], "r": [257, 347], "half": 30},
                "three": {"hours": [3], "r": [350, 358], "half": 29}},  # short index beside the date: radial 8, across 58
    "crown_box": [1200, 840, 1285, 990],  # fluted crown at 3
    "crown_teeth": 20,
    "rings_px": {"dial_map": 442, "insert_in": 444, "insert_out": 548, "rim_out": 585.2},  # about the bezel centre
    "insert_print_band": [452, 543],
    "insert_pip": [622, 380, 13],  # lume pip in the insert triangle at 12 (x, y, radius)
    "bezel_notches": 72,
    "lug_tip_rows": [245, 1606],
    # bracelet: three columns; brushed outer links, wide polished centre links. The top end is foreshortened in the render:
    # the bottom joints set the pitch
    "bracelet_joints_y": {"top_outer": [238], "top_centre": [204],
                          "bottom_outer": [1639, 1790, 1935], "bottom_centre": [1680, 1832, 1964]},
    "bracelet_centre_px": [452, 786],
    "end_link_x_px": [342, 896],
}
ARTEFACTS = ["the render is 28.5 px/mm: hand edges are +-2 px (+-0.07 mm)",
             "the render is slightly perspective: the bottom lug tip is 1.7 mm farther from the pivot than the top; the mean is used",
             "the crystal's chamfer mirrors the index ends near the rim; those reflections stay in the dial map",
             "the hour hand's shaft is slotted in the render; it is built solid"]


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

    ccx, ccy = M["bezel_centre"]
    rg = M["rings_px"]
    S = 2 * rg["rim_out"] / BEZEL_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(float(v) / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"coin-edge bezel = {BEZEL_MM} mm (Citizen case width)",
           "bezel_centre_mm": mm((ccx, ccy)), "rings_mm": {k: f(v) for k, v in rg.items()}, "bezel_notches": M["bezel_notches"]}

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
    out["bracelet_pitch_mm"] = {"outer": f(np.mean(diffs(j["bottom_outer"]))), "centre": f(np.mean(diffs(j["bottom_centre"])))}
    out["bracelet_joints_mm"] = {k: [f(abs(y - py0)) for y in v] for k, v in j.items()}
    shift = [abs(j["top_outer"][0] - py0) - abs(j["top_centre"][0] - py0), abs(j["bottom_outer"][0] - py0) - abs(j["bottom_centre"][0] - py0)]
    out["bracelet_centre_joint_shift_mm"] = f(np.mean(shift))
    c0, c1 = M["bracelet_centre_px"]
    out["bracelet_centre_half_mm"] = f((c1 - c0) / 2)
    xl, xr = M["end_link_x_px"]
    out["end_link_half_mm"] = f((xr - xl) / 2)
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "end_link_width_mm": f(xr - xl), "listed": LISTED,
                     "bezel_centre_vs_pivot_px": [round(ccx - px0, 1), round(ccy - py0, 1)]}

    # ---- hands (hand-local px -> hand-local mm; the step rotates them) ----
    hands = {}
    for name, hd in M["hands"].items():
        hands[name] = {"angle_deg": hd["angle_deg"], "body_mm": [[[f(a), f(b)] for a, b in lp] for lp in hd["body"]],
                       "lume_mm": [[[f(a), f(b)] for a, b in lp] for lp in hd.get("lume", [])],
                       "circles_mm": [[f(a), f(b)] for a, b in hd.get("circles", [])],
                       "lume_circles_mm": [[f(a), f(b)] for a, b in hd.get("lume_circles", [])]}
        if "spokes" in hd:
            hands[name]["spokes_deg"], hands[name]["spoke_half_mm"] = hd["spokes"], f(hd["spoke_half"])
    out["hands"] = hands
    ix = M["indices"]
    out["indices"] = {"centre_mm": mm((ccx, ccy)), "frame_mm": f(ix["frame"]),
                      "kinds": {k: {"hours": v["hours"], "r_mm": [f(x) for x in v["r"]], "half_mm": f(v["half"])} for k, v in ix.items() if k != "frame"}}
    out["hub_mm"] = {k: f(v) for k, v in M["hub_px"].items()}
    pc = M["insert_pip"]
    out["insert_pip_mm"] = {"centre": mm(pc[:2]), "radius": f(pc[2])}
    b = M["crown_box"]
    out["crown"] = {"x_from_to_mm": [f(b[0] - px0), f(b[2] - px0)], "centre_y_mm": mm((0, (b[1] + b[3]) / 2))[1], "radius_mm": f((b[3] - b[1]) / 2),
                    "teeth": M["crown_teeth"]}

    # ---- insert prints: silver on black inside the print band ----
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - ccx, yy - ccy)
    b0, b1 = M["insert_print_band"]
    pr = ((gray > 90) & (rr > b0) & (rr < b1)).astype(np.uint8) * 255  # the silver numerals are grained: close the grain
    pr = cv2.morphologyEx(cv2.morphologyEx(pr, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)
    pr = np.isin(lab, [i for i in range(1, n) if st[i, 4] >= 30]).astype(np.uint8) * 255
    x0b, y0b = int(ccx - b1 - 4), int(ccy - b1 - 4)
    sz = int(2 * b1 + 8)
    crop = pr[y0b:y0b + sz, x0b:x0b + sz]
    up = cv2.GaussianBlur(cv2.resize(crop, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
    to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
    area = lambda lp: 0.5 * abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(lp, lp[1:] + lp[:1])))
    out["insert_prints"] = [sh for sh in shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 20) if area(sh["outer"]) > 0.08]
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in rg.values():
            cv2.circle(ov, (int(ccx), int(ccy)), int(rk), (0, 0, 255), 1)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 1, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 1, (0, 255, 0), -1)
        for name, hd in M["hands"].items():
            a = math.radians(hd["angle_deg"])
            loc = lambda q: (int(round(px0 + q[0] * math.cos(a) + q[1] * math.sin(a))), int(round(py0 + q[0] * math.sin(a) - q[1] * math.cos(a))))
            for lp in hd["body"] + hd.get("lume", []):
                cv2.polylines(ov, [np.array([loc(q) for q in lp], np.int32)], True, (0, 255, 255), 1)
            for al_, rad in hd.get("circles", []) + hd.get("lume_circles", []):
                cv2.circle(ov, loc((0, al_)), int(rad), (0, 255, 255), 1)
        for k, v in M["indices"].items():
            if k == "frame":
                continue
            for hr in v["hours"]:
                a = math.radians(hr * 30)
                loc = lambda q: (int(round(ccx + q[0] * math.cos(a) + q[1] * math.sin(a))), int(round(ccy + q[0] * math.sin(a) - q[1] * math.cos(a))))
                (r0, r1), hw = v["r"], v["half"]
                cv2.polylines(ov, [np.array([loc(q) for q in ((-hw, r0), (hw, r0), (hw, r1), (-hw, r1))], np.int32)], True, (255, 0, 255), 1)
        cv2.rectangle(ov, tuple(M["crown_box"][:2]), tuple(M["crown_box"][2:]), (0, 200, 255), 1)
        for sh in out["insert_prints"]:
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
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "bezel_centre_mm", "rings_mm", "lug_tip_mm", "checks", "bracelet_pitch_mm",
                                           "bracelet_centre_joint_shift_mm", "bracelet_centre_half_mm", "end_link_half_mm")}, default=float),
          "->", dest, len(data["insert_prints"]), "insert prints")
