"""Measure the Tissot T137.207.11.091.00 (PRX Powermatic 80, 35 mm, green waffle dial, integrated steel bracelet) official front
render (1680 x 1680, transparent background, a drop shadow down to the right) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.tissot_t137207_trace [out.json] [overlay.png]   # default config/watches/tissot-t137.207.11.091.00-trace.json

Anchor: 35 mm case width (Tissot official) = twice the widest left half width on the alpha (the right side carries the crown
and the shadow). The case is drawn symmetric about the hand pivot from the left silhouette. mm, x right, y toward 12, origin =
hand pivot. Hands, indices, date frame, rings, crown and bracelet joints are read from gridded crops, straightened hand
strips, radial profiles and column profiles (MANUAL_PX).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/tissot-t137.207.11.091.00/front_official_1680x1680.png"
OUT = ROOT / "config/watches/tissot-t137.207.11.091.00-trace.json"
CASE_MM = 35.0  # Tissot official case width
LISTED = {"case_length_mm": 35.0, "thickness_mm": 10.93}

MANUAL_PX = {
    "hand_pivot": [840, 838],
    # outlines: [distance from the pivot, half width]; faceted batons with a lume strip and a short tail
    "hour": {"angle_deg": 304.2, "outline": [[-44, 8], [-38, 13], [-20, 14.5], [150, 14.7], [156, 10], [160, 3]], "lume": [80, 148], "lume_half": 4},
    "minute": {"angle_deg": 49.8, "outline": [[-44, 8], [-38, 12], [-20, 14], [228, 14], [234, 10], [238, 3]], "lume": [88, 226], "lume_half": 4.5},
    "seconds": {"angle_deg": 216.8, "length": 255, "half": 2.5, "tail": 62, "tail_half": 5},
    "hub_radius_px": [16, 8],
    # applied polished batons (double at 12, none at 3: date), a grey lume inset at the inner end
    "index": {"inner": 188, "outer": 260, "half": 6, "double_offset": 6.5, "double_half": 5.5, "lume": [191, 205], "lume_half": 3.5},
    "date": {"frame": [1007, 805, 1080, 872], "opening": [1015, 812, 1072, 863]},
    # green waffle dial to 278, light rehaut to 290, dark crystal edge, polished bezel 292-325, then the case top
    "rings_px": {"dial": 278, "rehaut": 290, "bezel_in": 292, "bezel_out": 325},
    "crown": {"angle_deg": 90.0, "r": [343, 401], "radius": 40, "teeth": 12},
    "case_edge_y": [505, 1171],  # where the first bracelet links meet the case
    # integrated H-link bracelet: outer pieces start with a short link, centre pieces offset; both taper with the bracelet
    "bracelet": {"pitch": 76, "outer_first": 50, "centre_ratio": 0.45, "taper_per_px": 0.243},
}
ARTEFACTS = ["official render: the bracelet curves away from the camera, link pitch read on the first rows next to the case at both ends",
             "the right half of the alpha carries the crown and a drop shadow; the case is mirrored from the left half",
             "waffle dial, minute track, prints, lume dots and the date disc stay in the dial map"]


def trace(path=FRONT, overlay=None):
    im = load(path)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)[..., 3] > 128
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    e0, e1 = M["case_edge_y"]
    rows = []
    for y in range(e0, e1 + 1):
        xs = np.nonzero(fg[y])[0]
        rows.append((y, px0 - xs.min()))
    S = 2 * max(h for _, h in rows) / CASE_MM
    f = lambda v: round(float(v) / S, 3)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Tissot official), widest left half width",
           "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}
    out["case_half_width_mm"] = [[f(py0 - y), f(h)] for y, h in rows[::3]]
    tip = (e1 - e0) / 2
    edge_half = (rows[0][1] + rows[-1][1]) / 2
    b = M["bracelet"]
    out["lug"] = {"photo_tips_mm": [f(py0 - e0), f(e1 - py0)], "tip_mm": f(tip), "edge_half_mm": f(edge_half)}
    out["bracelet"] = {"half_at_tip_mm": f(edge_half), "taper_mm_per_mm": b["taper_per_px"], "pitch_mm": f(b["pitch"]), "outer_first_mm": f(b["outer_first"]),
                       "centre_ratio": b["centre_ratio"]}
    xs_top = [px0 - np.nonzero(fg[y])[0].min() for y in (148, 319, 490)]
    out["checks"] = {"photo_case_length_mm": f(e1 - e0), "bracelet_half_rows_148_319_490_mm": [f(v) for v in xs_top], "listed": LISTED}
    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        hands[name] = {"angle_deg": hm["angle_deg"], "outline_mm": [[f(r), f(v)] for r, v in hm["outline"]], "lume_mm": [f(v) for v in hm["lume"]],
                       "lume_half_mm": f(hm["lume_half"]), "length_mm": f(hm["outline"][-1][0])}
    sm = M["seconds"]
    hands["seconds"] = {"angle_deg": sm["angle_deg"], "length_mm": f(sm["length"]), "half_width_mm": f(sm["half"]), "tail_mm": f(sm["tail"]),
                        "tail_half_mm": f(sm["tail_half"])}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    ix = M["index"]
    out["index"] = {k: ([f(x) for x in v] if isinstance(v, list) else f(v)) for k, v in ix.items()}
    dt = M["date"]
    out["date_mm"] = {k: mm(v[:2]) + mm(v[2:]) for k, v in dt.items()}
    cr = M["crown"]
    out["crown"] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2 + 60
        for v in M["rings_px"].values():
            cv2.circle(ov, (px0, py0), v, (0, 0, 255), 1)
        for y, h in rows[::2]:
            for sx in (1, -1):
                cv2.circle(ov, (int(px0 + sx * h), y), 1, (0, 200, 255), -1)
        for name in ("hour", "minute"):
            hd = M[name]
            t = math.radians(hd["angle_deg"])
            pts = hd["outline"]
            poly = [(v * math.cos(t) + r * math.sin(t), -v * math.sin(t) + r * math.cos(t)) for r, v in pts] + \
                   [(-v * math.cos(t) + r * math.sin(t), v * math.sin(t) + r * math.cos(t)) for r, v in pts[::-1]]
            cv2.polylines(ov, [np.array([(int(px0 + x), int(py0 - y)) for x, y in poly], np.int32)], True, (0, 255, 255), 1)
        t = math.radians(sm["angle_deg"])
        cv2.line(ov, (int(px0 - sm["tail"] * math.sin(t)), int(py0 + sm["tail"] * math.cos(t))), (int(px0 + sm["length"] * math.sin(t)), int(py0 - sm["length"] * math.cos(t))),
                 (0, 255, 255), 1)
        for hr in range(12):
            if hr == 3:
                continue
            t = math.radians(hr * 30)
            for off, hw in (((-ix["double_offset"], ix["double_half"]), (ix["double_offset"], ix["double_half"])) if hr == 0 else ((0, ix["half"]),)):
                q = [(off + hw, ix["inner"]), (off + hw, ix["outer"]), (off - hw, ix["outer"]), (off - hw, ix["inner"])]
                cv2.polylines(ov, [np.array([(int(px0 + x * math.cos(t) + y * math.sin(t)), int(py0 - (-x * math.sin(t) + y * math.cos(t)))) for x, y in q], np.int32)],
                              True, (0, 255, 0), 1)
        for v in dt.values():
            cv2.rectangle(ov, tuple(v[:2]), tuple(v[2:]), (0, 200, 255), 1)
        for y in M["case_edge_y"]:
            cv2.line(ov, (px0 - 300, y), (px0 + 300, y), (255, 128, 0), 1)
        cv2.circle(ov, (int(px0 + (cr["r"][0] + cr["r"][1]) / 2), py0), 3, (0, 0, 255), -1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "lug", "checks", "bracelet", "crown", "index")}, default=float), "->", dest)
