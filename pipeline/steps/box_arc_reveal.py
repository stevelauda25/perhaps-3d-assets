"""box_arc_reveal: build the 07 Arc Reveal cube box in an empty scene.

Params: spec (config/presets/box_arc_reveal.json, millimetres). Scene units are metres, all transforms identity.
`CTRL | Base` holds `Box | Base`, `Box | Insert`, `Box | Cushion`; `CTRL | Lid lift-off` holds `Box | Lid`
(the canonical control names, so floating_stage / cinematic_studio / box_lift work unchanged).
Meshes carry `export_product` for watch_export_glb. Fails if a mesh is not watertight, the closed parts overlap or an arch panel misses the accent.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MM = 0.001


def run(params):
    import bmesh
    import bpy
    from mathutils import Matrix
    from mathutils.bvhtree import BVHTree

    spec = json.loads((ROOT / params["spec"]).read_text())
    g = spec["geometry_mm"]
    scene = bpy.context.scene
    a = g["size"] / 2                                   # outer half size
    s = a - g["lid_wall"] - g["fit_clearance"]          # base sleeve half size (lid slides over it)
    c = s - g["base_wall"]                              # compartment half size
    p, r, n = g["plinth_height"], g["arch_radius"], g["arch_segments"]
    gap = g["seat_gap"]  # resting parts sit this far apart so the closed assembly has no touching faces

    def link(name, bm):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        scene.collection.objects.link(o)
        return o

    def cuboid(name, hx, hy, z0, z1):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            v.co = (v.co.x * 2 * hx * MM, v.co.y * 2 * hy * MM, ((z0 + z1) / 2 + v.co.z * (z1 - z0)) * MM)
        return link(name, bm)

    def arch(name, radius, y0, y1, turns, drop):
        """Closed prism: half disc of `radius` on the spring line z=p (XZ plane), squared off `drop` mm below it, y0..y1, turned k x 90 deg."""
        bm = bmesh.new()
        ring = [(radius * math.cos(math.pi * i / n), p + radius * math.sin(math.pi * i / n)) for i in range(n + 1)]
        ring += [(-radius, p - drop), (radius, p - drop)]
        front = [bm.verts.new((x * MM, y0 * MM, z * MM)) for x, z in ring]
        back = [bm.verts.new((x * MM, y1 * MM, z * MM)) for x, z in ring]
        bm.faces.new(front)
        bm.faces.new(back[::-1])
        for i in range(len(ring)):
            j = (i + 1) % len(ring)
            bm.faces.new((front[i], front[j], back[j], back[i]))
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(turns * math.pi / 2, 3, "Z"), verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return link(name, bm)

    def bake(o, mod):
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        old, o.data = o.data, me
        o.modifiers.remove(mod)
        bpy.data.meshes.remove(old)

    def bevel(o, width, segments):
        m = o.modifiers.new("Edge radius", "BEVEL")
        m.width, m.segments, m.limit_method, m.use_clamp_overlap = width * MM, segments, "ANGLE", True
        bake(o, m)

    def boolean(o, cutter, op):
        m = o.modifiers.new("Arch", "BOOLEAN")
        m.operation, m.solver, m.object = op, "EXACT", cutter
        bake(o, m)
        bpy.data.meshes.remove(cutter.data)

    # lid: bevelled shell, open at the bottom, one arch cut through each side
    lid = cuboid("Box | Lid", a, a, p + gap, g["size"])
    bevel(lid, g["edge_radius"], g["edge_segments"])
    boolean(lid, cuboid("cut", a - g["lid_wall"], a - g["lid_wall"], p - 1, g["size"] - g["lid_top"]), "DIFFERENCE")
    boolean(lid, arch("cut", r, -a - 5, a + 5, 0, 5), "DIFFERENCE")
    boolean(lid, arch("cut", r, -a - 5, a + 5, 1, 5), "DIFFERENCE")

    # base: bevelled plinth + sleeve + four arch panels flush with the lid face, then the compartment
    base = cuboid("Box | Base", a, a, 0, p)
    bevel(base, g["edge_radius"], g["edge_segments"])
    boolean(base, cuboid("add", s, s, 0, g["base_height"]), "UNION")
    for k in range(4):
        boolean(base, arch("add", r - g["arch_gap"], s - 0.5, a, k, 0.5), "UNION")
    boolean(base, cuboid("cut", c, c, g["base_floor"], g["base_height"] + 1), "DIFFERENCE")
    bm = bmesh.new()  # the union merges each flush panel face into the plinth face; split them again at the spring line
    bm.from_mesh(base.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, p * MM), plane_no=(0, 0, 1))
    bm.to_mesh(base.data)
    bm.free()

    # insert tray with a trough, and a soft cushion resting in it
    ins, top = c - g["insert_clearance"], g["base_floor"] + g["insert_height"]
    cl, cw, ch = g["cushion"]
    insert = cuboid("Box | Insert", ins, ins, g["base_floor"] + gap, top)
    boolean(insert, cuboid("cut", cl / 2 + 1, cw / 2 + 1, top - g["trough_depth"], top + 1), "DIFFERENCE")
    floor = top - g["trough_depth"]
    cushion = cuboid("Box | Cushion", cl / 2, cw / 2, floor + gap, floor + gap + ch)
    bevel(cushion, g["cushion_radius"], g["cushion_segments"])

    # metric UVs (1 unit = 1 m, dominant-axis projection) for later texture work at true scale
    for o in (lid, base, insert, cushion):
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
        wn = o.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")  # flat faces stay flat next to smooth bevels
        wn.mode, wn.keep_sharp = "FACE_AREA", True
        bake(o, wn)

    # materials: glTF-safe colour + grain (normal/roughness maps on Metric UV); renders swap in library leather with packaging_tier
    ms = spec["materials"]
    grain = ms["grain"]
    maps = {}
    for channel in ("normal", "roughness"):
        im = bpy.data.images.load(str(ROOT / grain["dir"] / grain[channel]))
        im.colorspace_settings.name = "Non-Color"
        im.scale(grain["px"], grain["px"])  # GLB size: 2K source maps would add ~11 MB
        im.file_format = "JPEG"
        im.pack()
        maps[channel] = im
    mats = {}
    for role in ("exterior", "accent"):
        mat = mats[role] = bpy.data.materials.new("Arc Reveal | " + role)
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
    # accent = compartment lining, insert, cushion and the four base arch panels (outer face and the curved edge in the gap)
    inner = {lid: lambda q: abs(q.x) < (a - g["lid_wall"] + 0.01) * MM and abs(q.y) < (a - g["lid_wall"] + 0.01) * MM
             and q.z < (g["size"] - g["lid_top"] + 0.01) * MM,
             base: lambda q: (abs(q.x) < (c + 0.01) * MM and abs(q.y) < (c + 0.01) * MM and q.z > (g["base_floor"] - 0.01) * MM)
             or panel(q)}

    def panel(q):
        u, w = (q.x, abs(q.y)) if abs(q.y) >= abs(q.x) else (q.y, abs(q.x))
        return (w > (s - 0.51) * MM and q.z > (p - 0.01) * MM
                and math.hypot(u, q.z - p * MM) < (r - g["arch_gap"] + 0.01) * MM)
    for o in (lid, base, insert, cushion):
        o.data.materials.clear()  # boolean bakes leave an empty first slot that would shift every index
        o.data.materials.append(mats["exterior"])
        o.data.materials.append(mats["accent"])
        for f in o.data.polygons:
            f.material_index = 1 if o not in inner or all(inner[o](o.data.vertices[i].co) for i in f.vertices) else 0
    accent_panel_faces = sum(all(panel(base.data.vertices[i].co) for i in f.vertices) for f in base.data.polygons)
    assert all(len(o.data.materials) == 2 for o in (lid, base, insert, cushion)), "unexpected material slots"
    assert accent_panel_faces >= 4 * (n + 1), "arch panel faces not all found (%d)" % accent_panel_faces  # n curved + 1 outer per side

    # controls (canonical names) and export tags
    ctrl = {}
    for name in ("CTRL | Base", "CTRL | Lid lift-off"):
        ctrl[name] = bpy.data.objects.new(name, None)
        scene.collection.objects.link(ctrl[name])
    for o in (lid, base, insert, cushion):
        o.parent = ctrl["CTRL | Lid lift-off" if o is lid else "CTRL | Base"]
        o["export_product"] = True
    # GLB open/close: the lid mesh rises lift_mm over `frames`; frame 1 stays closed for every render
    lift = spec["lid_animation"]
    for frame, z in ((1, 0.0), (lift["frames"], lift["lift_mm"] * MM)):
        lid.location.z = z
        lid.keyframe_insert("location", index=2, frame=frame)
    lid.animation_data.action.name = "Lid lift"
    scene.frame_set(1)

    # house scene: black world, Standard view
    world = scene.world or bpy.data.worlds.new("World")
    scene.world, world.use_nodes = world, True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0, 0, 0, 1), 0
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = spec["scene"]["view_transform"]
    scene.view_settings.exposure = spec["scene"]["exposure"]

    # self-check: every part watertight, closed parts do not intersect
    trees, summary = {}, {}
    for o in (lid, base, insert, cushion):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_edges = sum(not e.is_manifold for e in bm.edges)
        assert open_edges == 0, "%s has %d non-manifold edges" % (o.name, open_edges)
        trees[o.name] = BVHTree.FromBMesh(bm)
        summary[o.name] = {"faces": len(bm.faces), "dims_mm": [round(d / MM, 2) for d in o.dimensions]}
        bm.free()
    names = list(trees)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            hits = trees[x].overlap(trees[y])
            assert not hits, "%s intersects %s (%d triangle pairs)" % (x, y, len(hits))
    return {"parts": summary, "accent_panel_faces": accent_panel_faces}
