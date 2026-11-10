"""Cut the Orient FAC0000CA0 photo map (dial and black leather strap) from the front photo, hands and shadows removed.

    python3 -B -m pipeline.orient_fac0000ca0_dial [out.jpg] [review.png]   # default outputs/watches/orient-fac0000ca0/photo.jpg

Same method as RA-AK0705R10B (pipeline/orient_ra_ak0705r10b_dial.py), this photo's trace and spec. Silver hands, soft shadow to the
lower right. The batons are filled too: the 2 o'clock baton lies beside the minute hand.
"""
import sys
from pathlib import Path

from pipeline.orient_ra_ak0705r10b_dial import ROOT, build

TRACE = ROOT / "config/watches/orient-fac0000ca0-trace.json"
SPEC = ROOT / "config/watches/orient-fac0000ca0.json"
OUT = ROOT / "outputs/watches/orient-fac0000ca0/photo.jpg"
HAND_MARGIN_MM = {"hour": 0.3, "minute": 0.3, "seconds": 0.35}
SHADOWS_MM = {"hour": ((0.15, -0.15), (0.3, -0.3)), "minute": ((0.15, -0.15), (0.3, -0.3))}

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None, TRACE, SPEC, HAND_MARGIN_MM, SHADOWS_MM, True), "->", dest)
