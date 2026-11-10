"""Measure the Hamilton H70455733 (Khaki Field Auto 38 mm, black dial) official front render (2100 x 2054, composited on white)
into mm. Host-side, no Blender.

    python3 -B -m pipeline.hamilton_h70455733_trace [out.json] [overlay.png]   # default config/watches/hamilton-h70455733-trace.json

Same method and trace() as pipeline/hamilton_h69439940_trace.py. Anchor: case diameter 38.0 mm (Hamilton official) on the 9-3
row; strap width (20 mm) and lug to lug (47 mm, Hamilton official) are checks. mm, x right, y toward 12, origin = the hand
pivot. Hands (polished pencil hour and minute with lume and thin needle points, white seconds with a small counterweight
disc and a red arrow tip), date frame, crown and bezel radii come from gridded crops.
"""
from pipeline.hamilton_h69439940_trace import ROOT, circle, main, profile

FRONT = ROOT / "references/hamilton-h70455733/front_white_2100x2054.png"
OUT = ROOT / "config/watches/hamilton-h70455733-trace.json"
CASE_MM = 38.0  # Hamilton official
LISTED = {"lug_to_lug_mm": 47.0, "strap_width_mm": 20.0, "thickness_mm": 11.0}  # Hamilton official

HANDS_PX = {  # half widths read from the hand strips resampled along each axis (straightened crops)
    "hour": {"angle_deg": 305.6, "z": "hour", "parts": [
        {"mat": "hand", "layer": 0, "poly": profile([[-6, 11], [42, 11], [46, 15.5], [100, 17.3], [150, 19.8], [163, 19.5], [180, 10], [195, 2], [197, 0]])},
        {"mat": "hand", "layer": 0, "poly": [(-2.5, 190), (2.5, 190), (1.5, 245), (-1.5, 245)]},  # thin point past the 10
        {"mat": "lume_hands", "layer": 1, "poly": profile([[48, 13], [100, 13.1], [150, 14.4], [160, 14], [175, 7], [190, 1], [192, 0]])}]},
    "minute": {"angle_deg": 50.2, "z": "minute", "parts": [
        {"mat": "hand", "layer": 0, "poly": profile([[-6, 12], [40, 12], [100, 13.5], [210, 15.5], [240, 13.5], [250, 8], [257, 2], [259, 0]])},
        {"mat": "hand", "layer": 0, "poly": [(-2.5, 252), (2.5, 252), (1.5, 345), (-1.5, 345)]},  # needle point to the track
        {"mat": "lume_hands", "layer": 1, "poly": profile([[50, 7.5], [100, 8.5], [200, 10.6], [230, 10.5], [242, 6], [248, 1], [249, 0]])}]},
    "seconds": {"angle_deg": 223.2, "z": "seconds", "parts": [
        {"mat": "hand_white", "layer": 0, "poly": [(-2.6, -127), (2.6, -127), (2.4, 290), (-2.4, 290)]},
        {"mat": "hand_white", "layer": 0, "poly": circle(-127, 10.0, 24)},  # small counterweight disc
        {"mat": "seconds_red", "layer": 1, "poly": [(-10.5, 286), (10.5, 286), (0, 339)]}]},  # red arrow tip
}

MANUAL_PX = {
    "hand_pivot": [1050.9, 1013.4],
    "case_x": [599.0, 1502.8],  # case edge on the 9-3 row; right edge mirrored about the pivot (the crown root hides it)
    "case_step_r": 439,  # narrow brushed flank top, then the wide polished bezel slope
    "bezel_inner_r": 401,  # polished bezel ends at the crystal
    "rehaut_r": 360,  # flat dial edge; grey chapter ring with dots up to the crystal (kept in the dial map)
    "hub_radius_px": [25.7, 10],
    "crown_x": [1502, 1600],
    "crown_cap_x": 1580,
    "crown_radius_px": 69.5,
    "crown_teeth": 22,
    "date_window": [1250, 971, 1348, 1051],  # applied white frame, outer edge
    "date_frame_px": 3.6,
    "lug_inner_x_mm": 10.0,  # 20 mm strap (official lug width)
    "lug_tips_y": [452, 1577],  # rounded lug ends meet the strap
    "lug_depth_mm": 14.0,
}
ARTEFACTS = ["official front render: the top lugs and the strap are not perspective-shifted; the reflection under the bottom "
             "strap is not traced",
             "the strap's tan underside shows between the strap and the case at both ends; the strap map starts past the lug tips",
             "numerals, minute track with dots, 24-hour ring, logo and prints stay in the photo map; the date frame is modelled"]


if __name__ == "__main__":
    main(FRONT, OUT, MANUAL_PX, CASE_MM, LISTED, ARTEFACTS, HANDS_PX)
