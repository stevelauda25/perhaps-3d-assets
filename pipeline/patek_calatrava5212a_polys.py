"""Phase 1b for the PATEK PHILIPPE Calatrava Weekly Calendar 5212A: hand, hub, red-tip and applied-index polygons measured from the photo, written into the spec's `hands.polygons`.

    python3 -B -m pipeline.patek_calatrava5212a_polys [variant key]      # default 5212a
        reads    references/patek-calatrava-weekly-calendar-<variant>/patek-<variant>_original.png, config/watches/patek-calatrava5212a-<variant>-measure.json
        updates  config/watches/patek-calatrava5212a-<variant>.json  (keys hands.polygons only)

The 5212A has seven central hands (hour, minute, month needle to 12, day needle with red tip, week needle with red tip, a black spade-shaped hand pointing down, hub star)
and twelve gunmetal applied indices; none fits the 6007G profile-hand code, so every one is a free polygon (the step already extrudes `hands.polygons`).
The polygons are straight from the photo (the hands in the dial map stay, the polygons carry the same projected pixels, so the front view cannot differ; they give height and edges):
  - blades (hour, minute) and needles (month, day, week): strips rotated about the pivot, left / right edge from the first crossing of the grey threshold around the axis
    (`runs`), then robust straight-line fits over a clean range (prints and indices that touch the hand are rejected as outliers) and the polygon follows the two lines, 0.7 px wider;
  - spade: edges sampled directly (no print touches it);
  - red tips: contour of the red mask near the needle ends;  hub star: contour of the dark mask within 66 px of the pivot;  indices: contours of the dark components in the index annulus.
All pixel positions are CONTINUOUS photo coordinates (pixel i spans [i, i+1]); output mm, x right, y toward 12, origin = pivot.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VAR = (sys.argv[1] if len(sys.argv) > 1 else "5212a").lower()
NAME = "patek-calatrava5212a-%s" % VAR
SRC = ROOT / ("references/patek-calatrava-weekly-calendar-%s/patek-%s_original.png" % (VAR, VAR))
PX = json.loads((ROOT / ("config/watches/%s-measure.json" % NAME)).read_text())
SPEC = ROOT / ("config/watches/%s.json" % NAME)
im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
G = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
OX, OY = PX["pivot"]
S = 2 * PX["bezel_out_circle_px"][2] / 40.0
PAD = 0.7  # px the polygons are wider than the photographed hands, so the 3D hand hides the photographed edge


def to_mm(x, y):
    return [round((x - OX) / S, 3), round((OY - y) / S, 3)]


def strip(theta, s0, s1, vmax=60):
    t = math.radians(theta)
    d, n = np.array([math.sin(t), -math.cos(t)]), np.array([math.cos(t), math.sin(t)])  # along the hand, to its right
    ss, vv = np.arange(s0, s1 + 1e-6, 1.0), np.arange(-vmax, vmax + 1e-6, 0.5)
    X = OX + ss[:, None] * d[0] + vv[None, :] * n[0] - 0.5
    Y = OY + ss[:, None] * d[1] + vv[None, :] * n[1] - 0.5
    return ss, vv, cv2.remap(G, X.astype(np.float32), Y.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), d, n


def runs(theta, s0, s1, thr, centre=0.0):
    """Per s: (left v, right v) of the dark run that contains (or lies within 8 px of) v = centre, sub-pixel by linear interpolation; None where there is none."""
    ss, vv, I, _, _ = strip(theta, s0, s1)
    out = []
    for i in range(len(ss)):
        row = I[i] < thr
        c = int(np.argmin(np.abs(vv - centre)))
        if not row[c]:
            idx = np.nonzero(row)[0]
            idx = idx[np.abs(vv[idx] - centre) < 8]
            if len(idx) == 0:
                out.append(None)
                continue
            c = int(idx[np.argmin(np.abs(vv[idx] - centre))])
        l = c
        while l > 0 and row[l - 1]:
            l -= 1
        r = c
        while r < len(vv) - 1 and row[r + 1]:
            r += 1
        sub = lambda a, b: vv[a] + (thr - I[i][a]) / (I[i][b] - I[i][a] + 1e-9) * (vv[b] - vv[a])
        out.append((float(sub(l, max(l - 1, 0))), float(sub(r, min(r + 1, len(vv) - 1)))))
    return ss, out


def robust_line(x, y, tol=1.0):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.ones(len(x), bool)
    for _ in range(8):
        b, a = np.polyfit(x[m], y[m], 1)
        res = np.abs(y - (a + b * x))
        m2 = res < max(tol, 2.5 * res[m].std())
        if (m2 == m).all():
            break
        m = m2
    return a, b, int(m.sum())


def needle(theta, thr, fit, s_a, s_b):
    """Two straight edges fitted over s in `fit`; returns (polygon in photo px, theta used, fit info)."""
    th = theta
    for _ in range(3):  # re-aim the strip along the fitted centre line so the contiguous-run search stays on the hand
        ss, rr = runs(th, fit[0], fit[1], thr)
        ok = [(s, r) for s, r in zip(ss, rr) if r is not None]
        s_ = [s for s, _ in ok]
        al, bl, nl = robust_line(s_, [r[0] for _, r in ok])
        ar, br_, nr = robust_line(s_, [r[1] for _, r in ok])
        slope = (bl + br_) / 2
        if abs(slope) < 1e-4:
            break
        th += math.degrees(math.atan(slope))
    _, _, _, d, n = strip(th, 0, 1)
    pts = []
    for s in (s_a, s_b):
        pts.append((s, al + bl * s - PAD))
    for s in (s_b, s_a):
        pts.append((s, ar + br_ * s + PAD))
    poly = [(OX + s * d[0] + v * n[0], OY + s * d[1] + v * n[1]) for s, v in pts]
    return poly, th, {"theta": round(th, 3), "fit_points": [nl, nr], "half_width_px_at_a": [round(-(al + bl * s_a), 2), round(ar + br_ * s_a, 2)],
                      "half_width_px_at_b": [round(-(al + bl * s_b), 2), round(ar + br_ * s_b, 2)]}


def contour(mask, eps=0.7):
    """Largest external contour of a binary mask, dilated by one pixel (0.5 px outward), simplified, in continuous photo px."""
    m = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float) + 0.5
    return [tuple(p) for p in c]


def build():
    out, info = {}, {}
    yy, xx = np.mgrid[0:G.shape[0], 0:G.shape[1]]
    rr = np.hypot(xx - OX, yy - OY)
    H = PX["hands5212a"]
    for name, h in H["needles"].items():
        poly, th, nf = needle(h["theta"], h["thr"], h["fit"], h["s_a"], h["s_b"])
        out[name] = {"z": h["z"], "thick": h.get("thick", 0.12), "outline_mm": [to_mm(*p) for p in poly]}
        info[name] = nf
    # spade hand: edges sampled directly
    sp = H["spade"]
    ss, ed = runs(sp["theta"], sp["fit"][0], sp["fit"][1], sp["thr"])
    ok = [(s, e) for s, e in zip(ss, ed) if e is not None]
    s_, l_, r_ = [s for s, _ in ok], [e[0] for _, e in ok], [e[1] for _, e in ok]
    al, bl, _ = robust_line([s for s in s_ if s < sp["lin_to"]], [l for s, l in zip(s_, l_) if s < sp["lin_to"]])
    ar, br_, _ = robust_line([s for s in s_ if s < sp["lin_to"]], [r for s, r in zip(s_, r_) if s < sp["lin_to"]])
    t = math.radians(sp["theta"])
    d, n = np.array([math.sin(t), -math.cos(t)]), np.array([math.cos(t), math.sin(t)])
    side = [(s_a, al + bl * s_a - PAD, ar + br_ * s_a + PAD) for s_a in (sp["s_a"],)] + [(s, l - PAD, r + PAD) for s, l, r in zip(s_, l_, r_) if s >= sp["lin_to"] and s % 4 == 0 or s >= sp["tip_from"]]
    left = [(OX + s * d[0] + l * n[0], OY + s * d[1] + l * n[1]) for s, l, r in side]
    right = [(OX + s * d[0] + r * n[0], OY + s * d[1] + r * n[1]) for s, l, r in side]
    out["spade"] = {"z": sp["z"], "thick": 0.12, "outline_mm": [to_mm(*p) for p in left + right[::-1]]}
    # hub star: dark mask inside r < 66 around the pivot (the roots and tails of all hands, the cap), outer contour
    hub = (G < 185) & (rr < H["hub_star_r_px"])
    n_, lab = cv2.connectedComponents(hub.astype(np.uint8))
    comp = lab == lab[int(round(OY)) + 22, int(round(OX))]
    out["hub_star"] = {"z": H["hub_star_z"], "thick": 0.12, "outline_mm": [to_mm(*p) for p in contour(comp, 0.8)]}
    # red tips on the day and week needles
    b, g, r = [im[..., i].astype(int) for i in range(3)]
    red = (r > 140) & (g < 100) & (b < 100) & (r - g > 70)
    for name, (cx, cy, hw) in H["red_tips"].items():
        win = np.zeros_like(red)
        win[int(cy - hw):int(cy + hw), int(cx - hw):int(cx + hw)] = True
        out["tip_" + name] = {"z": H["red_tip_z"][name], "thick": 0.12, "outline_mm": [to_mm(*p) for p in contour(red & win, 0.6)]}
    # applied indices: dark components of the annulus
    ang = (np.degrees(np.arctan2(xx - OX, -(yy - OY))) % 360)
    ann = (G < 185) & (rr > H["index_r_px"][0]) & (rr < H["index_r_px"][1])
    n_, lab, st, cen = cv2.connectedComponentsWithStats(ann.astype(np.uint8))
    idx = {}
    for i in range(1, n_):
        if 2300 < st[i, 4] < 3100:  # an index is a ~2600 px bar centred 349 px from the pivot; the thin needles, prints and the date numerals are smaller or bigger
            a = (math.degrees(math.atan2(cen[i][0] - OX, -(cen[i][1] - OY)))) % 360
            if abs(math.hypot(cen[i][0] - OX, cen[i][1] - OY) - 349) > 15:
                continue
            idx[round(a)] = contour(lab == i, 0.7)
    # the 2 o'clock index is partly hidden by the minute hand tip: rotate the 1 o'clock one about the dial centre by 30 deg
    one = min(idx, key=lambda k: abs(k - 30))
    c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
    idx[60] = [(OX + (x - OX) * c - (y - OY) * s, OY + (x - OX) * s + (y - OY) * c) for x, y in idx[one]]
    for a in sorted(idx):
        if abs(a - 60) <= 6 and a != 60:
            del idx[a]
    for k, a in enumerate(sorted(idx)):
        out["index_%03d" % a] = {"z": H["index_z"], "thick": H["index_thick"], "outline_mm": [to_mm(*p) for p in idx[a]]}
    spec = json.loads(SPEC.read_text())
    spec["hands"]["polygons"] = out
    SPEC.write_text(json.dumps(spec, indent=1) + "\n")
    return {"needles": info, "polygons": {k: len(v["outline_mm"]) for k, v in out.items()}}


if __name__ == "__main__":
    print(json.dumps(build()))
