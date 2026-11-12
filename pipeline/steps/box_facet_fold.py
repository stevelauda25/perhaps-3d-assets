"""box_facet_fold: build the 12 Facet Fold cube box (two-part folding lid) in an empty scene.

Params: spec (config/presets/box_facet_fold.json, millimetres). Scene units are metres. Closed (frame 1) it is size x size x height.
Base group (never moves): `Box | Base` (faceted sides and back, recessed front wall), `Box | Liner`, optional `Box | Cushion`.
Lid: `Box | Top` hinged on the top back edge, carrying `Box | Card`, `Box | Card text`, `Box | Top text` (same origin and action);
`Box | Front` (faceted, the closed front face) is a child of `Box | Top` at the top front edge, held at 90 deg (the folded
cover flap), with `Box | Star` as its child. One `Lid open` action swings the whole L on the back hinge (reference video).
Fails if a solid is not watertight or any lid part meets the base at any frame.
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
    size, a = g["size"], g["size"] / 2
    H = g.get("height", size)  # closed height; the footprint is size x size
    tt, tf, gap, w = g["top_thickness"], g["front_thickness"], g["gap"], g["wall"]
    zt = H - tt             # underside of the top panel
    zb = zt - gap           # base top
    yb = -a + tf + gap      # base front face, behind the front panel

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

    cols, rows = g["facet_grid"]
    d = g["facet_depth"]

    def faceted(name, x0, x1, y0, y1, z0, z1, facet_sides):
        """Closed box solid; each side named in facet_sides is a cols x rows grid of inverted pyramids (cell edges on the
        side plane, centres facet_depth in), the others are flat but split into the same rows so the mesh stays manifold."""
        sides = {  # walked counter-clockwise seen from above: start, end, inward normal
            "front": (Vector((x0, y0, 0)), Vector((x1, y0, 0)), Vector((0, 1, 0))),
            "right": (Vector((x1, y0, 0)), Vector((x1, y1, 0)), Vector((-1, 0, 0))),
            "back": (Vector((x1, y1, 0)), Vector((x0, y1, 0)), Vector((0, -1, 0))),
            "left": (Vector((x0, y1, 0)), Vector((x0, y0, 0)), Vector((1, 0, 0))),
        }
        bm = bmesh.new()
        cache = {}

        def vert(p):
            key = tuple(round(c, 4) for c in p)  # mathutils is float32: 1e-4 mm merges corners reached along two sides
            if key not in cache:
                cache[key] = bm.verts.new(p * MM)
            return cache[key]
        zs = [z0 + j * (z1 - z0) / rows for j in range(rows + 1)]
        ring = []
        for side in ("front", "right", "back", "left"):
            p0, p1, inward = sides[side]
            n = cols if side in facet_sides else 1
            us = [p0 + (p1 - p0) * i / n for i in range(n + 1)]
            ring += us[:-1]
            for i in range(n):
                for j in range(rows):
                    c = [us[i] + Vector((0, 0, zs[j])), us[i + 1] + Vector((0, 0, zs[j])),
                         us[i + 1] + Vector((0, 0, zs[j + 1])), us[i] + Vector((0, 0, zs[j + 1]))]
                    if side in facet_sides:
                        apex = vert((c[0] + c[2]) / 2 + inward * d)
                        for k in range(4):
                            bm.faces.new((vert(c[k]), vert(c[(k + 1) % 4]), apex))
                    else:
                        bm.faces.new([vert(p) for p in c])
        bm.faces.new([vert(p + Vector((0, 0, z0))) for p in ring])
        bm.faces.new([vert(p + Vector((0, 0, z1))) for p in ring])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = link(name, bm)
        bevel(o, g["edge_radius"], g["edge_segments"])
        return o

    # base: stationary floor and four faceted walls; the front wall sits back behind the front flap
    base = faceted("Box | Base", -a, a, yb, a, 0, zb, {"front", "right", "back", "left"} if d > 0 else set())
    ox0, ox1, oy0, oy1 = -a + w, a - w, yb + w, a - w  # compartment opening
    boolean(base, block("cut", ox0, ox1, oy0, oy1, g["base_floor"], H + 5), "DIFFERENCE")
    lb = g["liner_border"]
    liner = block("Box | Liner", ox0 + 0.05, ox1 - 0.05, oy0 + 0.05, oy1 - 0.05, g["base_floor"] + 0.05, zb - g["liner_drop"])
    bevel(liner, g["liner_radius"], 4)
    boolean(liner, block("cut", ox0 + lb, ox1 - lb, oy0 + lb, oy1 - lb, g["base_floor"] + 1.5, H + 5), "DIFFERENCE")
    cush = g.get("cushion")  # optional fitted presentation cushion in the liner well, rounded like a pillow
    if cush:
        c0 = lb + cush["clearance"]
        cushion = block("Box | Cushion", ox0 + c0, ox1 - c0, oy0 + c0, oy1 - c0, g["base_floor"] + 1.5 + cush["clearance"], zb - g["liner_drop"] - cush["below_liner_top"])
        bevel(cushion, cush["radius"], cush["segments"])

    # top panel: the closed top behind the front panel; gold on the upper top_trim of its edges
    top = block("Box | Top", -a, a, -a + tf, a, zt, H)
    trim = g.get("top_trim")  # optional gold on the upper part of the top panel's edges
    if trim:
        bm = bmesh.new()
        bm.from_mesh(top.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, (H - trim) * MM), plane_no=(0, 0, 1))
        bm.to_mesh(top.data)
        bm.free()
    bevel(top, 0.4, 2)

    # front panel: the whole closed front face, faceted, with the star on its centre crossing
    front = faceted("Box | Front", -a, a, -a, -a + tf, 0, H, {"front"} if d > 0 else set())  # facet_depth 0 = plain sides
    s = g["star"]
    pts = []
    for i in range(96):  # sparkle outline |x|^p + |z|^p = tip^p
        t = 2 * math.pi * i / 96
        cx_, cz_ = math.cos(t), math.sin(t)
        pts.append((s["tip"] * math.copysign(abs(cx_) ** (2 / s["power"]), cx_), H / 2 + s["tip"] * math.copysign(abs(cz_) ** (2 / s["power"]), cz_)))
    # chamfer by scaling the face ring toward the centre: a bevel modifier folds the sub-0.3 mm tips inside out
    bv, th, n = s.get("bevel", 0.25), s["thickness"], len(pts)
    kc = 1 - 2 * bv / s["tip"]
    bm = bmesh.new()
    f0 = [bm.verts.new((x * kc * MM, (-a - th) * MM, (H / 2 + (z - H / 2) * kc) * MM)) for x, z in pts]
    f1 = [bm.verts.new((x * MM, (-a - th + min(bv, th / 2)) * MM, z * MM)) for x, z in pts]
    f2 = [bm.verts.new((x * MM, -a * MM, z * MM)) for x, z in pts]
    for ring, y in ((f0, -a - th), (f2, -a)):  # caps as fans from the centre: one concave 96-gon triangulates into overlapping slivers in the GLB
        c = bm.verts.new((0, y * MM, H / 2 * MM))
        for k in range(n):
            bm.faces.new((c, ring[k], ring[(k + 1) % n]))
    for ra, rb in ((f0, f1), (f1, f2)):
        for k in range(n):
            bm.faces.new((ra[k], ra[(k + 1) % n], rb[(k + 1) % n], rb[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    star = link("Box | Star", bm)

    # card under the top panel, centred on the compartment opening, thumb notch on the right
    ccx, ccy = 0.0, (oy0 + oy1) / 2
    ch = min(ox1 - ox0, oy1 - oy0) / 2 - g["card_margin"]
    ct = g["card_thickness"]
    card = block("Box | Card", ccx - ch, ccx + ch, ccy - ch, ccy + ch, zt - ct, zt + 0.5)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=g["card_notch_radius"] * MM, radius2=g["card_notch_radius"] * MM, depth=10 * MM)
    bm.transform(Matrix.Translation(Vector((ccx + ch, ccy, zt)) * MM))
    boolean(card, link("cut", bm), "DIFFERENCE")
    bevel(card, 0.3, 2)

    def lettering(name, t):
        """Gold set in a font (t: text, font, width mm, optional thickness / bevel mm for a raised emboss), centred on the origin in the XY plane, +y up."""
        font = Path(t["font"])
        assert font.exists(), "font not found: %s" % font
        cu = bpy.data.curves.new(name, "FONT")
        cu.body, cu.font = t["text"], bpy.data.fonts.load(str(font))
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        th, bv = t.get("thickness", g["lettering_thickness"]), t.get("bevel", 0.0)
        assert th / 2 > bv, "bevel must be under half the lettering thickness"
        cu.extrude, cu.bevel_depth, cu.bevel_resolution = (th / 2 - bv) * MM, bv * MM, 2
        tmp = bpy.data.objects.new(name, cu)
        scene.collection.objects.link(tmp)
        bpy.context.view_layer.update()
        me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        bpy.data.objects.remove(tmp)
        bpy.data.curves.remove(cu)
        xs, ys = [v.co.x for v in me.vertices], [v.co.y for v in me.vertices]
        k = t["width"] * MM / (max(xs) - min(xs))
        me.transform(Matrix.Diagonal((k, k, 1, 1)) @ Matrix.Translation(Vector((-(max(xs) + min(xs)) / 2, -(max(ys) + min(ys)) / 2, 0))))
        o = bpy.data.objects.new(name, me)
        scene.collection.objects.link(o)
        return o
    lt = g["lettering_thickness"]
    card_text = lettering("Box | Card text", g["card_text"])  # reads upright when the top panel stands open (up = its front edge)
    card_text.data.transform(Matrix.Translation(Vector((ccx, ccy, zt - ct - 0.01 - lt / 2)) * MM) @ Matrix.Rotation(math.pi, 4, "X"))
    top_text = lettering("Box | Top text", g["top_text"])     # reads upright from the front of the closed box
    top_text.data.transform(Matrix.Translation(Vector((0, (-a + tf + a) / 2, H + 0.01 + g["top_text"].get("thickness", lt) / 2)) * MM))

    top_group = [top, card, card_text, top_text]
    front_group = [front, star]
    base_group = [base, liner] + ([cushion] if cush else [])
    parts = top_group + front_group + base_group

    # metric UVs (dominant-axis projection); keep every facet crisp
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
        o.data.set_sharp_from_angle(angle=math.radians(2))
        wn = o.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
        wn.mode, wn.keep_sharp = "FACE_AREA", True
        bake(o, wn)

    # glTF-safe stand-ins; renders swap in the library look
    ms = spec["materials"]
    mats = {}
    for role in ("exterior", "accent", "card", "gold"):
        mat = mats[role] = bpy.data.materials.new("Facet Fold | " + role)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*ms[role]["color_linear"], 1)
        bsdf.inputs["Roughness"].default_value = ms[role]["roughness"]
        bsdf.inputs["Metallic"].default_value = ms[role].get("metallic", 0.0)
        if role == "exterior" and (ms.get("swatch") or ms.get("swatch_normal")):  # cloth colour and/or normal maps on the metric UVs, for the GLB
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            uvn = nodes.new("ShaderNodeUVMap")
            uvn.uv_map = "Metric UV"
            mp = nodes.new("ShaderNodeMapping")
            links.new(uvn.outputs["UV"], mp.inputs["Vector"])
            for key, socket in (("swatch", "Base Color"), ("swatch_normal", "Normal")):
                if not ms.get(key):
                    continue
                im = bpy.data.images.load(str(ROOT / ms[key]))
                if key == "swatch_normal":
                    im.colorspace_settings.name = "Non-Color"
                im.pack()
                tw = ms["swatch_tile_mm"]
                mp.inputs["Scale"].default_value = (1000 / tw, 1000 / tw * im.size[0] / im.size[1], 1)  # square texels
                tex = nodes.new("ShaderNodeTexImage")
                tex.image = im
                links.new(mp.outputs["Vector"], tex.inputs["Vector"])
                if socket == "Normal":
                    nm = nodes.new("ShaderNodeNormalMap")
                    links.new(tex.outputs["Color"], nm.inputs["Color"])
                    links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
                else:
                    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    t = 0.01
    for o in parts:
        o.data.materials.clear()  # boolean bakes leave an empty first slot that would shift every index
    for m in ("exterior", "accent"):
        base.data.materials.append(mats[m])
    inside = lambda q: ox0 - t < q.x / MM < ox1 + t and oy0 - t < q.y / MM < oy1 + t and q.z / MM > g["base_floor"] - t
    for f in base.data.polygons:
        f.material_index = 1 if all(inside(base.data.vertices[i].co) for i in f.vertices) else 0
    for m in ("exterior", "accent", "gold"):
        top.data.materials.append(mats[m])
    for f in top.data.polygons:  # leather on top and the lower edge, lining underneath, gold on the upper edge
        f.material_index = 1 if f.normal.z < -0.7 else 2 if trim and f.normal.z <= 0.7 and f.center.z > (H - trim) * MM else 0
    front.data.materials.append(mats["exterior"])
    for o in base_group[1:]:  # liner (and cushion)
        o.data.materials.append(mats["accent"])
    card.data.materials.append(mats["card"])
    for o in (star, card_text, top_text):
        o.data.materials.append(mats["gold"])
    assert sum(f.material_index for f in base.data.polygons), "base has no lining faces"

    # hinges: top panel on the top back edge, front panel on the top front edge (child of the top panel)
    back_hinge, fold_hinge = Vector((0, a, H)) * MM, Vector((0, -a, H)) * MM
    for o in top_group:
        o.data.transform(Matrix.Translation(-back_hinge))
        o.location = back_hinge
    for o in front_group:
        o.data.transform(Matrix.Translation(-fold_hinge))
    front.parent, front.matrix_parent_inverse, front.location = top, Matrix.Identity(4), fold_hinge - back_hinge
    star.parent, star.matrix_parent_inverse = front, Matrix.Identity(4)
    for o in top_group:
        o.rotation_mode = "QUATERNION"
    ctrl = {}
    for name in ("CTRL | Base", "CTRL | Lid lift-off"):
        ctrl[name] = bpy.data.objects.new(name, None)
        scene.collection.objects.link(ctrl[name])
    for o in base_group:
        o.parent = ctrl["CTRL | Base"]
    for o in top_group:
        o.parent = ctrl["CTRL | Lid lift-off"]
    for o in parts:
        o["export_product"] = True

    # one action, as in the reference video: the cover is one L (top panel + front flap held at 90 deg) that swings on the
    # back hinge; open, the top panel stands past upright and the front flap becomes a canopy over the box
    anim = spec["lid_animation"]
    end = anim["frames"]
    action = bpy.data.actions.new("Lid open")
    for o in top_group:
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

    # self-check: watertight solids; no lid part meets the base at any frame; closed it is the cube
    summary = {}
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_edges = sum(not e.is_manifold for e in bm.edges)
        assert o in (card_text, top_text) or open_edges == 0, "%s has %d non-manifold edges" % (o.name, open_edges)
        summary[o.name] = {"faces": len(bm.faces), "dims_mm": [round(dd / MM, 2) for dd in o.dimensions]}
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
        for x in top_group + front_group:
            for y in base_group:
                hits = trees[x.name].overlap(trees[y.name])
                assert not hits, "frame %d: %s meets %s (%d triangle pairs)" % (frame, x.name, y.name, len(hits))
    scene.frame_set(1)
    co = [o.matrix_world @ v.co for o in (base, top, front) for v in o.data.vertices]
    span = [round((max(c[i] for c in co) - min(c[i] for c in co)) / MM, 2) for i in range(3)]
    assert all(abs(x - want) < 0.05 for x, want in zip(span, (size, size, H))), "closed box is %s mm" % span
    scene.frame_set(end)
    tip = max((front.matrix_world @ v.co).z for v in front.data.vertices) / MM
    scene.frame_set(1)
    return {"parts": summary, "closed_mm": span, "open_front_tip_mm": round(tip, 1)}
