"""box_lift: raise `CTRL | Lid lift-off` by lift_mm for an open-lid view. Nothing else changes.

Params: lift_mm.
"""


def run(params):
    import bpy
    lid = bpy.data.objects["CTRL | Lid lift-off"]
    lid.location.z += params["lift_mm"] / 1000
    return {"lid_z_m": round(lid.location.z, 4)}
