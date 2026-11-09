"""Cut a clean dial map for the SNK357K1 from the front photo, with the hands removed.

    python3 -B -m pipeline.seiko_snk357_dial [out.jpg] [review.png]     # default outputs/watches/seiko-snk357k1/dial_photo.jpg

Same method as pipeline/seiko_snk361_dial.py (hand zones inpainted). No hand crosses SEIKO or the 5 shield in this photo,
so the logo stays as photographed.
"""
import sys
from pathlib import Path

from pipeline import seiko_snk361_dial as base

base.TRACE = base.ROOT / "config/watches/seiko-snk357k1-trace.json"
base.paste_logo = lambda img, t: None
OUT = base.ROOT / "outputs/watches/seiko-snk357k1/dial_photo.jpg"

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(base.build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None), "->", dest)
