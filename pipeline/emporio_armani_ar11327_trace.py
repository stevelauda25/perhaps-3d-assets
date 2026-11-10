"""Measure the Emporio Armani Matteo AR11327 front photo (white background, 3000 x 4962) into mm. numpy + OpenCV.

    python3 -B -m pipeline.emporio_armani_ar11327_trace [out.json] [overlay.png]   # default config/watches/emporio-armani-ar11327-trace.json

The photo is turned about 13 deg toward the crown side: the dial is an ellipse, narrower across than tall. Vertical
distances are true; horizontal ones are divided by the dial ellipse ratio (cos_tilt). Anchor: case height on the pivot
column = 43 mm (listing). mm, x right, y toward 12, origin = hand pivot.
Hands: needles from the pivot to the tips read from gridded crops (MANUAL_PX), widths measured across the gold mask.
Hour bars: gold components on the dial at least 2 mm long, stored as rectangles. Lug arm: left silhouette (the far side
shows the arm's top face), arm width and end caps from crops.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/emporio-armani-ar11327/front_3000x4962.png"
OUT = ROOT / "config/watches/emporio-armani-ar11327-trace.json"
CASE_MM = 43.0  # listing: case size 43 mm

MANUAL_PX = {
    "hand_pivot": [1378, 2440],
    "hub_px": {"radius": 44, "pin": 16},
    # tips (rounded end centre); seconds: thin needle, no tail
    "tips": {"hour": [880, 2063], "minute": [2240, 2040], "seconds": [1340, 1466]},
    # left edge (x) at the pivot row: outer edge of the domed bezel's groove, inner edge of the sloped flange (dial edge)
    "ring_x_left": {"groove": 200, "flange_inner": 268},
    # end caps: rows of the outer and inner edge (top at 12, bottom at 6); left and right ends of the top face (top cap)
    "end_cap_rows": {"top": [690, 1035], "bottom": [4240, 3885]}, "end_cap_x": [858, 2092],
    # mesh band clear of the end cap and the curl (for the repeat tile): rows, x range
    "mesh_rows": [4380, 4700], "mesh_x": [990, 2050],
    # lug arm: top end of the arm (round end) and its width across the arm
    "arm_top_row": 905, "arm_width_px": 125,
    # black knurled crown at 3: rows top/bottom, x where it leaves the case and its end
    "crown": {"y_top_bottom": [2265, 2625], "x_start_end": [2742, 2962], "teeth": 22},
}
ARTEFACTS = ["EMPORIO ARMANI print, eagle logo, minute marks, the short 12 o'clock mark, date window and the purple-grey "
             "flange: kept in the dial map (flat)",
             "photo turned ~13 deg about the vertical: the right lug arm and the end cap ends show their side faces, so "
             "the build mirrors the left arm; the comparison render is straight-on and cannot match the photo's turn"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    fg = im.min(2) < 215
    # scale: case run on the pivot column (end-cap gaps above and below are background)
    col = fg[:, px0]
    top = py0 - next(k for k in range(py0) if not col[py0 - k])
    bot = py0 + next(k for k in range(im.shape[0] - py0) if not col[py0 + k])
    S = (bot - top) / CASE_MM
    # dial ellipse: teal pixels joined to the pivot region, holes closed
    b, g, r = [im[..., k].astype(int) for k in range(3)]
    teal = ((b - r) > 25).astype(np.uint8)
    _, lab = cv2.connectedComponents(teal)
    d = cv2.morphologyEx((lab == lab[py0 + 160, px0]).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))
    cnt = max(cv2.findContours(d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
    (ex, ey), (ew, eh), ea = cv2.fitEllipse(cnt)
    ct = min(ew, eh) / max(ew, eh)
    mm = lambda p: [round((p[0] - px0) / (S * ct), 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "cos_tilt": round(ct, 4), "origin_px": [px0, py0],
           "anchor": f"case height on the pivot column = {CASE_MM} mm (listing), rows {top}-{bot}",
           "dial_ellipse_px": [round(ex, 1), round(ey, 1), round(ew / 2, 1), round(eh / 2, 1), round(ea, 2)]}
    rx = M["ring_x_left"]
    out["rings_mm"] = {"case": CASE_MM / 2, "groove": round((px0 - rx["groove"]) / (S * ct), 3),
                       "dial": round(max(ew, eh) / 2 / S, 3), "flange_inner_left": round((px0 - rx["flange_inner"]) / (S * ct), 3)}

    ec = M["end_cap_rows"]
    out["end_cap_mm"] = {"inner": round(((py0 - ec["top"][1]) + (ec["bottom"][1] - py0)) / 2 / S, 3),
                         "outer": round(((py0 - ec["top"][0]) + (ec["bottom"][0] - py0)) / 2 / S, 3),
                         "half_width": round((M["end_cap_x"][1] - M["end_cap_x"][0]) / 2 / (S * ct), 3)}
    mr, mx = M["mesh_rows"], M["mesh_x"]
    out["mesh_mm"] = {"photo_half_width": round((mx[1] - mx[0]) / 2 / (S * ct), 3)}

    # ---- lug arm: left silhouette from where it leaves the case circle to the arm's round top ----
    R = CASE_MM / 2
    rows = []
    for y_mm in np.arange(14.0, (py0 - M["arm_top_row"]) / S, 0.25):
        row = int(round(py0 - y_mm * S))
        x = np.nonzero(fg[row])[0].min()
        rows.append([round(float(y_mm), 2), round((px0 - x) / (S * ct), 3)])
    leave = next(y for y, x in rows if x > math.sqrt(max(R * R - y * y, 0)) + 1.0)  # the turned case flank already sits ~0.8 mm out
    out["arm"] = {"outer_y_x_mm": [p for p in rows if p[0] >= leave - 1.0], "from_y_mm": leave,
                  "top_y_mm": round((py0 - M["arm_top_row"]) / S, 3), "width_mm": round(M["arm_width_px"] / S, 3)}

    # ---- hands: needles from the pivot; half width from the gold mask across the hand ----
    gold = r > 115  # pale gold under the crystal (R ~150) on the teal dial (R ~76)
    ang = lambda dx, dy: math.degrees(math.atan2(dx, dy)) % 360  # mm vector -> clockwise from 12
    hands = {}
    for name, tip in M["tips"].items():
        u = np.float32(tip) - (px0, py0)
        L = float(np.hypot(*u))
        u /= L
        n = np.float32([-u[1], u[0]])
        widths = []
        for f in np.linspace(0.3, 0.85, 12):
            c = np.float32([px0, py0]) + u * L * f
            prof = [gold[int(round(c[1] + n[1] * k)), int(round(c[0] + n[0] * k))] for k in range(-25, 26)]
            widths.append(sum(prof))
        w = float(np.median(widths))
        t_mm, (x_t, y_t) = mm(tip), mm(tip)
        a = ang(x_t, y_t)
        hands[name] = {"angle_deg": round(a, 2), "length_mm": round(math.hypot(x_t, y_t), 3), "half_width_mm": round(w / 2 / S, 3), "tip_mm": t_mm}
    out["hands"] = hands
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub_px"].items()}

    # ---- applied hour bars: gold components on the dial at least 2 mm long, away from the hands ----
    hm = np.zeros(gold.shape, np.uint8)
    for tip in M["tips"].values():
        cv2.line(hm, (px0, py0), tuple(tip), 1, 40)
    cv2.circle(hm, (px0, py0), 70, 1, -1)
    inside = np.zeros(gold.shape, np.uint8)
    cv2.ellipse(inside, ((ex, ey), (ew - 30, eh - 30), ea), 1, -1)
    gm = (gold & (hm == 0) & (inside > 0)).astype(np.uint8)
    n_, lab, stats, _ = cv2.connectedComponentsWithStats(gm)
    bars = []
    for k in range(1, n_):
        ys, xs = np.nonzero(lab == k)
        if len(xs) < 300:
            continue
        rect = cv2.minAreaRect(np.c_[xs, ys].astype(np.float32))
        corners = [mm(p) for p in cv2.boxPoints(rect)]
        rr = [math.hypot(*c) for c in corners]
        length = max(math.dist(corners[0], corners[1]), math.dist(corners[1], corners[2]))
        a = ang(*np.mean(corners, 0))
        # hour positions only: the eagle logo pieces and the crystal glint on the flange are off the 30 deg grid
        if length >= 2.0 and min(rr) > 11.0 and abs((a + 15) % 30 - 15) < 2.0:
            bars.append({"corners_mm": corners, "length_mm": round(length, 3), "angle_deg": round(a, 1)})
    bars.sort(key=lambda bb: bb["angle_deg"])
    out["hour_bars"] = bars

    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"radius_mm": round((yb - yt) / 2 / S, 3), "centre_y_mm": round(-((yt + yb) / 2 - py0) / S, 3),
                    "r_start_end_mm": [round((x - px0) / (S * ct), 3) for x in cr["x_start_end"]], "teeth": cr["teeth"]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        Pp = lambda xy: (int(round(px0 + xy[0] * S * ct)), int(round(py0 - xy[1] * S)))
        cv2.ellipse(ov, ((ex, ey), (ew, eh), ea), (0, 0, 255), 2)
        for k in ("case", "groove"):
            cv2.ellipse(ov, (px0, py0), (int(out["rings_mm"][k] * S * ct), int(out["rings_mm"][k] * S)), 0, 0, 360, (255, 128, 0), 2)
        for y_mm, x in out["arm"]["outer_y_x_mm"]:
            cv2.circle(ov, Pp((-x, y_mm)), 3, (0, 255, 0), -1)
        for h in hands.values():
            cv2.line(ov, (px0, py0), Pp(h["tip_mm"]), (0, 200, 255), 2)
        for bb in bars:
            cv2.polylines(ov, [np.array([Pp(c) for c in bb["corners_mm"]])], True, (255, 0, 255), 2)
        e = out["end_cap_mm"]
        for sy in (1, -1):
            for k in ("inner", "outer"):
                cv2.line(ov, Pp((-e["half_width"], sy * e[k])), Pp((e["half_width"], sy * e[k])), (0, 128, 255), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "cos_tilt", "rings_mm", "end_cap_mm", "mesh_mm", "hands", "hub_mm", "crown")},
                     default=float), "->", dest)
    print("arm from", data["arm"]["from_y_mm"], "top", data["arm"]["top_y_mm"], "width", data["arm"]["width_mm"],
          "bars", [(b["angle_deg"], b["length_mm"]) for b in data["hour_bars"]])
