"""Cut the SMGG21P1 photo map (LCD dial and the printed octagon insert) from the official front image.

    python3 -B -m pipeline.seiko_smgg21_dial [out.jpg]     # default outputs/watches/seiko-smgg21p1/dial_photo.jpg

Digital watch: no hands to remove. Square crop centred on the octagon centre out to the insert's corners, at the image's
own resolution, light unsharp mask, JPEG. The build maps model mm to it: u = 0.5 + x / (2 half), v = 0.5 + y / (2 half).
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/seiko-smgg21p1-trace.json"
OUT = ROOT / "outputs/watches/seiko-smgg21p1/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
HALF_MM = 17.8  # past the insert's octagon corners


def build(out=OUT):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    im = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)
    a = im[..., 3:4] / 255.0
    img = (im[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    hw = int(round(HALF_MM * S))
    crop = img[py0 - hw:py0 + hw, px0 - hw:px0 + hw]
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_mm": round(hw / S, 4), "size_px": list(crop.shape[1::-1])}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest), "->", dest)
