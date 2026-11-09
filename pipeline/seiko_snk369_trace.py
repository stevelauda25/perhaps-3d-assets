"""Measure the Seiko 5 SNK369K1 front photo (white background, 2000 x 3708) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snk369_trace [out.json] [overlay.png]     # default config/watches/seiko-snk369k1-trace.json

Same method as pipeline/seiko_snk361_trace.py. Anchor: case diameter 37 mm (listings), from the LEFT flank only: the photo is
taken slightly from the crown side, so the right flank and the right bracelet edge also show the side faces. The silhouette is
mirrored from the left edge for the same reason. Cross-check: the end link between the lugs against the listed 18 mm band.
mm, x right, y toward 12, origin = hand pivot. The dial is white with a printed track, so hands, indices, day-date and
bracelet columns are read from gridded crops (MANUAL_PX, +-5 px = +-0.1 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snk369k1/front_2000x3708.png"
OUT = ROOT / "config/watches/seiko-snk369k1-trace.json"
CASE_MM = 37.0  # listings
LUG_GAP_MM = 18.0  # listed band width
CASE_RS_PX = (700, 950)  # radii searched for the left flank, photo px

MANUAL_PX = {
    "hand_pivot": [991, 1819],
    # hour: open arrow (black outline, lume head), shaft = two black rails with a white centre
    "hour_hand_tip": [707, 1626],
    "hour_head_base_r_px": 216,  # back edge of the arrow head, along the hand
    "hour_head_corners": [[848, 1650], [783, 1740]],
    "hour_shaft_width_px": 42,
    "hour_outline_px": 12,
    # minute: black stick, square tip, lume window from 160 to 530 px along the hand, solid black near the hub
    "minute_hand_tip": [1385, 1433],
    "minute_hand_width_px": 38,
    "minute_lume_r_px": [160, 530],
    "minute_outline_px": 13,
    # seconds: thin red needle (its tip is lost against the red track; read at the minute track), wide red tail
    "seconds_hand_tip": [1474, 1515],
    "seconds_hand_tail_end": [815, 1930],
    "seconds_hand_width_px": [5, 20],
    "hub_radius_px": [48, 35, 8],  # polished ring, red cap, pin
    "daydate_frame": [1200, 1760, 1567, 1878],
    "crown_box": [1712, 2030, 1805, 2235],
    "index_r_px": [418, 578],
    "index_width_px": [50, 92],  # single baton, wide baton at 12
    "end_link_x_px": [600, 1390],
    # bracelet, row at y = 2800: outer edges, then the column splits left to right
    "bracelet_row_2800": {"edges": [580, 1440], "splits": [800, 835, 945, 1065, 1180, 1225]},
    "bracelet_joints_y": {"outer_centre": [2700, 3005], "mid": [2862, 3160]},
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "photo taken slightly from the crown side: right flank and right bracelet edge include the side faces, so scale and silhouette use the left side",
             "the seconds hand runs along the red track lines; its tip is read where the track begins"]


def ring_radii(g, at):
    """Crystal ring = outer edge of the dark gasket band; dial edge = its inner edge (white dial, left half where nothing is printed). Photo px."""
    ring, inner = [], []
    for a in np.arange(190, 350, 2.0):
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(590, 720, 1.0)]
        dark = [i for i, v in enumerate(prof) if v < 150]
        inner.append(590 + dark[0])
        ring.append(590 + dark[-1])
    return float(np.median(ring)), float(np.median(inner))


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 2)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # case outline on the left flank only (see module note)
    edge = []
    for a in np.arange(260, 280.1, 1.0):
        rs = np.arange(*CASE_RS_PX, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    edge = np.array(edge)
    case_r = float(np.median(np.hypot(edge[:, 0] - px0, edge[:, 1] - py0)))
    S = 2 * case_r / CASE_MM
    rr, rd = ring_radii(g, at)
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case diameter {CASE_MM} mm (listings) from the left flank; lug gap checked against the listed {LUG_GAP_MM} mm band",
           "case": {"radius_mm": round(case_r / S, 3)},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "basis": "outer edge of the dark gasket band, left half"},
           "dial_edge_radius_mm": round(rd / S, 3)}

    # silhouette per y, mirrored from the left edge
    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                l = round((xs.min() - px0) / S, 3)
                prof.append([round(float(y_mm), 2), l, -l])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(15, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (22, 24, 28, 32, 36, -22, -24, -28, -32, -36) if y in width}
    near = [width[y] for y in width if 22 <= abs(y) <= 24]
    lug_gap = (M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S
    out["checks"] = {"bracelet_next_to_case_mm": round(float(np.median(near)), 2), "lug_gap_mm": round(lug_gap, 2), "expected_lug_gap_mm": LUG_GAP_MM}

    r0, r1 = M["index_r_px"]
    out["indices"] = {"inner_mm": round(r0 / S, 3), "outer_mm": round(r1 / S, 3),
                      "width_mm": round(M["index_width_px"][0] / S, 3), "width_12_mm": round(M["index_width_px"][1] / S, 3),
                      "layout": "applied polished batons with a lume fill; wide at 12; none at 3 (day-date)"}

    hands = {}
    for name in ("hour", "minute", "seconds"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r}
    hd = hands["hour"]
    hd["head_base_mm"] = round(M["hour_head_base_r_px"] / S, 3)
    t = math.radians(hd["angle_deg"])
    across = [abs(-x * math.cos(t) + y * math.sin(t)) for x, y in (mm(p) for p in M["hour_head_corners"])]
    hd["head_half_width_mm"] = round(sum(across) / 2, 3)
    hd["half_width_mm"] = round(M["hour_shaft_width_px"] / 2 / S, 3)
    hd["outline_mm"] = round(M["hour_outline_px"] / S, 3)
    hm = hands["minute"]
    hm["half_width_mm"] = round(M["minute_hand_width_px"] / 2 / S, 3)
    hm["lume_from_to_mm"] = [round(v / S, 3) for v in M["minute_lume_r_px"]]
    hm["outline_mm"] = round(M["minute_outline_px"] / S, 3)
    hs = hands["seconds"]
    hs["tail_mm"] = polar(M["seconds_hand_tail_end"])[0]
    hs["half_width_mm"], hs["tail_half_width_mm"] = (round(v / 2 / S, 3) for v in M["seconds_hand_width_px"])
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "crown_box"):
        out[k] = box(M[k])
    out["end_link_half_width_mm"] = round(lug_gap / 2, 3)
    row = M["bracelet_row_2800"]
    c, hw = sum(row["edges"]) / 2, (row["edges"][1] - row["edges"][0]) / 2
    f = [abs(x - c) / hw for x in row["splits"]]  # outer|narrow, narrow|mid, mid|centre, centre|mid, mid|narrow, narrow|outer
    avg = lambda i, j: round((f[i] + f[j]) / 2, 3)
    out["bracelet_columns"] = {"centre_half": avg(2, 3), "mid_from_to": [avg(2, 3), avg(1, 4)], "narrow_from_to": [avg(1, 4), avg(0, 5)],
                               "basis": "fractions of the bracelet half width, row at y = 2800 px, left and right averaged"}
    j = M["bracelet_joints_y"]
    pitch = [(b - a) / S for js in j.values() for a, b in zip(js[:-1], js[1:])]
    out["bracelet_pitch_mm"] = round(float(np.median(pitch)), 3)
    out["bracelet_joints_mm"] = {k: [round(-(y - py0) / S, 3) for y in v] for k, v in j.items()}

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r_ in (case_r, rr, rd):
            cv2.circle(ov, (px0, py0), int(r_), (0, 0, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for name, hd_ in hands.items():
            t = math.radians(hd_["angle_deg"])
            tail = hd_.get("tail_mm", 0)
            cv2.line(ov, P((-tail * math.sin(t), -tail * math.cos(t))), P((hd_["length_mm"] * math.sin(t), hd_["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            for k in ("inner_mm", "outer_mm"):
                r_ = out["indices"][k]
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 5, (255, 0, 255), 2)
        for k in ("daydate_frame", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "checks",
                                           "indices", "hands", "bracelet_columns", "bracelet_pitch_mm")}), "->", dest)
