"""watch_seiko_ssa425: build the Seiko Presage Style60's SSA425J1 as a flat-backed front relief (like the other GLBs in models/watches/).

Params: spec (config/watches/seiko-ssa425j1.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_seiko_front (SNK607K1), whose helpers it reuses. This model's parts: round polished case with a thin steel lip, a black
60-minute bezel insert (photo map) and a polished inner ring, a tall box crystal, three-rib polished batons (wide at 12; 8 and 9
cut short by the open-heart aperture), faceted sword hour and minute hands with cream lume (broad triangular tail on the hour
hand), a seconds needle with a paddle counterweight, a small arrow hand on the 24-hour sub-dial, a fluted crown with a plain cap,
brushed lugs and a three-column brushed bracelet. Plan sizes from config/watches/seiko-ssa425j1-trace.json; heights from the
spec. The dial and the bezel insert share the photo map from pipeline/seiko_ssa425_dial.py. Rebuild with --force after
regenerating the map (the map is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    map_meta = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Seiko Presage SSA425J1 front relief")
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

    H = map_meta["half_size_mm"]

    def photo_mesh(name, g, open_profile=True):
        """Mesh with the photo map as a planar UV centred on the pivot (dial and bezel insert); an open profile is turned to face +z."""
        me = g.mesh(P + name, True)
        if open_profile and me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
        return me

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"])
    pose.scale = (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
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

    # ---- case with the steel lip and inner bezel ring, photo-mapped bezel insert, gasket, box crystal ----
    c, lg, rg = cfg["case"], cfg["lug"], tr["rings_mm"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    bi = cfg["bezel_insert"]
    ri, ro = rg["insert_inner"], rg["insert_outer"]
    add("bezel_insert", photo_mesh("bezel_insert", Geo().lathe([(ri, 8.7), (ro, 8.7), (ro, bi["z_outer"]), (ri, bi["z_inner"]), (ri, 8.7)], segs=192), False), "dial")
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr, cr_r = cfg["crystal"], gk["r_in"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr_r, cr["z0"]), (cr_r, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial (sub-dial, aperture, print, lume pads in the map) + sloped crystal wall up to the gasket ----
    add("dial", photo_mesh("dial", Geo().lathe([(0, d["z"]), (rg["dial_flat"], d["z"]), (cr_r, d["rehaut_z"])], segs=192)), "dial")

    # ---- applied three-rib batons: wide at 12, short where the open-heart aperture cuts the ray ----
    ix, ti = cfg["indices"], tr["indices"]
    ac, ar = tr["aperture"]["centre_mm"], tr["aperture"]["radius_mm"] + ix["clear_of_aperture"]
    z0, top, n, gap = d["z"], d["z"] + ix["height"], ix["ribs"], ix["rib_gap"]
    g = Geo()

    def ribs(width, r0, r1, deg):
        w = (width - (n - 1) * gap) / n
        for k in range(n):
            x = -width / 2 + w / 2 + k * (w + gap)
            g.prism([rot(px, py, deg) for px, py in rect(x, (r0 + r1) / 2, w, r1 - r0)], z0, top)

    for hour in range(1, 12):
        a = math.radians(hour * 30)
        r0 = ti["inner_mm"]
        while math.hypot(r0 * math.sin(a) - ac[0], r0 * math.cos(a) - ac[1]) < ar:
            r0 += 0.05
        ribs(ti["width_mm"], r0, ti["outer_mm"], hour * 30)
    i12 = ti["index_12_mm"]
    ribs(i12["x"][1] - i12["x"][0], *i12["r"], 0)
    add("indices", g, "steel_polished", bevel=ix["bevel"])

    # ---- hands at the photo's time: faceted sword hour and minute with lume, seconds needle with a paddle, 24-hour arrow ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, half, deg, z, origin=(0, 0)):
        g_ = Geo()
        place = lambda x, y: (origin[0] + rot(x, y, deg)[0], origin[1] + rot(x, y, deg)[1])
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g_, [place(sx * x, y) for x, y in half], z, lambda x, y: z + th + hs["ridge"] * _on_axis(x - origin[0], y - origin[1], deg))
        add(name, g_, "steel_polished", bevel=0.02)

    lume = Geo()
    for name in ("hour", "minute"):
        h = t[name]
        L, deg, z = h["length_mm"], h["angle_deg"], hs["z"][name]
        w0, wm, w1 = h["half_width_root_mm"], h["half_width_mid_mm"], h["half_width_tip_mm"]
        if name == "hour":  # broad triangular tail
            tail = [(0, -h["tail_mm"]), (h["tail_half_width_mm"], 0)]
        else:
            tw = hs["minute_tail_half_width"]
            tail = [(0, -h["tail_mm"]), (tw, -h["tail_mm"] + 0.3), (tw, 0)]
        hand("hand_" + name, tail + [(w0, 0.25 * L), (wm, 0.75 * L), (w1, 0.95 * L), (0, L)], deg, z)
        f0, f1 = h["lume"]
        half_at = lambda f: float(_interp(f, [0.25, 0.75, 0.95], [w0, wm, w1])) - h["lume_inset_mm"]
        fs = [f0 + (f1 - f0) * k / 6 for k in range(7)]
        outline = [(half_at(f), f * L) for f in fs] + [(-half_at(f), f * L) for f in reversed(fs)]
        zl = z + th + hs["ridge"]
        lume.prism([rot(x, y, deg) for x, y in outline], zl - hs["ridge"] * 0.6, zl + hs["lume_height"])
    add("hand_lume", lume, "lume")
    h = t["seconds"]
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], h["tail_half_width_mm"]
    poly = [(nw, 0), (nw, L - 0.3), (0, L), (-nw, L - 0.3), (-nw, 0), (-cw * 0.6, -0.8), (-cw, -1.4), (-cw, -tail + cw), (0, -tail),
            (cw, -tail + cw), (cw, -1.4), (cw * 0.6, -0.8)]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in poly], z, z + th), "steel_polished", bevel=0.02)
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"]), (0, hs["z"]["minute"])], segs=48), "steel_polished")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, z - 0.1), (cap_r, z - 0.1), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    s24 = t["sub24"]
    L, (f0, f1), aw, nw, z = s24["length_mm"], s24["arrow"], s24["arrow_half_width_mm"], s24["half_width_mm"], hs["z"]["sub24"]
    o24 = s24["pivot_mm"]
    poly = [(nw, 0), (nw, f0 * L), (aw, f0 * L), (nw, f1 * L), (nw, L - 0.15), (0, L), (-nw, L - 0.15), (-nw, f1 * L), (-aw, f0 * L), (-nw, f0 * L), (-nw, 0)]
    add("hand_sub24", Geo().prism([(o24[0] + rot(x, y, s24["angle_deg"])[0], o24[1] + rot(x, y, s24["angle_deg"])[1]) for x, y in poly], z, z + th),
        "steel_polished", bevel=0.02)
    cr24 = s24["cap_radius_mm"]
    m24 = Matrix.Translation((o24[0], o24[1], 0))
    add("hub_sub24", Geo().lathe([(0, d["z"]), (cr24, d["z"]), (cr24, z + th + 0.05), (cr24 * 0.5, z + th + 0.12), (0, z + th + 0.12)], segs=32, m=m24),
        "steel_polished", smooth=True)

    # ---- crown: fluted cylinder plus a plain domed cap on a radial axis at the traced angle (3 o'clock) ----
    cw_, cb = cfg["crown"], tr["crown_box"]
    a = math.radians(math.degrees(math.atan2(*cb["centre_mm"])) % 360)
    r_fl, r_to = cb["flutes_to_mm"], cb["x0_y0_x1_y1_mm"][2]
    star = [((cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.cos(math.pi * i / cw_["teeth"]),
             (cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.sin(math.pi * i / cw_["teeth"])) for i in range(cw_["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    add("crown", Geo().prism(star, cw_["r_from"], r_fl, m), "steel_polished", bevel=0.15)
    cap = [(0, r_fl), (cw_["radius"] - 0.1, r_fl), (cw_["cap_radius"], r_to - 0.3), (cw_["cap_radius"] * 0.6, r_to), (0, r_to)]
    add("crown_cap", Geo().lathe(cap, segs=48, m=m), "steel_polished", smooth=True)

    # ---- brushed lugs from the traced silhouette (left/right and top/bottom averaged), polished bevel ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    tip = tr["lug_tip_mm"]["mean"]
    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- three brushed columns: outer links from the lug tips, the centre column `shift` nearer the case ----
    br, el, tb = cfg["bracelet"], cfg["end_link"], tr["bracelet"]
    ch, gap, hw, shift = tb["centre_half_mm"], br["gap"], br["half_width"], tb["centre_shift_mm"]
    outers = [(ch + gap, hw), (-hw, -ch - gap)]
    end = Geo()
    for sy in (1, -1):
        for (x0, x1), y1 in [(c_, tip) for c_ in outers] + [((-ch, ch), tip - shift - gap)]:
            end.prism(rect((x0 + x1) / 2, sy * (el["from_y"] + y1) / 2, x1 - x0, y1 - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)

    zm, R = ds * (br["z0"] + br["z_outer"]) / 2, br["bend_radius"]  # built at final depth: flattened thickness, unflattened curve
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    pitch = tb["pitch_mm"]
    links, back = Geo(), Geo()
    rows = 0
    za = ds * br["z0"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip - shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                if kind == "outer":
                    for x0, x1 in outers:
                        bent_box(links, x0, x1, y0, y1, za, ds * br["z_outer"], sy)
                    bent_box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(links, -ch, ch, y0, y1, za, ds * br["z_centre"], sy)
                y0 = y1 + gap
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
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


def _interp(f, xs, ys):
    if f <= xs[0]:
        return ys[0]
    for (x0, x1), (y0, y1) in zip(zip(xs, xs[1:]), zip(ys, ys[1:])):
        if f <= x1:
            return y0 + (y1 - y0) * (f - x0) / (x1 - x0)
    return ys[-1]


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
