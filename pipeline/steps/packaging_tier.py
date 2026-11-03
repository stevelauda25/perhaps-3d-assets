"""Apply a tier material preset (config/tiers/<tier>.json) and its studio card layout to a packaging scene.

Params: {"preset": "config/tiers/essential.json", "exposure_ev": optional float}.
Materials are swapped per slot; geometry, UVs, bevels and cameras are untouched. The preset's
`studio.lights` go through the same reference_studio.refine used by packaging_look.
"""


def run(params):
    import bpy
    from pipeline import reference_studio, tier_materials
    summary = tier_materials.apply(params["preset"])
    lights = tier_materials.load_preset(params["preset"]).get("studio", {}).get("lights")
    if lights:
        summary["cards"] = sorted(reference_studio.refine({"lights": lights}))
    if "exposure_ev" in params:
        bpy.context.scene.view_settings.exposure = params["exposure_ev"]
    # Drop images only the replaced materials used (new scene only; sources untouched).
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    summary["images_left"] = sorted(i.name for i in bpy.data.images if i.name != "Render Result")
    return summary
