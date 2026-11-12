"""box_arc_band: build the 13 Arc Band cube box in an empty scene.

Params: spec (config/presets/box_arc_band.json, millimetres). Scene units are metres.
`Box | Lid` is the top lid_height plus a shield-shaped front flap bounded by the two upper ribbons; it carries `Box | Band`
(gold band round its top edge), `Box | Ribbons lid` (the upper ribbons, the flap's gold edge), `Box | Plate` and `Box | Plate text`,
is hinged on the back edge of the seam and carries the `Lid open` action. `Box | Base` (velvet-lined compartment) keeps
`Box | Band base` (the same band round the bottom edge) and `Box | Ribbons` (the lower ribbons, bottom corners to the plate). `CTRL | Base` / `CTRL | Lid lift-off` hold the groups.
Fails if a solid is not watertight, the closed box is not size on every axis, or the lid meets the base while opening.
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

    def link(name, bm):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        scene.collection.objects.link(o)
        return o

    def bake(o, mod):
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        old, o.data = o.data, me
        o.modifiers.remove(mod)
        bpy.data.meshes.remove(old)

    def bevel(o, width, segments, angle=30):
        m = o.modifiers.new("Edge radius", "BEVEL")
        m.width, m.segments, m.limit_method, m.use_clamp_overlap = width * MM, segments, "ANGLE", True
        m.angle_limit = math.radians(angle)
        bake(o, m)

    def prism_xz(name, pts, y0, y1):
        """Closed prism over the XZ polygon `pts` (mm), from y0 to y1."""
        bm = bmesh.new()
        f0 = [bm.verts.new((x * MM, y0 * MM, z * MM)) for x, z in pts]
        f1 = [bm.verts.new((x * MM, y1 * MM, z * MM)) for x, z in pts]
        bm.faces.new(f0)
        bm.faces.new(f1[::-1])
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((f0[i], f0[j], f1[j], f1[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return link(name, bm)

    # body: the closed cube with soft cloth edges
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size * MM)
    bm.transform(Matrix.Translation(Vector((0, 0, a)) * MM))
    body = link("Box | Body", bm)
    bevel(body, g["edge_radius"], g["edge_segments"])

    # ribbons: cubic curves on the front face (x, z), corner to nameplate, as flat strips standing ribbon_proud off the cloth
    pw, ph, pt = g["plate"]
    zc = g["plate_center_z"]
    up, lo = g["ribbon_meet"]
    edge = a - g["ribbon_inset"]
    hug = g["ribbon_hug"] * size  # how far the ribbon runs down / up the vertical edge before it turns in

    def bez(p0, c1, c2, p3, t):
        s = 1 - t
        return p0 * s ** 3 + c1 * 3 * s * s * t + c2 * 3 * s * t * t + p3 * t ** 3
    def curve_pts(p0, c1, c2, p3, n):
        return [bez(p0, c1, c2, p3, i / n) for i in range(n + 1)]
    n, hw = g["ribbon_samples"], g["ribbon_width"] / 2
    mid = lambda sx: Vector((sx * (pw / 2 + 0.45 * (edge - pw / 2)), 0))
    upper, lower = {}, {}
    for sx in (-1, 1):
        x_edge = sx * edge
        # upper ribbon, corner -> plate: it is also the edge of the lid's front flap, so it runs to the plate's middle
        upper[sx] = curve_pts(Vector((x_edge, size - g["ribbon_inset"])), Vector((x_edge, size - hug)),
                              mid(sx) + Vector((0, zc + up)), Vector((sx * (pw / 2 - 0.5), zc + up)), n)
        # lower ribbon, corner -> plate side: on the base, it stops just short of the plate (which lifts with the lid)
        lower[sx] = curve_pts(Vector((x_edge, g["ribbon_inset"])), Vector((x_edge, hug)),
                              mid(sx) + Vector((0, zc + lo)), Vector((sx * (pw / 2 + 0.3), zc + lo)), n)

    def strip(name, pts, hw=hw, y0=-a - g["ribbon_proud"], y1=-a - 0.02):  # default: stands just off the cloth, lid and base parts never touch
        left, right, m = [], [], len(pts) - 1
        for i, p in enumerate(pts):
            d = (pts[min(i + 1, m)] - pts[max(i - 1, 0)]).normalized()
            nrm = Vector((-d.y, d.x)) * hw
            left.append(tuple(p + nrm))
            right.append(tuple(p - nrm))
        return prism_xz(name, left + right[::-1], y0, y1)

    def block(name, x0, x1, y0, y1, z0, z1):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            v.co = (((x0 + x1) / 2 + v.co.x * (x1 - x0)) * MM, ((y0 + y1) / 2 + v.co.y * (y1 - y0)) * MM,
                    ((z0 + z1) / 2 + v.co.z * (z1 - z0)) * MM)
        return link(name, bm)

    def boolean(o, cutter, op, self_=False):
        m = o.modifiers.new("Cut", "BOOLEAN")
        m.operation, m.solver, m.object, m.use_self = op, "EXACT", cutter, self_
        bake(o, m)
        bpy.data.meshes.remove(cutter.data)

    def joined(name, parts_):
        o = parts_[0]
        for q in parts_[1:]:
            boolean(o, q, "UNION")
        o.name = o.data.name = name
        bevel(o, 0.35, 2, angle=60)
        return o
    # v014 relief: shallow recesses on the front (x, z) whose soft steps draw the arcs; "faces" also repeats a recess on the
    # left and top faces by the 3-fold turn about the front-left-top corner, so one band runs on round three faces
    turn = Matrix.Translation(Vector((0, 0, a)) * MM) @ Matrix(((0, 1, 0, 0), (0, 0, -1, 0), (-1, 0, 0, 0), (0, 0, 0, 1))) @ Matrix.Translation(Vector((0, 0, -a)) * MM)
    A = a * MM
    faces_m = {"front": Matrix(), "left": turn, "top": turn @ turn,  # right / back: the front pattern turned about z
               "right": Matrix.Rotation(math.pi / 2, 4, "Z"), "back": Matrix.Rotation(math.pi, 4, "Z"),
               # v016: each side the mirror of its neighbour across their shared edge, so every arc meets its partner there
               "mirror_right": Matrix(((0, -1, 0, 0), (-1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))),
               "mirror_left": Matrix(((0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))),
               # top_xy: the curve's (u, v) read as (x, y + a) on the top, depth downward
               "top_xy": Matrix(((1, 0, 0, 0), (0, 0, 1, -A), (0, -1, 0, A), (0, 0, 0, 1)))}
    rel = g.get("relief")
    if rel:
        for rc in rel["recesses"]:
            # the recess lies right of the walk; its wall is a ramp ramp_mm wide, so the step shades softly instead of a dark groove
            pts = [q for k, seg in enumerate(rc["bezier"]) for q in curve_pts(*map(Vector, seg), n)[k > 0:]]
            if (pts[-1] - pts[0]).length < 1e-6:  # a closed outline (no close points)
                pts.pop()
            dep, m = rc["depth"], len(pts) - 1
            grow = rc["ramp_mm"] * (dep + 1) / dep  # the cutter's front ring sits 1 mm in front of the cloth
            nrm = [(lambda d: Vector((-d.y, d.x)))((pts[min(i + 1, m)] - pts[max(i - 1, 0)]).normalized()) for i in range(m + 1)]
            rings = [[q.to_tuple() for q in pts] + [tuple(c) for c in rc["close"]],
                     [(q + v * grow).to_tuple() for q, v in zip(pts, nrm)] + [tuple(c) for c in rc["close"]]]
            for face in rc["faces"]:
                bm = bmesh.new()
                r0 = [bm.verts.new((x * MM, (-a + dep) * MM, z * MM)) for x, z in rings[0]]
                r1 = [bm.verts.new((x * MM, (-a - 1) * MM, z * MM)) for x, z in rings[1]]
                bm.faces.new(r0)
                bm.faces.new(r1[::-1])
                for i in range(len(r0)):
                    j = (i + 1) % len(r0)
                    bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
                bm.transform(faces_m[face])
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)  # after the transform: the mirrors flip the winding
                boolean(body, link("cut", bm), "DIFFERENCE")
    trim = g.get("gold_trim", True)  # false: no ribbons, bands or bridge; the flap seam stays, the plate sits just off the cloth
    ribbons_lid = ribbons = band = band_base = None
    if trim:
        ribbons_lid = joined("Box | Ribbons lid", [strip("ribbon", upper[-1]), strip("ribbon", upper[1])])
        bridge = prism_xz("ribbon", [(-(pw / 2 + 0.6), zc + lo - hw), (pw / 2 + 0.6, zc + lo - hw), (pw / 2 + 0.6, zc + lo + hw), (-(pw / 2 + 0.6), zc + lo + hw)],
                          -a - g["ribbon_proud"], -a - 0.02)  # joins the lower ribbons behind the plate, so they stay one line when the lid lifts
        ribbons = joined("Box | Ribbons", [strip("ribbon", lower[-1]), strip("ribbon", lower[1]), bridge])

    # lid = the top lid_height plus a front flap shaped like a shield: everything on the front above the upper ribbons
    # (their centre lines are the flap edge, the ribbons cover the seam). Offset half the gap each way so the parts never touch.
    seam, gap, w = size - g["lid_height"], g["seam_gap"], g["wall"]
    # v013: the flap edge is one free curve (cubic segments, left corner -> right edge) instead of the ribbon shield
    seam_pts = [q for k, seg in enumerate(g.get("seam_bezier") or []) for q in curve_pts(*map(Vector, seg), n)[k > 0:]]

    def lid_region(off):
        """Solid: z above the seam, plus the front wall inside the shield; off > 0 shrinks it (lid), < 0 grows it (base cut)."""
        top = block("cut", -a - 10, a + 10, -a - 10, a + 10, seam + off, size + 10)
        if not g.get("front_flap", True):  # v015: a plain lid, the seam runs straight round at lid_height
            return top
        outline = []
        for pts in [seam_pts] if seam_pts else [upper[-1], upper[1][::-1]]:  # walk left -> right
            m = len(pts) - 1
            for i, p in enumerate(pts):
                d = (pts[min(i + 1, m)] - pts[max(i - 1, 0)]).normalized()
                outline.append(tuple(p + Vector((-d.y, d.x)) * off))  # +normal points into the shield on both walks
        outline += [(outline[-1][0], size + 10), (outline[0][0], size + 10)]
        flap = prism_xz("cut", outline, -a - 10, -a + w + 1 - off)  # the gap also on the inner face, inside the side walls
        boolean(top, flap, "UNION")
        return top
    lid = body.copy()
    lid.data = body.data.copy()
    scene.collection.objects.link(lid)
    lid.name = lid.data.name = "Box | Lid"
    boolean(lid, lid_region(gap / 2), "INTERSECT")
    boolean(lid, block("cut", -a + w, a - w, -a + w, a - w, seam - 5, size - g["lid_top"]), "DIFFERENCE")
    body.name = body.data.name = "Box | Base"
    base = body
    boolean(base, lid_region(-gap / 2), "DIFFERENCE")
    boolean(base, block("cut", -a + w, a - w, -a + w, a - w, g["base_floor"], size + 5), "DIFFERENCE")
    for gr in g.get("grooves", []):  # tone-on-tone panel lines cut into the base front; they run out through the soft edges
        pts = [q for k, seg in enumerate(gr["bezier"]) for q in curve_pts(*map(Vector, seg), n)[k > 0:]]
        boolean(base, strip("cut", pts, gr["width"] / 2, -a - 1, -a + gr["depth"]), "DIFFERENCE")

    # gold band round the lid's top edge, the same section as the ribbons, so the ribbons run into it at the front corners
    bp, bh = g["ribbon_proud"], g["ribbon_width"]
    if trim:
        band = block("Box | Band", -a - bp, a + bp, -a - bp, a + bp, size - bh, size)
        boolean(band, block("cut", -a + 0.6, a - 0.6, -a + 0.6, a - 0.6, size - bh - 1, size + 1), "DIFFERENCE")
        bevel(band, 0.35, 2, angle=60)
        band_base = block("Box | Band base", -a - bp, a + bp, -a - bp, a + bp, 0, bh)  # the same band round the bottom edge, joined to the lower ribbons
        boolean(band_base, block("cut", -a + 0.6, a - 0.6, -a + 0.6, a - 0.6, -1, bh + 1), "DIFFERENCE")
        bevel(band_base, 0.35, 2, angle=60)

    # nameplate: rounded gold bar standing off the front, the ribbons tucked under its sides
    deboss = g.get("wordmark_deboss")
    owner = lid if g.get("front_flap", True) else base  # the part the debossed wordmark is cut into  # mm: no plate, Perhaps. is pressed into the flap cloth
    plate = text = None
    r = g["plate_radius"]
    outline = []
    for cx, cz, a0 in ((pw / 2 - r, zc + ph / 2 - r, 0), (-pw / 2 + r, zc + ph / 2 - r, 90), (-pw / 2 + r, zc - ph / 2 + r, 180), (pw / 2 - r, zc - ph / 2 + r, 270)):
        for k in range(9):
            t = math.radians(a0 + k * 90 / 8)
            outline.append((cx + r * math.cos(t), cz + r * math.sin(t)))
    stand = (g["ribbon_proud"] if trim else 0) + 0.05  # the plate stands off the cloth over the ribbons (and the bridge behind it)
    if not deboss:
        plate = prism_xz("Box | Plate", outline, -a - stand - pt, -a - stand)  # on the flap, lifts with the lid
        bevel(plate, 0.8, 4, angle=60)

    # print: Perhaps. in a dark serif on the plate face
    t = g["plate_text"]
    font = Path(t["font"])
    assert font.exists(), "font not found: %s" % font
    cu = bpy.data.curves.new("plate text", "FONT")
    cu.body, cu.font = t["text"], bpy.data.fonts.load(str(font))
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.fill_mode = "BOTH"
    depth = deboss + 1 if deboss else g["text_thickness"]  # a deboss cutter starts 1 mm in front of the cloth
    cu.extrude = depth / 2 * MM
    tmp = bpy.data.objects.new("plate text", cu)
    scene.collection.objects.link(tmp)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    xs, ys = [v.co.x for v in me.vertices], [v.co.y for v in me.vertices]
    k = t["width"] * MM / (max(xs) - min(xs))
    me.transform(Matrix.Diagonal((k, k, 1, 1)) @ Matrix.Translation(Vector((-(max(xs) + min(xs)) / 2, -(max(ys) + min(ys)) / 2, 0))))
    # face the front: text up -> +z, its normal -> -y; sit on the plate face
    wm = (t.get("x", 0), zc, t["width"] / 2 + 0.5, (max(ys) - min(ys)) * k / MM / 2 + 0.5)  # x, z, half sizes (mm) round the letters
    y = -a - 1 + depth / 2 if deboss else -a - stand - pt - 0.01 - depth / 2
    me.transform(Matrix.Translation(Vector((t.get("x", 0), y, zc)) * MM) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    if deboss:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)  # glyph conversion leaves split seams
        bm.to_mesh(me)
        bm.free()
        cutter = bpy.data.objects.new("cut", me)
        scene.collection.objects.link(cutter)
        boolean(owner, cutter, "DIFFERENCE")
    else:
        text = bpy.data.objects.new("Box | Plate text", me)
        scene.collection.objects.link(text)

    lid_group = [o for o in (lid, band, ribbons_lid, plate, text) if o]
    base_group = [o for o in (base, ribbons, band_base) if o]
    parts = lid_group + base_group
    rr = g["edge_radius"]
    L, C = 2 * (a - rr), rr * math.pi / 2
    P = 4 * L + 4 * C

    def wrap_u(x, y):
        """Arc length (mm) round the rounded-square outline, so the cloth runs on unbroken round the vertical edges;
        the start (the one seam) sits mid-back."""
        h = a - rr
        if abs(x) <= h:
            s = x + h if y < 0 else 2 * L + 2 * C + (h - x)
        elif abs(y) <= h:
            s = L + C + (y + h) if x > 0 else 3 * L + 3 * C + (h - y)
        else:
            t = math.atan2(y - math.copysign(h, y), x - math.copysign(h, x)) % (2 * math.pi)
            if x > 0 and y < 0:
                s = L + rr * (t - 1.5 * math.pi)
            elif x > 0:
                s = 2 * L + C + rr * t
            elif y > 0:
                s = 3 * L + 2 * C + rr * (t - 0.5 * math.pi)
            else:
                s = 4 * L + 3 * C + rr * (t - math.pi)
        return (s - (2 * L + 2 * C + L / 2)) % P

    for o in parts:  # metric UVs (dominant-axis projection; the cloth sides wrapped round), smooth bevels with flat faces
        bm = bmesh.new()
        bm.from_mesh(o.data)
        uv = bm.loops.layers.uv.new("Metric UV")
        for f in bm.faces:
            if o in (lid, base) and abs(f.normal.z) < 0.7:
                us = [wrap_u(l.vert.co.x / MM, l.vert.co.y / MM) for l in f.loops]
                if max(us) - min(us) > P / 2:  # the face straddles the seam: keep it on one side
                    us = [u + P if u < P / 2 else u for u in us]
                for l, u_mm in zip(f.loops, us):
                    l[uv].uv = (u_mm * MM, l.vert.co.z)
                continue
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

    ms = spec["materials"]
    mats = {}
    for role in ("exterior", "accent", "gold", "ink"):
        mat = mats[role] = bpy.data.materials.new("Arc Band | " + role)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*ms[role]["color_linear"], 1)
        bsdf.inputs["Roughness"].default_value = ms[role]["roughness"]
        bsdf.inputs["Metallic"].default_value = ms[role].get("metallic", 0.0)
        if role == "exterior" and ms.get("swatch"):  # cloth colour (and normal) maps on the metric UVs, for the GLB
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            uvn = nodes.new("ShaderNodeUVMap")
            uvn.uv_map = "Metric UV"
            mp = nodes.new("ShaderNodeMapping")
            links.new(uvn.outputs["UV"], mp.inputs["Vector"])
            for key in ("swatch", "swatch_normal"):
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
                if key == "swatch_normal":
                    nm = nodes.new("ShaderNodeNormalMap")
                    links.new(tex.outputs["Color"], nm.inputs["Color"])
                    links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
                else:
                    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    for o, role in ((o, r) for o, r in ((ribbons, "gold"), (ribbons_lid, "gold"), (band, "gold"), (band_base, "gold"), (plate, "gold"), (text, "ink")) if o):
        o.data.materials.clear()
        o.data.materials.append(mats[role])
    t = 0.01
    inside = {lid: lambda q: abs(q.x) < (a - w + t) * MM and abs(q.y) < (a - w + t) * MM and q.z < (size - g["lid_top"] + t) * MM,
              base: lambda q: abs(q.x) < (a - w + t) * MM and abs(q.y) < (a - w + t) * MM and q.z > (g["base_floor"] - t) * MM}
    for o in (lid, base):  # cloth outside, velvet on every face inside the compartment or under the lid
        o.data.materials.clear()
        o.data.materials.append(mats["exterior"])
        o.data.materials.append(mats["accent"])
        for f in o.data.polygons:
            f.material_index = 1 if all(inside[o](o.data.vertices[i].co) for i in f.vertices) else 0
    if deboss and g.get("wordmark_ink"):  # letter walls and floors (a vertex within 0.25 mm of the floor) take the darker ink
        owner.data.materials.append(mats["ink"])
        vs = owner.data.vertices
        for f in owner.data.polygons:
            co = [vs[i].co / MM for i in f.vertices]
            if (all(abs(c.x - wm[0]) < wm[2] and abs(c.z - wm[1]) < wm[3] and c.y < -a + w - 0.5 for c in co)
                    and max(c.y for c in co) > -a + deboss - 0.25):
                f.material_index = 2
        assert any(f.material_index == 2 for f in owner.data.polygons), "no wordmark faces found"
    assert all(sum(f.material_index for f in o.data.polygons) for o in (lid, base)), "lining faces missing"

    ctrl = {}
    for name in ("CTRL | Base", "CTRL | Lid lift-off"):
        ctrl[name] = bpy.data.objects.new(name, None)
        scene.collection.objects.link(ctrl[name])
    hinge = Vector((0, a, seam)) * MM  # back edge of the seam
    for o in lid_group:
        o.data.transform(Matrix.Translation(-hinge))
        o.location = hinge
        o.rotation_mode = "QUATERNION"
    for o in parts:
        o.parent = ctrl["CTRL | Lid lift-off" if o in lid_group else "CTRL | Base"]
        o["export_product"] = True
    anim = spec["lid_animation"]
    action = bpy.data.actions.new("Lid open")
    for o in lid_group:
        o.animation_data_create().action = action
        for frame, deg in ((1, 0.0), (anim["frames"], anim["open_deg"])):
            o.rotation_quaternion = Quaternion((1, 0, 0), -math.radians(deg))  # front edge up, swinging back on the hinge
            o.keyframe_insert("rotation_quaternion", frame=frame)
    scene.frame_start, scene.frame_end = 1, anim["frames"]

    world = scene.world or bpy.data.worlds.new("World")
    scene.world, world.use_nodes = world, True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0, 0, 0, 1), 0
    scene.render.engine = "CYCLES"
    scene.view_settings.view_transform = spec["scene"]["view_transform"]
    scene.view_settings.exposure = spec["scene"]["exposure"]

    summary = {}
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        open_edges = sum(not e.is_manifold for e in bm.edges)
        assert o is text or open_edges == 0, "%s has %d non-manifold edges" % (o.name, open_edges)
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
    co = [o.matrix_world @ v.co for o in (lid, base) for v in o.data.vertices]
    span = [round((max(c[i] for c in co) - min(c[i] for c in co)) / MM, 2) for i in range(3)]
    assert all(abs(x - size) < 0.05 for x in span), "closed box is %s mm" % span
    return {"parts": summary, "closed_mm": span}
