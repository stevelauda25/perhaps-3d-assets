"""Cut the Hamilton H70405710 (Khaki Field Murph 38 mm) photo maps from the front photo: a clean white dial (hands and their
shadows removed) and the black leather strap resampled to a straight strip.

    python3 -B -m pipeline.hamilton_h70405710_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h70405710/dial_photo.jpg

Same method and build() as pipeline/hamilton_h69439940_dial.py. Print here is the black track, logo and numeral outlines plus
the cream numeral lume; the outer track numerals (5, 10 ...) sit among the ticks, so print counts as a feature out to 13.8 mm
and the ticks the needles cross are left to the 3D needles that cover them.
"""
import sys
from pathlib import Path

from pipeline.hamilton_h69439940_dial import ROOT, build

CFG = {
    "trace": ROOT / "config/watches/hamilton-h70405710-trace.json",
    "out": ROOT / "outputs/watches/hamilton-h70405710/dial_photo.jpg",
    "margin_mm": 0.3,
    "shadows_mm": ((0.3, 0.0), (0.6, -0.05), (0.9, -0.1)),  # soft grey shadows to the right
    "hub_zone_mm": 1.4,
    "feature_r_mm": 13.8,
    "feature": lambda img: (img.mean(2) < 150) | (img[..., 2].astype(int) - img[..., 0] > 30),  # black print, cream lume
    "strap_centre_x": 743,
    "strap_width_px": 702,  # 20 mm at the photo scale
    "strap_end_y": 2425,  # rounded strap end below this row
}

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else CFG["out"]
    print(build(CFG, dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
