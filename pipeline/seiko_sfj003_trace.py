"""Measure the Seiko SFJ003P1 front photo (white background, 3200 x 5264) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_sfj003_trace [out.json] [overlay.png]     # default config/watches/seiko-sfj003p1-trace.json

Same method as pipeline/seiko_ssb479_trace.py. Anchor: case width on the dial-centre row = 42 mm (listing, 2026-11-06);
the listed 48.3 mm lug to lug and 20 mm lug width are reported as checks. mm, x right, y toward 12, origin = dial centre
(centre of the grey crystal gasket ring, which the bezel edge matches left and right). The photo is taken slightly from
below: the inner wall of the bezel shows at 12 and the lug tips sit 0.85 mm lower than the dial centre; the build uses
the mean of both ends. Hour and minute hands turn about the time subdial at 6 (pivot 7.2 mm below the origin); the three
chronograph subdials (12, 9, 3) each have a white paddle hand pointing at 0. Hands, pushers, crown and bracelet joints
come from gridded crops (MANUAL_PX, +-5 px = +-0.08 mm); time-subdial index radii from radial profiles.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-sfj003p1/front_3200x5264.png"
OUT = ROOT / "config/watches/seiko-sfj003p1-trace.json"
CASE_MM = 42.0  # listing, 2026-11-06
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 48.3, "thickness_mm": 12.9}

MANUAL_PX = {
    "dial_centre": [1572, 2622],  # gasket ring: x 400-425 / 2720-2740 on the centre row, y 1460-1480 at 12
    "rings_px": {"bezel_inner": 1202, "gasket_outer": 1170, "flange_inner": 1020, "bezel_outer": 1272},
    # time subdial at 6: hour and minute hands (9:12)
    "time_pivot": [1576, 3091],
    "hub_radius_px": [50, 20],  # polished hub ring, screw
    "hour_tip": [1254, 3062],
    "hour_half_width_px": 34,
    "hour_lume_px": [[1288, 3062], [1471, 3075]],
    "hour_lume_half_width_px": 20,
    "hour_tail_px": 30,
    "minute_tip": [2038, 3072],
    "minute_half_width_px": 34,
    "minute_lume_px": [[1678, 3082], [1980, 3074]],
    "minute_lume_half_width_px": 18,
    "minute_tail_end": [1478, 3096],
    "minute_tail_half_width_px": 34,
    "hand_point_px": {"hour": 30, "minute": 64},
    "time_index_radius_px": 548,  # polished rim ring of the time subdial (run 533-559 on every ray)
    "index_width_px": 47,
    # chronograph subdial hands (white paddles at 0): pivot, tip, stem half width, paddle half width,
    # shoulder (full paddle width) and stem start above the pivot, tail below it
    "sub_hands": {
        "12": {"pivot": [1573, 2040], "tip": [1578, 1715], "stem_hw": 12.5, "paddle_hw": 51, "shoulder": 85, "neck": 140, "tail": 85},
        "9": {"pivot": [882, 2470], "tip": [875, 2242], "stem_hw": 12.5, "paddle_hw": 42, "shoulder": 45, "neck": 90, "tail": 85},
        "3": {"pivot": [2270, 2460], "tip": [2274, 2232], "stem_hw": 13, "paddle_hw": 41, "shoulder": 40, "neck": 85, "tail": 82},
    },
    "sub_radius_px": {"12": 350, "9": 330, "3": 330, "6": 560},
    # pushers at 10, 8, 2 and the fluted crown at 4: centre of each cap (axis direction from the dial centre)
    "pusher_caps": {"upper_left": [140, 1870], "lower_left": [140, 3450], "upper_right": [2940, 1860]},
    "crown_centre": [2870, 3410],
    # bracelet: three columns; outer links start at the lug tips, centre links half a row further out
    "bracelet_joints_y": {"top_outer": [1105, 790, 457], "top_centre": [964, 664, 364],
                          "bottom_outer": [4207, 4560, 4843], "bottom_centre": [4393, 4664, 4936]},
    "bracelet_columns_x": {"y900": [964, 1262, 1264, 1900, 1904, 2200], "y4450": [948, 1262, 1266, 1912, 1916, 2224]},
    "end_link_x": [930, 2240],  # outer edges between the lugs at the case
}
ARTEFACTS = ["the photo is taken slightly from below: the inner bezel wall shows at 12 (in the photo map) and the lug tips sit 0.85 mm lower than the dial centre",
             "subdial prints, the time-subdial rim, flange print (RESET/SPLIT, START/STOP, MODE, ADJUST, 1/100 SEC. CHRONOGRAPH) and its crystal reflection stay in the photo map",
             "pusher and crown radii and lengths are read from oblique views of their sides (+-0.2 mm)"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 1.5)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["dial_centre"]

    xs = np.nonzero(fg[py0])[0]
    x_left, x_right = float(xs.min()), float(xs.max())
    width_px = x_right - x_left
    S = width_px / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the dial-centre row = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(width_px / 2 / S, 3), "edges_px": [x_left, x_right],
                    "centre_offset_mm": round(((x_left + x_right) / 2 - px0) / S, 3)}}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["rings_px"].items()}
    out["rings_mm"]["case"] = out["case"]["radius_mm"]

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    left_x = {p[0]: -p[1] for p in prof}
    # lug tips: the left edge steps in from the lug corner (about 13 mm) to the bracelet (about 9.5 mm); halfway
    tips = []
    for sy in (1, -1):
        lo, hi = left_x[round(sy * 20.0, 2)], left_x[round(sy * 30.0, 2)]
        tips.append(next(y for y in np.arange(20, 30, 0.25) if left_x[round(sy * y, 2)] < (lo + hi) / 2) - 0.125)
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    rc = width_px / 2 / S
    leave = [next(y for y in np.arange(6, 22, 0.25) if left_x[round(sy * y, 2)] > math.sqrt(max(rc * rc - y * y, 0)) + 0.1) for sy in (1, -1)]
    out["lug_leaves_case_y_mm"] = {"top": leave[0], "bottom": leave[1], "mean": round(sum(leave) / 2, 3)}
    el = M["end_link_x"]
    out["end_link_half_width_mm"] = round((el[1] - el[0]) / 2 / S, 3)
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (26, 30, 34, 38, -28, -32, -36, -40) if y in width}
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "lug_width_mm": round(2 * out["end_link_half_width_mm"], 2), "listed": LISTED}

    # time subdial: hands, applied batons (bright run along each hour ray about the pivot)
    tp = np.array(M["time_pivot"], float)
    out["time_pivot_mm"] = mm(tp)
    idx = {}
    for hr in range(1, 13):
        t = math.radians(hr * 30)
        p = [g[int(tp[1] - r * math.cos(t)), int(tp[0] + r * math.sin(t))] for r in range(340, 530)]
        lit = [i for i, v in enumerate(p) if v > 140]
        runs, s = [], lit[0]
        for a_, b_ in zip(lit, lit[1:] + [None]):
            if b_ != a_ + 1:
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t_: t_[1] - t_[0])
        idx[str(hr)] = [round((340 + r0) / S, 3), round((340 + r1) / S, 3)]
    # 3 is under the minute hand: use 9
    idx["3"] = idx["9"]
    lng = [idx[k] for k in ("12", "6", "9")]
    sht = [idx[k] for k in idx if k not in ("12", "3", "6", "9")]
    medv = lambda rows, i: round(float(np.median([r[i] for r in rows])), 3)
    out["time_indices"] = {"per_hour_mm": idx, "long_mm": [medv(lng, 0), medv(lng, 1)], "short_mm": [medv(sht, 0), medv(sht, 1)],
                           "width_mm": round(M["index_width_px"] / S, 3), "rim_mm": round(M["time_index_radius_px"] / S, 3),
                           "layout": "applied polished batons filled with white lume; long at 12, 3, 6, 9"}

    def polar(p, piv=tp):
        v = np.array(p, float) - piv
        return round(float(np.hypot(*v)) / S, 3), round(math.degrees(math.atan2(v[0], -v[1])) % 360, 2)

    turn = lambda pts, deg: [[round(x * math.cos(math.radians(deg)) + y * math.sin(math.radians(deg)), 4),
                              round(-x * math.sin(math.radians(deg)) + y * math.cos(math.radians(deg)), 4)] for x, y in pts]
    hands = {}
    for name in ("hour", "minute"):
        L, a = polar(M[name + "_tip"])
        hw = M[name + "_half_width_px"] / S
        tail = polar(M["minute_tail_end"])[0] if name == "minute" else M["hour_tail_px"] / S
        thw = M["minute_tail_half_width_px"] / S if name == "minute" else hw
        pt = M["hand_point_px"][name] / S
        lume = sorted(polar(p)[0] for p in M[name + "_lume_px"])
        lw = M[name + "_lume_half_width_px"] / S
        hands[name] = {"angle_deg": a, "length_mm": L, "half_width_mm": round(hw, 3), "tail_mm": round(tail, 3),
                       "outline_mm": turn([(-thw, -tail), (thw, -tail), (thw, 0), (hw, 0), (hw, L - pt), (0, L), (-hw, L - pt), (-hw, 0), (-thw, 0)], a),
                       "lume_mm": turn([(-lw, lume[0]), (lw, lume[0]), (lw, lume[1]), (-lw, lume[1])], a)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]

    subs = {}
    for k, sh in M["sub_hands"].items():
        piv = np.array(sh["pivot"], float)
        L, a = polar(sh["tip"], piv)
        sw, pw = sh["stem_hw"] / S, sh["paddle_hw"] / S
        sd, nk, tl = sh["shoulder"] / S, sh["neck"] / S, sh["tail"] / S
        cap = [(sw * math.cos(math.radians(d)), L - sw + sw * math.sin(math.radians(d))) for d in range(0, 181, 30)]  # rounded tip
        poly = [(-pw, -tl), (pw, -tl), (pw, sd), (sw, nk)] + cap + [(-sw, nk), (-pw, sd)]
        subs[k] = {"pivot_mm": mm(piv), "angle_deg": a, "length_mm": L, "outline_mm": turn(poly, a),
                   "radius_mm": round(M["sub_radius_px"][k] / S, 3)}
    subs["6"] = {"pivot_mm": mm(tp), "radius_mm": round(M["sub_radius_px"]["6"] / S, 3)}
    out["subdials"] = subs

    # pushers and crown: axis angle from the cap centre, end = last case pixel along the axis
    def axis(p):
        x, y = mm(p)
        a = math.degrees(math.atan2(x, y)) % 360
        t = math.radians(a)
        rs = np.arange(20 * S, 28.5 * S, 0.5)
        hit = [r for r in rs if fg[int(py0 - r * math.cos(t)), int(px0 + r * math.sin(t))]]
        return {"angle_deg": round(a, 2), "end_r_mm": round(max(hit) / S, 3)}
    out["pushers"] = {k: axis(p) for k, p in M["pusher_caps"].items()}
    out["crown"] = axis(M["crown_centre"])

    j = M["bracelet_joints_y"]
    jm = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    out["bracelet_joints_mm"] = jm
    pitch = [abs(a - b_) for v in jm.values() for a, b_ in zip(v[1:], v[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.median(pitch)), 3)
    shift = [c - o for c, o in zip(jm["top_centre"], jm["top_outer"])] + [c - o for c, o in zip(jm["bottom_centre"], jm["bottom_outer"])]
    out["bracelet_centre_joint_shift_mm"] = round(float(np.mean(shift)), 3)
    out["bracelet_outer_start_after_tip_mm"] = round(float(np.mean([jm["top_outer"][0] - tips[0], jm["bottom_outer"][0] - tips[1]])), 3)
    fr = []
    for xs_ in M["bracelet_columns_x"].values():
        fr.append((xs_[3] - xs_[2]) / (xs_[-1] - xs_[0]))
    out["bracelet_centre_fraction"] = round(float(np.mean(fr)), 3)

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rad in out["rings_mm"].values():
            cv2.circle(ov, (px0, py0), int(rad * S), (0, 0, 255), 2)
        for y_mm, l_, r2 in prof:
            cv2.circle(ov, P((l_, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r2, y_mm)), 3, (0, 255, 0), -1)
        tpm = out["time_pivot_mm"]
        for hd in hands.values():
            pts = [P((x + tpm[0], y + tpm[1])) for x, y in hd["outline_mm"]]
            cv2.polylines(ov, [np.array(pts, np.int32)], True, (0, 255, 255), 3)
        for s_ in subs.values():
            cv2.circle(ov, P(s_["pivot_mm"]), int(s_["radius_mm"] * S), (255, 255, 0), 2)
            if "outline_mm" in s_:
                pts = [P((x + s_["pivot_mm"][0], y + s_["pivot_mm"][1])) for x, y in s_["outline_mm"]]
                cv2.polylines(ov, [np.array(pts, np.int32)], True, (0, 255, 255), 3)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            for r2 in (out["time_indices"]["long_mm"] if hr % 3 == 0 else out["time_indices"]["short_mm"]):
                cv2.circle(ov, P((tpm[0] + r2 * math.sin(t), tpm[1] + r2 * math.cos(t))), 8, (255, 0, 255), 3)
        for v in list(out["pushers"].values()) + [out["crown"]]:
            t = math.radians(v["angle_deg"])
            cv2.line(ov, P((20 * math.sin(t), 20 * math.cos(t))), P((v["end_r_mm"] * math.sin(t), v["end_r_mm"] * math.cos(t))), (0, 200, 255), 3)
        for y in (tips[0], -tips[1]):
            cv2.line(ov, P((-14, y)), P((14, y)), (0, 128, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "rings_mm", "lug_tip_mm", "lug_leaves_case_y_mm", "checks",
                                           "end_link_half_width_mm", "bracelet_width_mm", "time_pivot_mm", "time_indices", "pushers",
                                           "crown", "bracelet_pitch_mm", "bracelet_joints_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_outer_start_after_tip_mm", "bracelet_centre_fraction")}, default=float, indent=0), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, {k: v.get("angle_deg") for k, v in data["subdials"].items()})