"""Side-by-side crops of the official front reference and our orthographic front render at the SAME pixel scale (host-side, PIL).

    python3 -B -m pipeline.front_compare OUR.png OUT.png [region ...]

Regions are named boxes in reference pixels (2000 px front, 23.77 px/mm, dial centre (999, 883)). Each crop pair: reference left, ours right.
A comparison aid for the designer and for measuring: nothing here scores similarity.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references/omega-speedmaster-310-30-42-50-01-001/hires/official_main_2000.png"
REGIONS = {
    "top_bezel": (700, 330, 1300, 700),
    "crown_right": (1300, 560, 1700, 1160),
    "lug_left": (340, 330, 840, 830),
    "dial_centre": (700, 640, 1300, 1140),
    "subdial_left": (560, 820, 1000, 1160),
    "bottom": (700, 1180, 1300, 1560),
    "bracelet_top": (560, 0, 1440, 420),
    "lug_tl": (420, 200, 820, 520),
    "push_top": (1330, 560, 1630, 800),
}


def load_ref():
    ref = Image.open(REF).convert("RGBA")
    bg = Image.new("RGBA", ref.size, (255, 255, 255, 255))
    bg.alpha_composite(ref)
    return bg.convert("RGB")


def board(ours_path, out, names):
    ref, ours = load_ref(), Image.open(ours_path).convert("RGB")
    assert ours.size == ref.size, "render must be %s, got %s" % (ref.size, ours.size)
    rows = []
    for n in names:
        box = REGIONS[n]
        a, b = ref.crop(box), ours.crop(box)
        row = Image.new("RGB", (a.width * 2 + 8, a.height + 20), (255, 255, 255))
        row.paste(a, (0, 20)); row.paste(b, (a.width + 8, 20))
        ImageDraw.Draw(row).text((4, 4), n + ": reference (left) | ours (right)", fill=(200, 0, 0))
        rows.append(row)
    W, H = max(r.width for r in rows), sum(r.height for r in rows)
    sheet = Image.new("RGB", (W, H), (255, 255, 255)); y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.height
    sheet.save(out)
    return sheet.size


if __name__ == "__main__":
    names = sys.argv[3:] or ["top_bezel", "crown_right"]
    print(board(sys.argv[1], sys.argv[2], names))


def silhouette_report(mask_png, out_png=None):
    """IoU between the reference alpha and our silhouette mask (pipeline/front_silhouette.py), per band of |y| (mm), with a red/green difference image
    (red: reference only, green: ours only). The reference crops its bracelet at the image edges; ours is clipped identically."""
    import numpy as np
    S, cx, cy = 23.7709, 999.0, 882.98
    ref = np.asarray(Image.open(REF).split()[-1]) > 128
    ours = np.asarray(Image.open(mask_png).convert("L")) > 128
    yy = (cy - np.arange(2000))[:, None] / S
    bands = {"case |y|<18": (0, 18), "lugs 18-24": (18, 24), "bracelet 24-43": (24, 43)}
    rep = {"all": round(float((ref & ours).sum() / (ref | ours).sum()), 4)}
    for name, (a, b) in bands.items():
        sel = (np.abs(yy) >= a) & (np.abs(yy) < b)
        sel = np.broadcast_to(sel, ref.shape)
        rep[name] = round(float(((ref & ours) & sel).sum() / max(((ref | ours) & sel).sum(), 1)), 4)
    if out_png:
        vis = np.full(ref.shape + (3,), 255, np.uint8)
        vis[ref & ours] = (190, 190, 190)
        vis[ref & ~ours] = (0, 0, 255)
        vis[~ref & ours] = (0, 170, 0)
        Image.fromarray(vis[:, :, ::-1]).save(out_png)
    return rep
