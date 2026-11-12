"""box_wave: build the 09 Wave cube box in an empty scene.

Params: spec (config/presets/box_wave.json, millimetres). Scene units are metres, all transforms identity.
The lid / base seam follows the preset's measured seam_profile along every face (side corner to front / back corner). The lid ends `reveal`/2 above that wave,
the base `reveal`/2 below it, and a collar inside the base (set back by the lid wall) rises `collar_rise` above it,
filling the reveal when closed. `CTRL | Base` holds `Box | Base` and `Box | Collar`; `CTRL | Lid lift-off` holds `Box | Lid`.
Meshes carry `export_product` for watch_export_glb. Fails if a mesh is not watertight or the parts intersect, closed or lifted.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MM = 0.001


def run(params):
    import bmesh
    import bpy
    from mathutils.bvhtree import BVHTree

    spec = json.loads((ROOT / params["spec"]).read_text())
    g = spec["geometry_mm"]
    scene = bpy.context.scene
    size, a, w, gap = g["size"], g["size"] / 2, g["wall"], g["seat_gap"]
    ci = a - w - g["fit_clearance"]  # collar outer half size: clears the lid inside and the base inside

    prof = g["seam_profile"]  # mm above seam_low_z at s = 0, 1/n ... 1 (side corner to front / back corner)
    n = len(prof) - 1

    def profile(s):
        """Catmull-Rom through the table; mirrored at s = 0 so the side corners stay level."""
        k = min(int(s * n), n - 1)
        t = s * n - k
        p = [prof[abs(k - 1)], prof[k], prof[k + 1], prof[k + 2] if k + 2 <= n else 2 * prof[n] - prof[n - 1]]
        return 0.5 * (2 * p[1] + (p[2] - p[0]) * t + (2 * p[0] - 5 * p[1] + 4 * p[2] - p[3]) * t * t + (3 * p[1] - p[0] - 3 * p[2] + p[3]) * t ** 3)
    assert abs(profile(0) - prof[0]) < 1e-9 and abs(profile(1) - prof[n]) < 1e-9 and abs(profile(0.5) - prof[n // 2]) < 1e-9

    def seam(x, y):
        x, y = max(-a, min(a, x)), max(-a, min(a, y))  # flat beyond the walls
        q = -math.sin(math.pi * x / size) * math.sin(math.pi * y / size)  # 1 at the side corners, -1 front / back
        return g["seam_low_z"] + profile(math.acos(max(-1.0, min(1.0, q))) / math.pi)

    def link(name, bm):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        scene.collection.objects.link(o)
        return o

    def cuboid(name, h, z0, z1):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            v.co = (v.co.x * 2 * h * MM, v.co.y * 2 * h * MM, ((z0 + z1) / 2 + v.co.z * (z1 - z0)) * MM)
        return link(name, bm)

    def field(name, offset, below):
        """Closed solid between the wave surface (seam + offset) and z = -1 (below) or size + 1 (above)."""
        n = int(math.ceil((2 * a + 6) / g["field_step"]))
        ts = [-a - 3 + i * (2 * a + 6) / n for i in range(n + 1)]
        cap = -1 if below else size + 1
        bm = bmesh.new()
        top = [[bm.verts.new((x * MM, y * MM, (seam(x, y) + offset) * MM)) for y in ts] for x in ts]
        bot = [[bm.verts.new((x * MM, y * MM, cap * MM)) for y in ts] for x in ts]
        for i in range(n):
            for j in range(n):
                bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
                bm.faces.new((bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j], bot[i][j]))
        ring = [(i, 0) for i in range(n)] + [(n, j) for j in range(n)] + [(i, n) for i in range(n, 0, -1)] + [(0, j) for j in range(n, 0, -1)]
        for k, (i, j) in enumerate(ring):
            i2, j2 = ring[(k + 1) % len(ring)]
            bm.faces.new((top[i][j], bot[i][j], bot[i2][j2], top[i2][j2]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return link(name, bm)

    def bake(o, mod):
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        old, o.data = o.data, me
        o.modifiers.remove(mod)
        bpy.data.meshes.remove(old)

    def bevel(o):
        m = o.modifiers.new("Edge radius", "BEVEL")
        m.width, m.segments, m.limit_method, m.use_clamp_overlap = g["edge_radius"] * MM, g["edge_segments"], "ANGLE", True
        bake(o, m)

    def boolean(o, cutter, op):
        m = o.modifiers.new("Cut", "BOOLEAN")
        m.operation, m.solver, m.object = op, "EXACT", cutter
        bake(o, m)
        bpy.data.meshes.remove(cutter.data)

    half = g["reveal"] / 2
    # wave cut, then edge radius (outer cube and wave edges alike), then the cavity: a bevel after the cavity would
    # fillet the inside floor corner into the collar
    lid = cuboid("Box | Lid", a, 0, size)
    boolean(lid, field("cut", half, False), "INTERSECT")
    bevel(lid)
    boolean(lid, cuboid("cut", a - w, -1, size - g["lid_top"]), "DIFFERENCE")
    base = cuboid("Box | Base", a, 0, size)
    boolean(base, field("cut", -half, True), "INTERSECT")
    bevel(base)
    boolean(base, cuboid("cut", a - w, g["base_floor"], size + 1), "DIFFERENCE")
    z0 = g["base_floor"] + gap
    collar = cuboid("Box | Collar", ci, z0, size - g["lid_top"] - 1)
    boolean(collar, cuboid("cut", ci - g["collar_wall"], z0 + g["collar_floor"], size + 1), "DIFFERENCE")
    boolean(collar, field("cut", g["collar_rise"], True), "INTERSECT")
    parts = [lid, base, collar]

    # metric UVs (1 unit = 1 m, dominant-axis projection), smooth bevels with flat faces
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        uv = bm.loops.layers.uv.new("Metric UV")
        for f in bm.faces:
            axis = max(range(3), key=lambda i: abs(f.normal[i]))
            u, v = [i for i in range(3) if i != axis]
            for loop in f.loops:
                loop[uv].uv = (loop.vert.co[u], loop.vert.co[v])
        bm.to_mesh(o.data)
        bm.free()
        o.data.shade_smooth()
        o.data.set_sharp_from_angle(angle=math.radians(30))
        wn = o.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
        wn.mode, wn.keep_sharp = "FACE_AREA", True
        bake(o, wn)

    # placeholder materials (glTF-safe colour + paper grain); the job swaps in the Select look
    ms = spec["materials"]
    grain = ms["grain"]
    maps = {}
    for channel in ("normal", "roughness"):
        im = bpy.data.images.load(str(ROOT / grain["dir"] / grain[channel]))
        im.colorspace_settings.name = "Non-Color"
        im.scale(grain["px"], grain["px"])
        im.file_format = "JPEG"
        im.pack()
        maps[channel] = im
    mats = {}
    for role in ("exterior", "accent"):
        mat = mats[role] = bpy.data.materials.new("Wave | " + role)
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*ms[role]["color_linear"], 1)
        uvn = nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "Metric UV"
        mp = nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1000 / grain["tile_mm"],) * 3
        links.new(uvn.outputs["UV"], mp.inputs["Vector"])
        tex = {}
        for channel, im in maps.items():
            tex[channel] = nodes.new("ShaderNodeTexImage")
            tex[channel].image = im
            links.new(mp.outputs["Vector"], tex[channel].inputs["Vector"])
        nm = nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = grain["normal_strength"]
        links.new(tex["normal"].outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        links.new(tex["roughness"].outputs["Color"], bsdf.inputs["Roughness"])
    # accent = the whole collar and every face inside the lid or base cavity; outer faces and wave rims stay exterior
    t = 0.01
    inside = {lid: lambda q: abs(q.x) < (a - w + t) * MM and abs(q.y) < (a - w + t) * MM and q.z < (size - g["lid_top"] + t) * MM,
              base: lambda q: abs(q.x) < (a - w + t) * MM and abs(q.y) < (a - w + t) * MM and q.z > (g["base_floor"] - t) * MM,
              collar: lambda q: True}
    for o in parts:
        o.data.materials.clear()  # boolean bakes leave an empty first slot that would shift every index
        o.data.materials.append(mats["exterior"])
        o.data.materials.append(mats["accent"])
        for f in o.data.polygons:
            f.material_index = 1 if all(inside[o](o.data.vertices[i].co) for i in f.vertices) else 0
    white = {o.name: sum(f.material_index for f in o.data.polygons) for o in parts}
    assert all(white.values()), "a part has no accent faces: %s" % white

    # controls (canonical names) and export tags; GLB open/close: the lid rises lift_mm over `frames`, frame 1 closed
    ctrl = {}
    for name in ("CTRL | Base", "CTRL | Lid lift-off"):
        ctrl[name] = bpy.data.objects.new(name, None)
        scene.collection.objects.link(ctrl[name])
    for o in parts:
        o.parent = ctrl["CTRL | Lid lift-off" if o is lid else "CTRL | Base"]
        o["export_product"] = True
    lift = spec["lid_animation"]
    for frame, z in ((1, 0.0), (lift["frames"], lift["lift_mm"] * MM)):
        lid.location.z = z
        lid.keyframe_insert("location", index=2, frame=frame)
    lid.animation_data.action.name = "Lid lift"
    scene.frame_start, scene.frame_end = 1, lift["frames"]

    # house scene: black world, Standard view
    world = scene.world or bpy.data.worlds.new("World")
    scene.world, world.use_nodes = world, True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0, 0, 0, 1), 0
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = spec["scene"]["view_transform"]
    scene.view_settings.exposure = spec["scene"]["exposure"]

    # self-check: every part watertight; no two parts intersect anywhere along the lift
    summary = {}
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_edges = sum(not e.is_manifold for e in bm.edges)
        assert open_edges == 0, "%s has %d non-manifold edges" % (o.name, open_edges)
        summary[o.name] = {"faces": len(bm.faces), "dims_mm": [round(d / MM, 2) for d in o.dimensions]}
        bm.free()
    for frame in [*range(1, lift["frames"], 3), lift["frames"]]:
        scene.frame_set(frame)
        trees = {}
        for o in parts:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.transform(o.matrix_world)
            trees[o.name] = BVHTree.FromBMesh(bm)
            bm.free()
        names = list(trees)
        for i, x in enumerate(names):
            for y in names[i + 1:]:
                hits = trees[x].overlap(trees[y])
                assert not hits, "frame %d: %s intersects %s (%d triangle pairs)" % (frame, x, y, len(hits))
    scene.frame_set(1)
    return {"parts": summary, "accent_faces": white}
