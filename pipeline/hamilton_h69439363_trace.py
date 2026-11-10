"""Measure the Hamilton H69439363 (Khaki Field Mechanical 38 mm, green dial) official front render (2100 x 2054, composited on
white) into mm. Host-side, no Blender.

    python3 -B -m pipeline.hamilton_h69439363_trace [out.json] [overlay.png]   # default config/watches/hamilton-h69439363-trace.json

Same method and trace() as pipeline/hamilton_h69439940_trace.py. Anchor: case diameter 38.0 mm (Hamilton official) on the 9-3
row; strap width (20 mm) and lug to lug (47 mm, Hamilton official) are checks. mm, x right, y toward 12, origin = the hand
pivot. Hands (polished pencil hour and minute with lume, polished seconds with a round counterweight and a lume-filled arrow),
date frame, crown and bezel radii come from gridded crops and hand strips resampled along each axis.
"""
from pipeline.hamilton_h69439940_trace import ROOT, circle, main, profile

FRONT = ROOT / "references/hamilton-h69439363/front_white_2100x2054.png"
OUT = ROOT / "config/watches/hamilton-h69439363-trace.json"
CASE_MM = 38.0  # Hamilton official
LISTED = {"lug_to_lug_mm": 47.0, "strap_width_mm": 20.0, "thickness_mm": 9.5}  # Hamilton official

HANDS_PX = {
    "hour": {"angle_deg": 304.3, "z": "hour", "parts": [
        {"mat": "hand", "layer": 0, "poly": profile([[-6, 14.5], [40, 14.6], [45, 16], [100, 17.3], [150, 19.1], [158, 18.5], [175, 9], [190, 3], [196, 0]])},
        {"mat": "lume_hands", "layer": 1, "poly": profile([[44, 12], [100, 13.3], [150, 15], [158, 14], [170, 6], [176, 1], [177, 0]])}]},
    "minute": {"angle_deg": 54.5, "z": "minute", "parts": [
        {"mat": "hand", "layer": 0, "poly": profile([[-6, 12], [50, 11], [100, 11.5], [200, 13], [250, 12.5], [262, 6], [268, 3], [270, 0]])},
        {"mat": "hand", "layer": 0, "poly": [(-2.0, 262), (2.0, 262), (1.2, 300), (-1.2, 300)]},  # short needle point
        {"mat": "lume_hands", "layer": 1, "poly": profile([[45, 6.5], [100, 7.3], [200, 9], [250, 8.5], [258, 4], [262, 0]])}]},
    "seconds": {"angle_deg": 222.4, "z": "seconds", "parts": [
        {"mat": "hand", "layer": 0, "poly": [(-2.5, -129), (2.5, -129), (2.5, 252), (-2.5, 252)]},
        {"mat": "hand", "layer": 0, "poly": circle(-129, 21.0, 40)},  # round counterweight
        {"mat": "hand", "layer": 0, "poly": [(-11.25, 250), (11.25, 250), (0, 307.5)]},  # arrow
        {"mat": "lume_hands", "layer": 1, "poly": [(-7.5, 255), (7.5, 255), (0, 299)]}]},
}

MANUAL_PX = {
    "hand_pivot": [1050.0, 954.9],
    "case_x": [601.0, 1499.0],  # case edge on the 9-3 row; right edge mirrored about the pivot (the crown root hides it)
    "case_step_r": 431,  # ridge between the bead-blasted flank and the sloped bezel
    "bezel_inner_r": 386,  # sloped blasted bezel meets the crystal
    "rehaut_r": 355,  # flat dial edge; grey crystal edge rings between (kept in the dial map)
    "hub_radius_px": [26.6, 12],
    "crown_x": [1496, 1600],
    "crown_cap_x": 1574,
    "crown_radius_px": 77,
    "crown_teeth": 24,
    "date_window": [1246, 918, 1342, 997],  # applied white frame, outer edge
    "date_frame_px": 3.0,
    "lug_inner_x_mm": 10.0,  # 20 mm strap (official lug width)
    "lug_tips_y": [420, 1494],  # rounded lug ends meet the strap
    "lug_depth_mm": 14.0,
}
ARTEFACTS = ["official front render; the render's lug to lug reads 45.4 mm (lug ends drawn rounded and short); the official 47 mm is used",
             "the strap's steel keeper band shows between the strap and the case at both ends; the strap map starts past the lug tips",
             "numerals, minute track, triangles, logo and prints stay in the photo map; the date frame is modelled"]


if __name__ == "__main__":
    main(FRONT, OUT, MANUAL_PX, CASE_MM, LISTED, ARTEFACTS, HANDS_PX)
