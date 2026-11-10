"""Measure the Hamilton H70405710 (Khaki Field Murph 38 mm) front photo (native 1650 x 2539) into mm. Host-side, no Blender.

    python3 -B -m pipeline.hamilton_h70405710_trace [out.json] [overlay.png]   # default config/watches/hamilton-h70405710-trace.json

Same method and trace() as pipeline/hamilton_h69439940_trace.py. Anchor: case diameter 38.0 mm (Hamilton official) on the 9-3
row; the strap width (20 mm official) and lug to lug (44.7 mm listed) are checks. mm, x right, y toward 12, origin = the hand
pivot. Hands (leaf hour hand with four lume petals and a thin point, minute sword with three lume segments and a needle point,
thin seconds needle), crown and bezel radii come from gridded crops.
"""
from pathlib import Path

from pipeline.hamilton_h69439940_trace import ROOT, leaf, main, profile

FRONT = ROOT / "references/hamilton-h70405710/front_1650x2539.jpg"
OUT = ROOT / "config/watches/hamilton-h70405710-trace.json"
CASE_MM = 38.0  # Hamilton official
LISTED = {"lug_to_lug_mm": 44.7, "strap_width_mm": 20.0, "thickness_mm": 11.1}  # lug width official; lug to lug and height from retailers


def petals(grow, dl):
    return [leaf(158, 26 + dl, 7 + grow), leaf(198, 86 + dl, 13 + grow, 22.6), leaf(198, 86 + dl, 13 + grow, -23.4), leaf(252, 46 + dl, 12 + grow)]


HANDS_PX = {
    "hour": {"angle_deg": 306.1, "z": "hour", "parts": [
        {"mat": "hand", "layer": 0, "poly": profile([[-8, 7.5], [140, 7.5], [150, 6], [160, 0]])},
        {"mat": "hand", "layer": 0, "poly": [(-2, 262), (2, 262), (0.9, 370), (-0.9, 370)]},  # thin point past the petals
    ] + [{"mat": "hand", "layer": 0, "poly": p} for p in petals(3.5, 8)] + [{"mat": "lume_hands", "layer": 1, "poly": p} for p in petals(0, 0)]},
    "minute": {"angle_deg": 56.2, "z": "minute", "parts": [
        {"mat": "hand", "layer": 0, "poly": profile([[-8, 10], [50, 11], [95, 11.5], [236, 14.5], [300, 15.5], [334, 3], [338, 0]])},
        {"mat": "hand", "layer": 0, "poly": [(-2.5, 320), (2.5, 320), (1.2, 493), (-1.2, 493)]},  # needle point to the track
        {"mat": "lume_hands", "layer": 1, "poly": profile([[56, 7.5], [92, 8.2]]) },
        {"mat": "lume_hands", "layer": 1, "poly": profile([[100, 8.3], [236, 11.0]])},
        {"mat": "lume_hands", "layer": 1, "poly": profile([[241, 12.0], [298, 12.5], [326, 3], [331, 0]])}]},
    "seconds": {"angle_deg": 124.5, "z": "seconds", "parts": [
        {"mat": "hand", "layer": 0, "poly": [(-3.5, -30), (3.5, -30), (2.5, 440), (0, 505), (-2.5, 440)]}]},
}

MANUAL_PX = {
    "hand_pivot": [739.3, 1286.3],  # pin hole; the case circle centre is within 1 px in x
    "case_x": [72.4, 1406.2],  # case edge on the 9-3 row, crown root
    "case_step_r": 640,  # narrow brushed flank top, then the wide polished bezel slope
    "bezel_inner_r": 578,  # polished bezel ends at the crystal (thin black ring just inside)
    "rehaut_r": 523,  # flat dial edge; grey sloped chapter ring with dots up to the crystal (kept in the dial map)
    "hub_radius_px": [42, 15],
    "crown_x": [1406, 1549],
    "crown_cap_x": 1522,
    "crown_radius_px": 110.7,
    "crown_teeth": 26,
    "lug_inner_x_mm": 10.0,  # 20 mm strap (official lug width)
    "lug_tips_y": [521, 2066],  # inner corners of the slanted lug ends
    "lug_depth_mm": 14.0,
}
ARTEFACTS = ["the lugs curve down: the photo's lug to lug reads 44.0 mm (foreshortened); the listed 44.7 mm is used",
             "the lug ends read slanted from the front (bent-down tips); the outline by depth keeps that slant",
             "numerals (lume with black outline), minute track, logo and prints are printed: they stay in the photo map"]


if __name__ == "__main__":
    main(FRONT, OUT, MANUAL_PX, CASE_MM, LISTED, ARTEFACTS, HANDS_PX)
