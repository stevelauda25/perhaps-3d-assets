"""Cut the Orient RA-AK0704N10B photo map (dial and grey leather strap) from the front photo, hands and their shadows removed.

    python3 -B -m pipeline.orient_ra_ak0704n10b_dial [out.jpg] [review.png]   # default outputs/watches/orient-ra-ak0704n10b/photo.jpg

Same method as RA-AK0705R10B (pipeline/orient_ra_ak0705r10b_dial.py), this photo's trace and spec. Silver hands: light from the
upper left, shadows fall to the lower right.
"""
import sys
from pathlib import Path

from pipeline.orient_ra_ak0705r10b_dial import ROOT, build

TRACE = ROOT / "config/watches/orient-ra-ak0704n10b-trace.json"
SPEC = ROOT / "config/watches/orient-ra-ak0704n10b.json"
OUT = ROOT / "outputs/watches/orient-ra-ak0704n10b/photo.jpg"
HAND_MARGIN_MM = {"hour": 0.25, "minute": 0.25}
SHADOWS_MM = {"hour": ((0.15, -0.15), (0.3, -0.3)), "minute": ((0.15, -0.15), (0.3, -0.3))}

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None, TRACE, SPEC, HAND_MARGIN_MM, SHADOWS_MM), "->", dest)
