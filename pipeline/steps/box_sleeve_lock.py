"""box_sleeve_lock: build the 10 Signature Sleeve Lock cube box in an empty scene.

Params: spec (config/presets/box_sleeve_lock.json, millimetres). Scene units are metres.
Lid group (lifts straight up): `Box | Lid`, `Box | Skirt`, `Box | Bead lid`, `Box | Strap lid`, `Box | Clasp`, `Box | Wordmark`, all
carrying the `Lid lift` action. Base group: `Box | Base`, `Box | Bead base`, `Box | Strap base`, `Box | Collar`, `Box | Pad`.
`CTRL | Base` / `CTRL | Lid lift-off` hold the groups (names floating_stage expects).
Fails if a mesh is not watertight (the wordmark excepted: a filled curve) or the lid group meets the base group anywhere
along the lift.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MM = 0.001


def run(params):
    import bmesh
    import bpy
    from mathutils import Matrix, Vector
    from mathutils.bvhtree import BVHTree
    from pipeline.steps.logo_deboss import parse_svg

    spec = json.loads((ROOT / params["spec"]).read_text())
    g = spec["geometry_mm"]
    scene = bpy.context.scene
    size, a, w = g["size"], g["size"] / 2, g["wall"]
    half, st, sw = g["reveal"] / 2, g["strap_thickness"], g["strap_width"] / 2
    hi, lo = g["seam_side_z"], g["seam_low_z"]

    def seam(x, y):
        """Level at seam_side_z; across the front wall a V down to seam_low_z at x = 0, meeting the level at the inside
        of the side walls. Inside the cavity the V eases back to level so the cut surface has no step."""
        v = lo + (hi - lo) * min(abs(x) / (a - w), 1.0)
        return hi - (hi - v) * max(0.0, min(1.0, -y / (a - w)))

    def link(name, bm):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        scene.collection.objects.link(o)
        return o

    def block(name, x0, x1, y0, y1, z0, z1):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            v.co = (((x0 + x1) / 2 + v.co.x * (x1 - x0)) * MM, ((y0 + y1) / 2 + v.co.y * (y1 - y0)) * MM,
                    ((z0 + z1) / 2 + v.co.z * (z1 - z0)) * MM)
        return link(name, bm)

    def field(offset, below):
        """Closed solid between the seam surface (+ offset) and z = -5 (below) or size + 5 (above)."""
        L = a + 8
        n = int(math.ceil(2 * L / g["field_step"]))
        ts = [-L + i * 2 * L / n for i in range(n + 1)]
        cap = -5 if below else size + 5
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
        return link("cut", bm)

    def bake(o, mod):
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        old, o.data = o.data, me
        o.modifiers.remove(mod)
        bpy.data.meshes.remove(old)

    def bevel(o, width=None, segments=None):
        m = o.modifiers.new("Edge radius", "BEVEL")
        m.width, m.segments = (width or g["edge_radius"]) * MM, segments or g["edge_segments"]
        m.limit_method, m.use_clamp_overlap = "ANGLE", True
        bake(o, m)

    def boolean(o, cutter, op):
        m = o.modifiers.new("Cut", "BOOLEAN")
        m.operation, m.solver, m.object = op, "EXACT", cutter
        bake(o, m)
        bpy.data.meshes.remove(cutter.data)

    # shells: cut along the seam (lid above the reveal, base below it), edges rounded, then the cavities
    lid = block("Box | Lid", -a, a, -a, a, 0, size)
    boolean(lid, field(half, False), "INTERSECT")
    bevel(lid)
    boolean(lid, block("cut", -a + w, a - w, -a + w, a - w, -5, size - g["lid_top"]), "DIFFERENCE")
    base = block("Box | Base", -a, a, -a, a, 0, size)
    boolean(base, field(-half, True), "INTERSECT")
    bevel(base)
    boolean(base, block("cut", -a + w, a - w, -a + w, a - w, g["base_floor"], size + 5), "DIFFERENCE")

    # collar: thick velvet sleeve inside the base, rising collar_rise above the seam into the lid; rounded top
    ci, cw = a - w - g["collar_clearance"], g["collar_wall"]
    collar = block("Box | Collar", -ci, ci, -ci, ci, g["base_floor"] + 0.05, size)
    boolean(collar, field(g["collar_rise"], True), "INTERSECT")
    bevel(collar, g["collar_radius"], 4)
    boolean(collar, block("cut", -ci + cw, ci - cw, -ci + cw, ci - cw, g["base_floor"] + 1, size + 5), "DIFFERENCE")

    # lid lining skirt: velvet sleeve inside the lid wall that hangs through the reveal to just above the base rim
    so, si = g["skirt"][1], g["skirt"][0]
    skirt = block("Box | Skirt", -so, so, -so, so, -5, size)
    boolean(skirt, block("cut", -si, si, -si, si, -10, size + 10), "DIFFERENCE")
    boolean(skirt, field(-half + g["skirt_gap"], False), "INTERSECT")
    boolean(skirt, field(half + 3, True), "INTERSECT")
    bevel(skirt, 0.8, 3)

    # ring pad: two rounded velvet rolls across the tray with a slot between them
    pc, (slot_w, slot_d) = ci - cw - 0.2, g["pad_slot"]
    pad = block("Box | Pad", -pc, pc, -pc, -slot_w / 2, g["base_floor"] + 1.05, g["pad_top_z"])
    bevel(pad, g["pad_radius"], 6)
    roll = block("pad", -pc, pc, slot_w / 2, pc, g["base_floor"] + 1.05, g["pad_top_z"])
    bevel(roll, g["pad_radius"], 6)
    boolean(pad, roll, "UNION")
    boolean(pad, block("cut", -pc - 1, pc + 1, -slot_w / 2, slot_w / 2, g["pad_top_z"] - slot_d, size), "DIFFERENCE")

    # half-round gold beads: along the lid's lower edge and along the base rim, broken where the strap crosses
    bp, bh = g["bead_proud"], g["bead_height"]

    def bead(name, z_lo, z_hi):
        o = block(name, -a - bp, a + bp, -a - bp, a + bp, -5, size + 5)
        boolean(o, block("cut", -a + 0.6, a - 0.6, -a + 0.6, a - 0.6, -10, size + 10), "DIFFERENCE")
        boolean(o, field(z_lo, False), "INTERSECT")
        boolean(o, field(z_hi, True), "INTERSECT")
        boolean(o, block("cut", -sw - 0.4, sw + 0.4, -a - 5, a + 5, -10, size + 10), "DIFFERENCE")
        bevel(o, g["bead_radius"], 4)
        return o
    beads = bh > 0  # bead_height 0 = no gold beads
    bead_lid = bead("Box | Bead lid", half, half + bh) if beads else None
    bead_base = bead("Box | Bead base", -half - bh, -half) if beads else None

    # strap: up the front, over the lid, down the back; lid and base parts end at the reveal
    def strap(name, offset, below):
        o = block(name, -sw, sw, -a - st, a + st, 0, size + st)
        boolean(o, block("cut", -sw - 1, sw + 1, -a, a, -1, size), "DIFFERENCE")
        boolean(o, field(offset, below), "INTERSECT")
        bevel(o, 0.4, 2)
        return o
    strap_lid = strap("Box | Strap lid", half, False)
    strap_base = strap("Box | Strap base", -half, True)

    # clasp: plain gold square on the lid strap at the V tip, bridging the reveal in front of the base strap
    cw_, ch, cd = g["clasp"]
    clasp = block("Box | Clasp", -cw_ / 2, cw_ / 2, -a - st - 0.05 - cd, -a - st - 0.05, lo - ch / 2, lo + ch / 2)
    bevel(clasp, g["clasp_radius"], 4)

    # wordmark: gold foil on the lid ceiling, reading upright from below with the front edge as top
    subpaths = parse_svg((ROOT / spec["wordmark_svg"]).read_text())
    xs = [q[0] for s in subpaths for seg in s for q in seg]
    ys = [q[1] for s in subpaths for seg in s for q in seg]
    k = g["wordmark_width"] / (max(xs) - min(xs))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    cu = bpy.data.curves.new("Box | Wordmark", "CURVE")
    cu.dimensions, cu.fill_mode, cu.extrude = "2D", "BOTH", g["wordmark_thickness"] / 2 * MM
    for segs in subpaths:
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(segs) - 1)
        sp.use_cyclic_u = True
        for i, (p0, c1, c2, p1) in enumerate(segs):
            bpt, nxt = sp.bezier_points[i], sp.bezier_points[(i + 1) % len(segs)]
            bpt.co = ((p0[0] - cx) * k * MM, -(p0[1] - cy) * k * MM, 0)  # SVG y runs down
            bpt.handle_right = ((c1[0] - cx) * k * MM, -(c1[1] - cy) * k * MM, 0)
            nxt.handle_left = ((c2[0] - cx) * k * MM, -(c2[1] - cy) * k * MM, 0)
            bpt.handle_left_type = bpt.handle_right_type = "FREE"
    tmp = bpy.data.objects.new("wordmark curve", cu)
    scene.collection.objects.link(tmp)
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    wordmark = bpy.data.objects.new("Box | Wordmark", me)
    scene.collection.objects.link(wordmark)
    ceiling = size - g["lid_top"] - 0.01 - g["wordmark_thickness"] / 2
    wordmark.data.transform(Matrix.Translation(Vector((0, g["wordmark_center_y"], ceiling)) * MM) @ Matrix.Rotation(math.pi, 4, "X"))

    lid_group = [o for o in (lid, skirt, bead_lid, strap_lid, clasp, wordmark) if o]
    base_group = [o for o in (base, bead_base, strap_base, collar, pad) if o]
    parts = lid_group + base_group

    # metric UVs (dominant-axis projection), shifted uv_offset_mm so each 100 mm face sits inside one swatch tile
    off = g["uv_offset_mm"] * MM
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        uv = bm.loops.layers.uv.new("Metric UV")
        for f in bm.faces:
            axis = max(range(3), key=lambda i: abs(f.normal[i]))
            u, v = [i for i in range(3) if i != axis]
            for loop in f.loops:
                loop[uv].uv = (loop.vert.co[u] + off, loop.vert.co[v] + off)
        bm.to_mesh(o.data)
        bm.free()
        o.data.shade_smooth()
        o.data.set_sharp_from_angle(angle=math.radians(30))
        wn = o.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
        wn.mode, wn.keep_sharp = "FACE_AREA", True
        bake(o, wn)

    # glTF-safe stand-ins (the swatch as colour on the cloth); renders swap in the library look
    ms = spec["materials"]
    swatch = bpy.data.images.load(str(ROOT / ms["swatch"]))
    swatch.pack()
    mats = {}
    for role in ("exterior", "accent", "strap", "gold"):
        mat = mats[role] = bpy.data.materials.new("Sleeve Lock | " + role)
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*ms[role]["color_linear"], 1)
        bsdf.inputs["Roughness"].default_value = ms[role]["roughness"]
        bsdf.inputs["Metallic"].default_value = ms[role].get("metallic", 0.0)
        if role == "exterior":
            uvn = nodes.new("ShaderNodeUVMap")
            uvn.uv_map = "Metric UV"
            mp = nodes.new("ShaderNodeMapping")
            tw = ms["swatch_tile_mm"]
            mp.inputs["Scale"].default_value = (1000 / tw, 1000 / tw * swatch.size[0] / swatch.size[1], 1)  # square texels
            tex = nodes.new("ShaderNodeTexImage")
            tex.image = swatch
            links.new(uvn.outputs["UV"], mp.inputs["Vector"])
            links.new(mp.outputs["Vector"], tex.inputs["Vector"])
            links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    t = 0.01
    inside = {lid: lambda q: abs(q.x) < (a - w + t) * MM and abs(q.y) < (a - w + t) * MM and q.z < (size - g["lid_top"] + t) * MM,
              base: lambda q: abs(q.x) < (a - w + t) * MM and abs(q.y) < (a - w + t) * MM and q.z > (g["base_floor"] - t) * MM}
    role_of = {strap_lid: "strap", strap_base: "strap", collar: "accent", pad: "accent", skirt: "accent"}
    for o in parts:
        o.data.materials.clear()  # boolean bakes leave an empty first slot that would shift every index
        if o in inside:
            o.data.materials.append(mats["exterior"])
            o.data.materials.append(mats["accent"])
            for f in o.data.polygons:
                f.material_index = 1 if all(inside[o](o.data.vertices[i].co) for i in f.vertices) else 0
        else:
            o.data.materials.append(mats[role_of.get(o, "gold")])
    velvet = {o.name: sum(f.material_index for f in o.data.polygons) for o in inside}
    assert all(velvet.values()), "a shell has no velvet faces: %s" % velvet

    # controls, export tags, GLB lift: the lid group rises lift_mm over `frames`, frame 1 closed
    ctrl = {}
    for name in ("CTRL | Base", "CTRL | Lid lift-off"):
        ctrl[name] = bpy.data.objects.new(name, None)
        scene.collection.objects.link(ctrl[name])
    for o in parts:
        o.parent = ctrl["CTRL | Lid lift-off" if o in lid_group else "CTRL | Base"]
        o["export_product"] = True
    anim = spec["lid_animation"]
    action = bpy.data.actions.new("Lid lift")
    for o in lid_group:
        o.animation_data_create().action = action
        for frame, z in ((1, 0.0), (anim["frames"], anim["lift_mm"] * MM)):
            o.location.z = z
            o.keyframe_insert("location", index=2, frame=frame)
    scene.frame_start, scene.frame_end = 1, anim["frames"]

    # house scene: black world, Standard view
    world = scene.world or bpy.data.worlds.new("World")
    scene.world, world.use_nodes = world, True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0, 0, 0, 1), 0
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = spec["scene"]["view_transform"]
    scene.view_settings.exposure = spec["scene"]["exposure"]

    # self-check: watertight solids; the lid group never meets the base group, closed or lifting
    summary = {}
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_edges = sum(not e.is_manifold for e in bm.edges)
        assert o is wordmark or open_edges == 0, "%s has %d non-manifold edges" % (o.name, open_edges)
        summary[o.name] = {"faces": len(bm.faces), "dims_mm": [round(d / MM, 2) for d in o.dimensions]}
        bm.free()
    for frame in [*range(1, anim["frames"], 3), anim["frames"]]:
        scene.frame_set(frame)
        trees = {}
        for o in parts:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.transform(o.matrix_world)
            trees[o.name] = BVHTree.FromBMesh(bm)
            bm.free()
        for x in lid_group:
            for y in base_group:
                hits = trees[x.name].overlap(trees[y.name])
                assert not hits, "frame %d: %s meets %s (%d triangle pairs)" % (frame, x.name, y.name, len(hits))
    scene.frame_set(1)
    zs = [(o.matrix_world @ v.co).z / MM for o in parts for v in o.data.vertices]
    assert abs(max(zs) - size - st) < 0.05 and min(zs) > -1e-3, "closed box spans %.2f .. %.2f mm" % (min(zs), max(zs))
    return {"parts": summary, "velvet_faces": velvet}
