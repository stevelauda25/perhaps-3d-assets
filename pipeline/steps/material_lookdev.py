"""Apply a library material to the lookdev samples and select a light set.

Params: {"material": "<library id>", "lighting": "neutral" | "grazing", "overrides": {...optional preset overrides}}.
Same material twice in a row only toggles lighting (cheap); a different id replaces the sample material.
"""


def run(params):
    import bpy
    from pipeline import material_library, pbr_material
    mat = bpy.data.materials.get("LOOKDEV | " + params["material"])
    if mat is None or params.get("overrides"):
        mat = pbr_material.build(material_library.load(params["material"]), params.get("overrides"),
                                 name="LOOKDEV | " + params["material"])
    for o in bpy.data.objects:
        if o.name.startswith("SAMPLE |"):
            o.material_slots[0].material = mat
        if o.name.startswith("LIGHT "):
            o.hide_render = not o.name.startswith("LIGHT " + params["lighting"])
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    return {"material": params["material"], "lighting": params["lighting"]}
