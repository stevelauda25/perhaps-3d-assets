"""watch_speedmaster_v3: Speedmaster 310.30.42.50.01.001 from traced dimensions, built into the Casio studio base.

Params: spec (config/watches/speedmaster-moonwatch-black-v11.json). Same pose/studio convention as watch_speedmaster (v002,
kept untouched). Differences: case flank, lug outline, crown guards, index/lume sizes, subdial centres, hands and
bracelet link structure come from config/watches/speedmaster-trace.json (pipeline/watch_trace.py); lugs follow the traced
silhouette with a sloped top; links are arched; indices are frame + lume inlay; case chamfer and links get their own
polished/brushed material slots. Materials: `material_for(role)` returns a library material when the spec's
`library_roles` maps the role, else the inline Principled value (kept so the step runs before the library entries exist).
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

from pipeline import subd
from pipeline.steps.watch_speedmaster import Geo, P, ROOT, principled, rect, rot

X_ALONG = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # local (u, v, w) -> (w, u, v)
ARCH = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # local (u, v, w) -> (u, -w, v): extrude along -y


def skin_prism(g, poly, z_bottom, z_top):
    """Prism whose top/bottom heights vary per vertex (z_bottom/z_top are functions of the vertex y)."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    poly = poly if area > 0 else poly[::-1]
    n, base = len(poly), len(g.v)
    g.v += [(x, y, z_bottom(y)) for x, y in poly] + [(x, y, z_top(y)) for x, y in poly]
    g.f.append(tuple(range(base + n - 1, base - 1, -1)))
    g.f.append(tuple(range(base + n, base + 2 * n)))
    g.f += [(base + i, base + (i + 1) % n, base + n + (i + 1) % n, base + n + i) for i in range(n)]
    g.smooth += [False] * (n + 2)


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    trace = json.loads((ROOT / cfg["trace"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Speedmaster 310.30.42.50.01.001 v3")
    scene.collection.children.link(coll)
    roles, lib = params.get("library_roles", {}), {}

    def role_material(key, spec):
        if key not in roles:
            return principled(key, spec)  # inline Principled value (v003 behaviour)
        if roles[key] not in lib:
            from pipeline import material_library, pbr_material
            lib[roles[key]] = pbr_material.build(material_library.load(roles[key]), name=P + roles[key])
        return lib[roles[key]]

    mats = {k: role_material(k, v) for k, v in cfg["materials"].items()}
    parts = {}

    # ---- bracelet loop path (right half, y/z of the centre line), resampled by arc length ----
    b = cfg["bracelet"]
    ctrl = [Vector(p) for p in b["path_yz"]]
    ctrl = [ctrl[0] * 2 - ctrl[1]] + ctrl + [ctrl[-1] * 2 - ctrl[-2]]
    dense = []
    for i in range(1, len(ctrl) - 2):
        p0, p1, p2, p3 = ctrl[i - 1:i + 3]
        for s in range(20):
            t = s / 20
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(ctrl[-2])
    cum = [0.0]
    for a, c in zip(dense, dense[1:]):
        cum.append(cum[-1] + (c - a).length)
    half_len = cum[-1]

    def at(u):
        i = max(k for k in range(len(cum) - 1) if cum[k] <= min(max(u, 0), half_len))
        f = (min(max(u, 0), half_len) - cum[i]) / max(cum[i + 1] - cum[i], 1e-9)
        return dense[i].lerp(dense[i + 1], f), (dense[i + 1] - dense[i]).normalized()

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler = (math.pi / 2, 0, cfg["pose"]["yaw_rad"])
    pose.scale = (0.001,) * 3
    pose.location = (cfg["pose"]["x_m"], 0, cfg["pose"].get("z_m", (max(p.x for p in dense) + b["thickness"] / 2) * 0.001))

    segs = cfg.get("bevel_segments", 2)
    polished = cfg.get("polished_bevel")  # role of the polished slot: bevel faces use it, flat faces keep the part's material

    def add(name, geo, mat, bevel=None, loc=None):
        me = geo.mesh(name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if bevel:
            two = polished and mat == "steel_brushed"
            if two:
                me.materials.append(mats[polished])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, segs, "ANGLE", math.radians(35)
            if two:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if loc:
            o.location = loc
        parts[name] = o
        return o

    sd = cfg.get("subd")  # subdivision-surface rebuild of links, lugs and guards (pipeline/subd.py); absent = v003-v006 prisms

    def subd_mesh(name, data, slots):
        verts, faces, mat_ids = data
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        me.validate()
        me.update()
        assert len(me.polygons) == len(mat_ids), name + ": validate dropped faces"
        me.polygons.foreach_set("use_smooth", [True] * len(mat_ids))
        me.polygons.foreach_set("material_index", mat_ids)
        for m in slots:
            me.materials.append(mats[m])
        return me

    def subsurf(o, view=1, render=None):
        m = o.modifiers.new("Subdivision", "SUBSURF")
        m.levels, m.render_levels = view, render if render is not None else sd["render_levels"]

    def add_subd(name, data, slots=("steel_brushed", "steel_polished"), sharp=False):
        me = subd_mesh(name, data, slots)
        if sharp:  # faceted solids keep flat shading: crisp planar facets
            me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        if sharp:
            md = o.modifiers.new("Edge", "BEVEL")
            md.width, md.segments, md.limit_method, md.angle_limit = 0.07, 1, "ANGLE", math.radians(20)
        else:
            subsurf(o)
        parts[name] = o
        return o

    # ---- case: flank (brushed) + chamfer ring (polished) + caseback medallion ----
    c = cfg["case"]
    R, top, ch = c["flank_radius"], c["top_z"], c["chamfer"]
    add("case", Geo().lathe([(0, 0.35), (17.0, 0.35), (17.0, 0.0), (R - 2.6, 0.0), (R - 0.8, 0.9), (R, 2.6), (R, top - ch * 0.8), (R - ch, top), (0, top)]), "steel_brushed")
    add("case_chamfer", Geo().lathe([(R + 0.01, top - ch * 0.8 - 0.02), (R - ch + 0.01, top + 0.01)]), "steel_polished")
    mr = c["caseback"]["medallion_radius"]
    add("medallion", Geo().lathe([(0, 0.35), (mr, 0.35), (mr - 0.3, 0.02), (0, 0.02)]), "steel_polished")

    # ---- lugs: traced outline, sloped top; guards beside the crown ----
    lug = c["lug"]
    sil = {round(r[0], 2): r[1] for r in trace["silhouette_y_left_right_mm"]}  # y -> left edge (mm, negative)
    ys = [y for y in sorted(sil) if lug["start_y"] <= y <= lug["tip_y"]]
    outer = [(-sil[y], y) for y in ys]
    poly = outer + [(lug["inner_x"], lug["tip_y"]), (lug["inner_x"], lug["start_y"])]
    both = {round(r[0], 2): (r[1], r[2]) for r in trace["silhouette_y_left_right_mm"]}

    def rdp(pts, tol):
        """Ramer-Douglas-Peucker polyline simplification."""
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        i, dmax = max(((k, abs(dy * (p[0] - x0) - dx * (p[1] - y0)) / ln) for k, p in enumerate(pts[1:-1], 1)), key=lambda t: t[1], default=(0, 0))
        if dmax <= tol:
            return [pts[0], pts[-1]]
        return rdp(pts[:i + 1], tol)[:-1] + rdp(pts[i:], tol)

    def side_outline(sx):
        """Each side keeps its own measured outline (the case is asymmetric); top and bottom are averaged because the product render is slightly in perspective."""
        pts = []
        for y in ys:
            a, b_ = both.get(y), both.get(round(-y, 2))
            tb = min(max((y - lug.get("sym_until_y", 0)) / 3.0, 0.0), 1.0)  # beside the crown/pushers the right edge is the pusher, not the lug: use the left edge, fade to the right one over 3 mm (no step)
            e = [(abs(v[0]) if sx < 0 else abs(v[0]) * (1 - tb) + abs(v[1]) * tb) for v in (a, b_) if v]
            pts.append((sx * sum(e) / len(e), y))
        return rdp(pts, 0.12) + [(sx * lug["inner_x"], lug["tip_y"]), (sx * lug["inner_x"], lug["start_y"])]  # traced pixel jitter -> few clean vertices (no mitre spikes)

    def z_top(y):
        t = min(max((y - lug["flat_until_y"]) / (lug["tip_y"] - lug["flat_until_y"]), 0), 1)
        return lug["tip_top_z"] + (lug["top_z"] - lug["tip_top_z"]) * (1 - t * t)

    def z_bot(y):
        t = min(max((y - 18) / (lug["tip_y"] - 18), 0), 1)
        return lug["bottom_z"] + (lug["tip_bottom_z"] - lug["bottom_z"]) * t * t

    for sy in (1, -1):
        for sx in (1, -1):
            if cfg.get("faceted"):
                fc = cfg["faceted"]
                side_poly = side_outline(sx) if cfg.get("lug_per_side") else [(sx * x, y) for x, y in poly]
                add_subd("lug_%+d%+d" % (sx, sy), subd.faceted_slab([(x, sy * y) for x, y in side_poly], lambda x, y: z_bot(abs(y)), lambda x, y: z_top(abs(y)),
                                                                   lambda x, y: min(fc["lug_chamfer"], 0.42 * max(abs(x) - lug["inner_x"], 0.2)), fc["lug_drop"]), sharp=True)
                continue
            if sd:
                add_subd("lug_%+d%+d" % (sx, sy), subd.rounded_slab([(sx * x, sy * y) for x, y in poly], lambda x, y: z_bot(abs(y)), lambda x, y: z_top(abs(y)), sd["lug_r_bottom"], sd["lug_r_top"], cap_rings=2))
                continue
            g = Geo()
            skin_prism(g, [(sx * x, sy * y) for x, y in poly], lambda y, s=sy: z_bot(abs(y)), lambda y, s=sy: z_top(abs(y)))
            add("lug_%+d%+d" % (sx, sy), g, "steel_brushed", bevel=lug["bevel"])
    gd = c["guard"]
    if gd.get("from_silhouette"):  # thin shoulders: the measured right edge of the silhouette beside the crown (front reference)
        edge = {round(r[0], 2): r[2] for r in trace["silhouette_y_left_right_mm"]}
        if gd.get("outline"):  # one clean shoulder polygon behind crown + pushers (the traced edge is bumpy there)
            fc = cfg["faceted"]
            add_subd("crown_guard_0", subd.faceted_slab([tuple(pt) for pt in gd["outline"]], lambda x, y: gd["z0"], lambda x, y: gd["z1"], lambda x, y: fc["guard_chamfer"], fc["guard_drop"]), slots=("steel_polished", "steel_polished"), sharp=True)
            gd = dict(gd, ranges=[])
        for k_, (y0_, y1_) in enumerate(gd["ranges"]):
            ys_ = [y for y in sorted(edge) if y0_ <= y <= y1_][::2] or [y0_, y1_]  # every other sample: smooth, no stair-steps
            outline = [(min(edge[y], gd.get("max_x", 99)), y) for y in ys_] + [(gd["inner_x"], ys_[-1]), (gd["inner_x"], ys_[0])]
            fc = cfg["faceted"]
            add_subd("crown_guard_%d" % k_, subd.faceted_slab(outline, lambda x, y: gd["z0"], lambda x, y: gd["z1"], lambda x, y: fc["guard_chamfer"], fc["guard_drop"]), sharp=True)
        gd = dict(gd, ranges=[])
    for sy in (1, -1) if not gd.get("from_silhouette") else ():  # two shoulders flank the crown (crown sits between them, y = +-gap)
        y0, y1 = sy * gd["gap"], sy * gd["y"]
        guard = [(gd["x0"], y0), (gd["x1"], y0), (gd["x1"], y1 - sy * 2.5), (gd["x0"], y1)]
        if cfg.get("faceted"):
            fc = cfg["faceted"]
            add_subd("crown_guard_%+d" % sy, subd.faceted_slab(guard, lambda x, y: gd["z0"], lambda x, y: gd["z1"], lambda x, y: fc["guard_chamfer"], fc["guard_drop"]), sharp=True)
            continue
        if sd:
            add_subd("crown_guard_%+d" % sy, subd.rounded_slab(guard, lambda x, y: gd["z0"], lambda x, y: gd["z1"], sd["guard_r"], sd["guard_r"], cap_rings=1))
            continue
        add("crown_guard_%+d" % sy, Geo().prism(guard, gd["z0"], gd["z1"]), "steel_brushed", bevel=gd["bevel"])

    # ---- bezel, tachymeter, crystal ----
    z = cfg["bezel"]
    add("bezel", Geo().lathe([tuple(p) for p in z["profile_rz"]] + [tuple(z["profile_rz"][0])]), "bezel_black")
    if z.get("ring_profile_rz"):  # polished steel ring around the black insert, as on the real watch
        add("bezel_ring", Geo().lathe([tuple(p) for p in z["ring_profile_rz"]] + [tuple(z["ring_profile_rz"][0])], segs=128), "steel_polished")
    cr = cfg["crystal"]
    h = cr["apex_z"] - cr["rim_top_z"]
    big_r = (cr["rim_radius"] ** 2 + h * h) / (2 * h)
    arc = [(big_r * math.sin(math.asin(cr["rim_radius"] / big_r) * (1 - i / cr["segments"])),
            cr["apex_z"] - big_r * (1 - math.cos(math.asin(cr["rim_radius"] / big_r) * (1 - i / cr["segments"])))) for i in range(1, cr["segments"] + 1)]
    add("crystal_hesalite", Geo().lathe([(0, cr["base_z"]), (cr["rim_radius"], cr["base_z"]), (cr["rim_radius"], cr["rim_top_z"])] + arc, segs=128), "hesalite")

    # ---- dial ----
    d = cfg["dial"]
    add("dial", Geo().lathe([(0, 8.0), (d["outer_radius"], 8.0), (d["outer_radius"], d["outer_z"]), (d["inner_radius"], d["outer_z"]),
                             (d["inner_radius"] - 0.3, d["inner_z"]), (0, d["inner_z"])]), "dial_black")
    sub = d["subdial"]
    g = Geo()
    for cx, cy in sub["centers"]:
        g.lathe([(0, d["inner_z"] - 0.05), (sub["radius"], d["inner_z"] - 0.05), (sub["radius"] - 0.12, sub["z"]), (0, sub["z"])], segs=64, m=Matrix.Translation((cx, cy, 0)))
    add("subdials", g, "subdial_black")
    ix = d["index"]
    top_z = d["inner_z"]
    frame, lume = Geo(), Geo()
    for hour in range(12):
        ang = hour * 30
        frame.prism([rot(x, y, ang) for x, y in rect(0, ix["radius"], ix["lume_w"] + ix["frame_extra"], ix["lume_l"] + ix["frame_extra"])], top_z, top_z + ix["frame_h"])
        lume.prism([rot(x, y, ang) for x, y in rect(0, ix["radius"], ix["lume_w"], ix["lume_l"])], top_z + ix["frame_h"], top_z + ix["frame_h"] + ix["lume_h"])
    for sx in (-1, 1):
        dot = Matrix.Translation((sx * ix["dots"]["x"], ix["dots"]["y"], 0))
        frame.lathe([(0, top_z), (ix["dots"]["d"] / 2 + ix["dots"].get("frame", 0.2), top_z), (ix["dots"]["d"] / 2 + ix["dots"].get("frame", 0.2), top_z + ix["frame_h"] * 0.8), (0, top_z + ix["frame_h"] * 0.8)], segs=20, m=dot)
        lume.lathe([(0, top_z + ix["frame_h"] * 0.8), (ix["dots"]["d"] / 2, top_z + ix["frame_h"] * 0.8), (ix["dots"]["d"] / 2, top_z + ix["frame_h"] * 0.8 + ix["lume_h"]), (0, top_z + ix["frame_h"] * 0.8 + ix["lume_h"])], segs=20, m=dot)
    add("indices_frame", frame, "steel_polished")
    add("indices_lume", lume, "lume")
    def traced_print():
        """Printed layers from the real watch's front render (pipeline/watch_print.py): exact glyphs, numerals, ticks, logo; flat decals."""
        from mathutils import geometry as mg
        data = json.loads((ROOT / cfg["print"]).read_text())["groups"]
        zs = {"dial": d["inner_z"] + 0.02, "subdials": sub["z"] + 0.02, "track": d["outer_z"] + 0.02, "bezel": max(pt[1] for pt in z["profile_rz"]) + 0.015}
        for name, shapes in data.items():
            verts, faces = [], []
            for sh in shapes:
                polys = [[Vector((x, y, 0)) for x, y in sh["outer"]]] + [[Vector((x, y, 0)) for x, y in hole] for hole in sh["holes"]]
                base = len(verts)
                for pl in polys:
                    verts += [(v.x, v.y, zs[name]) for v in pl]
                for tri in mg.tessellate_polygon(polys):
                    pts = [verts[base + i] for i in tri]
                    cross = (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[1][1] - pts[0][1]) * (pts[2][0] - pts[0][0])
                    faces.append(tuple(base + i for i in (tri if cross > 0 else tri[::-1])))
            me = bpy.data.meshes.new("print_" + name)
            me.from_pydata(verts, [], faces)
            me.update()
            me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))
            add("print_" + name, me, "print_white")

    def legacy_print():
        mt = d["minute_track"]
        g = Geo()
        for i in range(mt["count"]):
            long_tick = i % 4 == 0
            pts = [rot(x, y, i * 360 / mt["count"]) for x, y in rect(0, (mt["r_in"] + mt["r_out"]) / 2, mt["width"] * (1.6 if i % 20 == 0 else 1), mt["r_out"] - mt["r_in"] - (0 if long_tick else 0.5))]
            g.prism(pts, d["outer_z"], d["outer_z"] + 0.04)
        add("minute_track", g, "print_white")

        def text(name, body, x, y, size, zpos, deg=0):
            cu = bpy.data.curves.new(P + name, "FONT")
            cu.body, cu.size, cu.align_x, cu.align_y = body, size, "CENTER", "CENTER"
            o = bpy.data.objects.new(P + name, cu)
            coll.objects.link(o)
            o.parent = pose
            o.location, o.rotation_euler = (x, y, zpos), (0, 0, math.radians(-deg))
            cu.materials.append(mats["print_white"])
            return o

        def join_texts(objs, name):
            bpy.ops.object.select_all(action="DESELECT")
            for o in objs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = objs[0]
            bpy.ops.object.convert(target="MESH")
            bpy.ops.object.join()
            bpy.context.active_object.name = P + name
            parts[name] = bpy.context.active_object

        texts = [text("t_" + k, k, v[0], v[1], v[2], d["inner_z"] + 0.03) for k, v in d["text"].items()]
        for (cx, cy), labels in zip(sub["centers"], [[("60", 0), ("20", 120), ("40", 240)], [("30", 0), ("10", 120), ("20", 240)], [("12", 0), ("3", 90), ("6", 180), ("9", 270)]]):
            for label, ang in labels:
                px, py = rot(0, sub["radius"] - 1.25, ang)
                texts.append(text("s_%s_%d_%d" % (label, cx, ang), label, cx + px, cy + py, 0.95, sub["z"] + 0.03))
        join_texts(texts, "dial_print")
        bz = z["profile_rz"][4][1] + 0.02
        texts = []
        for n in z["numerals"]:
            theta = (360 * 60 / n) % 360
            px, py = rot(0, z["numeral_radius"], theta)
            texts.append(text("b_%d" % n, str(n), px, py, z["numeral_size"], bz, theta))
        join_texts(texts, "bezel_numerals")
        g = Geo()
        for n in z["numerals"]:
            px, py = rot(0, z["dot_radius"], (360 * 60 / n) % 360)
            g.lathe([(0, bz), (0.14, bz), (0.14, bz + 0.03), (0, bz + 0.03)], segs=12, m=Matrix.Translation((px, py, 0)))
        add("bezel_dots", g, "print_white")

    if cfg.get("print"):
        traced_print()
    else:
        legacy_print()

    # ---- hands (lengths/angles traced) ----
    hz, th, tm, ln = cfg["hands"]["z"], cfg["hands"]["thickness"], cfg["hands"]["time"], cfg["hands"]["lengths"]

    def hand(name, poly, deg, z0, lume_scale=None, center=(0, 0)):
        place = lambda pts: [(center[0] + rot(x, y, deg)[0], center[1] + rot(x, y, deg)[1]) for x, y in pts]
        add(name, Geo().prism(place(poly), z0, z0 + th), "hand_white", bevel=0.03)
        if lume_scale:
            add(name + "_lume", Geo().prism(place([(x * lume_scale[0], y * lume_scale[1] + lume_scale[2]) for x, y in poly]), z0 + th, z0 + th + 0.04), "lume")

    if cfg["hands"].get("traced"):  # outlines + lume inlays traced from the real watch (pipeline/watch_hands.py), posed at the configured time
        from mathutils import geometry as mg
        hd = json.loads((ROOT / cfg["hands"]["traced"]).read_text())["hands"]
        deg_of = {"hour": tm["hour_deg"], "minute": tm["minute_deg"], "chrono": tm["chrono_deg"]}
        z_of = {"hour": hz["hour"], "minute": hz["minute"], "chrono": hz["chrono"]}
        for hname, parts_ in hd.items():
            for part, shapes in parts_.items():
                verts, faces = [], []
                z0 = z_of[hname] + (th if part == "lume" else 0.0)
                z1 = z0 + (0.04 if part == "lume" else th)
                for sh in shapes:
                    polys = [[Vector((x, y, 0)) for x, y in sh["outer"]]] + [[Vector((x, y, 0)) for x, y in hole] for hole in sh["holes"]]
                    base = len(verts)
                    pts = [pt for pl in polys for pt in pl]
                    pos = [rot(p_.x, p_.y, deg_of[hname]) for p_ in pts]
                    verts += [(x, y, z1) for x, y in pos] + [(x, y, z0) for x, y in pos]
                    nloc = len(pts)
                    for tri in mg.tessellate_polygon(polys):
                        va, vb, vc = (verts[base + i] for i in tri)
                        cross = (vb[0] - va[0]) * (vc[1] - va[1]) - (vb[1] - va[1]) * (vc[0] - va[0])
                        faces.append(tuple(base + i for i in (tri if cross > 0 else tri[::-1])))
                    off = 0
                    for pl in polys:  # side walls of the outline and of each hole
                        m_ = len(pl)
                        for k_ in range(m_):
                            a_, b_ = off + k_, off + (k_ + 1) % m_
                            faces.append((base + a_, base + b_, base + nloc + b_, base + nloc + a_))
                        off += m_
                me = bpy.data.meshes.new("hand_" + hname + "_" + part)
                me.from_pydata(verts, [], faces)
                me.update()
                me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))
                add("hand_%s_%s" % (hname, part), me, "lume" if part == "lume" else "hand_white")
        # slim bridges from the hub to the traced start of the hour/minute hands (their root lies under the hub in the source image)
        for hname, wid, y1 in (("hour", 0.62, 1.6), ("minute", 0.5, 5.8)):
            add("hand_%s_root" % hname, Geo().prism([rot(x, y, deg_of[hname]) for x, y in rect(0, y1 / 2, wid * 2, y1)], z_of[hname], z_of[hname] + th), "hand_white")
        subs = cfg["dial"]["subdial"]
        for i, (cx_, cy_) in enumerate(subs["centers"]):  # sub-dial hands + their pivot caps (visible white discs in the reference)
            add("subhub%d" % i, Geo().lathe([(0, subs["z"] + 0.04), (0.69, subs["z"] + 0.04), (0.69, subs["z"] + 0.12), (0.45, subs["z"] + 0.16), (0, subs["z"] + 0.17)], segs=40, m=Matrix.Translation((cx_, cy_, 0))), "hand_white")  # flat white disc like the render
    elif cfg["hands"].get("style") == "baton":  # per the real watch: slim parallel batons with lume strips, thin chrono hand with lume arrow tip
        L = ln["hour"]
        hand("hand_hour", [(-0.62, -2.0), (0.62, -2.0), (0.62, L - 2.4), (0, L), (-0.62, L - 2.4)], tm["hour_deg"], hz["hour"], (0.46, (L - 3.2) / (L + 2.0), 1.0))
        L = ln["minute"]
        hand("hand_minute", [(-0.5, -2.0), (0.5, -2.0), (0.5, L - 3.0), (0, L), (-0.5, L - 3.0)], tm["minute_deg"], hz["minute"], (0.42, (L - 4.0) / (L + 2.0), 1.0))
        L = ln["chrono"]
        hand("hand_chrono", [(-0.16, -4.6), (0.16, -4.6), (0.16, L - 2.4), (0, L), (-0.16, L - 2.4)], tm["chrono_deg"], hz["chrono"])
        ang = math.radians(tm["chrono_deg"])
        arrow = [(0, L - 0.2), (0.62, L - 2.6), (0, L - 2.1), (-0.62, L - 2.6)]
        add("hand_chrono_lume", Geo().prism([rot(x, y, tm["chrono_deg"]) for x, y in arrow], hz["chrono"] + th, hz["chrono"] + th + 0.05), "lume")
        add("hand_chrono_tail", Geo().prism([rot(0.8 * math.cos(2 * math.pi * k / 20), -3.7 + 0.8 * math.sin(2 * math.pi * k / 20), tm["chrono_deg"]) for k in range(20)], hz["chrono"], hz["chrono"] + th), "hand_white")
    else:
        L = ln["hour"]
        hand("hand_hour", [(-0.5, -2), (0.5, -2), (0.6, 0), (1.2, 0.36 * L), (0, L), (-1.2, 0.36 * L), (-0.6, 0)], tm["hour_deg"], hz["hour"], (0.5, 0.62, 0.6))
        L = ln["minute"]
        hand("hand_minute", [(-0.45, -2), (0.45, -2), (0.6, 0), (1.0, 0.4 * L), (0, L), (-1.0, 0.4 * L), (-0.6, 0)], tm["minute_deg"], hz["minute"], (0.5, 0.7, 0.8))
        L = ln["chrono"]
        hand("hand_chrono", [(-0.18, -4.5), (0.18, -4.5), (0.18, L - 0.8), (0, L), (-0.18, L - 0.8)], tm["chrono_deg"], hz["chrono"])
        hand("hand_chrono_tail", [(-0.55, -4.9), (0.55, -4.9), (0.55, -2.6), (-0.55, -2.6)], tm["chrono_deg"], hz["chrono"])

    for i, (cx, cy) in enumerate(sub["centers"]):
        hand("hand_sub%d" % i, [(-0.12, -0.8), (0.12, -0.8), (0.12, sub["radius"] - 0.9), (0, sub["radius"] - 0.6), (-0.12, sub["radius"] - 0.9)], 0, sub["z"] + 0.05, center=(cx, cy))
    add("hand_hub", Geo().lathe([(0, hz["hour"] - 0.1), (1.05, hz["hour"] - 0.1), (1.05, hz["chrono"] + th), (0.75, hz["chrono"] + th + 0.14), (0, hz["chrono"] + th + 0.18)], segs=48), "hand_white")

    # ---- crown, pushers ----
    cw = cfg["crown"]
    pu = cfg["pushers"]
    fl = cfg.get("fluted")
    ROT = Matrix(((0, 0, 1, 0), (0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 0, 1)))  # lathe axis z -> +x

    def star_poly(r, depth, teeth):
        return [((r if i % 2 == 0 else r - depth) * math.cos(math.pi * i / teeth), (r if i % 2 == 0 else r - depth) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]

    def dome(r, h, n=10):
        return [(r * math.cos(math.pi / 2 * i / n), h * math.sin(math.pi / 2 * i / n)) for i in range(n + 1)]

    if "face" in cw:  # measured crown (cap face centre/radius from the front silhouette, height from the registered 3/4 photo) + tilted pushers
        g = Geo()
        fx, fy = cw["face"]
        cap_h = cw["cap_h"]
        if cw.get("profile"):  # real crown: flat flutes, softened case end, rounded shoulder at the free end, small emblem disc (macro of the Omega render)
            star = star_poly(cw["radius"], cw["flute"], cw["teeth"])
            nst = len(star)
            ctr = Matrix.Translation((0, fy, cw["z"])) @ X_ALONG
            xe = fx - cw["emblem_h"]
            rings = [(xx if xx > 0 else xe + xx, sc) for xx, sc in cw["profile"]]  # x relative to the free end when <= 0
            base_ = len(g.v)
            for xx, sc in rings:
                g.v += [Geo._t((px * sc, py * sc, xx), ctr) for px, py in star]
            for j in range(len(rings) - 1):
                for k in range(nst):
                    k2 = (k + 1) % nst
                    g.f.append((base_ + j * nst + k, base_ + j * nst + k2, base_ + (j + 1) * nst + k2, base_ + (j + 1) * nst + k))
                    g.smooth.append(False)
            g.f.append(tuple(range(base_ + (len(rings) - 1) * nst, base_ + len(rings) * nst)))
            g.smooth.append(False)
            g.f.append(tuple(range(base_ + nst - 1, base_ - 1, -1)))
            g.smooth.append(False)
            g.lathe(dome(cw["emblem_r"], cw["emblem_h"], 10) + [(0, cw["emblem_h"])][:0], segs=64, m=Matrix.Translation((xe, fy, cw["z"])) @ ROT)
            add("crown", g, "steel_polished")
            cl_ = None
        else:
            cl_, cr_ = cw.get("cap_len", 0), cw.get("cap_r", cw["radius"] - 0.2)
            g.prism(star_poly(cw["radius"], cw["flute"], cw["teeth"]), cw["x_in"], fx - cap_h - cl_, Matrix.Translation((0, fy, cw["z"])) @ X_ALONG)
            if cl_:  # stepped cap: smooth narrower drum behind the dome
                g.lathe([(0, 0), (cr_, 0), (cr_, cl_), (0, cl_)], segs=64, m=Matrix.Translation((fx - cap_h - cl_, fy, cw["z"])) @ ROT)
            g.lathe(dome(cr_, cap_h, 12), segs=64, m=Matrix.Translation((fx - cap_h, fy, cw["z"])) @ ROT)
            add("crown", g, "steel_polished")
        g = Geo()
        for pface in pu["faces"]:
            ang = math.radians(pface["angle_deg"])
            rz = Matrix(((math.cos(ang), -math.sin(ang), 0, 0), (math.sin(ang), math.cos(ang), 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
            base = Matrix.Translation((pface["center"][0], pface["center"][1], pu["z"])) @ rz @ ROT  # local z = pusher axis, face at z = 0
            L = pu["length"]
            rc, rf, lc = pu["r_cap"], pu.get("fillet", 0.55), pu.get("cap_len", 4.2)
            prof = [(0, -L), (pu["r_tube"], -L), (pu["r_tube"], -lc - 0.2), (rc - 0.12, -lc - 0.2), (rc, -lc)]
            prof += [(rc - rf + rf * math.cos(math.pi / 2 * i / 6), -rf + rf * math.sin(math.pi / 2 * i / 6)) for i in range(7)] + [(0, 0)]
            g.lathe(prof, segs=64, hard=60, m=base)
        add("pushers", g, "steel_polished")
    elif fl:  # real flutes on the collars, domed polished caps (they sweep reflections instead of mirroring black)
        g = Geo()
        lead = (0, cw["y"], cw["z"])
        g.prism(star_poly(cw["radius"], fl["crown_flute"], cw["teeth"]), cw["x0"], cw["x1"] - fl["cap_h"], Matrix.Translation(lead) @ X_ALONG)
        g.lathe(dome(cw["radius"] - 0.15, fl["cap_h"], 12), segs=64, m=Matrix.Translation((cw["x1"] - fl["cap_h"], cw["y"], cw["z"])) @ ROT)
        add("crown", g, "steel_polished")
        g = Geo()
        for y in pu["y"]:
            g.prism(star_poly(pu["radius"] + 0.2, fl["pusher_flute"], fl["pusher_teeth"]), pu["x0"], pu["x0"] + 1.8, Matrix.Translation((0, y, pu["z"])) @ X_ALONG)
            g.lathe([(0, 0), (pu["radius"] - 0.3, 0), (pu["radius"] - 0.3, pu["x1"] - pu["x0"] - 1.8 - fl["pusher_cap_h"]), (0, pu["x1"] - pu["x0"] - 1.8 - fl["pusher_cap_h"])],
                    segs=40, m=Matrix.Translation((pu["x0"] + 1.8, y, pu["z"])) @ ROT)
            g.lathe(dome(pu["radius"] - 0.05, fl["pusher_cap_h"], 10), segs=48, m=Matrix.Translation((pu["x1"] - fl["pusher_cap_h"], y, pu["z"])) @ ROT)
        add("pushers", g, "steel_polished")
    else:
        star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - 0.4) * math.cos(math.pi * i / cw["teeth"]),
                 (cw["radius"] if i % 2 == 0 else cw["radius"] - 0.4) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
        add("crown", Geo().prism(star, cw["x0"], cw["x1"], Matrix.Translation((0, cw["y"], cw["z"])) @ X_ALONG), "steel_polished", bevel=0.2)
        pu, g = cfg["pushers"], Geo()
        ln_p = pu["x1"] - pu["x0"]
        for y in pu["y"]:
            tr = Matrix.Translation((pu["x0"], y, pu["z"])) @ Matrix(((0, 0, 1, 0), (0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 0, 1)))
            g.lathe([(0, 0), (pu["radius"] * 0.8, 0), (pu["radius"] * 0.8, 1.2), (pu["radius"], 1.2), (pu["radius"], ln_p - 0.4), (pu["radius"] - 0.4, ln_p), (0, ln_p)], segs=40, m=tr)
        add("pushers", g, "steel_polished")


    def fold_clasp(fc):
        """Omega fold-over clasp at the bottom of the worn loop (references/omega-clasp/): a brushed cover with polished
        grooves and a raised polished Omega at one end, oval push buttons on both flanks, and an end barrel at each end
        joining the bracelet. Built straight in a clasp frame (x across, s along, n outward from the wrist), then bent
        onto a circular arc through the loop bottom and the loop path at the clasp ends (the path kinks at its end)."""
        L, W, n0, n1 = fc["length"], fc["width"], fc["inner"], fc["outer"]
        (ey, ez), _ = at(half_len - L / 2)
        bz = b["path_yz"][-1][1]
        zc = (ey ** 2 + ez ** 2 - bz ** 2) / (2 * (ez - bz))
        R = zc - bz

        def bend(x, s_, n):
            ph = s_ / R
            return (x, (R + n) * math.sin(ph), zc - (R + n) * math.cos(ph))

        def solid(name, verts, faces, mat_ids, slots, bevel=None):
            import bmesh
            me = subd_mesh(P + name, (verts, faces, mat_ids), slots)
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)  # the bend mirrors the frame; let each solid face outward
            bm.to_mesh(me)
            bm.free()
            o = bpy.data.objects.new(P + name, me)
            coll.objects.link(o)
            o.parent = pose
            if bevel:
                md = o.modifiers.new("Edge", "BEVEL")
                md.width, md.segments, md.limit_method, md.angle_limit, md.material = bevel, 2, "ANGLE", math.radians(30), 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
            parts[name] = o
            return o

        def arc(cx, cn, r, a0, a1, k=5):
            return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / k)), cn + r * math.sin(math.radians(a0 + (a1 - a0) * i / k))) for i in range(k + 1)]

        # cover cross-section, counter-clockwise in (x, n); edge i (point i -> i+1) is polished on the groove flanks
        ro, ri, crown, gw, gd = fc["r_outer"], fc["r_inner"], fc["crown"], fc["groove_w"], fc["groove_d"]
        top = lambda x: n1 - crown * (2 * x / W) ** 2
        sec, pol, floor = [], [], {}  # floor: section index of a groove bottom -> its groove x

        def put(pts, polished=False):
            for q in pts:
                sec.append(q)
                pol.append(polished)
        put(arc(-W / 2 + ri, n0 + ri, ri, 180, 270))
        put(arc(W / 2 - ri, n0 + ri, ri, 270, 360))
        put(arc(W / 2 - ro, top(W / 2) - ro, ro, 0, 90))
        xs = [W / 2 - ro - 0.5 * i for i in range(1, int((W - 2 * ro) / 0.5))]
        grooves = sorted(fc["grooves"], reverse=True)
        x_prev = W / 2 - ro
        for g in grooves:
            put([(x, top(x)) for x in xs if g + gw / 2 < x < x_prev])
            put([(g + gw / 2, top(g + gw / 2))], polished=True)
            floor[len(sec)] = g
            put([(g, top(g) - gd)], polished=True)
            put([(g - gw / 2, top(g - gw / 2))])
            x_prev = g - gw / 2
        put([(x, top(x)) for x in xs if x < x_prev])
        put(arc(-W / 2 + ro, top(W / 2) - ro, ro, 90, 180))
        NS = fc["stations"]
        verts, faces, mids = [], [], []
        m = len(sec)
        stop = L / 2 - fc["logo"]["from_end"] - fc["logo"]["r_outer"] - fc["logo"]["clear"]  # the centre grooves end short of the Omega
        for j in range(NS + 1):
            s_ = -L / 2 + L * j / NS
            verts += [bend(x, s_, top(x) if s_ > stop and abs(floor.get(i, 99)) < fc["logo"]["r_outer"] else n) for i, (x, n) in enumerate(sec)]
        for j in range(NS):
            for i in range(m):
                a, c = j * m + i, j * m + (i + 1) % m
                faces.append((a, c, c + m, a + m))
                mids.append(1 if pol[i] else 0)
        faces += [tuple(range(m)), tuple(range(NS * m, NS * m + m))]
        mids += [0, 0]
        solid("clasp_cover", verts, faces, mids, ("steel_links", "steel_polished"), bevel=fc["chamfer"])

        # raised Omega on the logo end (upright toward that end), push buttons, end barrels: polished / brushed
        g_v, g_f = [], []

        def prism(poly, lo, hi, m_=None):  # poly in (x, s); n from lo to hi
            base, k = len(g_v), len(poly)
            for n in (lo, hi):
                g_v.extend(bend(x, s_, n) for x, s_ in poly)
            g_f.append(tuple(range(base + k - 1, base - 1, -1)))
            g_f.append(tuple(range(base + k, base + 2 * k)))
            g_f.extend((base + i, base + (i + 1) % k, base + k + (i + 1) % k, base + k + i) for i in range(k))
        lg = fc["logo"]
        sc, r_o, r_i, h = L / 2 - lg["from_end"], lg["r_outer"], lg["r_inner"], lg["height"]
        ring = [(x, sc + y) for x, y in arc(0, 0, r_o, -58, 238, 28)] + [(x, sc + y) for x, y in arc(0, 0, r_i, 238, -58, 28)]
        prism(ring, top(0) - 0.05, top(0) + h)
        for side in (1, -1):
            foot = [(side * 0.6, sc - r_o - 0.02), (side * (r_o + 0.4), sc - r_o - 0.02), (side * (r_o + 0.4), sc - r_o + 0.4), (side * 0.6, sc - r_o + 0.4)]
            prism(foot, top(0) - 0.05, top(0) + h - 0.02)
        bt = fc["button"]
        for side in (1, -1):  # oval domes half-sunk into each flank
            base = len(g_v)
            la, lo_ = 8, 16
            for i in range(la + 1):
                th = math.pi * i / la
                for k in range(lo_):
                    ph = 2 * math.pi * k / lo_
                    a, b_, c = math.cos(th), math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph)
                    g_v.append(bend(side * (W / 2 - bt["sink"] + bt["out"] * a), L / 2 - bt["from_end"] + bt["half_len"] * b_, (n0 + n1) / 2 + bt["lift"] + bt["half_h"] * c))
            for i in range(la):
                for k in range(lo_):
                    p0, p1 = base + i * lo_ + k, base + i * lo_ + (k + 1) % lo_
                    g_f.append((p0, p1, p1 + lo_, p0 + lo_))
        solid("clasp_polished", g_v, g_f, [0] * len(g_f), ("steel_polished",))

        g_v, g_f = [], []
        gap, rb = fc["barrel_gap"], fc["barrel_r"]
        for end in (1, -1):  # cylinders across the bracelet, axis x
            sc_ = end * (L / 2 + gap / 2)
            circ = [(sc_ + rb * math.cos(2 * math.pi * k / 24), rb * math.sin(2 * math.pi * k / 24)) for k in range(24)]
            hw = fc["barrel_width"] / 2
            base = len(g_v)
            for x in (-hw, hw):
                g_v.extend(bend(x, s_, n) for s_, n in circ)
            g_f.append(tuple(range(base + 23, base - 1, -1)))
            g_f.append(tuple(range(base + 24, base + 48)))
            g_f.extend((base + i, base + (i + 1) % 24, base + 24 + (i + 1) % 24, base + 24 + i) for i in range(24))
        solid("clasp_barrels", g_v, g_f, [0] * len(g_f), ("steel_links", "steel_polished"), bevel=fc["chamfer"])

    # ---- bracelet (straight pose): per-column links with rounded barrel ends, end links reaching the case ----
    bc = b.get("columns")
    if bc:
        xs_ = [-sum(bc["widths"]) / 2]
        for w_ in bc["widths"]:
            xs_.append(xs_[-1] + w_)
        t_, rr = bc["thickness"], bc["end_round"] * bc["thickness"] / 2
        base_w = sum(bc["widths"])
        taper = lambda y: max(0.5, (bc["taper_w0"] - bc["taper_slope"] * (abs(y) - bc["taper_y0"])) / base_w) if bc.get("taper_w0") else 1.0
        link_meshes = {}
        for sign in (1, -1):
            for ci, w_ in enumerate(bc["widths"]):
                cxm = (xs_[ci] + xs_[ci + 1]) / 2
                bnd, k_ = bc["first_boundary"][ci], 0
                pitch_c = bc["pitch"] * (bc.get("rail_rows", 1) if ci in (1, 3) else 1)  # the thin links are long rails spanning several rows
                spans = []
                y_a = bc["y_start"]
                fc = b.get("fold_clasp") if bc.get("follow_path") else None
                # With the fold clasp the links stop short of it (its end barrels fill the gap); a sliver is merged.
                y_stop = b["path_yz"][0][0] + half_len - fc["length"] / 2 - fc["barrel_gap"] if fc else bc["y_end"]
                while y_a < y_stop:
                    y_b = bnd + k_ * pitch_c - bc["gap"] / 2
                    if fc and y_stop - y_b < 1.0:
                        y_b = y_stop
                    spans.append((y_a, y_b))
                    y_a, k_ = y_b + bc["gap"], k_ + 1
                for si, (ya, yb) in enumerate(spans):
                    ln_ = yb - ya
                    fx = taper((ya + yb) / 2)
                    w_eff = w_ * fx
                    key = (ci, round(ln_, 2), round(fx, 3))
                    if key not in link_meshes:
                        n_ = 4  # rounded rectangle in the y-z profile (corner radius rr), flat brushed top
                        prof = []
                        for qy, qz, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
                            for i in range(n_ + 1):
                                th = math.radians(a0 + 90 * i / n_)
                                prof.append((qy * (ln_ / 2 - rr) * 1.0 + rr * math.cos(th), qz * (t_ / 2 - rr) + rr * math.sin(th)))
                        gm = Geo().prism(prof, -w_eff / 2 + 0.05, w_eff / 2 - 0.05, X_ALONG)
                        me_ = gm.mesh(P + "link_%d_%.2f" % (ci, ln_), True)
                        me_.materials.append(mats.get("steel_links", mats["steel_brushed"]))
                        me_.materials.append(mats["steel_polished"])
                        link_meshes[key] = me_
                    o = bpy.data.objects.new(P + "link_%+d_%d_%02d" % (sign, ci, si), link_meshes[key])
                    coll.objects.link(o)
                    o.parent = pose
                    o.location = (cxm * fx, sign * (ya + yb) / 2, bc["z"])
                    if bc.get("follow_path"):  # worn pose: lay the link along the loop path (arc length from the path start)
                        u = (ya + yb) / 2 - b["path_yz"][0][0]
                        if u > 0:
                            pos_, tan_ = at(u)
                            o.location = (cxm * fx, sign * pos_.x, pos_.y + bc["z"] - b["path_yz"][0][1])
                            o.rotation_euler = (sign * math.atan2(tan_.y, tan_.x), 0, 0)
                    md = o.modifiers.new("Edge", "BEVEL")
                    md.width, md.segments, md.limit_method, md.angle_limit, md.material = bc.get("chamfer", 0.12), 2, "ANGLE", math.radians(30), 1
                    o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if bc.get("backing") and not bc.get("follow_path"):  # solid plate behind the links: the gaps between links read as thin dark lines, nothing shows through
            for sign in (1, -1):
                ya_, yb_ = bc["y_start"], bc["y_end"]
                trap = [(-base_w * taper(ya_) / 2 + 0.15, sign * ya_), (base_w * taper(ya_) / 2 - 0.15, sign * ya_), (base_w * taper(yb_) / 2 - 0.15, sign * yb_), (-base_w * taper(yb_) / 2 + 0.15, sign * yb_)]
                add("bracelet_backing_%+d" % sign, Geo().prism(trap, bc["z"] - 0.9, bc["z"] + bc.get("backing_top", 0.9)), bc.get("backing_mat", "steel_polished"))
        if b.get("fold_clasp") and bc.get("follow_path"):
            fold_clasp(b["fold_clasp"])
        b = dict(b, no_clasp=True)
        usable_rows = 0
    # ---- bracelet: five-link row, one shared mesh ----
    widths, phase = b["link_widths"], b["link_phase"]
    if bc:
        row_mesh = None
    elif sd:  # scalloped, crowned, filleted links (SubD): convex end +y, concave end -y, pitch = length + gap
        parts_ = []
        x = -sum(widths) / 2
        for w, ph in zip(widths, phase):
            cx = x + w / 2
            outline = [(cx + px, ph * b["pitch"] + py) for px, py in subd.scallop_outline(w, b["pitch"] - sd["link_gap"], sd["link_scallop"])]
            parts_.append(subd.rounded_slab(outline, lambda xx, yy: -b["thickness"] / 2,
                                            lambda xx, yy, cx=cx, w=w: b["thickness"] / 2 - b["arch_sag"] * (2 * (xx - cx) / w) ** 2,
                                            sd["link_r_bottom"], sd["link_r_top"], cap_rings=1))
            x += w
        row_mesh = subd_mesh(P + "bracelet_row", subd.merge(parts_), ("steel_brushed", "steel_polished"))
    else:
        widths, phase = b["link_widths"], b["link_phase"]
        g, x = Geo(), -sum(widths) / 2
        for w, ph in zip(widths, phase):
            arch = []
            for k in range(9):  # arched top: x across, z = thickness with sag toward the edges
                t = -1 + 2 * k / 8
                arch.append((x + w / 2 + t * (w - 0.1) / 2, b["thickness"] / 2 - b["arch_sag"] * t * t))
            section = [(x + 0.05, -b["thickness"] / 2), (x + w - 0.05, -b["thickness"] / 2)] + arch[::-1]
            y0 = ph * b["pitch"] - b["row_length"] / 2
            g.prism(section, y0, y0 + b["row_length"], Matrix.Translation((0, 0, 0)) @ ARCH)
            x += w
        row_mesh = g.mesh(P + "bracelet_row", True)
        row_mesh.materials.append(mats["steel_brushed"])
        if polished:
            row_mesh.materials.append(mats[polished])
    usable = half_len - b["clasp_half"]
    rows = int(usable // b["pitch"]) if not bc else 0
    pitch = usable / rows if rows else 1
    for side in (1, -1) if not bc else ():
        for k in range(rows):
            pos, tan = at((k + 0.5) * pitch)
            n = Vector((-tan.y, tan.x))
            yaxis, zaxis = Vector((0, side * tan.x, tan.y)), Vector((0, side * n.x, n.y))
            m = Matrix((yaxis.cross(zaxis), yaxis, zaxis)).transposed().to_4x4()
            m.translation = (0, side * pos.x, pos.y)
            o = bpy.data.objects.new(P + "row_%+d_%02d" % (side, k), row_mesh)
            coll.objects.link(o)
            o.parent = pose
            if sd:
                subsurf(o)
            else:
                md = o.modifiers.new("Edge radius", "BEVEL")
                md.width, md.segments, md.limit_method, md.angle_limit = b["bevel"], segs, "ANGLE", math.radians(35)
                if polished:
                    md.material = 1
                o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
            o.matrix_basis = m @ Matrix.Diagonal((1 - (1 - b["end_width"] / b["width"]) * (k + 0.5) / rows, 1, 1, 1))
    end, _ = at(half_len)
    if not b.get("no_clasp"):
        add("clasp", Geo().prism(rect(0, 0, b["end_width"] + 0.6, 2 * b["clasp_half"]), -b["thickness"] / 2 - 0.6, b["thickness"] / 2 + 0.4), "steel_brushed", bevel=0.5, loc=(0, 0, end.y))

    # ---- verified dimensions + base ----
    def extent(names, axis):
        vals = [v.co[axis] for n in names for v in parts[n].data.vertices]
        return min(vals), max(vals)
    lugs = [n for n in parts if n.startswith("lug_")]
    out = {"lug_to_lug": round(extent(lugs, 1)[1] - extent(lugs, 1)[0], 3), "diameter": round(extent([n for n in ("bezel", "bezel_ring") if n in parts], 0)[1] - extent([n for n in ("bezel", "bezel_ring") if n in parts], 0)[0], 3),
           "thickness": round(extent(["crystal_hesalite"], 2)[1] - min(extent(["case", "medallion"], 2)[0], 0), 3), "lug_width": round(2 * lug["inner_x"], 3)}
    cfg_lug_to_lug = cfg["verified_mm"]["lug_to_lug"]
    for key, want in cfg["verified_mm"].items():
        tol = 0.02
        assert abs(out[key] - want) < tol, "%s %.3f != %.3f" % (key, out[key], want)
    for name in cfg["base_requires"]:
        assert name in bpy.data.objects, "base scene lacks " + name
    scene.camera = bpy.data.objects["CAM | Hero"]
    bpy.ops.file.make_paths_relative()  # external 2K maps stay outside the .blend and resolve relative to it
    bpy.context.view_layer.update()
    tris = sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")
    return {"measured_mm": out, "spec_lug_to_lug": cfg_lug_to_lug, "objects": len(coll.objects), "polygons": tris, "bracelet_rows": rows * 2, "library_materials": sorted(lib)}
