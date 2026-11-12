"""glb_bake_look: export the GLB with glTF-safe bakes of render materials from another .blend (e.g. the Select look).

Params: source (.blend), materials {build slot material: source material}, tile_mm, px, uv (metric UV map on the parts), glb.
Each source material is baked once on a flat tile (base colour, roughness, tangent normal) the way it shades object space,
rebuilt as image textures on `uv` repeating every tile_mm, swapped onto the export_product slots for the export, then
swapped back so later look stages still find the build materials. Run it right after the build (closed, unposed box).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(params):
    import bpy
    from pipeline.steps import watch_export_glb
    scene = bpy.context.scene
    px, t = params["px"], params["tile_mm"] / 1000
    names = sorted(set(params["materials"].values()))
    with bpy.data.libraries.load(str(ROOT / params["source"]), link=False) as (have, want):
        missing = set(names) - set(have.materials)
        assert not missing, "source has no material %s" % sorted(missing)
        want.materials = list(names)
    src = dict(zip(names, want.materials))

    engine, samples = scene.render.engine, scene.cycles.samples
    scene.render.engine, scene.cycles.samples = "CYCLES", 4
    built = {}
    for name, mat in src.items():
        me = bpy.data.meshes.new("bake tile")
        me.from_pydata([(0, 0, 0), (t, 0, 0), (t, t, 0), (0, t, 0)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new(name="bake")
        for loop, co in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop.uv = co
        tile = bpy.data.objects.new("bake tile", me)
        scene.collection.objects.link(tile)
        me.materials.append(mat)
        target = mat.node_tree.nodes.new("ShaderNodeTexImage")
        mat.node_tree.nodes.active = target
        bpy.ops.object.select_all(action="DESELECT")
        tile.select_set(True)
        bpy.context.view_layer.objects.active = tile
        maps = {}
        for kind, bake, colorspace in (("color", "DIFFUSE", "sRGB"), ("roughness", "ROUGHNESS", "Non-Color"), ("normal", "NORMAL", "Non-Color")):
            im = maps[kind] = bpy.data.images.new("%s | glb %s" % (name, kind), px, px)
            im.colorspace_settings.name = colorspace
            target.image = im
            bpy.ops.object.bake(type=bake, pass_filter={"COLOR"}, normal_space="TANGENT", margin=0, use_clear=True)
            im.file_format = "PNG" if kind == "normal" else "JPEG"
            im.pack()
        bpy.data.objects.remove(tile)
        bpy.data.meshes.remove(me)

        out = built[name] = bpy.data.materials.new(name + " | glb")
        out.use_nodes = True
        nodes, links = out.node_tree.nodes, out.node_tree.links
        bsdf = nodes["Principled BSDF"]
        uvn = nodes.new("ShaderNodeUVMap")
        uvn.uv_map = params["uv"]
        mp = nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1 / t,) * 3
        links.new(uvn.outputs["UV"], mp.inputs["Vector"])
        tex = {}
        for kind, im in maps.items():
            tex[kind] = nodes.new("ShaderNodeTexImage")
            tex[kind].image = im
            links.new(mp.outputs["Vector"], tex[kind].inputs["Vector"])
        nm = nodes.new("ShaderNodeNormalMap")
        links.new(tex["color"].outputs["Color"], bsdf.inputs["Base Color"])
        links.new(tex["roughness"].outputs["Color"], bsdf.inputs["Roughness"])
        links.new(tex["normal"].outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    scene.render.engine, scene.cycles.samples = engine, samples

    slots = [s for o in scene.objects if o.get("export_product") for s in o.material_slots
             if s.material and s.material.name in params["materials"]]
    assert slots, "no export_product slot uses %s" % sorted(params["materials"])
    keep = [s.material for s in slots]
    for s in slots:
        s.material = built[params["materials"][s.material.name]]
    result = watch_export_glb.run({"glb": params["glb"]})
    for s, m in zip(slots, keep):
        s.material = m
    return {**result, "slots_baked": len(slots)}
