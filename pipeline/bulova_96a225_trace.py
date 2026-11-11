"""Measure the Bulova 96A225 (Lunar Pilot, 45 mm chronograph, black dial, black NATO strap) official front render (1208 x 2048,
transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.bulova_96a225_trace [out.json] [overlay.png]   # default config/watches/bulova-96a225-trace.json

Anchor: 45 mm case width (Bulova) = twice the left flank's widest half from the hand pivot (the right flank carries the crown
and the pushers); the strap then measures 19.8 mm against the listed 20 mm lug width. mm, x right, y toward 12, origin = hand
pivot. The rings (dial, flange, tachymeter, polished bezel) are centred 4.3 px below the pivot (render perspective): bezel and
indices are placed about that centre, hands about the pivot. Hands, subdials and the crown come from axis profiles and gridded
crops (hand-local px: x across, + = clockwise side; y along the hand). Applied indices (polished frame round lume) found by
threshold. The dial, subdials, flange, tachymeter ring and prints stay in the dial map; the NATO strap is a photo map.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/bulova-96a225/front_official_1208x2048.png"
OUT = ROOT / "config/watches/bulova-96a225-trace.json"
CASE_MM = 45.0
LISTED = {"case_width_mm": 45.0, "lug_width_mm": 20.0, "thickness_mm": 10.3, "case_length_mm": 52.8}

MANUAL_PX = {
    "hand_pivot": [571.5, 1082.0],
    "hands": {
        # hour / minute: white lume batons in a polished frame, pointed tip
        "hour": {"angle_deg": 299.4, "body": [[[-13, 26], [13, 26], [12, 232], [0, 256], [-12, 232]]],
                 "lume": [[[-8.5, 34], [8.5, 34], [7.5, 230], [0, 246], [-7.5, 230]]]},
        "minute": {"angle_deg": 55.8, "body": [[[-11, 26], [11, 26], [10, 340], [0, 364], [-10, 340]]],
                   "lume": [[[-6.5, 34], [6.5, 34], [6, 338], [0, 354], [-6, 338]]]},
        # chrono: white needle with a lozenge, thin pointer over the 12 index, tail widening to a rounded end
        "chrono": {"angle_deg": 0.2, "body": [[[-5.5, -116], [5.5, -116], [12, -108], [12, -100], [6.5, 0], [5.5, 215], [19.5, 240], [3.5, 268],
                                                [2.0, 370], [-2.0, 370], [-3.5, 268], [-19.5, 240], [-5.5, 215], [-6.5, 0], [-12, -100],
                                                [-12, -108]]]},
    },
    "hub_px": {"disc": 30, "ring": 20, "pin": 4},
    # subdials: pivot (px), hand angle, length, half width; white needles on small polished hubs
    "subdials": {"9": [[358, 1086], 0.0, 96, 2.6, 11], "3": [[779, 1087], 0.0, 102, 2.6, 11], "6": [[570, 1300], 222.0, 76, 2.6, 11]},
    # applied indices about the ring centre (outer size incl. the 4 px polished frame): [r0, r1, half]
    "indices": {"frame": 5.0, "bar": {"hours": [1, 2, 4, 5, 7, 8, 10, 11], "r": [269, 356], "half": 12.8},
                "wide": {"hours": [3, 6, 9], "r": [325, 356], "half": 25.0}, "twelve": {"hours": [0], "r": [239, 359], "half": 28.0}},
    "ring_centre": [571.6, 1086.3],  # circle fitted to the tachymeter ring's outer edge (r 466 px)
    "rings_px": {"dial_out": 358, "flange_out": 395, "tach_out": 466, "bezel_out": 501},
    "crown_box": [1098, 999, 1176, 1175],  # fluted crown at 3 (case edge to crown end)
    "crown_teeth": 24,
    "crown_rows": [990, 1190],  # rows where the crown, not the case, is the right silhouette
}
ARTEFACTS = ["the render is 24.0 px/mm: hand and index edges are +-2 px (+-0.08 mm)",
             "the pushers at 2 and 4 are part of the right silhouette: the case slab follows both edges",
             "the subdial hands are thin (0.2 mm); their shapes are estimates"]


def trace(path=FRONT, overlay=None):
    raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    al = raw[..., 3:].astype(float) / 255
    im = (raw[..., :3] * al + 255 * (1 - al)).astype(np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = raw[..., 3] > 250
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    rcx, rcy = M["ring_centre"]

    # scale: the left flank's widest half from the pivot (case rows only)
    lefts = [(px0 - np.nonzero(fg[r])[0].min(), r) for r in range(700, 1450)]
    half_px, widest_row = max(lefts)
    S = 2 * half_px / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(float(v) / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Bulova) = twice the left flank half at row {widest_row}",
           "ring_centre_mm": mm((rcx, rcy)), "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}

    # ---- strap width and the case's top / bottom edges (first row from the centre where the outline is the strap) ----
    strap_w = float(np.median([np.ptp(np.nonzero(fg[r])[0]) for r in list(range(250, 420)) + list(range(1760, 1860))]))
    edges = []
    for sy in (1, -1):
        row = int(round(py0 - sy * 20 * S))
        while np.ptp(np.nonzero(fg[row])[0]) > strap_w + 12:
            row -= sy
        edges.append(row + sy)
    t0, t1 = edges
    tips = [(py0 - t0) / S, (t1 - py0) / S]
    out["case_edge_mm"] = {"top": round(tips[0], 3), "bottom": round(tips[1], 3), "mean": round(sum(tips) / 2, 3)}
    out["case_edge_rows"] = edges

    # ---- case outline: left and right edge per y (right edge bridged across the crown rows) ----
    c0, c1 = M["crown_rows"]
    xr_c0, xr_c1 = np.nonzero(fg[c0])[0].max(), np.nonzero(fg[c1])[0].max()
    left, right = [], []
    for row in range(t0, t1 + 1):
        xs = np.nonzero(fg[row])[0]
        xr = xs.max() if not c0 <= row <= c1 else xr_c0 + (xr_c1 - xr_c0) * (row - c0) / (c1 - c0)
        y_mm = -(row - py0) / S
        left.append([round(y_mm, 3), f(xs.min() - px0)])
        right.append([round(y_mm, 3), f(xr - px0)])
    out["case_outline_mm"] = {"left": left[::4] + [left[-1]], "right": right[::4] + [right[-1]]}

    # strap half width per mm from the case edge outward (both ends averaged)
    widths = []
    for k in range(0, 260):
        s_mm = k * 0.1
        ws = []
        for sy, row0 in ((1, t0), (-1, t1)):
            row = int(round(row0 - sy * s_mm * S))
            xs = np.nonzero(fg[row])[0] if 0 <= row < h else []
            if len(xs) > 10:
                ws.append(np.ptp(xs) / 2 / S)
        if len(ws) == 2:
            widths.append([round(s_mm, 2), round(float(np.mean(ws)), 3)])
    out["strap"] = {"half_width_by_s_mm": widths, "width_mm": f(strap_w)}
    out["checks"] = {"case_length_mm": round(sum(tips), 2), "strap_width_mm": f(strap_w), "listed": LISTED,
                     "ring_centre_vs_pivot_px": [round(rcx - px0, 1), round(rcy - py0, 1)]}

    # ---- hands, subdials, indices, crown ----
    hands = {}
    for name, hd in M["hands"].items():
        hands[name] = {"angle_deg": hd["angle_deg"], "body_mm": [[[f(a), f(b)] for a, b in lp] for lp in hd["body"]],
                       "lume_mm": [[[f(a), f(b)] for a, b in lp] for lp in hd.get("lume", [])]}
    out["hands"] = hands
    out["hub_mm"] = {k: f(v) for k, v in M["hub_px"].items()}
    out["subdials"] = {k: {"centre_mm": mm(c), "angle_deg": a, "length_mm": f(L), "half_mm": f(hw), "hub_mm": f(hb)}
                       for k, (c, a, L, hw, hb) in M["subdials"].items()}
    ix = M["indices"]
    out["indices"] = {"centre_mm": mm((rcx, rcy)), "frame_mm": f(ix["frame"]),
                      "kinds": {k: {"hours": v["hours"], "r_mm": [f(x) for x in v["r"]], "half_mm": f(v["half"])} for k, v in ix.items() if k != "frame"}}
    b = M["crown_box"]
    out["crown"] = {"x_from_to_mm": [f(b[0] - px0), f(b[2] - px0)], "centre_y_mm": mm((0, (b[1] + b[3]) / 2))[1], "radius_mm": f((b[3] - b[1]) / 2),
                    "teeth": M["crown_teeth"]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in M["rings_px"].values():
            cv2.circle(ov, (int(rcx), int(rcy)), int(rk), (0, 0, 255), 1)
        for k in ("left", "right"):
            for y_mm, x_mm in out["case_outline_mm"][k]:
                cv2.circle(ov, P((x_mm, y_mm)), 1, (0, 255, 0), -1)
        for name, hd in M["hands"].items():
            a = math.radians(hd["angle_deg"])
            loc = lambda q: (int(round(px0 + q[0] * math.cos(a) + q[1] * math.sin(a))), int(round(py0 + q[0] * math.sin(a) - q[1] * math.cos(a))))
            for lp in hd["body"] + hd.get("lume", []):
                cv2.polylines(ov, [np.array([loc(q) for q in lp], np.int32)], True, (0, 255, 255), 1)
        for (c, a, L, hw, hb) in M["subdials"].values():
            t = math.radians(a)
            cv2.line(ov, tuple(int(v) for v in c), (int(c[0] + L * math.sin(t)), int(c[1] - L * math.cos(t))), (0, 255, 255), 1)
        for k, v in ix.items():
            if k == "frame":
                continue
            for hr in v["hours"]:
                a = math.radians(hr * 30)
                loc = lambda q: (int(round(rcx + q[0] * math.cos(a) + q[1] * math.sin(a))), int(round(rcy + q[0] * math.sin(a) - q[1] * math.cos(a))))
                (r0, r1), hw = v["r"], v["half"]
                cv2.polylines(ov, [np.array([loc(q) for q in ((-hw, r0), (hw, r0), (hw, r1), (-hw, r1))], np.int32)], True, (255, 0, 255), 1)
        cv2.rectangle(ov, tuple(M["crown_box"][:2]), tuple(M["crown_box"][2:]), (0, 200, 255), 1)
        for row in edges:
            cv2.line(ov, (200, row), (1000, row), (255, 0, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "ring_centre_mm", "rings_mm", "case_edge_mm", "case_edge_rows", "checks")}, default=float),
          "->", dest, "strap", data["strap"]["half_width_by_s_mm"][::30])
