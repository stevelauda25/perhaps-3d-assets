"""Lossless-in-effect lean maps for the Private Edition leather (same 8192 px, no resampling).

    python3 -B -m pipeline.lean_leather_maps OUT_TEXTURES_DIR

The v012 leather only reads the colour map through RGB-to-BW (pigment variation), so the 8-bit RGB scan is
replaced by its Rec.709 linear luminance stored as an 8-bit sRGB greyscale PNG (same node graph, same decode).
Roughness (already greyscale) and normal are re-encoded with maximum PNG compression and kept only if the
pixels are identical. Writes maps.json with sizes and the colour-map error actually measured.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "textures/sources/polyhaven_leather_red_02_8k"
ACTIVE_MAX = 0.093  # luminance_range top in config/private_edition_v013.json
W709 = np.array([0.2126729, 0.7151522, 0.0721750], dtype=np.float32)  # Blender scene-linear luminance


def to_linear(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def to_srgb(v):
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(v, 1 / 2.4) - 0.055)


def luminance_map(src, dst):
    rgb = np.asarray(Image.open(src))
    lum = np.empty(rgb.shape[:2], np.uint8)
    err_max, err_sum, err_active = 0.0, 0.0, 0.0
    for y in range(0, rgb.shape[0], 512):  # row bands keep float memory small
        c = to_linear(rgb[y:y + 512].astype(np.float32) / 255)
        lin = c[..., 0] * W709[0] + c[..., 1] * W709[1] + c[..., 2] * W709[2]  # explicit sum: macOS matmul warns spuriously
        q = np.rint(to_srgb(lin) * 255).astype(np.uint8)
        lum[y:y + 512] = q
        e = np.abs(to_linear(q.astype(np.float32) / 255) - lin)  # linear-light error of the stored value
        err_max, err_sum = max(err_max, float(e.max())), err_sum + float(e.sum())
        live = lin <= ACTIVE_MAX  # luminance above the preset's map-range top is clipped, so its error is moot
        err_active = max(err_active, float(e[live].max(initial=0)))
    Image.fromarray(lum).save(dst, optimize=True, compress_level=9)
    return {"max_linear_error_all": err_max, "max_linear_error_active_range": err_active, "active_range_max": ACTIVE_MAX,
            "max_linear_error": err_max, "mean_linear_error": err_sum / lum.size}


def recompress(src, dst):
    im = Image.open(src)
    im.save(dst, optimize=True, compress_level=9)
    same = np.array_equal(np.asarray(im), np.asarray(Image.open(dst)))
    if not same or dst.stat().st_size >= src.stat().st_size:
        dst.write_bytes(src.read_bytes())  # never ship a bigger or non-identical file
    return same


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    report["luminance"] = luminance_map(SRC / "leather_red_02_coll1_8k.png", out / "leather_red_02_lum_8k.png")
    for key, name in (("roughness", "leather_red_02_rough_8k.png"), ("normal", "leather_red_02_nor_gl_8k.png")):
        report[key] = {"pixels_identical": recompress(SRC / name, out / name)}
    for p in sorted(out.glob("*.png")):
        report.setdefault(p.name, {}).update(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                             size=list(Image.open(p).size), mode=Image.open(p).mode)
    (out / "maps.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
