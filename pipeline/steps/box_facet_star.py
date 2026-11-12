"""box_facet_star: build the 11 Facet Star cube box in an empty scene.

Params: spec (config/presets/box_facet_star.json, millimetres). Scene units are metres.
Base group: `Box | Base` (faceted sides, thick walls), `Box | Star`, `Box | Liner` (upholstered border). Lid group (hinged on the back edge of the seam):
`Box | Lid`, `Box | Card`, `Box | Wordmark` (card lettering),
`Box | Lid mark` (optional lettering on the lid top); each has its origin on the hinge and carries the `Lid open` action.
`CTRL | Base` / `CTRL | Lid lift-off` hold the groups (names floating_stage expects).
Fails if a mesh is not watertight (the wordmark excepted: a filled curve) or the lid group meets the base group at any
frame of the opening.
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
    from pipeline.steps.logo_deboss import parse_svg

    spec = json.loads((ROOT / params["spec"]).read_text())
    g = spec["geometry_mm"]
    scene = bpy.context.scene
    size, a = g["size"], g["size"] / 2
    H = g.get("height", size)                        # closed height; the footprint stays size x size
    zb = H - g["lid_thickness"] - g["seam_gap"]      # base top
    zl = H - g["lid_thickness"]                      # lid underside

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

    def bevel(o, width, segments):
        m = o.modifiers.new("Edge radius", "BEVEL")
        m.width, m.segments, m.limit_method, m.use_clamp_overlap = width * MM, segments, "ANGLE", True
        bake(o, m)

    def boolean(o, cutter, op):
        m = o.modifiers.new("Cut", "BOOLEAN")
        m.operation, m.solver, m.object = op, "EXACT", cutter
        bake(o, m)
        bpy.data.meshes.remove(cutter.data)

    # base: closed solid whose four sides are grids of inverted pyramids (cell edges on the cube plane)
    cols, rows = g["facet_grid"]
    d = g["facet_depth"]
    sides = (  # point on the side from (u, z), inward normal; u runs left to right seen from outside
        (lambda u, z: Vector((u, -a, z)), Vector((0, 1, 0))),
        (lambda u, z: Vector((a, u, z)), Vector((-1, 0, 0))),
        (lambda u, z: Vector((-u, a, z)), Vector((0, -1, 0))),
        (lambda u, z: Vector((-a, -u, z)), Vector((1, 0, 0))),
    )
    bm = bmesh.new()
    cache = {}

    def vert(p):
        key = tuple(round(c, 6) for c in p)
        if key not in cache:
            cache[key] = bm.verts.new(p * MM)
        return cache[key]
    us = [-a + i * 2 * a / cols for i in range(cols + 1)]
    zs = [j * zb / rows for j in range(rows + 1)]
    for point, inward in sides:
        for i in range(cols):
            for j in range(rows):
                c = [point(us[i], zs[j]), point(us[i + 1], zs[j]), point(us[i + 1], zs[j + 1]), point(us[i], zs[j + 1])]
                apex = vert(point((us[i] + us[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2) + inward * d)
                for k in range(4):
                    bm.faces.new((vert(c[k]), vert(c[(k + 1) % 4]), apex))
    ring = [p for point, _ in sides for p in (point(u, 0) for u in us[:-1])]
    bm.faces.new([vert(p) for p in ring])
    bm.faces.new([vert(p + Vector((0, 0, zb))) for p in ring])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    base = link("Box | Base", bm)
    bevel(base, g["edge_radius"], g["edge_segments"])
    w = g["wall"]
    boolean(base, block("cut", -a + w, a - w, -a + w, a - w, g["base_floor"], H), "DIFFERENCE")

    # upholstered border: a thick rounded velvet ring inside the compartment, its top liner_drop below the rim
    lb, li = g["liner_border"], a - w
    liner = block("Box | Liner", -li + 0.05, li - 0.05, -li + 0.05, li - 0.05, g["base_floor"] + 0.05, zb - g["liner_drop"])
    bevel(liner, g["liner_radius"], 4)
    boolean(liner, block("cut", -li + lb, li - lb, -li + lb, li - lb, g["base_floor"] + 1.5, H), "DIFFERENCE")

    # gold four-point star on the front at a grid crossing, standing proud of the ridge
    s = g["star"]
    sx, sz = s["x"], s["z"] if s["z"] is not None else zb / 2
    # sparkle outline: |x|^p + |z|^p = tip^p, p < 1 gives four sharp tips joined by inward-curving sides
    pw = s["power"]
    pts = []
    for i in range(96):
        t = 2 * math.pi * i / 96
        cx_, cz_ = math.cos(t), math.sin(t)
        pts.append((sx + s["tip"] * math.copysign(abs(cx_) ** (2 / pw), cx_), sz + s["tip"] * math.copysign(abs(cz_) ** (2 / pw), cz_)))
    bm = bmesh.new()
    f0 = [bm.verts.new((x * MM, (-a - s["thickness"]) * MM, z * MM)) for x, z in pts]
    f1 = [bm.verts.new((x * MM, -a * MM, z * MM)) for x, z in pts]
    bm.faces.new(f0)
    bm.faces.new(f1[::-1])
    for k in range(len(pts)):
        bm.faces.new((f0[k], f0[(k + 1) % len(pts)], f1[(k + 1) % len(pts)], f1[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    star = link("Box | Star", bm)
    bevel(star, 0.25, 2)

    # lid: thin slab with gold edges; card under it with a thumb notch on the right
    lid = block("Box | Lid", -a, a, -a, a, zl, H)
    bm = bmesh.new()  # split the edges where the gold trim starts
    bm.from_mesh(lid.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, (H - g["lid_trim"]) * MM), plane_no=(0, 0, 1))
    bm.to_mesh(lid.data)
    bm.free()
    bevel(lid, 0.4, 2)
    ch, ct = g["card_half"], g["card_thickness"]
    card = block("Box | Card", -ch, ch, -ch, ch, zl - ct, zl + 0.5)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=g["card_notch_radius"] * MM,
                          radius2=g["card_notch_radius"] * MM, depth=10 * MM)
    bm.transform(Matrix.Translation(Vector((ch, 0, zl)) * MM))
    boolean(card, link("cut", bm), "DIFFERENCE")
    bevel(card, 0.3, 2)

    # card lettering in gold foil, reading upright when the lid stands open (up = towards the front edge): either set text
    # in a font (card_text: text, font, width) or the house wordmark SVG
    def set_text(t):
        """Gold foil lettering set in a font (t: text, font, width mm): a mesh centred on the origin in the XY plane, +y up."""
        font = Path(t["font"])
        assert font.exists(), "font not found: %s" % font
        cu = bpy.data.curves.new("lettering", "FONT")
        cu.body, cu.font = t["text"], bpy.data.fonts.load(str(font))
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.extrude = g["wordmark_thickness"] / 2 * MM
        tmp = bpy.data.objects.new("lettering", cu)
        scene.collection.objects.link(tmp)
        bpy.context.view_layer.update()
        me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        bpy.data.objects.remove(tmp)
        bpy.data.curves.remove(cu)
        xs = [v.co.x for v in me.vertices]
        ys = [v.co.y for v in me.vertices]
        k = t["width"] * MM / (max(xs) - min(xs))
        me.transform(Matrix.Diagonal((k, k, 1, 1)) @ Matrix.Translation(Vector((-(max(xs) + min(xs)) / 2, -(max(ys) + min(ys)) / 2, 0))))
        return me

    ctext = g.get("card_text")
    if ctext:
        me = set_text(ctext)
    else:
        subpaths = parse_svg((ROOT / spec["wordmark_svg"]).read_text())
        xs = [q[0] for sp in subpaths for seg in sp for q in seg]
        ys = [q[1] for sp in subpaths for seg in sp for q in seg]
        k = g["wordmark_width"] / (max(xs) - min(xs))
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        cu = bpy.data.curves.new("Box | Wordmark", "CURVE")
        cu.dimensions, cu.fill_mode, cu.extrude = "2D", "BOTH", g["wordmark_thickness"] / 2 * MM
        for segs in subpaths:
            spl = cu.splines.new("BEZIER")
            spl.bezier_points.add(len(segs) - 1)
            spl.use_cyclic_u = True
            for i, (p0, c1, c2, p1) in enumerate(segs):
                bpt, nxt = spl.bezier_points[i], spl.bezier_points[(i + 1) % len(segs)]
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
    face = zl - ct - 0.01 - g["wordmark_thickness"] / 2
    wordmark.data.transform(Matrix.Translation(Vector((0, 0, face)) * MM) @ Matrix.Rotation(math.pi, 4, "X"))
    lid_group = [lid, card, wordmark]

    # optional lettering on the lid's outer top, reading upright from the front of the closed box
    if g.get("lid_text"):
        mark = bpy.data.objects.new("Box | Lid mark", set_text(g["lid_text"]))
        scene.collection.objects.link(mark)
        mark.data.transform(Matrix.Translation(Vector((0, g["lid_text"].get("y", 0.0), H + 0.01 + g["wordmark_thickness"] / 2)) * MM))
        lid_group.append(mark)
    base_group = [base, star, liner]
    parts = lid_group + base_group

    # metric UVs (dominant-axis projection), smooth bevels with flat faces
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
        o.data.set_sharp_from_angle(angle=math.radians(2))  # keep every facet crisp
        wn = o.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
        wn.mode, wn.keep_sharp = "FACE_AREA", True
        bake(o, wn)

    # glTF-safe stand-ins; renders swap in the library look and Select | interior
    ms = spec["materials"]
    swatch = bpy.data.images.load(str(ROOT / ms["swatch"])) if ms.get("swatch") else None  # optional colour map on the cloth
    if swatch:
        swatch.pack()
    mats = {}
    for role in ("exterior", "accent", "card", "gold"):
        mat = mats[role] = bpy.data.materials.new("Facet Star | " + role)
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*ms[role]["color_linear"], 1)
        bsdf.inputs["Roughness"].default_value = ms[role]["roughness"]
        bsdf.inputs["Metallic"].default_value = ms[role].get("metallic", 0.0)
        if role == "exterior" and swatch:
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
    for o in parts:
        o.data.materials.clear()  # boolean bakes leave an empty first slot that would shift every index
    for m in ("exterior", "accent"):
        base.data.materials.append(mats[m])
    for f in base.data.polygons:  # lining: every face inside the cavity
        f.material_index = 1 if all(abs(base.data.vertices[i].co.x) < (a - w + t) * MM and abs(base.data.vertices[i].co.y) < (a - w + t) * MM
                                    and base.data.vertices[i].co.z > (g["base_floor"] - t) * MM for i in f.vertices) else 0
    for m in ("exterior", "accent", "gold"):
        lid.data.materials.append(mats[m])
    for f in lid.data.polygons:  # cloth on top and the lower edge, lining underneath, gold on the upper lid_trim of the edge
        f.material_index = 1 if f.normal.z < -0.7 else 2 if f.normal.z <= 0.7 and f.center.z > (H - g["lid_trim"]) * MM else 0
    card.data.materials.append(mats["card"])
    liner.data.materials.append(mats["accent"])
    for o in [star, wordmark] + [o for o in lid_group if o.name == "Box | Lid mark"]:
        o.data.materials.append(mats["gold"])
    assert sum(f.material_index for f in base.data.polygons), "base has no lining faces"

    # lid group: origin on the hinge (back edge of the seam), one shared rotation action
    hinge = Vector((0, a, zb + g["seam_gap"] / 2)) * MM
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
    action = bpy.data.actions.new("Lid open")
    for o in lid_group:
        o.animation_data_create().action = action
        for frame, deg in ((1, 0.0), (anim["frames"], anim["open_deg"])):
            o.rotation_quaternion = Quaternion((1, 0, 0), -math.radians(deg))  # front edge up, swinging back over the hinge
            o.keyframe_insert("rotation_quaternion", frame=frame)
    scene.frame_start, scene.frame_end = 1, anim["frames"]

    # house scene: black world, Standard view
    world = scene.world or bpy.data.worlds.new("World")
    scene.world, world.use_nodes = world, True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0, 0, 0, 1), 0
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = spec["scene"]["view_transform"]
    scene.view_settings.exposure = spec["scene"]["exposure"]

    # self-check: watertight solids; the lid group never meets the base group, closed or opening; closed = the cube
    summary = {}
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_edges = sum(not e.is_manifold for e in bm.edges)
        assert o is wordmark or o.name == "Box | Lid mark" or open_edges == 0, "%s has %d non-manifold edges" % (o.name, open_edges)
        summary[o.name] = {"faces": len(bm.faces), "dims_mm": [round(dd / MM, 2) for dd in o.dimensions]}
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
    co = [o.matrix_world @ v.co for o in (base, lid) for v in o.data.vertices]
    span = [round((max(c[i] for c in co) - min(c[i] for c in co)) / MM, 2) for i in range(3)]
    assert all(abs(x - want) < 0.05 for x, want in zip(span, (size, size, H))), "closed box is %s mm" % span
    return {"parts": summary, "closed_mm": span}
