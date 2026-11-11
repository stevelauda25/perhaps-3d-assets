"""box_diagonal_split: build the Diagonal Split cube box in an empty scene.

Params: spec (config/presets/box_diagonal_split.json, millimetres). Scene units are metres.
The top `lid_depth` mm is a lid cut corner to corner along the diagonal x = y into two triangular trays,
`Box | Lid A` (corner +x -y) and `Box | Lid B` (corner -x +y). Each tray has its origin on its hinge pin
and rotates on a brass butt hinge on one outer top edge, the edge that runs from its outer corner to the back cut corner
(+x, +y): Lid A on x = +a, Lid B on y = +a. The cut edge swings up (one action, one GLB animation). Hinge leaves and knuckles are part of the tray and base meshes (material `hinge`).
`CTRL | Base` holds `Box | Base` and `Box | Insert`; `CTRL | Lid lift-off` holds both trays (the names floating_stage expects).
Finger notches (`grip_radius`) scoop the base rim at the two corners on the cut.
Fails if a mesh is not watertight or two parts intersect, closed or at any animation frame.
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
    a, w, gap = g["size"] / 2, g["wall"], g["seat_gap"]
    zl = g["size"] - g["lid_depth"]                       # top of the base shell = bottom of the lid
    si = a - w - g["insert_clearance"]                    # inner tray outer half size
    ci = si - g["insert_wall"]                            # inner tray cavity half size

    def link(name, bm):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        scene.collection.objects.link(o)
        return o

    def prism(name, pts, z0, z1):
        """Closed vertical prism over the XY polygon `pts` (mm, counter-clockwise), z0..z1."""
        bm = bmesh.new()
        lo = [bm.verts.new((x * MM, y * MM, z0 * MM)) for x, y in pts]
        hi = [bm.verts.new((x * MM, y * MM, z1 * MM)) for x, y in pts]
        bm.faces.new(lo[::-1])
        bm.faces.new(hi)
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        return link(name, bm)

    def square(name, h, z0, z1):
        return prism(name, [(-h, -h), (h, -h), (h, h), (-h, h)], z0, z1)

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

    # base: bevelled shell open at the top; inner tray standing on its floor and rising into the lid
    base = square("Box | Base", a, 0, zl)
    bevel(base)
    boolean(base, square("cut", a - w, g["base_floor"], zl + 1), "DIFFERENCE")
    # finger notches: a horizontal cylinder along the diagonal scoops the rim at the two corners where the trays meet,
    # so a finger reaches the lid edge farthest from both hinges
    rn = g["grip_radius"]
    for sx in (-1, 1):
        inward = Vector((-sx, -sx, 0)).normalized()
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=rn * MM, radius2=rn * MM, depth=4 * rn * MM)
        bm.transform(Matrix.Translation(Vector((sx * a, sx * a, zl)) * MM) @ Vector((0, 0, 1)).rotation_difference(inward).to_matrix().to_4x4())
        boolean(base, link("cut", bm), "DIFFERENCE")
    z0 = g["base_floor"] + gap
    insert = square("Box | Insert", si, z0, zl + g["insert_rise"])
    boolean(insert, square("cut", ci, z0 + g["insert_floor"], zl + g["insert_rise"] + 1), "DIFFERENCE")

    # lid: one bevelled tray, then split along x = y with `seam` between the halves
    c = g["seam"] / 2 * math.sqrt(2)  # each half keeps |x - y| > c
    lids = []
    for name, far in (("Box | Lid A", [(-300, -300 - c), (300, 300 - c), (-300, 300)]),     # drop x - y < c
                      ("Box | Lid B", [(-300 - c, -300), (300, -300), (300 - c, 300)])):    # drop y - x < c
        lid = square(name, a, zl + gap, g["size"])
        bevel(lid)
        boolean(lid, square("cut", a - w, zl, g["size"] - g["lid_top"]), "DIFFERENCE")
        boolean(lid, prism("cut", far, zl - 1, g["size"] + 1), "DIFFERENCE")
        lids.append(lid)

    # edge hinges: local frame per hinge, t along the edge, u outward from the face, z from the lid bottom.
    # Leaves lie flat on the face (lid leaf above the seam, base leaf below); three knuckles, the middle one on the lid.
    rk, gk, hl, hh, th = g["knuckle_radius"], g["knuckle_gap"], g["hinge_length"], g["hinge_height"], g["hinge_leaf"]
    ck = rk + 2 * gk  # pin axis this far outside the face, so knuckle slots never cut the box itself
    s6 = hl / 6

    def local(M, t, u, z):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        bm.transform(M @ Matrix.Translation(((t[0] + t[1]) / 2, (u[0] + u[1]) / 2, (z[0] + z[1]) / 2))
                     @ Matrix.Diagonal((t[1] - t[0], u[1] - u[0], z[1] - z[0], 1)))
        return link("cut", bm)

    def knuckle(M, t, r):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=r, radius2=r, depth=t[1] - t[0])
        bm.transform(M @ Matrix.Translation(((t[0] + t[1]) / 2, ck, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        return link("cut", bm)

    def leaf(M, z, slots):
        o = local(M, (-hl / 2, hl / 2), (-hl, ck), z)
        boolean(o, square("cut", a + th, -1, g["size"] + 1), "INTERSECT")
        boolean(o, square("cut", a - 1, -1, g["size"] + 1), "DIFFERENCE")  # sinks 1 mm into the wall for a clean union
        for t in slots:
            boolean(o, knuckle(M, t, rk + gk), "DIFFERENCE")
        return o

    pivots = {}
    off = g["hinge_from_corner"]
    for lid, n, corner in ((lids[0], Vector((1, 0, 0)), Vector((a, -a + off, zl + gap))),     # Lid A on edge x = +a
                           (lids[1], Vector((0, 1, 0)), Vector((-a + off, a, zl + gap)))):    # Lid B on edge y = +a
        d = n.cross(Vector((0, 0, 1)))
        M = Matrix.Scale(MM, 4) @ Matrix(((d.x, n.x, 0, corner.x), (d.y, n.y, 0, corner.y), (0, 0, 1, corner.z), (0, 0, 0, 1)))
        boolean(lid, leaf(M, (0, hh), [(-hl / 2 - 1, -s6 + gk / 2), (s6 - gk / 2, hl / 2 + 1)]), "UNION")
        boolean(lid, knuckle(M, (-s6 + gk / 2, s6 - gk / 2), rk), "UNION")
        boolean(base, leaf(M, (-hh, -gap), [(-s6 - gk / 2, s6 + gk / 2)]), "UNION")
        for t in ((-hl / 2, -s6 - gk / 2), (s6 + gk / 2, hl / 2)):
            boolean(base, knuckle(M, t, rk), "UNION")
        pivots[lid] = ((corner + ck * n) * MM, d)  # rotating by -angle about d lifts the inward side

    parts = [base, insert] + lids
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

    # materials: glTF-safe colour + paper relief; renders swap in library paper with packaging_tier
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
        mat = mats[role] = bpy.data.materials.new("Diagonal Split | " + role)
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
    mat = mats["hinge"] = bpy.data.materials.new("Diagonal Split | hinge")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*ms["hinge"]["color_linear"], 1)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = ms["hinge"]["roughness"]
    # accent (white) = inner tray and every face inside the base or lid cavities; outer faces, rims and cut edges stay kraft
    t = 0.01
    inside = {base: lambda q: abs(q.x) < (a - w + t) * MM and abs(q.y) < (a - w + t) * MM and q.z > (g["base_floor"] - t) * MM,
              insert: lambda q: True}
    for lid in lids:
        inside[lid] = lambda q: abs(q.x) < (a - w + t) * MM and abs(q.y) < (a - w + t) * MM and q.z < (g["size"] - g["lid_top"] + t) * MM
    for o in parts:
        o.data.materials.clear()  # boolean bakes leave an empty first slot that would shift every index
        o.data.materials.append(mats["exterior"])
        o.data.materials.append(mats["accent"])
        o.data.materials.append(mats["hinge"])
        for f in o.data.polygons:
            c = f.center
            if max(abs(c.x), abs(c.y)) > (a + t) * MM:  # only hinge faces stand proud of the cube
                f.material_index = 2
            else:
                f.material_index = 1 if all(inside[o](o.data.vertices[i].co) for i in f.vertices) else 0
    white = {o.name: sum(f.material_index == 1 for f in o.data.polygons) for o in parts}
    assert all(white.values()), "a part has no white faces: %s" % white
    brass = {o.name: sum(f.material_index == 2 for f in o.data.polygons) for o in parts}
    assert all(brass[o.name] for o in [base] + lids), "a hinge is missing: %s" % brass

    # trays: origin on the hinge pin, so the GLB rotation needs no pivot node
    hinge = pivots
    for lid, (pivot, _) in hinge.items():
        lid.data.transform(Matrix.Translation(-pivot))
        lid.location = pivot
        lid.rotation_mode = "QUATERNION"

    # controls (canonical names) and export tags
    ctrl = {}
    for name in ("CTRL | Base", "CTRL | Lid lift-off"):
        ctrl[name] = bpy.data.objects.new(name, None)
        scene.collection.objects.link(ctrl[name])
    for o in parts:
        o.parent = ctrl["CTRL | Lid lift-off" if o in lids else "CTRL | Base"]
        o["export_product"] = True

    # GLB open/close: one action with a slot per tray, so model-viewer plays both as one clip; frame 1 stays closed
    anim = spec["lid_animation"]
    action = bpy.data.actions.new("Lid open")
    for lid, (_, axis) in hinge.items():
        lid.animation_data_create().action = action
        for frame, deg in ((1, 0.0), (anim["frames"], anim["open_deg"])):
            lid.rotation_quaternion = Quaternion(axis, -math.radians(deg))
            lid.keyframe_insert("rotation_quaternion", frame=frame)
    scene.frame_start, scene.frame_end = 1, anim["frames"]
    scene.frame_set(1)

    # house scene: black world, Standard view
    world = scene.world or bpy.data.worlds.new("World")
    scene.world, world.use_nodes = world, True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0, 0, 0, 1), 0
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = spec["scene"]["view_transform"]
    scene.view_settings.exposure = spec["scene"]["exposure"]

    # self-check: every part watertight; no two parts intersect closed or anywhere along the opening
    summary = {}
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_edges = sum(not e.is_manifold for e in bm.edges)
        assert open_edges == 0, "%s has %d non-manifold edges" % (o.name, open_edges)
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
        names = list(trees)
        for i, x in enumerate(names):
            for y in names[i + 1:]:
                hits = trees[x].overlap(trees[y])
                assert not hits, "frame %d: %s intersects %s (%d triangle pairs)" % (frame, x, y, len(hits))
    scene.frame_set(1)
    return {"parts": summary, "white_faces": white, "hinge_faces": brass}
