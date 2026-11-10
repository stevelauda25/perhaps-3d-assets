"""Measure the Orient Star Modern Skeleton front photos (RE-AV0004N00B steel bracelet, RE-AV0005L00B leather strap; official
renders, 2000 x 2000) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_re_av00_trace <sku> [out.json] [overlay.png]   # sku: re-av0004n00b | re-av0005l00b

Same method as pipeline/orient_ra_aa0c02l19b_trace.py. Anchor: case width 41 mm (Orient official), read on the 9-3 row from the
case edge to the crown root; the official height (lug to lug) 49 mm is reported as a check. mm, x right, y toward 12, origin =
the hand pivot. Both renders show the same dial at the same time (10:08), so the dial layout (rings, batons, hands) is read once
on RE-AV0004N00B in mm and checked on RE-AV0005L00B with the overlay; per photo: scale, pivot, lug outline, XII, strap or
bracelet. The open heart, power reserve, small seconds (with their hands), chapter ring print and logo stay in the photo map.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_print import UP, shapes_from_mask

ROOT = Path(__file__).resolve().parents[1]
CASE_MM = 41.0  # Orient official, case width
LISTED = {"lug_to_lug_mm": 49.0, "lug_width_mm": [20.0, 21.0]}  # official height; lug width: ocarat 20, delugs 21 (photos read 21.2-21.6)
S4 = 1103 / CASE_MM  # RE-AV0004N00B px per mm: the dial layout below is read on that photo

# dial layout in RE-AV0004N00B pixels about its pivot, converted to mm with S4
LAYOUT_PX = {
    "bezel_inner_r": 510,  # polished bezel ends here
    "rehaut_r": 470,  # grey inner slope from the crystal ring down to the black chapter ring
    # hands (outline incl. the counterweight tail): (distance from the pivot, half width); rose gold or steel frame, lume inlay
    "hour_angle_deg": 302.1,
    "hour_profile_px": [[-112, 22], [-20, 22], [40, 21], [225, 20], [266, 0]],
    "hour_lume_px": [[50, 11], [222, 10], [246, 0]],
    "minute_angle_deg": 51.7,
    "minute_profile_px": [[-125, 18], [-20, 18], [50, 18], [290, 13.5], [390, 10], [412, 0]],
    "minute_lume_px": [[60, 9], [385, 5.5], [400, 0]],
    "hub_radius_px": [24, 12],  # collar, cap
    # applied faceted wedges: outer end r 401 (half 22), inner end r 301 (half 8); short ones end at the open heart / window
    "baton_px": {"inner": 301, "outer": 401, "half_inner": 8, "half_outer": 22},
    "baton_inner_px_by_hour": {"8": 345, "10": 345},
    "baton_hours": [1, 2, 3, 4, 5, 6, 7, 8, 10, 11],
    "xii_box": [-58, 300, 80, 406],  # x0, y0 (up), x1, y1 about the pivot
    "logo_box": [100, -80, 380, 115],  # OrientStar emblem, name, AUTOMATIC
}

SKUS = {
    "re-av0004n00b": {
        "front": "references/orient-re-av0004n00b/front_2000x2000.webp",
        "hand_pivot": [945, 902],
        "lug_tips_y": [278, 1595],  # rounded tips: where the silhouette reaches the bracelet width
        "case_x": [400, 1503],  # left case edge, crown root (9-3 row)
        "crown_x": [1505, 1600], "crown_cap_x": 1580, "crown_radius_px": 95, "crown_teeth": 24,
        "metal": "rose",  # XII, hands and hub colour
        "bracelet": {"columns_x": [670, 841, 882, 1055, 1096, 1241], "centre_x": 956,  # lug inner edges (end link row), narrow and centre links (row 1640)
                     "joints_y": {"bottom_outer": [1595, 1783], "bottom_centre": [1540, 1708, 1886]}},
    },
    "re-av0005l00b": {
        "front": "references/orient-re-av0005l00b/front_2000x2000.webp",
        "hand_pivot": [950, 885],
        "lug_tips_y": [292, 1550],
        "case_x": [426, 1480],
        "crown_x": [1480, 1580], "crown_cap_x": 1558, "crown_radius_px": 92, "crown_teeth": 24,
        "metal": "steel",
        "strap": {"centre_x": 990, "lug_gap_x": [680, 1235]},  # leather between the lug inner edges, 1440-1480 rows
    },
}


def trace(sku, overlay=None):
    M = SKUS[sku]
    path = ROOT / M["front"]
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    hx, hy = M["hand_pivot"]
    S = (M["case_x"][1] - M["case_x"][0]) / CASE_MM
    L = LAYOUT_PX
    mm4 = lambda v: round(v / S4, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [hx, hy], "hand_pivot_px": [hx, hy],
           "anchor": f"case width = {CASE_MM} mm (Orient official)", "case": {"radius_mm": CASE_MM / 2},
           "bezel_inner_mm": mm4(L["bezel_inner_r"]), "rehaut_mm": mm4(L["rehaut_r"])}

    t0, t1 = M["lug_tips_y"]
    half = lambda row: np.ptp(np.nonzero(fg[row])[0]) / 2 / S
    depth = [[round(float(d), 2), round((half(t0 + int(round(d * S))) + half(t1 - int(round(d * S)))) / 2, 3)] for d in np.arange(0.25, 14.01, 0.25)]  # down to where the lug runs into the case flank
    tip = LISTED["lug_to_lug_mm"] / 2
    out["lug"] = {"tip_mm": tip, "photo_tips_px": [int(t0), int(t1)], "photo_lug_to_lug_mm": round((t1 - t0) / S, 2),
                  "half_width_by_depth_mm": depth}
    out["checks"] = {"lug_to_lug_mm": out["lug"]["photo_lug_to_lug_mm"], "listed": LISTED}

    hands = {n: {"angle_deg": L[n + "_angle_deg"], "length_mm": mm4(L[n + "_profile_px"][-1][0]),
                 "outline_mm": [[mm4(a), mm4(b)] for a, b in L[n + "_profile_px"]],
                 "lume_mm": [[mm4(a), mm4(b)] for a, b in L[n + "_lume_px"]]} for n in ("hour", "minute")}
    out["hands"] = hands
    out["hub_radius_mm"] = [mm4(v) for v in L["hub_radius_px"]]
    b = L["baton_px"]
    out["indices"] = {"baton_mm": {k: mm4(v) for k, v in b.items()}, "hours": L["baton_hours"],
                      "inner_mm_by_hour": {k: mm4(v) for k, v in L["baton_inner_px_by_hour"].items()},
                      "layout": "applied faceted wedges at 1-8, 10, 11 (8 and 10 short), applied XII"}
    for k in ("xii_box", "logo_box"):
        x0, y0, x1, y1 = L[k]
        out[k.replace("_box", "")] = {"x0_y0_x1_y1_mm": [mm4(x0), mm4(y1), mm4(x1), mm4(y0)]}

    # applied XII: hand-coloured pixels (rose gold or bright steel) inside its box, traced to plates with holes
    x0, y0, x1, y1 = out["xii"]["x0_y0_x1_y1_mm"]
    bx0, by0, bx1, by1 = int(hx + x0 * S), int(hy - y0 * S), int(hx + x1 * S), int(hy - y1 * S)
    c = im[by0:by1, bx0:bx1].astype(int)
    m = ((c[..., 2] - c[..., 0] > 18) & (c[..., 2] > 120)) if M["metal"] == "rose" else (c.mean(2) > 150)
    m = cv2.morphologyEx(m.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    up = cv2.GaussianBlur(cv2.resize(m, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.6)
    to_mm = lambda p: [round((p[0] / UP + bx0 - hx) / S, 3), round(-(p[1] / UP + by0 - hy) / S, 3)]
    out["xii_shapes"] = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 150)

    cx0, cx1 = M["crown_x"]
    ccx = (M["case_x"][0] + M["case_x"][1]) / 2
    out["crown"] = {"from_mm": round((cx0 - ccx) / S, 3), "to_mm": round((cx1 - ccx) / S, 3), "cap_from_mm": round((M["crown_cap_x"] - ccx) / S, 3),
                    "radius_mm": round(M["crown_radius_px"] / S, 3), "teeth": M["crown_teeth"]}
    out["metal"] = M["metal"]

    if "bracelet" in M:
        br = M["bracelet"]
        c = br["columns_x"]
        j = br["joints_y"]
        pitch = [(q - p) / S for v in j.values() for p, q in zip(v, v[1:])]
        out["bracelet"] = {"pitch_mm": round(float(np.mean(pitch)), 3),
                           "lug_inner_x_mm": round((c[5] - c[0]) / 2 / S, 3),
                           "narrow_half_mm": round((c[4] - c[1]) / 2 / S, 3), "centre_half_mm": round((c[3] - c[2]) / 2 / S, 3),
                           "centre_joint_shift_mm": round(float(np.mean([(j["bottom_outer"][0] - j["bottom_centre"][0]) / S,
                                                                         (j["bottom_outer"][1] - j["bottom_centre"][1]) / S])), 3),
                           "half_width_by_s_mm": [[round(tip + (y - t1) / S, 2), round((br["centre_x"] - np.nonzero(fg[y])[0].min()) / S, 3)]
                                                  for y in range(t1 + 15, im.shape[0] - 10, 10) if fg[y].any()]}
        out["checks"]["end_link_width_mm"] = round((c[5] - c[0]) / S, 2)
    else:
        st = M["strap"]
        widths = [[round(tip + (y - t1) / S, 2), round(np.ptp(np.nonzero(fg[y])[0]) / S, 2)] for y in range(t1 + 15, min(t1 + 400, im.shape[0] - 10), 25) if fg[y].any()]
        out["strap"] = {"centre_x_px": st["centre_x"], "width_by_s_mm": widths, "lug_tips_px": [int(t0), int(t1)],
                        "half_mm": round((st["lug_gap_x"][1] - st["lug_gap_x"][0]) / 2 / S, 3)}
        out["checks"]["strap_width_mm"] = widths[:3]
    out["layout_px_re_av0004n00b"] = L
    out["manual_px"] = M

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(hx + xy[0] * S)), int(round(hy - xy[1] * S)))
        for r in (out["bezel_inner_mm"], out["rehaut_mm"], CASE_MM / 2):
            cv2.circle(ov, (hx, hy), int(r * S), (0, 0, 255), 1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            for key in ("outline_mm", "lume_mm"):
                pts = hd[key]
                poly = [(w * math.cos(t) + rr * math.sin(t), -w * math.sin(t) + rr * math.cos(t)) for rr, w in pts] + \
                       [(-w * math.cos(t) + rr * math.sin(t), w * math.sin(t) + rr * math.cos(t)) for rr, w in pts[::-1]]
                cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (0, 255, 255), 1)
        q = out["indices"]["baton_mm"]
        for hr in out["indices"]["hours"]:
            t = math.radians(hr * 30)
            r0 = out["indices"]["inner_mm_by_hour"].get(str(hr), q["inner"])
            h0 = q["half_inner"] + (q["half_outer"] - q["half_inner"]) * (r0 - q["inner"]) / (q["outer"] - q["inner"])
            quad = [(sx * hh * math.cos(t) + rr * math.sin(t), -sx * hh * math.sin(t) + rr * math.cos(t))
                    for sx, hh, rr in ((1, h0, r0), (1, q["half_outer"], q["outer"]), (-1, q["half_outer"], q["outer"]), (-1, h0, r0))]
            cv2.polylines(ov, [np.array([P(p) for p in quad], np.int32)], True, (255, 0, 255), 1)
        for sh in out["xii_shapes"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        x0, y0, x1, y1 = out["logo"]["x0_y0_x1_y1_mm"]
        cv2.rectangle(ov, P((x0, y0)), P((x1, y1)), (0, 200, 255), 1)
        for y in (t0, t1):
            cv2.line(ov, (500, int(y)), (1400, int(y)), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    sku = sys.argv[1]
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / f"config/watches/orient-{sku}-trace.json"
    data = trace(sku, overlay=Path(sys.argv[3]) if len(sys.argv) > 3 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "bezel_inner_mm", "rehaut_mm", "checks", "hub_radius_mm", "crown")},
                     default=float), len(data["xii_shapes"]), "XII shapes ->", dest)
