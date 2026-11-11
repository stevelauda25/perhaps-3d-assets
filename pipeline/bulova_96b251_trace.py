"""Measure the Bulova 96B251 (Lunar Pilot chronograph, 45 mm, black leather strap) official front render (1293 x 2048,
transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.bulova_96b251_trace [out.json] [overlay.png]   # default config/watches/bulova-96b251-trace.json

Same watch head and hand pose as the 96B258 render (pipeline/bulova_96b258_trace.py), drawn 1.17x larger: the 96B258 head
matches this render at 1.17x about the pivot (normalised correlation 0.966), so MANUAL_PX is the 96B258 one moved to this
pivot and scaled by 1.17, and the scale is the 96B258 one times 1.17 (the left flank touches the image edge here, so the
widest half width cannot anchor it; 45 mm Bulova official through the 96B258 render). The case is drawn symmetric about the hand pivot: per row the mean of the left and right half widths, the left one
where the crown or the 2/4 o'clock pusher shoulders widen the right side; those shoulders are kept as their own outlines.
mm, x right, y toward 12, origin = hand pivot. Hands, indices, rings, subdials, crown and bracelet joints are read from
gridded crops, straightened hand strips and radial profiles (MANUAL_PX).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/bulova-96b251/front_official_1293x2048.png"
OUT = ROOT / "config/watches/bulova-96b251-trace.json"
CASE_MM = 45.0  # Bulova official case diameter
LISTED = {"lug_width_mm": 20.0}
SIDE_GAP_PX = 3.5  # 96B258's 3 px x 1.17: the render's case centre sits right of the pivot
SCALE_PX_PER_MM = round(22.9111 * 1.17, 4)  # 96B258 scale x 1.17

MANUAL_PX = {
    "hand_pivot": [
        602,
        993
    ],
    "hour": {
        "angle_deg": 305.9,
        "outline": [
            [
                -7.0,
                15.2
            ],
            [
                58.5,
                15.2
            ],
            [
                257.4,
                12.9
            ],
            [
                269.1,
                10.5
            ],
            [
                280.8,
                3.5
            ],
            [
                286.6,
                0.6
            ]
        ]
    },
    "minute": {
        "angle_deg": 55.9,
        "outline": [
            [
                -7.0,
                14.6
            ],
            [
                70.2,
                14.6
            ],
            [
                374.4,
                12.6
            ],
            [
                386.1,
                10.9
            ],
            [
                397.8,
                5.3
            ],
            [
                407.2,
                1.2
            ]
        ]
    },
    "chrono": {
        "angle_deg": 212.8,
        "outline": [
            [
                -134.5,
                3.5
            ],
            [
                -126.4,
                10.5
            ],
            [
                -117.0,
                13.8
            ],
            [
                -70.2,
                10.5
            ],
            [
                -46.8,
                7.6
            ],
            [
                0.0,
                7.0
            ],
            [
                222.3,
                5.8
            ],
            [
                231.7,
                6.4
            ],
            [
                239.8,
                12.9
            ],
            [
                253.9,
                21.6
            ],
            [
                280.8,
                15.8
            ],
            [
                315.9,
                7.4
            ],
            [
                327.6,
                5.3
            ],
            [
                403.6,
                4.7
            ],
            [
                411.8,
                1.2
            ]
        ]
    },
    "lume_inset": 2.9,
    "hub_radius_px": [
        33.9,
        23.4
    ],
    "subs": {
        "centres": [
            [
                370.3,
                991.8
            ],
            [
                834.8,
                991.8
            ],
            [
                604.3,
                1225.8
            ]
        ],
        "radius": 93.6,
        "length": 84.2,
        "half": 2.9,
        "tail": 21.1,
        "hub": 15.2
    },
    "index": {
        "inner": 294.8,
        "outer": 388.4,
        "half": 13.5,
        "half_12": 31.0,
        "square_inner": 359.2,
        "square_half": 26.3,
        "frame": 5.8
    },
    "crown": {
        "angle_deg": 90.0,
        "r": [
            599.0,
            688.0
        ],
        "radius": 72.5,
        "teeth": 18
    },
    "crown_rows": [
        880,
        1102
    ],
    "lug_tips_y": [
        294,
        1693
    ],
    "notch": {
        "half": 267.9,
        "y": [
            464,
            1523
        ]
    },
    "rings_px": {
        "dial": 397.8,
        "chapter": 439.9,
        "bezel_in": 524.2,
        "bezel_out": 556.9
    },
    "date": [
        789,
        1182,
        858,
        1244
    ],
    "strap_half": 265.6,
}
ARTEFACTS = ["the left flank touches the image edge at 9 o'clock (rows 987-1004): those half widths are short by up to 1 px",
             "tachymeter, chapter ring, subdial tracks, date and all prints stay in the dial map"]


def trace(path=FRONT, overlay=None):
    im = load(path)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)[..., 3] > 128
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    t0, t1 = M["lug_tips_y"]
    c0, c1 = M["crown_rows"]
    rows, shoulders = [], {1: [], -1: []}
    for y in range(t0, t1 + 1):
        xs = np.nonzero(fg[y])[0]
        L, R = px0 - xs.min(), xs.max() - px0 - SIDE_GAP_PX
        side = R - L > 8
        h = L + SIDE_GAP_PX / 2 if side or c0 <= y <= c1 else (L + R + SIDE_GAP_PX) / 2
        rows.append((y, h))
        if side and not c0 <= y <= c1:
            shoulders[1 if y < py0 else -1].append((y, R + SIDE_GAP_PX / 2))
    S = SCALE_PX_PER_MM
    f = lambda v: round(float(v) / S, 3)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Bulova official) through the 96B258 render at 1.17x",
           "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}
    out["case_half_width_mm"] = [[f(py0 - y), f(h)] for y, h in rows[::4]]
    out["shoulders_mm"] = {("top" if k == 1 else "bottom"): [[f(py0 - y), f(r)] for y, r in v[::3]] for k, v in shoulders.items()}
    out["lug"] = {"photo_tips_mm": [f(py0 - t0), f(t1 - py0)], "tip_mm": f((t1 - t0) / 2), "notch_half_mm": f(M["notch"]["half"]),
                  "notch_y_mm": f((M["notch"]["y"][1] - M["notch"]["y"][0]) / 2)}
    out["strap"] = {"half_mm": f(M["strap_half"])}
    out["checks"] = {"photo_lug_to_lug_mm": f(t1 - t0), "strap_width_mm": f(2 * M["strap_half"]), "case_width_mm": f(2 * max(h for _, h in rows)), "listed": LISTED}
    hands = {}
    for name in ("hour", "minute", "chrono"):
        hm = M[name]
        hands[name] = {"angle_deg": hm["angle_deg"], "outline_mm": [[f(r), f(v)] for r, v in hm["outline"]], "length_mm": f(hm["outline"][-1][0])}
    out["hands"] = hands
    out["lume_inset_mm"] = f(M["lume_inset"])
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    sb = M["subs"]
    out["subs"] = {"centres_mm": [mm(c) for c in sb["centres"]], "radius_mm": f(sb["radius"]), "length_mm": f(sb["length"]), "half_mm": f(sb["half"]),
                   "tail_mm": f(sb["tail"]), "hub_mm": f(sb["hub"]), "angle_deg": 0.0}
    out["index"] = {k: f(v) for k, v in M["index"].items()}
    cr = M["crown"]
    out["crown"] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"]}
    d = M["date"]
    out["date_mm"] = mm(d[:2]) + mm(d[2:])
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2 + 60
        P = lambda x, y: (int(round(px0 + x * S)), int(round(py0 - y * S)))
        for v in M["rings_px"].values():
            cv2.circle(ov, (int(px0), int(py0)), int(v), (0, 0, 255), 1)
        for y, h in rows[::2]:
            for sx in (1, -1):
                cv2.circle(ov, (int(px0 + sx * h), y), 1, (0, 200, 255), -1)
        for v in shoulders.values():
            for y, r in v:
                cv2.circle(ov, (int(px0 + r), y), 1, (255, 0, 255), -1)
        for name in ("hour", "minute", "chrono"):
            hd = M[name]
            t = math.radians(hd["angle_deg"])
            pts = hd["outline"]
            poly = [(v * math.cos(t) + r * math.sin(t), -v * math.sin(t) + r * math.cos(t)) for r, v in pts] + \
                   [(-v * math.cos(t) + r * math.sin(t), v * math.sin(t) + r * math.cos(t)) for r, v in pts[::-1]]
            cv2.polylines(ov, [np.array([(int(px0 + x), int(py0 - y)) for x, y in poly], np.int32)], True, (0, 255, 255), 1)
        for cx, cy in sb["centres"]:
            cv2.circle(ov, (int(cx), int(cy)), int(sb["radius"]), (255, 128, 0), 1)
            cv2.line(ov, (int(cx), int(cy + sb["tail"])), (int(cx), int(cy - sb["length"])), (0, 255, 255), 1)
        ix = M["index"]
        for hr in range(12):
            t = math.radians(hr * 30)
            r0, hw = (ix["square_inner"], ix["square_half"]) if hr in (3, 6, 9) else (ix["inner"], ix["half_12"] if hr == 0 else ix["half"])
            q = [(hw, r0), (hw, ix["outer"]), (-hw, ix["outer"]), (-hw, r0)]
            cv2.polylines(ov, [np.array([(int(px0 + x * math.cos(t) + y * math.sin(t)), int(py0 - (-x * math.sin(t) + y * math.cos(t)))) for x, y in q], np.int32)],
                          True, (0, 255, 0), 1)
        n = M["notch"]
        for y in n["y"]:
            cv2.line(ov, (int(px0 - n["half"]), y), (int(px0 + n["half"]), y), (255, 128, 0), 1)
        for y in M["lug_tips_y"]:
            cv2.line(ov, (int(px0 - 300), y), (int(px0 + 300), y), (255, 128, 0), 1)
        for x in (-M["strap_half"], M["strap_half"]):
            cv2.line(ov, (int(px0 + x), 140), (int(px0 + x), 1900), (255, 128, 0), 1)
        cv2.circle(ov, P(*[(cr["r"][0] + cr["r"][1]) / 2 / S, 0]), 3, (0, 0, 255), -1)
        cv2.rectangle(ov, tuple(d[:2]), tuple(d[2:]), (0, 200, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "lug", "checks", "strap", "crown", "index")}, default=float), "->", dest)
