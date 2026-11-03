"""Register a white-background reference photo to the model's coordinate system (host-side, numpy + OpenCV).

    python3 -B -m pipeline.ref_register config/watches/ref_landmarks/bobs_3q.json [out.json]

Landmarks = lume bars of the dial (their model positions are the traced radius/angles, config/watches/speedmaster-trace.json), coarse pixel
positions picked from the photo and refined here to the centroid of the bright blob. All lie on the dial plane, so a planar PnP gives the
camera pose; the focal length is scanned for the lowest reprojection error (principal point = image centre). Output: rotation/translation of
the model in camera space, focal in px and mm, yaw/pitch/roll of the dial and the camera distance in mm.
Everything reported is a measurement against a real photo, not a visual score.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def refine(gray, pt, win=34, thr=200):
    x, y = int(pt[0]), int(pt[1])
    x0, y0 = max(x - win, 0), max(y - win, 0)
    patch = gray[y0:y + win, x0:x + win]
    m = (patch > thr).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return pt, False
    # component whose centroid is nearest the coarse point and that is bar-sized (not a hand: reject > 4000 px)
    best, bd = None, 1e9
    for i in range(1, n):
        if st[i, 4] < 60 or st[i, 4] > 4000:
            continue
        d = math.hypot(cen[i][0] + x0 - pt[0], cen[i][1] + y0 - pt[1])
        if d < bd:
            best, bd = (cen[i][0] + x0, cen[i][1] + y0), d
    return (best, True) if best is not None and bd < win else (pt, False)


def register(spec):
    img = cv2.imread(str(ROOT / spec["image"]))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    r_mm = spec.get("bar_radius_mm", 13.85)
    z_mm = spec.get("plane_z_mm", 9.0)
    obj, pix, names = [], [], []
    for name, coarse in spec["bars_px"].items():
        k = int(name)  # hour 1..12 (12 uses its dot pair centre, listed separately)
        ang = math.radians(k * 30)
        pt, ok = refine(gray, coarse)
        obj.append((r_mm * math.sin(ang), r_mm * math.cos(ang), z_mm))
        pix.append(pt)
        names.append((name, ok))
    obj, pix = np.array(obj, np.float64), np.array(pix, np.float64)
    best = None
    for f in np.arange(spec.get("f_min", 3000), spec.get("f_max", 60000), spec.get("f_step", 250)):
        K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]], np.float64)
        ok, rvec, tvec = cv2.solvePnP(obj, pix, K, None, flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            continue
        proj, _ = cv2.projectPoints(obj, rvec, tvec, K, None)
        err = float(np.sqrt(((proj[:, 0, :] - pix) ** 2).sum(1)).mean())
        if best is None or err < best[0]:
            best = (err, f, rvec, tvec, K)
    err, f, rvec, tvec, K = best
    R, _ = cv2.Rodrigues(rvec)
    # dial normal in camera space = third column of R; camera looks along +z
    n = R[:, 2]
    tilt = math.degrees(math.acos(abs(n[2])))
    # camera position in model space
    cam = (-R.T @ tvec).ravel()
    out = {"image": spec["image"], "size": [w, h], "focal_px": round(float(f), 1), "focal_mm_35": round(float(f) * 36 / w, 1),
           "mean_reproj_px": round(err, 2), "dial_normal_vs_view_deg": round(tilt, 1), "camera_distance_mm": round(float(np.linalg.norm(cam)), 1),
           "camera_pos_model_mm": [round(float(v), 1) for v in cam], "rvec": [float(v) for v in rvec.ravel()], "tvec": [float(v) for v in tvec.ravel()],
           "landmarks_refined": [[n_, ok_] for n_, ok_ in names]}
    return out


if __name__ == "__main__":
    spec = json.loads((ROOT / sys.argv[1]).read_text())
    res = register(spec)
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else (ROOT / sys.argv[1]).with_name(Path(sys.argv[1]).stem + "_pose.json")
    dest.write_text(json.dumps(res, indent=1))
    print({k: v for k, v in res.items() if k not in ("rvec", "tvec", "landmarks_refined")}, "->", dest)
