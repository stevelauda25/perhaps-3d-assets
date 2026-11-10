"""Measure the Hamilton H69439940 front photo (native 1869 x 2909) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.hamilton_h69439940_trace [out.json] [overlay.png]   # default config/watches/hamilton-h69439940-trace.json

Same method as pipeline/orient_ra_ac0p03l10b_trace.py. Anchor: case diameter 38.0 mm (Hamilton official), read on the 9-3 row
from the case edge to the crown root; the strap width (20 mm official) and lug to lug (47 mm listed) are reported as checks.
mm, x right, y toward 12, origin = the hand pivot. Hands, crown and bezel radii come from gridded crops (MANUAL_PX).
Hands are stored as parts (polygons in hand-local mm: x across, y along the hand) so one build step and one dial mask serve
every hand shape. trace() is shared with pipeline/hamilton_h70405710_trace.py.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/hamilton-h69439940/front_1869x2909.jpg"
OUT = ROOT / "config/watches/hamilton-h69439940-trace.json"
CASE_MM = 38.0  # Hamilton official
LISTED = {"lug_to_lug_mm": 47.0, "strap_width_mm": 20.0, "thickness_mm": 9.5}  # Hamilton: 20 mm, 9.5 mm; lug to lug from reviews


def profile(prof):
    """Half-width profile [[distance along, half width], ...] -> polygon mirrored about the hand axis."""
    return [(w, r) for r, w in prof] + [(-w, r) for r, w in prof[::-1] if w > 1e-6]


def circle(cy, rad, n=40, cx=0.0):
    return [(cx + rad * math.cos(2 * math.pi * i / n), cy + rad * math.sin(2 * math.pi * i / n)) for i in range(n)]


def leaf(cy, length, half, cx=0.0, n=12):
    """Pointed-oval petal along the hand axis, centred at (cx, cy)."""
    side = [(cx + half * math.sin(math.pi * k / n), cy - length / 2 + length * k / n) for k in range(n + 1)]
    return side + [(2 * cx - x, y) for x, y in side[-2:0:-1]]


# shapes in px about the hand pivot (x across, y along the hand); layer 0 = hand body, 1 = on top of it (lume)
HANDS_PX = {
    "hour": {"angle_deg": 304.0, "z": "hour", "parts": [
        {"mat": "hand", "layer": 0, "poly": profile([[-8, 23], [50, 23], [200, 27.2], [232, 29.5], [246, 33], [254, 26], [260, 16],
                                                    [270, 11], [285, 7.5], [300, 5], [307, 0]])},
        {"mat": "lume_hands", "layer": 1, "poly": profile([[66, 13], [150, 15.5], [235, 18], [245, 15], [252, 9], [258, 4], [263, 0]])}]},
    "minute": {"angle_deg": 42.9, "z": "minute", "parts": [
        {"mat": "hand", "layer": 0, "poly": profile([[-8, 17], [40, 17], [200, 20.9], [300, 22.75], [375, 24.4], [383, 22], [392, 16],
                                                    [402, 12], [412, 9], [422, 7], [440, 6], [448, 4], [452, 0]])},
        {"mat": "lume_hands", "layer": 1, "poly": profile([[68, 6.5], [100, 8.2], [200, 10.6], [300, 11.7], [370, 14.3], [382, 11],
                                                          [390, 6], [395, 0]])}]},
    "seconds": {"angle_deg": 161.25, "z": "seconds", "parts": [
        {"mat": "hand", "layer": 0, "poly": [(-6, -193), (6, -193), (6.5, 0), (4.5, 440), (0, 514), (-4.5, 440), (-6.5, 0)]},
        {"mat": "hand", "layer": 0, "poly": circle(-193, 34.7)},  # round counterweight
        {"mat": "hand", "layer": 0, "poly": [(-16.8, 367.5), (16.8, 367.5), (0, 452)]},  # arrow frame
        {"mat": "lume_hands", "layer": 1, "poly": [(-11.5, 373), (11.5, 373), (0, 431)]}]},
}

MANUAL_PX = {
    "hand_pivot": [862.8, 1401.4],  # dark pin hole; the case circle centre is within 1 px
    "case_x": [189.5, 1541.0],  # case edge on the 9-3 row, crown root
    "case_step_r": 650,  # ridge between the case flank and the sloped bezel
    "bezel_inner_r": 589,  # sloped bead-blasted bezel meets the crystal
    "rehaut_r": 534,  # dial edge; between it and the bezel a grey crystal edge and a dark flange (kept in the dial map)
    "hub_radius_px": [40, 14],  # white boss shared by the hands, seconds cap
    "crown_x": [1540, 1690],  # root at the case, end of the crown
    "crown_cap_x": 1660,  # flutes end, rounded smooth end cap
    "crown_radius_px": 113.5,
    "crown_teeth": 24,
    "lug_inner_x_mm": 10.0,  # 20 mm strap (official lug width)
    "lug_tips_y": [589, 2251],  # flat lug ends, top and bottom
    "lug_depth_mm": 14.0,  # outline read from the tip down to where the lug runs into the case
}
ARTEFACTS = ["the photo is taken a little from below: the top lugs read 1.1 mm shorter than the bottom ones; the model is symmetric "
             "about the hand pivot and uses the listed 47 mm lug to lug",
             "the NATO strap's buckle and keeper show beside the top strap past the lug tips; not modelled (the strap is mapped "
             "from the bottom strap)",
             "numerals, minute track, lume triangles and logo are printed: they stay in the photo map"]


def trace(path, M, case_mm, listed, artefacts, overlay=None, hands_px=HANDS_PX):
    im = cv2.imread(str(path))
    fg = (765 - im.astype(int).sum(2)) > 30
    hx, hy = M["hand_pivot"]
    S = (M["case_x"][1] - M["case_x"][0]) / case_mm
    mm = lambda p: [round((p[0] - hx) / S, 3), round(-(p[1] - hy) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [hx, hy], "hand_pivot_px": [hx, hy],
           "anchor": f"case diameter = {case_mm} mm (Hamilton official)",
           "case": {"radius_mm": round(case_mm / 2, 3), "step_mm": round(M["case_step_r"] / S, 3)},
           "bezel_inner_mm": round(M["bezel_inner_r"] / S, 3), "rehaut_mm": round(M["rehaut_r"] / S, 3)}

    # lug outline: silhouette half width by depth from the tip, top and bottom averaged (the photo's lugs are not centred)
    t0, t1 = M["lug_tips_y"]
    half = lambda row: (np.nonzero(fg[row])[0].max() - np.nonzero(fg[row])[0].min()) / 2 / S
    depth = []
    tip_mm, photo_tip = listed["lug_to_lug_mm"] / 2, (t1 - t0) / 2 / S
    for d in np.arange(0.0, M["lug_depth_mm"] + 0.01, 0.25):
        k = int(round(d * S))
        # stretched about the pivot so the photo's tip lands on the listed tip and the case junction stays in place
        depth.append([round(float(tip_mm - (photo_tip - d) * tip_mm / photo_tip), 3), round((half(t0 + k + 1) + half(t1 - k - 1)) / 2, 3)])
    out["lug"] = {"tip_mm": round(listed["lug_to_lug_mm"] / 2, 3), "photo_lug_to_lug_mm": round((t1 - t0) / S, 2),
                  "photo_tips_mm": [round((hy - t0) / S, 2), round((t1 - hy) / S, 2)],
                  "inner_x_mm": M["lug_inner_x_mm"], "half_width_by_depth_mm": depth}
    widths = {}
    for row in (t1 + 40, t1 + 150, t1 + 300):
        xs = np.nonzero(fg[row])[0]
        widths[str(row)] = round((xs.max() - xs.min()) / S, 2)
    out["checks"] = {"lug_to_lug_mm": out["lug"]["photo_lug_to_lug_mm"], "strap_width_past_tips_mm": widths, "listed": listed}

    out["hands"] = {name: {"angle_deg": h["angle_deg"], "z": h["z"],
                           "parts": [{"mat": p["mat"], "layer": p["layer"],
                                      "poly_mm": [[round(x / S, 3), round(y / S, 3)] for x, y in p["poly"]]} for p in h["parts"]]}
                    for name, h in hands_px.items()}
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    cx0, cx1 = M["crown_x"]
    out["crown"] = {"from_mm": round((cx0 - hx) / S, 3), "to_mm": round((cx1 - hx) / S, 3), "cap_from_mm": round((M["crown_cap_x"] - hx) / S, 3),
                    "radius_mm": round(M["crown_radius_px"] / S, 3), "teeth": M["crown_teeth"]}
    if "date_window" in M:  # applied frame around the date window (outer edge in px, frame width in px)
        b = M["date_window"]
        out["date_window"] = {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "frame_mm": round(M["date_frame_px"] / S, 3)}
    out["manual_px"] = M
    out["artefacts_not_traced"] = artefacts

    if overlay:
        ov = (im // 2).copy()
        P = lambda xy: (int(round(hx + xy[0] * S)), int(round(hy - xy[1] * S)))
        for r in (case_mm / 2 * S, M["case_step_r"], M["bezel_inner_r"], M["rehaut_r"]):
            cv2.circle(ov, (int(hx), int(hy)), int(r), (0, 128, 255), 1)
        for h in out["hands"].values():
            t = math.radians(h["angle_deg"])
            for p in h["parts"]:
                pts = [(x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)) for x, y in p["poly_mm"]]
                cv2.polylines(ov, [np.array([P(q) for q in pts], np.int32)], True, (0, 255, 255) if p["layer"] == 0 else (255, 0, 255), 1)
        for y in M["lug_tips_y"]:
            cv2.line(ov, (int(hx - 500), y), (int(hx + 500), y), (255, 128, 0), 1)
        cv2.circle(ov, (int((cx0 + cx1) / 2), int(hy)), int(M["crown_radius_px"]), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


def main(front, out_default, M, case_mm, listed, artefacts, hands_px):
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else out_default
    data = trace(front, M, case_mm, listed, artefacts, Path(sys.argv[2]) if len(sys.argv) > 2 else None, hands_px)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_inner_mm", "rehaut_mm", "checks", "hub_radius_mm", "crown")},
                     default=float), "->", dest)


if __name__ == "__main__":
    main(FRONT, OUT, MANUAL_PX, CASE_MM, LISTED, ARTEFACTS, HANDS_PX)
