"""watch_citizen_bj7150: build the Citizen BJ7150-50W (Promaster Land GMT, 39.5 mm, red textured dial, steel 24-hour bezel,
steel bracelet) as a flat-backed front relief.

Params: spec (config/watches/citizen-bj7150-50w.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_tissot_t120410. Parts from Citizen's official render: a satin steel bezel with the traced black 24-hour numerals and marks
as inlays, house glass, the photo-mapped dial (textured red dial with its printed lume numerals, triangle, bars, date and the
red flange), hands as traced polygons (hour and minute with lume panels in polished frames, a white seconds needle with an
oval counterweight, a yellow GMT hand with an outlined lume triangle), a black hub, a knurled crown in the case bulge,
brushed lugs from the silhouette and a three-column bracelet (brushed outer links, polished centre links). The dial map comes
from pipeline/citizen_bj7150_dial.py; rebuild with --force after regenerating it (it is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    maps = {}
    for key, pm in cfg["photo_maps"].items():  # dial
        mats[key] = photo_material(key, ROOT / pm["image"], pm["roughness"])
        maps[key] = json.loads((ROOT / pm["image"]).with_suffix(".json").read_text())
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
    H = maps["dial"]["half_size_mm"]
    dial_uv = lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H))  # planar about the pivot

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile, lines along the 12-6 axis (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if mat in maps:
            f = uv_of or dial_uv
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = f(*me.vertices[loop.vertex_index].co)
        if bevel:
            if polished_bevel:
                me.materials.append(mats["steel_polished"])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        elif smooth:
            for poly in me.polygons:
                poly.use_smooth = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    circle = lambda r, n=192, cx=0.0, cy=0.0: [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
    cx, cy = tr["case"]["centre_mm"]
    rg = tr["rings_mm"]
    centred = Matrix.Translation((cx, cy, 0))

    # ---- case under the bezel, crystal ----
    add("case", Geo().lathe([tuple(p) for p in cfg["case"]["profile_rz"]], segs=192, m=centred), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_in"], cr["z0"]), (rg["bezel_in"], cr["z1"]), (0, cr["z1"])], segs=192, m=centred), "crystal")

    # ---- satin steel bezel: flat top with chamfered edges, black 24-hour numerals and marks as inlays ----
    bz = cfg["bezel"]
    ri, ro, zt, ch_ = rg["bezel_in"], rg["bezel_out"], bz["top_z"], bz["chamfer"]
    add("bezel", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, zt - ch_), (ro - ch_, zt), (ri + ch_, zt), (ri, zt - ch_)], segs=256, m=centred),
        "steel_satin", smooth=True)
    add("bezel_prints", plate(tr["bezel_prints"], zt - 0.1, zt + bz["print_raise"], P + "bezel_prints"), "print_black")

    # ---- dial + sloped flange, photo map ----
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["flange_in"], d["z"]), (rg["dial_map"], d["flange_z"])], segs=192, m=centred).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial")

    # ---- hands at the render's time: traced polygons ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name, h in tr["hands"].items():
        z, mat = hs["z"][name], hs["material"][name]
        deg = h["angle_deg"]
        add("hand_" + name, Geo().prism([rot(x, y, deg) for x, y in h["body_mm"]], z, z + th), mat, bevel=0.02)
        if "counterweight_mm" in h:
            add("hand_%s_counterweight" % name, Geo().prism([rot(x, y, deg + 180) for x, y in h["counterweight_mm"]], z, z + th), mat, bevel=0.02)
        if h["lume_mm"]:
            g = Geo()
            for lp in h["lume_mm"]:
                g.prism([rot(x, y, deg) for x, y in lp], z + th, z + th + hs["lume"])
            add("hand_%s_lume" % name, g, "lume")
    hub = tr["hub_mm"]
    z_top = max(hs["z"].values()) + th
    add("hub", Geo().lathe([(0, d["z"]), (hub["black"], d["z"]), (hub["black"], hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=64),
        "hand_dark", smooth=True)
    add("hub_cap", Geo().lathe([(0, d["z"]), (hub["cap"], d["z"]), (hub["cap"], z_top), (hub["cap"] * 0.6, z_top + 0.08), (0, z_top + 0.08)], segs=48),
        "hand_white", smooth=True)

    # ---- knurled crown on the 3 o'clock axis, case bulge round it ----
    cw_, tc = cfg["crown"], tr["crown"]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, tc["centre_y_mm"], cw_["z"])
    R0, (r1, r2), n_ = tc["radius_mm"], tc["x_from_to_mm"], tc["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / n_),
             (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / n_)) for i in range(n_ * 2)]
    add("crown_collar", Geo().lathe([(0, cw_["collar"][0]), (cw_["collar_r"], cw_["collar"][0]), (cw_["collar_r"], r1 + 0.2), (0, r1 + 0.2)], segs=48, m=m),
        "steel_polished", smooth=True)
    add("crown", Geo().prism(star, r1, r2 - cw_["end"], m), "steel_polished", bevel=0.08)
    add("crown_end", Geo().lathe([(0, r2 - cw_["end"]), (R0 - 0.1, r2 - cw_["end"]), (R0 - 0.35, r2 - cw_["end"] * 0.3), (R0 - 0.8, r2), (0, r2)],
                                 segs=64, m=m), "steel_polished", smooth=True)
    add("crown_guard", Geo().prism([tuple(p) for p in tr["crown_guard_mm"]], 0.0, cfg["crown_guard"]["top_z"]), "steel_brushed",
        bevel=cfg["crown_guard"]["bevel"], polished_bevel=True)

    # ---- case flanks and lugs from the traced silhouette (left edge, top/bottom averaged): brushed top, polished chamfer ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):  # left edge only: the crown and its bulge widen the right side
        ys = [sil[k_] for k_ in (round(y, 2), round(-y, 2)) if k_ in sil]
        return sum(-p[1] for p in ys) / len(ys)

    lg = cfg["lug"]
    tip = tr["lug_tip_mm"]["mean"]
    xi = tr["end_link_half_mm"]
    steps = [lg["from_y"] + k_ * 0.25 for k_ in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(xi, lg["from_y"])] + [(half(y), y) for y in steps] + [(xi, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- three-column bracelet: brushed outer links, polished centre links, centre joints `shift` nearer the case ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, shift, gap = tr["bracelet_centre_half_mm"], tr["bracelet_centre_joint_shift_mm"], br["gap"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), xi)
    end, end_c = Geo(), Geo()
    for sy in (1, -1):
        M = Matrix.Translation((0, sy * (el["from_y"] + tip) / 2, 0))
        for sx in (1, -1):
            end.prism(rect(sx * (ch + gap + xi) / 2, 0, xi - ch - gap, tip - el["from_y"]), 0.0, el["top_z"], M)
        y1 = tip - shift - gap
        end_c.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"] + br["centre_raise"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_link_centre", end_c, "steel_polished", bevel=el["bevel"])

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    end_y = tip + br["bend_after_tip"] + R * br["arc_over_radius"]
    bent_box = curl(tip + br["bend_after_tip"], R, zm)
    pitches = tr["bracelet_pitch_mm"]
    links, centre, back = Geo(), Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip - shift)):
            y0 = start
            pitch = pitches[kind]
            while y0 < end_y - 0.5:
                y1 = min(y0 + pitch - gap, end_y)
                hw_ = hw_at((y0 + y1) / 2)
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw_))
                        bent_box(links, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(centre, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_centre", centre, "steel_polished", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"bezel_width": round(2 * rg["bezel_out"], 3), "end_link_width": round(2 * xi, 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_end_y_mm": round(end_y, 2), "bracelet_rows": rows,
            "bezel_prints": len(tr["bezel_prints"]), "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
