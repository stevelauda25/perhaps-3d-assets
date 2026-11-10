"""watch_orient_ra_ac0e01b10b: build the Orient RA-AC0E01B10B (Contemporary, black dial, steel bracelet) as a flat-backed front
relief, the house way (modelled parts, house steel and glass, photo map only for the dial print).

Params: spec (config/watches/orient-ra-ac0e01b10b.json). Same frame, pose, depth scale, materials and bracelet curl as
watch_orient_re_au01, whose structure it follows without the power reserve and numerals. Own construction from the photos:
round case with a wide sloped polished bezel, lugs (brushed top, polished outer facet) from the photo silhouette on the 6 o'clock
side (it faces the camera), fluted crown with a smooth end cap, applied faceted batons (the 3 starting further out beside the date), faceted stick hour and minute hands, a polished seconds needle with a paddle counterweight, and a
three-column bracelet (brushed) whose centre joints sit nearer the case than the outer ones. Plan sizes from
config/watches/orient-ra-ac0e01b10b-trace.json; heights from the spec. Rebuild with --force after regenerating the dial map
(pipeline/orient_ra_ac0e01b10b_dial.py; the map is not part of the stage fingerprint).
"""
import json
import math

import bmesh
import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def ribbon(geo, rows, sx, sy):
    """Solid swept along y: rows of (y, xa, xb, top at xa, top at xb), flat bottom at z = 0, mirrored by sx, sy."""
    base = len(geo.v)
    for y, xa, xb, za, zb in rows:
        geo.v += [(sx * xa, sy * y, 0.0), (sx * xb, sy * y, 0.0), (sx * xb, sy * y, zb), (sx * xa, sy * y, za)]
    faces = [(0, 1, 2, 3)]
    for k in range(len(rows) - 1):
        b, c = 4 * k, 4 * k + 4
        faces += [(b, c, c + 1, b + 1), (b + 1, c + 1, c + 2, b + 2), (b + 2, c + 2, c + 3, b + 3), (b + 3, c + 3, c, b)]
    e = 4 * (len(rows) - 1)
    faces.append((e + 3, e + 2, e + 1, e))
    for f in faces:
        geo.f.append(tuple(base + i for i in f))
        geo.smooth.append(False)


def outward(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return me


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
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

    def brushed_uv(me, tile_mm):
        """Planar UV in mm / tile, turned 90 deg so the texture's lines (along image X) run along the bracelet (model Y)."""
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (y / tile_mm, -x / tile_mm)

    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    H = dm["half_size_mm"]

    def dial_uv(me):
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"])
    pose.scale = (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None, fix_normals=False):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        if fix_normals:
            outward(me)
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
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    # ---- case with the wide sloped polished bezel (full circle: end links run under it), gasket, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished")
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + rehaut, photo map on a planar UV ----
    me = Geo().lathe([(0, d["z"]), (tr["rings_mm"]["dial"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    dial_uv(me)
    add("dial", me, "dial")

    # ---- applied indices: faceted batons (ridge on the centre line), the 3 shortened beside the date; polished date frame ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    g = Geo()
    for hour in range(1, 13):
        r0, r1 = ti["at_3"] if hour == 3 else (ti["inner_mm"], ti["outer_mm"])
        hw = ti["width_mm"] / 2
        half = [(0, r0), (hw, r0), (hw, r1), (0, r1)]
        for sx in (1, -1):
            slab(g, [rot(sx * x, y, hour * 30) for x, y in half], z0, lambda x, y, h=hour: top + ix["ridge"] * _on_axis(x, y, h))
    add("indices", g, "steel_polished", bevel=0.04)
    dx0, dy0, dx1, dy1 = tr["date_window"]["x0_y0_x1_y1_mm"]
    f = ix["date_frame"]
    if f > 0:  # plain cut-out on this dial: no frame
        add("date_frame", plate([{"outer": [[dx0 - f, dy0 + f], [dx1 + f, dy0 + f], [dx1 + f, dy1 - f], [dx0 - f, dy1 - f]],
                                  "holes": [[[dx0, dy0], [dx1, dy0], [dx1, dy1], [dx0, dy1]]]}], z0, z0 + ix["date_frame_height"], P + "date_frame"),
            "steel_polished")

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def faceted(name, half, deg, z, centre=(0, 0), mat="steel_polished"):
        g_ = Geo()
        for sx in (1, -1):
            pts = [rot(sx * x, y, deg) for x, y in half]
            slab(g_, [(centre[0] + x, centre[1] + y) for x, y in pts], z,
                 lambda x, y, deg=deg: z + th + hs["ridge"] * _on_axis(x - centre[0], y - centre[1], deg / 30))
        add(name, g_, mat, bevel=0.02)

    for name in ("hour", "minute"):  # faceted sticks: ridge on the centre line, pointed tip, short tail
        h = t[name]
        L, tail, (w0, w1) = h["length_mm"], h["tail_mm"], h["half_width_mm"]
        w0, w1 = w0 * hs["width_scale"], w1 * hs["width_scale"]
        faceted("hand_" + name, [(0, -tail), (w0, -tail + 0.3), (w0, 0.5), (w1, L - 1.2), (0, L)], h["angle_deg"], hs["z"][name])
    h = t["seconds"]  # polished needle, paddle counterweight widest at its end
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], h["tail_half_width_mm"] * hs["width_scale"]
    g = Geo().prism([rot(x, y, deg) for x, y in [(nw, 0), (nw * 0.6, L), (-nw * 0.6, L), (-nw, 0)]], z, z + th)
    g.prism([rot(x, y, deg) for x, y in [(0.12, 0.4), (cw, -tail + 0.5), (cw * 0.7, -tail), (-cw * 0.7, -tail), (-cw, -tail + 0.5), (-0.12, 0.4)]], z, z + th)
    add("hand_seconds", g, "steel_polished", bevel=0.02)
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["hour"] + th), (cap_r * 1.6, z), (0, z)], segs=48), "steel_polished")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r * 1.6, zc), (cap_r * 1.6, zc + 0.08), (cap_r, zc + 0.14), (0, zc + 0.14)], segs=48), "steel_polished")

    # ---- crown on the 3 o'clock axis: fluted body, smooth end cap ----
    cw_ = ct = cfg["crown"]
    teeth, rad, fd = cw_["teeth"], ct["radius"], cw_["flute_depth"]
    star = [((rad if i % 2 == 0 else rad - fd) * math.cos(math.pi * i / teeth), (rad if i % 2 == 0 else rad - fd) * math.sin(math.pi * i / teeth))
            for i in range(teeth * 2)]
    m = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0))).to_4x4()  # local z -> +x (radial axis at 3 o'clock), local y -> +z
    m.translation = (0, 0, cw_["z"])
    add("crown", Geo().prism(star, ct["r_from"], ct["flute_to"], m), "steel_polished", bevel=0.12)
    cap = ct["cap_radius"]
    add("crown_cap", Geo().lathe([(0, ct["flute_to"] - 0.1), (cap, ct["flute_to"] - 0.1), (cap, ct["cap_to"] - 0.25),
                                  (cap - 0.3, ct["cap_to"]), (0, ct["cap_to"])], segs=64, m=m), "steel_polished")

    # ---- lugs from the photo silhouette: brushed top sloping toward the tip, polished outer facet ----
    lg = cfg["lug"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):  # 6 o'clock side (faces the camera); half the width, symmetric about the pivot
        p = sil[round(-abs(y), 2)]
        return (p[2] - p[1]) / 2

    tip = lg["tip"]
    rows_top, rows_facet = [], []
    y = lg["from_y"]
    while y <= tip + 1e-6:
        xo = half(round(y * 4) / 4)
        xi = max(lg["inner_x"], math.sqrt(max(lg["case_r_in"] ** 2 - y * y, 0)))
        xf = max(xi + 0.3, xo - min(lg["facet_width"], 0.6 * (xo - xi)))
        zt = lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (y - lg["from_y"]) / (tip - lg["from_y"])
        rows_top.append((y, xi, xf, zt, zt))
        rows_facet.append((y, xf, xo, zt, zt - lg["facet_drop"]))
        y += 0.25
    g_top, g_facet = Geo(), Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            ribbon(g_top, rows_top, sx, sy)
            ribbon(g_facet, rows_facet, sx, sy)
    add("lugs", g_top, "steel_brushed", bevel=lg["bevel"], polished_bevel=True, fix_normals=True)
    add("lug_facets", g_facet, "steel_polished", bevel=lg["bevel"], fix_normals=True)

    # ---- bracelet: brushed centre and outer links; centre joints `shift` nearer the case ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, shift, gap = tr["bracelet_centre_half_mm"], tr["bracelet_centre_joint_shift_mm"], br["gap"]
    sil_max = -min(sil) - 0.25
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), el["half_width"])

    end = Geo()
    for sy in (1, -1):
        M = Matrix.Translation((0, sy * (el["from_y"] + tip) / 2, 0))
        for sx in (1, -1):
            end.prism(rect(sx * (ch + gap + el["half_width"]) / 2, 0, el["half_width"] - ch - gap, tip - el["from_y"]), 0.0, el["top_z"], M)
        y1 = tip - shift - gap
        end.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]  # built at final depth: flattened thickness, unflattened curve
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    pitch = tr["bracelet_pitch_mm"]
    brushed, back = Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip - shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                hw = hw_at((y0 + y1) / 2)
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw))
                        bent_box(brushed, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(brushed, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, hour):
    """1 on the radial centre line through angle hour * 30 deg (the ridge), 0 elsewhere."""
    a = math.radians(hour * 30)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
