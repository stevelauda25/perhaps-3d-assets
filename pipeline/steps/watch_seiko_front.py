"""watch_seiko_front: build the Seiko 5 SNK607K1 as a flat-backed front relief (like the Casio GLBs in models/watches/).

Params: spec (config/watches/seiko-snk607k1-v1.json). Model in mm, origin = hand pivot, dial faces +z, back flat at z = 0,
under one pose empty `SKO | pose` (scale 0.001, rotated 90 deg about X so the dial faces -Y in Blender and +Z in glTF).
Plan sizes come from the trace (config/watches/seiko-snk607k1-trace.json); heights from the spec. The dial is the photo map
from pipeline/seiko_dial.py on a planar UV. Materials are plain Principled BSDFs with direct image links so the GLB keeps
them. Rebuild with --force after regenerating the dial map (the map is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot

P = "SKO | "


def principled(name, p):
    m = bpy.data.materials.new(P + name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    for key, value in {"Base Color": (*p["color"], 1), "Metallic": p["metallic"], "Roughness": p["roughness"],
                       "Transmission Weight": p.get("transmission"), "IOR": p.get("ior"), "Alpha": p.get("alpha")}.items():
        if value is not None:
            b.inputs[key].default_value = value
    return m


def photo_material(name, image_path, roughness):
    m = bpy.data.materials.new(P + name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    im = bpy.data.images.load(str(image_path), check_existing=True)
    im.pack()
    tex = nodes.new("ShaderNodeTexImage")
    tex.image, tex.interpolation, tex.location = im, "Cubic", (-400, 200)
    links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = 0.0, roughness
    return m


def slab(g, poly, z0, top):
    """Like Geo.prism, but the top of each vertex is top(x, y): sloped lug tops."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    poly = poly if area > 0 else poly[::-1]
    n, base = len(poly), len(g.v)
    g.v += [(x, y, z0) for x, y in poly] + [(x, y, top(x, y)) for x, y in poly]
    g.f += [tuple(range(base + n - 1, base - 1, -1)), tuple(range(base + n, base + 2 * n))]
    g.f += [(base + i, base + (i + 1) % n, base + n + (i + 1) % n, base + n + i) for i in range(n)]
    g.smooth += [False] * (n + 2)
    return g


def plate(shapes, z0, z1, name):
    """Solid from traced outlines with holes ({"outer", "holes"} in mm): capped top and bottom, walls on every loop."""
    from mathutils import Vector, geometry as mg
    verts, faces = [], []
    for sh in shapes:
        loops = []
        for i, lp in enumerate([sh["outer"]] + sh["holes"]):
            area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(lp, lp[1:] + lp[:1]))
            loops.append(lp if (area > 0) == (i == 0) else lp[::-1])  # outer counter-clockwise, holes clockwise
        offs = []
        for lp in loops:
            o, n = len(verts), len(lp)
            offs.append(o)
            verts += [(x, y, z0) for x, y in lp] + [(x, y, z1) for x, y in lp]
            faces += [(o + i, o + (i + 1) % n, o + n + (i + 1) % n, o + n + i) for i in range(n)]
        flat = [(o, len(lp)) for o, lp in zip(offs, loops)]

        def where(k):
            for o, n in flat:
                if k < n:
                    return o, n, k
                k -= n

        for tri in mg.tessellate_polygon([[Vector((x, y, 0)) for x, y in lp] for lp in loops]):
            pts = [where(k) for k in tri]
            xy = [verts[o + k][:2] for o, n, k in pts]
            ccw = (xy[1][0] - xy[0][0]) * (xy[2][1] - xy[0][1]) - (xy[1][1] - xy[0][1]) * (xy[2][0] - xy[0][0]) > 0
            top = tuple(o + n + k for o, n, k in pts)
            bottom = tuple(o + k for o, n, k in pts)
            faces += [top if ccw else top[::-1], bottom[::-1] if ccw else bottom]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    return me


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Seiko 5 SNK607K1 front relief")
    scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    textured = cfg.get("steel_textures", {})
    for key, tx in textured.items():  # brushed lines as a tangent-space normal map: a plain image link, so the GLB keeps it
        nodes, links = mats[key].node_tree.nodes, mats[key].node_tree.links
        b = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        im = bpy.data.images.load(str(ROOT / tx["normal"]), check_existing=True)
        im.colorspace_settings.name = "Non-Color"
        im.pack()
        tex, nm = nodes.new("ShaderNodeTexImage"), nodes.new("ShaderNodeNormalMap")
        tex.image, tex.location, nm.location = im, (-600, -300), (-250, -300)
        nm.inputs["Strength"].default_value = tx["strength"]
        links.new(tex.outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], b.inputs["Normal"])
    parts = {}

    def brushed_uv(me, tile_mm):
        """Planar UV in mm / tile, turned 90 deg so the texture's lines (along image X) run along the bracelet (model Y)."""
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (y / tile_mm, -x / tile_mm)

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.scale, pose.location = (math.pi / 2, 0, 0), (0.001,) * 3, (0, 0, cfg["pose"]["z_m"])

    def add(name, geo, mat, bevel=None, polished_bevel=False):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:
            brushed_uv(me, textured[mat]["tile_mm"])
        if bevel:
            if polished_bevel:
                me.materials.append(mats["steel_polished"])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        parts[name] = o
        return o

    # ---- case, gasket, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + rehaut, photo map on a planar UV ----
    g = Geo().lathe([(0, d["z"]), (d["texture_edge_r"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192)
    me = g.mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    H = d["map_half_mm"]
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied indices (polished batons with a dark centre line), day-date frame ----
    ix, top = cfg["indices"], d["z"] + cfg["indices"]["height"]
    radii = tr["indices"]["inner_outer_radius_mm"]
    full, short = radii["9"], radii["6"]
    g, line = Geo(), Geo()
    for hour in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        r0, r1 = short if hour == 6 else full
        rc, ln = (r0 + r1) / 2, r1 - r0
        if hour == 12:
            for sx in (-ix["double_offset"], ix["double_offset"]):
                g.prism(rect(sx, rc, ix["double_width"], ln), d["z"], top)
            continue
        g.prism([rot(x, y, hour * 30) for x, y in rect(0, rc, ix["width"], ln)], d["z"], top)
        line.prism([rot(x, y, hour * 30) for x, y in rect(0, rc, ix["line_width"], ln - 0.3)], top, top + 0.02)
    add("indices", g, "steel_polished", bevel=0.05)
    add("index_lines", line, "index_line")
    fr, box = cfg["daydate_frame"], tr["daydate_frame"]
    (fx, fy), (fw, fh), wl = box["centre_mm"], box["size_mm"], cfg["daydate_frame"]["wall"]
    g = Geo()
    for cx_, cy_, w_, h_ in ((fx, fy + fh / 2 - wl / 2, fw, wl), (fx, fy - fh / 2 + wl / 2, fw, wl),
                             (fx - fw / 2 + wl / 2, fy, wl, fh - 2 * wl), (fx + fw / 2 - wl / 2, fy, wl, fh - 2 * wl)):
        g.prism(rect(cx_, cy_, w_, h_), d["z"], d["z"] + fr["height"])
    add("daydate_frame", g, "steel_polished")

    # ---- applied "5" shield (traced outline, the 5 is a hole showing the dial) and lume dots ----
    lg_ = cfg["logo"]
    add("logo_5_shield", plate(tr["logo_5_shield_shapes"], d["z"], d["z"] + lg_["shield_height"], P + "logo_5_shield"), "steel_polished")
    g = Geo()
    for dot in tr["lume_dots"].values():
        x, y = rot(0, dot["radius_mm"], dot["angle_deg"])
        g.lathe([(0, d["z"]), (lg_["lume_dot_radius"], d["z"]), (lg_["lume_dot_radius"], d["z"] + 0.05), (0, d["z"] + 0.05)], segs=24, m=Matrix.Translation((x, y, 0)))
    add("lume_dots", g, "lume")

    # ---- hands at the photo's time (traced angles and lengths) ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    t = tr["hands"]

    def hand(name, poly, deg, z0, mat):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z0, z0 + th), mat, bevel=0.03)

    for name in ("hour", "minute"):
        L, s = t[name]["length_mm"], hs[name]
        hw, rw = s["half_width"], s["root_half_width"]
        hand("hand_" + name, [(-rw, -1.0), (rw, -1.0), (hw, 0.5), (hw, L - 1.2), (0, L), (-hw, L - 1.2), (-hw, 0.5)], t[name]["angle_deg"], hs["z"][name], "steel_polished")
        a, b = t[name]["lume_from_to_mm"]
        z = hs["z"][name] + th
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, t[name]["angle_deg"]) for x, y in rect(0, (a + b) / 2, 2 * s["lume_half_width"], b - a)], z, z + 0.03), "lume")
    s, L, tail, deg = hs["seconds"], t["seconds"]["length_mm"], t["seconds"]["tail_mm"], t["seconds"]["angle_deg"]
    hand("hand_seconds", rect(0, (L - tail) / 2, 2 * s["half_width"], L + tail), deg, hs["z"]["seconds"], "seconds_red")
    hand("hand_seconds_counterweight", rect(0, -(tail + s["counterweight_from"]) / 2, 2 * s["counterweight_half_width"], tail - s["counterweight_from"]), deg, hs["z"]["seconds"], "seconds_red")
    tx, ty = rot(0, L - 0.35, deg)
    z = hs["z"]["seconds"] + th
    add("hand_seconds_tip", Geo().lathe([(0, z), (s["tip_dot_radius"], z), (s["tip_dot_radius"], z + 0.03), (0, z + 0.03)], segs=24, m=Matrix.Translation((tx, ty, 0))), "lume")
    hb = hs["hub"]
    add("hub", Geo().lathe([(0, d["z"]), (hb["radius"], d["z"]), (hb["radius"], hs["z"]["seconds"]), (0, hs["z"]["seconds"])], segs=48), "steel_polished")
    zc = hs["z"]["seconds"] + th
    add("hub_cap", Geo().lathe([(0, zc), (hb["cap_radius"], zc), (hb["cap_radius"], zc + hb["cap_height"] * 0.6), (hb["cap_radius"] * 0.6, zc + hb["cap_height"]), (0, zc + hb["cap_height"])], segs=48), "seconds_red")

    # ---- crown: fluted cylinder on a radial axis at the traced angle (4 o'clock) ----
    cw = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, cw["r_from"], cw["r_to"], m), "steel_polished", bevel=0.15)

    # ---- lugs and end links from the traced silhouette (left/right and top/bottom averaged: the photo is 0.35 mm off-centre) ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    lg = cfg["lug"]
    tip = next(y / 4 for y in range(64, 160) if half(y / 4) < lg["inner_x"] + 0.35)
    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)
    # ---- bracelet: centre links start at the case, outer links at the lug tips (half a row apart, as in the photo) ----
    br, el = cfg["bracelet"], cfg["end_link"]
    hw_at = lambda y: half(round(min(max(y, tip), br["end_y"] - 0.25) * 4) / 4)  # silhouette rows are 0.25 mm apart
    cw_at = lambda y: br["centre_ratio"] * hw_at(y)
    g = Geo()  # end-link sides: between the first centre link and the lugs, from inside the case to the lug tips
    for sy in (1, -1):
        for sx in (1, -1):
            x0 = cw_at(tip) + br["gap"]
            g.prism(rect(sx * (x0 + lg["inner_x"]) / 2, sy * (lg["from_y"] + tip) / 2, lg["inner_x"] - x0, tip - lg["from_y"]), 0.0, el["top_z"])
    add("end_links", g, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    links, back = Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for start, centre in ((br["centre_start_y"], True), (tip, False)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + br["pitch"] - br["gap"], br["end_y"])
                ym = (y0 + y1) / 2
                if centre:
                    links.prism(rect(0, sy * ym, 2 * cw_at(ym), y1 - y0), br["z0"], br["z1"])
                    rows += 1
                else:
                    x0, x1 = cw_at(ym) + br["gap"], hw_at(ym)
                    for sx in (1, -1):
                        links.prism(rect(sx * (x0 + x1) / 2, sy * ym, x1 - x0, y1 - y0), br["z0"], br["z1"])
                y0 += br["pitch"]
        y_back = min(br["centre_start_y"], tip) - 1
        back.prism(rect(0, sy * (y_back + br["end_y"]) / 2, 2 * (hw_at(tip) - 0.3), br["end_y"] - y_back), *br["backing_z"])
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    near = sorted(p[2] - p[1] for y, p in sil.items() if 22 <= abs(y) <= 24)  # same rows as the trace's check
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "bracelet_next_to_case": round(near[len(near) // 2], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
