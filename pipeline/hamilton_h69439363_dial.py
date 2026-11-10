"""Cut the Hamilton H69439363 (Khaki Field Mechanical 38 mm, green dial) photo maps from the official front render: a clean
green dial (hands removed) and the green canvas strap resampled to a straight strip.

    python3 -B -m pipeline.hamilton_h69439363_dial [out.jpg] [review.png]   # default outputs/watches/hamilton-h69439363/dial_photo.jpg

Same method and build() as pipeline/hamilton_h69439940_dial.py. Light print on the green dial; print counts as a feature
inside the minute track (13.4-14.2 mm), which is copied 6 deg over. The render casts soft hand shadows to the lower right; the hand zones include them.
"""
import sys
from pathlib import Path

from pipeline.hamilton_h69439940_dial import ROOT, build

CFG = {
    "trace": ROOT / "config/watches/hamilton-h69439363-trace.json",
    "out": ROOT / "outputs/watches/hamilton-h69439363/dial_photo.jpg",
    "margin_mm": 0.25,
    "shadows_mm": ((0.15, -0.15), (0.3, -0.3), (0.45, -0.45), (0.6, -0.6)),  # soft drop shadows to the lower right
    "hub_zone_mm": 1.2,
    "feature_r_mm": 13.2,
    "feature": lambda img: img[..., 2].astype(int) > 130,  # light print on the green dial
    "copy_from_r_mm": 13.2,  # plain green dial inside the track: inpainted (6 deg copies dragged hand edges in)
    "tight_mm": 0.12,  # the render's hand edges are soft: replace a little more of the hand next to print
    "strap_centre_x": 1050,
    "strap_width_px": 473,  # 20 mm at the render scale
    "strap_end_y": 1940,  # the strap end is below this row
}

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else CFG["out"]
    print(build(CFG, dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
