"""watch_seiko_sfj003: build the Seiko SFJ003P1 (solar 1/100 s chronograph, four subdials, three-column bracelet) as a
flat-backed front relief.

Params: spec (config/watches/seiko-sfj003p1.json). Same frame as watch_seiko_ssb479: mm, origin = dial centre, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final
depth with the house curl. Parts: round brushed case with straight shoulders out to the lug corners, polished sloped bezel,
the dial, subdials and printed flange from one photo map (pipeline/seiko_sfj003_dial.py, all hands removed), applied
batons with white lume on the time subdial at 6, sword hour and minute hands on that subdial's pivot, white paddle hands
on the 12, 9 and 3 subdials, three pushers (10, 8, 2) and a fluted crown at 4, and a three-column bracelet: outer links
from the lug tips, centre links half a row further out. Rebuild with --force after regenerating the photo map.
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
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Seiko SFJ003P1 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)
    textured = cfg.get("steel_textures", {})
    for key, tx in textured.items():  # brushed lines as a tangent-space normal map (plain image link, kept by the GLB)
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

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]
    H = pm["half_mm"]
    photo_uv = lambda x, y: (0.5 + x / (2 * H), 0.5 + y / (2 * H))

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV, lines along the bracelet (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if uv_of:
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co)
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

    def upward(me):
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg = tr["rings_mm"]
    # ---- case, polished bezel, photo-mapped dial + flange cone, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_brushed", bevel=0.2, polished_bevel=True)
    add("bezel", Geo().lathe([tuple(p) for p in cfg["bezel"]["profile_rz"]], segs=192), "steel_polished")
    d, ri = cfg["dial"], rg["bezel_inner"]
    me = upward(Geo().lathe([(0, d["z"]), (rg["flange_inner"], d["z"]), (ri, d["wall_top_z"])], segs=192).mesh(P + "dial", True))
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (ri, cr["z0"]), (ri, cr["z_edge"]), (ri - cr["chamfer"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- time subdial at 6: applied batons with white lume, long at 12, 3, 6, 9 ----
    ix, ti = cfg["time_indices"], tr["time_indices"]
    px, py = tr["time_pivot_mm"]
    at_pivot = lambda pts: [(x + px, y + py) for x, y in pts]
    zb_, zt = d["z"], d["z"] + ix["height"]
    steel, lume = Geo(), Geo()
    w, li = ti["width_mm"], ix["lume_inset"]
    for hr in range(1, 13):
        r0, r1 = ti["long_mm"] if hr % 3 == 0 else ti["short_mm"]
        steel.prism(at_pivot([rot(x, y, hr * 30) for x, y in rect(0, (r0 + r1) / 2, w, r1 - r0)]), zb_, zt)
        lume.prism(at_pivot([rot(x, y, hr * 30) for x, y in rect(0, (r0 + r1) / 2, w - 2 * li, r1 - r0 - 2 * li)]), zt, zt + ix["lume_height"])
    add("indices", steel, "steel_polished", bevel=0.04)
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time: hour and minute on the time subdial, white paddles on the chronograph subdials ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism(at_pivot(t[name]["outline_mm"]), z, z + th), "steel_polished", bevel=0.03)
        add("hand_%s_lume" % name, Geo().prism(at_pivot(t[name]["lume_mm"]), z + th, z + th + 0.03), "lume")
    hub_r, cap_r = tr["hub_radius_mm"]
    zc = hs["z"]["minute"] + th
    ch = hs["hub_cap_height"]
    hub_m = Matrix.Translation((px, py, 0))
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zc), (0, zc)], segs=48, m=hub_m), "steel_polished")
    add("hub_cap", Geo().lathe([(0, zc), (hub_r, zc), (hub_r, zc + ch * 0.5), (cap_r, zc + ch), (0, zc + ch)], segs=48, m=hub_m), "steel_polished")
    subs, zs = Geo(), hs["z"]["sub"]
    for k, s in tr["subdials"].items():
        if "outline_mm" in s:
            sx, sy = s["pivot_mm"]
            subs.prism([(x + sx, y + sy) for x, y in s["outline_mm"]], zs, zs + hs["sub_thickness"])
    add("hands_subdials", subs, "hand_white", bevel=0.02)

    # ---- crown (fluted) and pushers (stem + grooved cap) on radial axes ----
    def radial(a_deg, z):
        a = math.radians(a_deg)
        m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
        m.translation = (0, 0, z)
        return m

    cw = cfg["crown"]
    n = cw["teeth"]
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.cos(math.pi * i / n),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.sin(math.pi * i / n)) for i in range(2 * n)]
    circ = lambda r: [(r * math.cos(2 * math.pi * k / 40), r * math.sin(2 * math.pi * k / 40)) for k in range(40)]
    a_cr = tr["crown"]["angle_deg"]
    add("crown_collar", Geo().prism(circ(cw["collar_radius"]), cw["collar_from"], cw["r_from"], radial(a_cr, cw["z"])), "steel_polished", bevel=0.1)
    add("crown", Geo().prism(star, cw["r_from"], tr["crown"]["end_r_mm"], radial(a_cr, cw["z"])), "steel_polished", bevel=0.15)
    pu = cfg["pushers"]
    g0, g1, gr = pu["groove"]
    stems, caps = Geo(), Geo()
    for v in tr["pushers"].values():
        m = radial(v["angle_deg"], cw["z"])
        stems.prism(circ(pu["stem_radius"]), pu["stem_from"], pu["cap_from"], m)
        stems.prism(circ(gr), g0, g1, m)
        caps.prism(circ(pu["cap_radius"]), pu["cap_from"], g0, m)
        caps.prism(circ(pu["cap_radius"]), g1, v["end_r_mm"], m)
    add("pusher_stems", stems, "steel_polished", bevel=0.08)
    add("pusher_caps", caps, "steel_polished", bevel=0.2)

    # ---- shoulders/lugs: left silhouette measured from each side's own tip and averaged; straight edge below the corner ----
    lg = cfg["lug"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    q = lambda y: round(round(y * 4) / 4, 2)
    tips = tr["lug_tip_mm"]
    tip = tips["mean"]
    left = lambda dd: (-sil[q(tips["top"] - dd)][1] - sil[q(-(tips["bottom"] - dd))][1]) / 2  # dd = distance below the tip
    fit = [(tip - dd, left(dd)) for dd in [k * 0.25 for k in range(1, 80)] if lg["line_fit_y"][0] <= tip - dd <= lg["line_fit_y"][1]]
    my_, mx_ = sum(p[0] for p in fit) / len(fit), sum(p[1] for p in fit) / len(fit)
    slope_ = sum((y - my_) * (x - mx_) for y, x in fit) / sum((y - my_) ** 2 for y, _ in fit)
    line = lambda y: mx_ + slope_ * (y - my_)
    edge = [(min(left(dd), line(tip - dd)), tip - dd) for dd in [k * 0.25 for k in range(1, 80)] if tip - dd > lg["line_fit_y"][0]]
    # inner side follows a circle under the brushed case slope, so the slab never shows inside the bezel
    rc, ix_ = lg["inner_r"], lg["inner_x"]
    a0, a1 = math.atan2(lg["from_y"], math.sqrt(rc * rc - lg["from_y"] ** 2)), math.atan2(math.sqrt(rc * rc - ix_ * ix_), ix_)
    arc = [(rc * math.cos(a0 + (a1 - a0) * k / 12), rc * math.sin(a0 + (a1 - a0) * k / 12)) for k in range(13)]
    outline = arc + [(ix_, tip)] + edge + [(line(lg["from_y"]), lg["from_y"])]
    top = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, top)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- three columns with the house curl: outer links from the lug tips, centre links `shift` further out ----
    br, el = cfg["bracelet"], cfg["end_link"]
    fc = tr["bracelet_centre_fraction"]
    pitch, gap = tr["bracelet_pitch_mm"], br["gap"]
    outer0 = tip + tr["bracelet_outer_start_after_tip_mm"]
    centre0 = outer0 + tr["bracelet_centre_joint_shift_mm"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    width = lambda y: (sil[q(y)][2] - sil[q(y)][1] + sil[q(-y)][2] - sil[q(-y)][1]) / 4
    hw_at = lambda y: min(width(min(max(y, tip + 1.0), sil_max)), el["half_width"])

    def columns(hw):
        """[(x0, x1, kind)] for one row."""
        return [(-fc * hw, fc * hw, "centre"), (fc * hw + gap, hw, "outer"), (-hw, -(fc * hw + gap), "outer")]

    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip + br["bend_after_tip"], br["bend_radius"], zm)
    za, zb = ds * br["z0"], ds * br["z1"]
    links, ends, back = Geo(), Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for x0, x1, kind in columns(el["half_width"]):
            box(ends, x0, x1, el["from_y"], (outer0 if kind == "outer" else centre0) - gap, 0.0, ds * el["top_z"], sy)
        for kind, start in (("outer", outer0), ("centre", centre0)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                hw = hw_at((y0 + y1) / 2)
                for x0, x1, k in columns(hw):
                    if k == kind:
                        box(links, x0, x1, y0, y1, za, zb, sy)
                if kind == "outer":
                    box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                y0 = y1 + gap
    add("bracelet_end_links", ends, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_width": round(2 * hw_at(tip + 1.0), 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "shoulder_slope": round(slope_, 3), "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
