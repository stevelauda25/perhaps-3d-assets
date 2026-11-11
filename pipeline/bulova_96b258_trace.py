"""Measure the Bulova 96B258 (Lunar Pilot chronograph, 45 mm, steel bracelet) official front render (1243 x 2048, transparent
background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.bulova_96b258_trace [out.json] [overlay.png]   # default config/watches/bulova-96b258-trace.json

Anchor: 45 mm case (Bulova official) = twice the widest case half width on the alpha (left flank, the right one is under the
crown). The case is drawn symmetric about the hand pivot: per row the mean of the left and right half widths, the left one
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
FRONT = ROOT / "references/bulova-96b258/front_official_1243x2048.png"
OUT = ROOT / "config/watches/bulova-96b258-trace.json"
CASE_MM = 45.0  # Bulova official case diameter
LISTED = {"lug_width_mm": 20.0}
SIDE_GAP_PX = 3.0  # the silhouette is 3 px wider on the right everywhere: the render's case centre sits right of the pivot

MANUAL_PX = {
    "hand_pivot": [594, 997],  # hub hole (593-594) and the 9/3 subdial mid point (594.5)
    # outlines: [distance from the pivot, half width]; white lume hands in a thin polished frame
    "hour": {"angle_deg": 305.9, "outline": [[-6, 13], [50, 13], [220, 11], [230, 9], [240, 3], [245, 0.5]]},
    "minute": {"angle_deg": 55.9, "outline": [[-6, 12.5], [60, 12.5], [320, 10.8], [330, 9.3], [340, 4.5], [348, 1]]},
    "lume_inset": 2.5,
    # central chronograph seconds: white, counterweight to -115, lozenge at 200-280, needle to 352
    "chrono": {"angle_deg": 212.8, "outline": [[-115, 3], [-108, 9], [-100, 11.8], [-60, 9], [-40, 6.5], [0, 6], [190, 5], [198, 5.5],
                                               [205, 11], [217, 18.5], [240, 13.5], [270, 6.3], [280, 4.5], [345, 4], [352, 1]]},
    "hub_radius_px": [29, 20],
    # subdials at 9 (running seconds), 3 (1/10 s) and 6 (chrono minutes): white needles, all at 12 in the render
    "subs": {"centres": [[396, 996], [793, 996], [596, 1196]], "radius": 80, "length": 72, "half": 2.5, "tail": 18, "hub": 13},
    # applied polished frames with white lume: batons, a wide 12, small squares at 3, 6 and 9
    "index": {"inner": 252, "outer": 332, "half": 11.5, "half_12": 26.5, "square_inner": 307, "square_half": 22.5, "frame": 5},
    # dial flat to 340, sloped chapter ring (1/5 s ticks) to 376, black tachymeter flange to 448; polished bezel 448-476
    "rings_px": {"dial": 340, "chapter": 376, "bezel_in": 448, "bezel_out": 476},
    "crown": {"angle_deg": 90.0, "r": [512, 588], "radius": 62, "teeth": 18},
    "crown_rows": [900, 1090],
    "lug_tips_y": [400, 1595],
    "notch": {"half": 229, "y": [545, 1450]},  # the bracelet's end link sits in a recess between the case horns
    "bracelet": {"half": 227, "centre_half": 106, "pitch": 77, "centre_offset": 12},  # pitch: first links next to both ends
    "date": [754, 1159, 813, 1212],
}
ARTEFACTS = ["official render: the bracelet curves away from the camera, link pitch averaged on the first links at both ends (69 and 84 px)",
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
    S = 2 * max(h for _, h in rows) / CASE_MM
    f = lambda v: round(float(v) / S, 3)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Bulova official), widest case half width on the left flank",
           "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}
    out["case_half_width_mm"] = [[f(py0 - y), f(h)] for y, h in rows[::4]]
    out["shoulders_mm"] = {("top" if k == 1 else "bottom"): [[f(py0 - y), f(r)] for y, r in v[::3]] for k, v in shoulders.items()}
    out["lug"] = {"photo_tips_mm": [f(py0 - t0), f(t1 - py0)], "tip_mm": f((t1 - t0) / 2), "notch_half_mm": f(M["notch"]["half"]),
                  "notch_y_mm": f((M["notch"]["y"][1] - M["notch"]["y"][0]) / 2)}
    b = M["bracelet"]
    out["bracelet"] = {"half_mm": f(b["half"]), "centre_half_mm": f(b["centre_half"]), "pitch_mm": f(b["pitch"]), "centre_offset_mm": f(b["centre_offset"])}
    out["checks"] = {"photo_lug_to_lug_mm": f(t1 - t0), "bracelet_width_mm": f(2 * b["half"]), "listed": LISTED}
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
            cv2.circle(ov, (int(px0), int(py0)), v, (0, 0, 255), 1)
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
            cv2.circle(ov, (cx, cy), sb["radius"], (255, 128, 0), 1)
            cv2.line(ov, (cx, cy + sb["tail"]), (cx, cy - sb["length"]), (0, 255, 255), 1)
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
        for x in (-b["half"], -b["centre_half"], b["centre_half"], b["half"]):
            cv2.line(ov, (int(px0 + x), 140), (int(px0 + x), 1900), (255, 128, 0), 1)
        cv2.circle(ov, P(*[(cr["r"][0] + cr["r"][1]) / 2 / S, 0]), 3, (0, 0, 255), -1)
        cv2.rectangle(ov, tuple(d[:2]), tuple(d[2:]), (0, 200, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "lug", "checks", "bracelet", "crown", "index")}, default=float), "->", dest)
