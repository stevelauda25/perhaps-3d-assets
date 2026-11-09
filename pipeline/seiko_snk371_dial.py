"""Cut a clean dial map for the SNK371K1 from the front photo, with the hands and their shadows removed.

    python3 -B -m pipeline.seiko_snk371_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snk371k1/dial_photo.jpg

Same method as pipeline/seiko_snk369_dial.py (same dial layout): hand pixels on the yellow and grey track are copied from one
hour round the pivot; the plain blue dial is filled from its own shade plus grain. The 50, 45 and 10 beside the hands are kept.
"""
import sys
from pathlib import Path

from pipeline import seiko_snk369_dial as base

base.TRACE = base.ROOT / "config/watches/seiko-snk371k1-trace.json"
OUT = base.ROOT / "outputs/watches/seiko-snk371k1/dial_photo.jpg"
base.KEEP_OUT = ((1012, 2738, 50), (942, 3045, 50), (2095, 2730, 45))  # photo px: the 50, 45 and 10 numerals
base.ONE_OF_10 = None  # no print under a hand here
base.GRAIN_BOX = (1300, 3150, 1400, 3250)  # plain blue dial below the hub
# Rotation-copy zones, each with its shifts (deg) tried in order. The track starts at 9.62 mm and its blocks repeat every
# 6 deg, so it is copied from one minute round, away from the 2 o'clock index first (inside 9.5 mm: the 10, filled as plain
# dial); the outer minute ticks under the seconds needle are copied from the 10 o'clock side, away from the 9 o'clock index.
ZONES = (((9.5, 0.0, 125.0), (-6, -12, -18, -24, -30, 6, 12, 18)),
         ((11.0, 0.0, 360.0), (6, 12, 18, 24, -6, -12)))
_fill_track = base.fill_track


def fill_zones(img, mask, t):
    for base.TRACK, base.TRACK_SHIFTS in ZONES:
        mask = _fill_track(img, mask, t)
    return mask


base.fill_track = fill_zones
base.plain_dial = lambda out: (out[..., 0] > 110) & (out[..., 1] < 60) & (out[..., 2] < 40)  # BGR: blue dial only

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(base.build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
