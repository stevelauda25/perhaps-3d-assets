"""box_medallion: build the 14 Medallion square ring box (back-hinged lid, front tab with a gold medallion) in an empty scene.

Params: spec (config/presets/box_medallion.json, millimetres). Scene units are metres. Closed (frame 1) it is size x size x height.
Base group (never moves): `Box | Base` (U notch at the front centre), `Box | Collar` (lining sleeve rising into the lid), `Box | Pad`.
Lid group: `Box | Lid` (shell with the front tab), `Box | Medallion`, `Box | Lid text`, all with their origin on the hinge (outer
back edge at the lid's lower edge) and one `Lid open` action. `CTRL | Base` / `CTRL | Lid lift-off` hold the groups.
Fails if a solid is not watertight (the lettering excepted) or any lid part meets the base group at any frame.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MM = 0.001


def run(params):
    import bmesh
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    from mathutils.bvhtree import BVHTree

    spec = json.loads((ROOT / params["spec"]).read_text())
    g = spec["geometry_mm"]
    scene = bpy.context.scene
    size, a, H, w = g["size"], g["size"] / 2, g["height"], g["wall"]
    zb = g["base_top"]
    zl = zb + g["reveal"]  # lid's lower edge
    nw, nd = g["notch"]
    tc = g["tab_clearance"]

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

    # base: shell with the tray cavity and the U notch through the front wall at the centre
    base = block("Box | Base", -a, a, -a, a, 0, zb)
    bevel(base)
    boolean(base, block("cut", -a + w, a - w, -a + w, a - w, g["base_floor"], zb + 5), "DIFFERENCE")
    boolean(base, block("cut", -nw / 2, nw / 2, -a - 1, -a + w + 1, zb - nd, zb + 5), "DIFFERENCE")

    # lid: shell from the reveal up, plus the tab that drops into the notch (clearance tc each side and below)
    lid = block("Box | Lid", -a, a, -a, a, zl, H)
    boolean(lid, block("tab", -nw / 2 + tc, nw / 2 - tc, -a, -a + w, zb - nd + tc, zl + 1), "UNION")
    bevel(lid)
    boolean(lid, block("cut", -a + w, a - w, -a + w, a - w, zb - nd - 5, H - g["lid_top"]), "DIFFERENCE")

    # optional: the official perhaps wordmark pressed into the lid top (tone-on-tone), rim softened by a weighted bevel
    db = g.get("lid_deboss")
    if db:
        from pipeline.steps.logo_deboss import parse_svg, solids_with_holes
        subpaths = parse_svg((ROOT / db["svg"]).read_text())
        pts = [q for sp in subpaths for seg in sp for q in seg]
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        k, cx, cy = db["width"] / (max(xs) - min(xs)), (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        f = lambda q: ((q[0] - cx) * k * MM, (db.get("center_y", 0) - (q[1] - cy) * k) * MM, 0)  # SVG y is down; tops toward the back
        dbm = bmesh.new()
        for group in solids_with_holes(subpaths):  # one welded solid per glyph part; the parts overlap, so the cut uses self-intersection
            cu = bpy.data.curves.new("die", "CURVE")
            cu.dimensions, cu.fill_mode, cu.resolution_u, cu.extrude = "2D", "BOTH", 16, db["depth"] * MM
            for segs in group:
                sp = cu.splines.new("BEZIER")
                sp.use_cyclic_u = True
                sp.bezier_points.add(len(segs) - 1)
                for bp, (p0, c1, c2, p1), prev in zip(sp.bezier_points, segs, [segs[-1]] + segs[:-1]):
                    bp.co, bp.handle_left_type, bp.handle_right_type = f(p0), "FREE", "FREE"
                    bp.handle_left, bp.handle_right = f(prev[2]), f(c1)
            tmp = bpy.data.objects.new("die", cu)
            scene.collection.objects.link(tmp)
            bpy.context.view_layer.update()
            me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
            bpy.data.objects.remove(tmp)
            bpy.data.curves.remove(cu)
            gb = bmesh.new()
            gb.from_mesh(me)
            bmesh.ops.remove_doubles(gb, verts=gb.verts, dist=1e-7)  # curve caps and walls come out unwelded
            gb.to_mesh(me)
            gb.free()
            dbm.from_mesh(me)
            bpy.data.meshes.remove(me)
        dbm.transform(Matrix.Translation(Vector((0, 0, H * MM))))  # die spans H - depth .. H + depth
        me = bpy.data.meshes.new("die")
        dbm.to_mesh(me)
        dbm.free()
        die = bpy.data.objects.new("die", me)
        scene.collection.objects.link(die)
        dx = [v.co.x for v in me.vertices]; dy = [v.co.y for v in me.vertices]
        box = (min(dx) - 0.002, max(dx) + 0.002, min(dy) - 0.002, max(dy) + 0.002)
        m = lid.modifiers.new("Cut", "BOOLEAN")
        m.operation, m.solver, m.object, m.use_self = "DIFFERENCE", "EXACT", die, True
        bake(lid, m)
        bpy.data.meshes.remove(die.data)
        bm = bmesh.new()
        bm.from_mesh(lid.data)
        wt = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
        rim = 0
        for e in bm.edges:  # the letters' top rim only: on the lid top plane, inside the die box, and a real fold (not a flat triangulation edge)
            if all(abs(v.co.z - H * MM) < 1e-6 and box[0] < v.co.x < box[1] and box[2] < v.co.y < box[3] for v in e.verts) \
                    and e.is_manifold and e.calc_face_angle(0) > math.radians(20):
                e[wt], rim = 1.0, rim + 1
        bm.to_mesh(lid.data)
        bm.free()
        assert rim, "deboss cut no rim edges into the lid top"
        m = lid.modifiers.new("Soft die lip", "BEVEL")
        m.limit_method, m.width, m.segments, m.profile, m.use_clamp_overlap = "WEIGHT", db["lip"] * MM, 3, 0.62, True
        bake(lid, m)

    # collar: lining sleeve inside the base rising collar_rise above the lid's lower edge (the band in the reveal)
    ci, cw = a - w - g["collar_clearance"], g["collar_wall"]
    collar = block("Box | Collar", -ci, ci, -ci, ci, g["base_floor"] + 0.05, zl + g["collar_rise"])
    bevel(collar, g["collar_radius"], 4)
    boolean(collar, block("cut", -ci + cw, ci - cw, -ci + cw, ci - cw, g["base_floor"] + 1, H + 5), "DIFFERENCE")

    # ring pad: two rounded rolls across the tray with one slit between them
    pc, (slot_w, slot_d) = ci - cw - 0.2, g["pad_slot"]
    pad = block("Box | Pad", -pc, pc, -pc, -slot_w / 2, g["base_floor"] + 1.05, g["pad_top_z"])
    bevel(pad, g["pad_radius"], 6)
    roll = block("pad", -pc, pc, slot_w / 2, pc, g["base_floor"] + 1.05, g["pad_top_z"])
    bevel(roll, g["pad_radius"], 6)
    boolean(pad, roll, "UNION")
    boolean(pad, block("cut", -pc - 1, pc + 1, -slot_w / 2, slot_w / 2, g["pad_top_z"] - slot_d, H), "DIFFERENCE")

    # medallion: domed rounded square |x/hw|^p + |z/hh|^p = 1 on the tab, straddling the reveal; caps are fans from the
    # centre (the outline is convex) and the dome is a stack of shrinking rings
    md = g["medallion"]
    hw, hh, p, dome, mz = md["size"][0] / 2, md["size"][1] / 2, md.get("power", 4.0), md.get("dome", 0.0), md["center_z"]
    n = 96
    outline = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        outline.append((hw * math.copysign(abs(c) ** (2 / p), c), hh * math.copysign(abs(s) ** (2 / p), s)))
    y0 = -a - 0.05  # back face just in front of the tab
    bm = bmesh.new()
    rings = [[bm.verts.new((x * k * MM, (y0 - d) * MM, (mz + z * k) * MM)) for x, z in outline]
             for k, d in ((1.0, 0.0), (1.0, 0.25 * dome), (0.94, 0.6 * dome), (0.8, 0.85 * dome), (0.5, dome))]
    for ring, d in ((rings[0], 0.0), (rings[-1], dome + 0.15)):
        cv = bm.verts.new((0, (y0 - d) * MM, mz * MM))
        for k in range(n):
            bm.faces.new((cv, ring[k], ring[(k + 1) % n]))
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    medallion = link("Box | Medallion", bm)
    if md.get("shape", "cushion") == "rect":  # sharp flat rectangular plate instead of the dome, crisp 1-segment chamfer
        bpy.data.meshes.remove(medallion.data)
        medallion = block("Box | Medallion", -hw, hw, y0 - md["thickness"], y0, mz - hh, mz + hh)
        bevel(medallion, md.get("chamfer", 0.15), 1)
    assert hw < nw / 2 - tc and mz - hh > zb - nd + tc, "medallion overhangs the tab"

    # Perhaps in gold foil on the lid lining, reading upright when the lid stands open (up = the lid's front edge)
    t = g["lid_text"]
    font = Path(t["font"])
    assert font.exists(), "font not found: %s" % font
    cu = bpy.data.curves.new("Box | Lid text", "FONT")
    cu.body, cu.font = t["text"], bpy.data.fonts.load(str(font))
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    lt = g["lettering_thickness"]
    cu.extrude = lt / 2 * MM
    tmp = bpy.data.objects.new("lid text", cu)
    scene.collection.objects.link(tmp)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    xs, ys = [v.co.x for v in me.vertices], [v.co.y for v in me.vertices]
    k = t["width"] * MM / (max(xs) - min(xs))
    me.transform(Matrix.Diagonal((k, k, 1, 1)) @ Matrix.Translation(Vector((-(max(xs) + min(xs)) / 2, -(max(ys) + min(ys)) / 2, 0))))
    me.transform(Matrix.Translation(Vector((0, t["center_y"], H - g["lid_top"] - 0.01 - lt / 2)) * MM) @ Matrix.Rotation(math.pi, 4, "X"))
    lid_text = bpy.data.objects.new("Box | Lid text", me)
    scene.collection.objects.link(lid_text)

    lid_group = [lid, medallion, lid_text]
    base_group = [base, collar, pad]
    parts = lid_group + base_group

    # metric UVs (dominant-axis projection) for the GLB swatch; smooth shading with sharp edges kept
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

    # glTF-safe stand-ins (the charcoal swatch on the cloth); renders swap in the library look
    ms = spec["materials"]
    swatch = bpy.data.images.load(str(ROOT / ms["swatch"]))
    swatch.pack()
    mats = {}
    for role in ("exterior", "accent", "gold"):
        mat = mats[role] = bpy.data.materials.new("Medallion | " + role)
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
            if ms.get("swatch_normal"):
                nim = bpy.data.images.load(str(ROOT / ms["swatch_normal"]))
                nim.colorspace_settings.name = "Non-Color"
                nim.pack()
                ntex, nmap = nodes.new("ShaderNodeTexImage"), nodes.new("ShaderNodeNormalMap")
                ntex.image = nim
                links.new(mp.outputs["Vector"], ntex.inputs["Vector"])
                links.new(ntex.outputs["Color"], nmap.inputs["Color"])
                links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    tol = 0.01
    inside = {lid: lambda q: abs(q.x) < (a - w + tol) * MM and abs(q.y) < (a - w + tol) * MM and q.z < (H - g["lid_top"] + tol) * MM,
              base: lambda q: abs(q.x) < (a - w + tol) * MM and abs(q.y) < (a - w + tol) * MM and q.z > (g["base_floor"] - tol) * MM}
    role_of = {collar: "accent", pad: "accent"}
    for o in parts:
        o.data.materials.clear()  # boolean bakes leave an empty first slot that would shift every index
        if o in inside:
            o.data.materials.append(mats["exterior"])
            o.data.materials.append(mats["accent"])
            for f in o.data.polygons:
                f.material_index = 1 if all(inside[o](o.data.vertices[i].co) for i in f.vertices) else 0
        else:
            o.data.materials.append(mats[role_of.get(o, "gold")])
    lining = {o.name: sum(f.material_index for f in o.data.polygons) for o in inside}
    assert all(lining.values()), "a shell has no lining faces: %s" % lining

    # hinge: the lid group pivots on the lid's outer back edge at its lower edge
    hinge = Vector((0, a, zl)) * MM
    for o in lid_group:
        o.data.transform(Matrix.Translation(-hinge))
        o.location = hinge
        o.rotation_mode = "QUATERNION"
    ctrl = {}
    for name in ("CTRL | Base", "CTRL | Lid lift-off"):
        ctrl[name] = bpy.data.objects.new(name, None)
        scene.collection.objects.link(ctrl[name])
    for o in parts:
        o.parent = ctrl["CTRL | Lid lift-off" if o in lid_group else "CTRL | Base"]
        o["export_product"] = True
    anim = spec["lid_animation"]
    end = anim["frames"]
    action = bpy.data.actions.new("Lid open")
    for o in lid_group:
        o.animation_data_create().action = action
        for frame, deg in ((1, 0.0), (end, anim["open_deg"])):
            o.rotation_quaternion = Quaternion((1, 0, 0), -math.radians(deg))  # front edge up, about +x
            o.keyframe_insert("rotation_quaternion", frame=frame)
    scene.frame_start, scene.frame_end = 1, end

    # house scene: black world, Standard view
    world = scene.world or bpy.data.worlds.new("World")
    scene.world, world.use_nodes = world, True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0, 0, 0, 1), 0
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = spec["scene"]["view_transform"]
    scene.view_settings.exposure = spec["scene"]["exposure"]

    # self-check: watertight solids; the lid group never meets the base group, closed or opening; closed it is the box
    summary = {}
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_edges = sum(not e.is_manifold for e in bm.edges)
        assert o is lid_text or open_edges == 0, "%s has %d non-manifold edges" % (o.name, open_edges)
        summary[o.name] = {"faces": len(bm.faces), "dims_mm": [round(d / MM, 2) for d in o.dimensions]}
        bm.free()
    for frame in [*range(1, end, 2), end]:
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
    co = [o.matrix_world @ v.co for o in (base, lid) for v in o.data.vertices]
    span = [round((max(c[i] for c in co) - min(c[i] for c in co)) / MM, 2) for i in range(3)]
    assert all(abs(x - want) < 0.05 for x, want in zip(span, (size, size, H))), "closed box is %s mm" % span
    return {"parts": summary, "closed_mm": span, "lining_faces": lining}
