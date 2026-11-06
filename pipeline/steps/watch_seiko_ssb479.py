"""watch_seiko_ssb479: build the Seiko SSB479P1 (quartz chronograph, black tachymeter bezel, five-column bracelet) as a
flat-backed front relief.

Params: spec (config/watches/seiko-ssb479p1.json). Same frame as watch_seiko_sur419_front: mm, origin = case and dial
centre, dial faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale,
bracelet built at final depth with the house curl. Differences: a steel bezel edge around a photo-mapped black tachymeter
insert, a sloped crystal wall and the dial from the same photo map (subdials, date and print stay in it), polished batons
with a cream lume tip (wide at 12, short at 3, 6, 9), silver sword hands with lume and a long chronograph needle with a
tapered counterweight, a fluted crown with two cylindrical pushers, and a bracelet of five columns: brushed outer and
centre links sharing joints at the lug tips, polished narrow links whose joints sit nearer the case. Rebuild with --force
after regenerating the photo map (pipeline/seiko_ssb479_dial.py).
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
    coll = bpy.data.collections.new("WATCH | Seiko SSB479P1 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():  # one image, two surfaces
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
    # ---- case, steel bezel edge, photo-mapped tachymeter insert, crystal wall + dial, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished")
    bz = cfg["bezel"]
    add("bezel", Geo().lathe([tuple(p) for p in bz["profile_rz"]], segs=192), "steel_polished")
    ri, ro = rg["insert_inner"], rg["insert_outer"]
    dx = tr["insert_centre_mm"][0]  # the insert sits right of the dial centre in the photo
    z0, (zi, zo) = bz["insert_z0"], bz["insert_top_z"]
    add("bezel_insert", upward(Geo().lathe([(ri, z0), (ro, z0), (ro, zo), (ri, zi), (ri, z0)], segs=192).mesh(P + "bezel_insert", True)),
        "bezel_insert", uv_of=lambda x, y, z: photo_uv(x + dx, y))
    d = cfg["dial"]
    me = upward(Geo().lathe([(0, d["z"]), (rg["dial_edge"], d["z"]), (ri, d["wall_top_z"])], segs=192).mesh(P + "dial", True))
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (ri, cr["z0"]), (ri, cr["z_edge"]), (ri - cr["chamfer"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- applied batons, cream lume at the outer end; wide at 12, short at 3, 6, 9 ----
    ix, ti = cfg["indices"], tr["indices"]
    zb_, zt = d["z"], d["z"] + ix["height"]
    long_ = [v for h, v in ti["per_hour_mm"].items() if h in ("1", "2", "4", "5", "7", "8", "10", "11")]
    med = lambda k: sorted(v[k] for v in long_)[len(long_) // 2]
    steel, lume = Geo(), Geo()
    for hr in range(1, 13):
        v = ti["per_hour_mm"][str(hr)] if hr in (3, 6, 9, 12) else {"inner": med("inner"), "outer": med("outer")}
        w = ti["width_12_mm"] if hr == 12 else ti["width_mm"]
        r0, r1 = v["inner"], min(v["outer"], ix["max_outer_r"])
        steel.prism([rot(x, y, hr * 30) for x, y in rect(0, (r0 + r1) / 2, w, r1 - r0)], zb_, zt)
        lm = ti["lume_mm"]
        lume.prism([rot(x, y, hr * 30) for x, y in rect(0, r1 - lm / 2 - ix["lume_inset"], w - 2 * ix["lume_inset"], lm)], zt, zt + ix["lume_height"])
    add("indices", steel, "steel_polished", bevel=0.04)
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time (traced outlines, pivot on the origin) ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "chrono"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "steel_polished", bevel=0.03)
        if "lume_mm" in t[name]:
            add("hand_%s_lume" % name, Geo().prism([tuple(p) for p in t[name]["lume_mm"]], z + th, z + th + 0.03), "lume")
    hub_r, cap_r = tr["hub_radius_mm"]
    zc = hs["z"]["chrono"] + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zc), (0, zc)], segs=48), "steel_polished")
    ch = hs["hub_cap_height"]
    add("hub_cap", Geo().lathe([(0, zc), (hub_r, zc), (hub_r, zc + ch * 0.5), (cap_r, zc + ch), (0, zc + ch)], segs=48), "steel_polished")

    # ---- crown (fluted) and pushers (stem + cap) on radial axes ----
    def radial(a_deg, z):
        a = math.radians(a_deg)
        m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
        m.translation = (0, 0, z)
        return m

    cw = cfg["crown"]
    n = cw["teeth"]
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.cos(math.pi * i / n),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.sin(math.pi * i / n)) for i in range(2 * n)]
    a_cr = math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360
    g = Geo()
    g.prism([(cw["collar_radius"] * math.cos(2 * math.pi * k / 32), cw["collar_radius"] * math.sin(2 * math.pi * k / 32)) for k in range(32)],
            cw["collar_from"], cw["r_from"], radial(a_cr, cw["z"]))
    add("crown_collar", g, "steel_polished", bevel=0.1)
    add("crown", Geo().prism(star, cw["r_from"], tr["crown_box"]["x0_y0_x1_y1_mm"][2], radial(a_cr, cw["z"])), "steel_polished", bevel=0.15)
    pu = cfg["pushers"]
    circ = lambda r: [(r * math.cos(2 * math.pi * k / 40), r * math.sin(2 * math.pi * k / 40)) for k in range(40)]
    stems, caps = Geo(), Geo()
    for k in ("upper", "lower"):
        m = radial(tr["pushers"][k]["angle_deg"], cw["z"])
        stems.prism(circ(pu["stem_radius"]), pu["stem_from"], pu["cap_from"], m)
        caps.prism(circ(pu["cap_radius"]), pu["cap_from"], tr["pusher_cap_end_r_mm"], m)
    add("pusher_stems", stems, "steel_polished", bevel=0.08)
    add("pusher_caps", caps, "steel_polished", bevel=0.25)

    # ---- lugs from the left silhouette (the right one carries the pushers), mirrored; brushed tops, polished edges ----
    lg = cfg["lug"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    q = lambda y: round(round(y * 4) / 4, 2)
    left = lambda y: (-sil[q(y)][1] - sil[q(-y)][1]) / 2  # 12 and 6 sides averaged
    tip = tr["lug_tip_mm"]["mean"]
    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(left(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- five columns: brushed outer and centre share joints from the lug tips; polished narrow links `shift` nearer ----
    br, el = cfg["bracelet"], cfg["end_link"]
    fc, fp = tr["bracelet_column_fractions"]["centre_half"], tr["bracelet_column_fractions"]["polished_outer"]
    shift, pitch, gap = tr["bracelet_polished_joint_shift_mm"], tr["bracelet_pitch_mm"], br["gap"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    width = lambda y: (sil[q(y)][2] - sil[q(y)][1] + sil[q(-y)][2] - sil[q(-y)][1]) / 4
    hw_at = lambda y: min(width(min(max(y, tip + 1.0), sil_max)), el["half_width"])

    def columns(hw):
        """[(x0, x1, kind)] for one row: centre and outer brushed, polished between."""
        cols = [(-fc * hw, fc * hw, "brushed")]
        for s in (1, -1):
            cols += [tuple(sorted((s * (fc * hw + gap), s * (fp * hw)))) + ("polished",),
                     tuple(sorted((s * (fp * hw + gap), s * hw))) + ("brushed",)]
        return cols

    end_b, end_p = Geo(), Geo()
    for sy in (1, -1):
        for x0, x1, kind in columns(el["half_width"]):
            y1 = tip if kind == "brushed" else tip - shift - gap
            (end_b if kind == "brushed" else end_p).prism(rect((x0 + x1) / 2, sy * (el["from_y"] + y1) / 2, x1 - x0, y1 - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end_b, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_links_polished", end_p, "steel_polished", bevel=el["bevel"])

    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip + br["bend_after_tip"], br["bend_radius"], zm)
    za, zb = ds * br["z0"], ds * br["z1"]
    brushed, polished, back = Geo(), Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for kind, start in (("brushed", tip), ("polished", tip - shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                hw = hw_at((y0 + y1) / 2)
                for x0, x1, k in columns(hw):
                    if k == kind:
                        box(brushed if kind == "brushed" else polished, x0, x1, y0, y1, za, zb, sy)
                if kind == "brushed":
                    box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                y0 = y1 + gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links_polished", polished, "steel_polished", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_width": round(2 * hw_at(tip + 1.0), 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
