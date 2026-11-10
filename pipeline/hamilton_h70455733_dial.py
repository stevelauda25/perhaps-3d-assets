"""Cut the Hamilton H70455733 (Khaki Field Auto 38 mm) photo maps from the official front render: a clean black dial (hands
removed) and the black leather strap resampled to a straight strip.

    python3 -B -m pipeline.hamilton_h70455733_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h70455733/dial_photo.jpg

Same method and build() as pipeline/hamilton_h69439940_dial.py. White print on the black dial; print counts as a feature
inside the minute track (12.7-14.3 mm), which is copied 6 deg over. The render's hand shadows are faint and short.
"""
import sys
from pathlib import Path

from pipeline.hamilton_h69439940_dial import ROOT, build

CFG = {
    "trace": ROOT / "config/watches/hamilton-h70455733-trace.json",
    "out": ROOT / "outputs/watches/hamilton-h70455733/dial_photo.jpg",
    "margin_mm": 0.25,
    "shadows_mm": ((0.15, -0.15), (0.3, -0.3)),
    "hub_zone_mm": 1.2,
    "feature_r_mm": 12.6,
    "feature": lambda img: img[..., 2].astype(int) > 170,  # white print on the black dial (not the grey ring's glare)
    "copy_from_r_mm": 12.5,  # plain black dial inside the track: inpainted (6 deg copies dragged hand edges in)
    "tight_mm": 0.12,  # the render's hand edges are soft: replace a little more of the hand next to print
    "strap_centre_x": 1052,
    "strap_width_px": 476,  # 20 mm at the render scale
    "strap_end_y": 1940,  # the strap end and its floor reflection are below this row
}

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else CFG["out"]
    print(build(CFG, dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
