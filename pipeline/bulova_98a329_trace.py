"""Measure the Bulova 98A329 (Lunar Pilot Timascus, 43.5 mm) front photo into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.bulova_98a329_trace [out.json] [overlay.png]   # default config/watches/bulova-98a329-trace.json

Same method as pipeline/hamilton_h82405130_trace.py. The retailer photo (1225 x 2066) is turned 1.9 deg clockwise (3 / 9 and
12 / 6 indices, bracelet axis); references/bulova-98a329/front_straight_1225x2066.jpg is the same photo turned back about the
hand pivot and is the working reference. Anchor: 43.5 mm case width (Bulova) = twice the left flank's widest half from the
bezel centre (the right flank carries the crown and pushers). mm, x right, y toward 12, origin = hand pivot. Hands, subdials,
indices, crown, pushers and bracelet joints come from gridded and hand-aligned crops (MANUAL_PX, +-1 px = +-0.05 mm). The
applied numerals are traced by threshold and become geometry; the Timascus dial, subdials, minute track, tachymeter ring,
logo and prints stay in the dial map.
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
FRONT = ROOT / "references/bulova-98a329/front_straight_1225x2066.jpg"
OUT = ROOT / "config/watches/bulova-98a329-trace.json"
CASE_MM = 43.5  # Bulova: case width
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 50.0, "thickness_mm": 13.0}

MANUAL_PX = {
    "hand_pivot": [576.5, 1018.5],
    "photo_rotation_deg": 1.9,  # applied to the original photo to make the working reference
    # hour / minute: white lume batons in a polished frame, pointed tip: [length, half at the root, half at the tip, tip point]
    "hour_hand": {"angle_deg": 303.2, "length": 228, "half": [13.5, 12.0], "point": 14},
    "minute_hand": {"angle_deg": 37.0, "length": 337, "half": [13.0, 11.5], "point": 16},
    # chrono seconds: white needle, lozenge at r 195-245, thin pointer to the 12 index, tail widening to its rounded end
    "chrono_hand": {"angle_deg": 0.0, "length": 326, "half": 6, "lozenge": [195, 218, 18, 245], "pointer_half": 2.5,
                    "tail": [100, 11]},
    "hub_radius_px": [30, 20, 4],  # white chrono hub disc, polished ring, black pin
    "outline_px": 3,
    # subdials: hand pivot, hand angle, hand length, half width at the root / tip, hub radius (black needles, black hubs)
    "subdials": {"9": [[381.0, 1023.3], 0.0, 88, [2.4, 1.4], 14], "3": [[770.0, 1021.7], 0.0, 90, [2.4, 1.4], 14],
                 "6": [[574.3, 1215.7], 181.4, 92, [2.4, 1.4], 14]},
    "subdial_disc_px": {"9": [[384.5, 1024.0], 95.5], "3": [[774.3, 1025.3], 94.5], "6": [[573.0, 1216.5], 100.0]},
    # applied indices (white, polished): [r0, r1, half width] for the hour bars, the 3 / 6 / 9 bars and the 12 bar
    "bar_px": [297, 328, 12.2], "wide_bar_px": [301, 331, 23.0], "twelve_px": [247, 326, 27.0],
    "numeral_boxes": {"1": [695, 771, 721, 862], "2": [778, 856, 834, 925], "4": [778, 1118, 836, 1188], "5": [680, 1213, 736, 1284],
                      "7": [416, 1213, 475, 1284], "8": [326, 1119, 382, 1190], "10": [322, 855, 402, 927], "11": [415, 770, 473, 842]},
    "logo": [476, 846, 674, 892],  # applied black BULOVA plate with white letters
    "print_khz": [488, 1240, 662, 1272],
    # rings about the bezel centre: dial edge, minute track flange, tachymeter ring, black groove, blue bezel
    "rings_px": {"dial_out": 332, "flange_out": 367, "tach_out": 424, "groove_out": 432},
    "crown": {"angle_deg": 91.5, "r": [463, 580], "radius": 91, "teeth": 20, "collar": [450, 470], "collar_radius": 62},
    # blue pushers at 2 and 4 seen from above (photo px); the inner corners run under the case flank
    "pushers": [[[925, 690], [950, 656], [975, 650], [1003, 655], [1022, 672], [1040, 720], [1052, 780], [1062, 840], [1065, 890],
                 [1060, 905], [1030, 908], [990, 905], [935, 760]],
                [[935, 1300], [990, 1158], [1035, 1155], [1062, 1160], [1066, 1200], [1062, 1260], [1052, 1320], [1040, 1375],
                 [1025, 1410], [1000, 1425], [970, 1428], [945, 1420]]],
    # rows where a pusher's outer edge is the right silhouette (ends excluded: they round off into the case)
    "pusher_rows_y": [[662, 908], [1146, 1422]],
    "pusher_width_px": 80,  # the block runs this far in from the outer edge, under the case flank
    "lug_tips_y": [485, 1635],  # outer corners of the lug horns (top foreshortened, bottom stretched by the camera angle)
    "lug_inner_x": [345, 805],
    "bracelet_centre_x": [470, 682],
    # joints: centre / outer columns, first ones nearest the case (the bracelet curls away, later joints are foreshortened)
    "bracelet_joints_y": {"top_centre": [491, 366, 249], "top_outer": [475, 344, 216],
                          "bottom_centre": [1601, 1699, 1790], "bottom_outer": [1625, 1726, 1814]},
}
ARTEFACTS = ["the photo is 1225 px wide (22.6 px/mm): hand and index edges are +-1 px = +-0.05 mm",
             "the camera sits slightly toward 6: the top lugs and bracelet are foreshortened, the bottom ones stretched; the "
             "listed 50 mm lug to lug is used and the case outline is the mean of the two halves scaled to it",
             "the right flank looks about 0.5 mm wider than the left (camera to the right); the left flank is mirrored"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * math.sin(math.radians(a)), c[1] - r * math.cos(math.radians(a)))

    # bezel outer edge: first blue pixel coming in from outside (B - R), clear of the crown and pushers
    blue = cv2.GaussianBlur(im[..., 0].astype(float) - im[..., 2].astype(float), (0, 0), 1.5)
    edge = []
    for a in [a_ for a_ in range(0, 360, 3) if not 40 < a_ < 140]:
        rs = np.arange(560, 380, -0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        k = np.nonzero(blue[ys.astype(int), xs.astype(int)] > 40)[0]
        if len(k):
            edge.append((xs[k[0]], ys[k[0]]))
    bcx, bcy, bez_r = fit_circle(np.array(edge))
    # case width: left flank, widest half from the bezel centre
    left = {y: np.nonzero(fg[y])[0].min() for y in range(int(bcy) - 120, int(bcy) + 121)}
    case_half_px = bcx - min(left.values())
    S = 2 * case_half_px / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    rg = dict(M["rings_px"], bezel_out=round(float(bez_r), 1))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Bulova), twice the left flank's half width from the bezel centre",
           "bezel_offset_mm": mm((bcx, bcy)), "bezel_rings_mm": {k: f(v) for k, v in rg.items()}, "case_half_mm": f(case_half_px)}

    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - bcx, yy - bcy)
    srgb = lambda m: [round(float(v) / 255, 3) for v in np.median(im[m][:, ::-1], 0)]
    out["bezel_srgb"] = srgb((rr > rg["groove_out"] + 10) & (rr < rg["bezel_out"] - 6) & ((xx < bcx - 150) | (yy > bcy + 300)))
    pmask = np.zeros((h, w), np.uint8)
    for poly in M["pushers"]:
        cv2.fillPoly(pmask, [np.array(poly, np.int32)], 1)
    out["pusher_srgb"] = srgb(pmask.astype(bool) & (blue > 25) & ~(rr < rg["bezel_out"] + 8))

    # case outline: left edge per row, top and bottom halves each scaled so the lug tip sits at the listed 25 mm
    tip = LISTED["lug_to_lug_mm"] / 2
    tips_px = [bcy - M["lug_tips_y"][0], M["lug_tips_y"][1] - bcy]
    rows = {}
    for sy, tp in ((1, tips_px[0]), (-1, tips_px[1])):
        for k in range(int(tp) + 1):
            row = int(round(bcy - sy * k))
            xs = np.nonzero(fg[row])[0]
            y_mm = round(k / tp * tip * 4) / 4
            rows.setdefault(y_mm, []).append((bcx - xs.min()) / S)
    out["case_half_width_by_y_mm"] = [[y, round(float(np.mean(v)), 3)] for y, v in sorted(rows.items())]
    out["lug"] = {"tip_mm": tip, "photo_tips_mm": [f(v) for v in tips_px], "inner_x_mm": f((M["lug_inner_x"][1] - M["lug_inner_x"][0]) / 2)}
    out["checks"] = {"case_width_mm": CASE_MM, "bezel_diameter_mm": f(2 * bez_r), "photo_lug_to_lug_mm": f(sum(tips_px)),
                     "end_link_width_mm": f(M["lug_inner_x"][1] - M["lug_inner_x"][0]),
                     "bracelet_width_near_case_mm": [f(float(np.ptp(np.nonzero(fg[y])[0]))) for y in (400, 1680)], "listed": LISTED}

    # hands
    hands = {}
    for name in ("hour", "minute"):
        hm = M[name + "_hand"]
        hands[name] = {"angle_deg": hm["angle_deg"], "length_mm": f(hm["length"]), "half_mm": [f(v) for v in hm["half"]], "point_mm": f(hm["point"])}
    cm = M["chrono_hand"]
    hands["chrono"] = {"angle_deg": cm["angle_deg"], "length_mm": f(cm["length"]), "half_mm": f(cm["half"]), "lozenge_mm": [f(v) for v in cm["lozenge"]],
                       "pointer_half_mm": f(cm["pointer_half"]), "tail_mm": [f(v) for v in cm["tail"]]}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_outline_mm"] = f(M["outline_px"])
    out["subdials"] = {k: {"centre_mm": mm(c), "angle_deg": a, "length_mm": f(L), "half_mm": [f(v) for v in hw], "hub_mm": f(hb),
                           "disc_centre_mm": mm(M["subdial_disc_px"][k][0]), "disc_r_mm": f(M["subdial_disc_px"][k][1])}
                       for k, (c, a, L, hw, hb) in M["subdials"].items()}
    out["indices"] = {"bar_mm": [f(v) for v in M["bar_px"]], "wide_bar_mm": [f(v) for v in M["wide_bar_px"]], "twelve_mm": [f(v) for v in M["twelve_px"]],
                      "layout": "applied white bars: wide at 3 6 9, long and wide at 12, narrow at the other hours"}

    # applied numerals: white above the dial, hands cut away (dilated) so the 0 of 10 and the 1 keep their own outline
    hm = np.zeros((h, w), np.uint8)
    for name in ("hour", "minute"):
        hd = M[name + "_hand"]
        t = math.radians(hd["angle_deg"])
        ux, uy, nx, ny = math.sin(t), -math.cos(t), math.cos(t), math.sin(t)
        hw = hd["half"][0] + 0.5  # the 3D hand covers the cut
        L = hd["length"]
        cv2.fillPoly(hm, [np.array([[px0 + a * ux + b * nx, py0 + a * uy + b * ny] for a, b in ((0, -hw), (0, hw), (L, hw), (L, -hw))], np.int32)], 1)
    white = ((gray > 200) & ~hm.astype(bool)).astype(np.uint8) * 255
    out["numerals"] = {}
    for key, (x0, y0, x1, y1) in M["numeral_boxes"].items():
        m = white[y0:y1, x0:x1].copy()
        up = cv2.GaussianBlur(cv2.resize(m, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
        to_mm = lambda p, x0=x0, y0=y0: [round((p[0] / UP + x0 - px0) / S, 3), round(-(p[1] / UP + y0 - py0) / S, 3)]
        shapes = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 20)
        area = [abs(cv2.contourArea(np.array(sh["outer"], np.float32))) for sh in shapes]
        out["numerals"][key] = [sh for sh, a in zip(shapes, area) if a >= 0.3 * max(area)]  # drops bits of bars and subdial rims

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [f(b[2] - b[0]), f(b[3] - b[1])], "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    out["logo"], out["print_khz"] = box(M["logo"]), box(M["print_khz"])
    cr = M["crown"]
    out["crown"] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"],
                    "collar_mm": [f(v) for v in cr["collar"]], "collar_radius_mm": f(cr["collar_radius"])}
    # pushers: outer edge = right silhouette per row; inner edge moved toward the bezel centre by the block width; round caps
    out["pushers_mm"] = []
    for y0, y1 in M["pusher_rows_y"]:
        xs_ = np.array([np.nonzero(fg[y])[0].max() + 0.5 for y in range(y0, y1 + 1)], float)
        xs_ = np.convolve(np.pad(xs_, 4, mode="edge"), np.ones(9) / 9, "valid")  # +-1 px jpeg edge noise
        outer = [(float(xs_[y - y0]), float(y)) for y in range(y0, y1 + 1, 4)]
        inward = lambda p, d: (p[0] + d * (bcx - p[0]) / math.hypot(bcx - p[0], bcy - p[1]), p[1] + d * (bcy - p[1]) / math.hypot(bcx - p[0], bcy - p[1]))
        inner = [inward(p, M["pusher_width_px"]) for p in outer]

        def cap(a_, b_, away):  # half circle from a_ to b_, bulging away from the block's middle
            cx_, cy_ = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
            r_ = math.hypot(a_[0] - cx_, a_[1] - cy_)
            t0 = math.atan2(a_[1] - cy_, a_[0] - cx_)
            sgn = 1 if math.sin(math.atan2(away[1], away[0]) - t0) > 0 else -1
            return [(cx_ + r_ * math.cos(t0 + sgn * math.pi * k / 10), cy_ + r_ * math.sin(t0 + sgn * math.pi * k / 10)) for k in range(1, 10)]
        tail = (outer[-1][0] - outer[-2][0], outer[-1][1] - outer[-2][1])
        head = (outer[0][0] - outer[1][0], outer[0][1] - outer[1][1])
        loop = outer + cap(outer[-1], inner[-1], tail) + inner[::-1] + cap(inner[0], outer[0], head)
        out["pushers_mm"].append([mm(p) for p in loop])

    j = M["bracelet_joints_y"]
    first = lambda v: abs(v[1] - v[0])
    out["bracelet_pitch_photo_mm"] = {k: [f(abs(a - b)) for a, b in zip(v[1:], v[:-1])] for k, v in j.items()}
    out["bracelet_pitch_mm"] = f(float(np.mean([first(v) for v in j.values()])))
    out["bracelet_centre_joint_shift_mm"] = f(float(np.mean([abs(j["top_outer"][0] - j["top_centre"][0]), abs(j["bottom_outer"][0] - j["bottom_centre"][0])])))
    out["bracelet_centre_half_mm"] = f((M["bracelet_centre_x"][1] - M["bracelet_centre_x"][0]) / 2)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in rg.values():
            cv2.circle(ov, (int(bcx), int(bcy)), int(rk), (0, 0, 255), 1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, P((0, 0)), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        for sd in out["subdials"].values():
            t = math.radians(sd["angle_deg"])
            c = sd["centre_mm"]
            cv2.line(ov, P(c), P((c[0] + sd["length_mm"] * math.sin(t), c[1] + sd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
            cv2.circle(ov, P(sd["disc_centre_mm"]), int(sd["disc_r_mm"] * S), (255, 0, 255), 1)
        for hr in range(12):
            r0, r1, hw = M["twelve_px"] if hr == 0 else M["wide_bar_px"] if hr % 3 == 0 else M["bar_px"]
            t = math.radians(hr * 30)
            pts = [(px0 + a * math.sin(t) + b * math.cos(t), py0 - a * math.cos(t) + b * math.sin(t)) for a, b in ((r0, -hw), (r0, hw), (r1, hw), (r1, -hw))]
            cv2.polylines(ov, [np.array(pts, np.int32)], True, (255, 0, 255), 1)
        for shapes in out["numerals"].values():
            for sh in shapes:
                for lp in [sh["outer"]] + sh["holes"]:
                    cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        for poly in out["pushers_mm"]:
            cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (0, 200, 255), 1)
        for y, hw in out["case_half_width_by_y_mm"]:
            for sy, tp in ((1, tips_px[0]), (-1, tips_px[1])):
                cv2.circle(ov, (int(bcx - hw * S), int(bcy - sy * y / tip * tp)), 1, (0, 255, 0), -1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (330, y), (830, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "bezel_offset_mm", "bezel_rings_mm", "case_half_mm", "bezel_srgb", "pusher_srgb",
                                           "lug", "checks", "bracelet_pitch_photo_mm", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_centre_half_mm")}, default=float), "->", dest,
          {k: len(v) for k, v in data["numerals"].items()}, "numeral shapes")
