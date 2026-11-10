"""Cut the Orient RA-AC0E04L10B photo map (dial, rehaut and navy leather strap) from the front photo, hands and shadows removed.

    python3 -B -m pipeline.orient_ra_ac0e04l10b_dial [out.jpg] [review.png]   # default outputs/watches/orient-ra-ac0e04l10b/photo.jpg

Same method as RA-AK0705R10B (pipeline/orient_ra_ak0705r10b_dial.py), this photo's trace and spec. Silver hands, soft shadow to the
lower right. The strap leaves the photo at the top edge only 5.5 mm past the lug tip (photo_past_tip in the spec stays inside).
"""
import sys
from pathlib import Path

from pipeline.orient_ra_ak0705r10b_dial import ROOT, build

TRACE = ROOT / "config/watches/orient-ra-ac0e04l10b-trace.json"
SPEC = ROOT / "config/watches/orient-ra-ac0e04l10b.json"
OUT = ROOT / "outputs/watches/orient-ra-ac0e04l10b/photo.jpg"
HAND_MARGIN_MM = {"hour": 0.3, "minute": 0.3, "seconds": 0.35}  # seconds: its tail sits next to the minute hand; the gap between them goes too
SHADOWS_MM = {"hour": ((0.15, -0.15), (0.3, -0.3)), "minute": ((0.15, -0.15), (0.3, -0.3))}

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None, TRACE, SPEC, HAND_MARGIN_MM, SHADOWS_MM), "->", dest)
