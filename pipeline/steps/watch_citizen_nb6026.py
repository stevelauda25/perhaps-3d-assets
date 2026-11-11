"""watch_citizen_nb6026: build the Citizen NB6026-56L (Promaster Fujitsubo, 41 mm titanium, blue dial, black insert in a
blue coin-edge bezel, titanium bracelet) as a flat-backed front relief.

Params: spec (config/watches/citizen-nb6026-56l.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_citizen_bj7150. Parts from Citizen's official render: a blue coin-edge bezel ring, a black insert with the traced silver
numerals, bars, dots and triangle as inlays and a lume pip, house glass, the photo-mapped dial (blue gradient, prints, date,
minute track), applied rectangular indices (polished frame round lume) about the bezel centre, hands as traced polygons and
circles (hour with a three-spoke lume ring and a lume tip, minute with a lume panel, seconds with a lume dot in a ring), a
polished hub, a fluted crown, brushed lugs from the silhouette and a three-column bracelet (brushed outer links, polished
centre links). The dial map comes from pipeline/citizen_nb6026_dial.py; rebuild with --force after regenerating it.
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
    cx, cy = tr["bezel_centre_mm"]
    rg = tr["rings_mm"]
    centred = Matrix.Translation((cx, cy, 0))

    # ---- case under the bezel, crystal ----
    add("case", Geo().lathe([tuple(p) for p in cfg["case"]["profile_rz"]], segs=192, m=centred), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["insert_in"], cr["z0"]), (rg["insert_in"], cr["z1"]), (0, cr["z1"])], segs=192, m=centred), "crystal")

    # ---- bezel: black insert with silver prints and a lume pip, blue ring with a coin edge ----
    bz = cfg["bezel"]
    ri, ro, tip_r = rg["insert_in"], rg["insert_out"], rg["rim_out"]
    add("insert", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_z"]), (ri + 0.3, bz["insert_z"]), (ri, bz["insert_z"] - 0.3)], segs=256, m=centred),
        "insert_black", smooth=True)
    add("insert_prints", plate(tr["insert_prints"], bz["insert_z"] - 0.05, bz["insert_z"] + bz["print_raise"], P + "insert_prints"), "print_silver")
    pip = tr["insert_pip_mm"]
    add("insert_pip", Geo().lathe([(0, bz["insert_z"]), (pip["radius"], bz["insert_z"]), (pip["radius"], bz["insert_z"] + bz["print_raise"] + 0.04),
                                   (0, bz["insert_z"] + bz["print_raise"] + 0.04)], segs=48, m=Matrix.Translation((*pip["centre"], 0))), "lume")
    n, depth, notch = tr["bezel_notches"], bz["scallop_depth"], bz["notch_fraction"]
    u = lambda f: max(0.0, 1 - ((2 * f - 1) / notch) ** 2) ** 0.5
    star = [(lambda a, f: (cx + (tip_r - depth * u(f)) * math.sin(a), cy + (tip_r - depth * u(f)) * math.cos(a)))(2 * math.pi * k / (12 * n), (k % 12) / 12)
            for k in range(12 * n)]
    add("bezel_rim", Geo().lathe([(ro - 0.05, bz["z0"]), (tip_r - depth, bz["z0"]), (tip_r - depth, bz["rim_z"]), (ro - 0.05, bz["rim_z"])], segs=384, m=centred),
        "bezel_blue", bevel=bz["rim_bevel"])
    add("bezel_coin_edge", plate([{"outer": star, "holes": [circle(tip_r - depth - 0.05, 384, cx, cy)]}], bz["z0"] + bz["scallop_z"], bz["rim_z"] - 0.1,
                                 P + "bezel_coin_edge"), "bezel_blue", bevel=bz["rim_bevel"])

    # ---- dial, photo map ----
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["dial_map"] - 0.6, d["z"]), (rg["dial_map"], d["edge_z"])], segs=192, m=centred).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial")

    # ---- applied indices about the bezel centre: polished frame, lume ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, z1, fw = d["z"], d["z"] + ix["height"], ti["frame_mm"]
    frames, lume = [], Geo()
    for v in ti["kinds"].values():
        (r0, r1), hw = v["r_mm"], v["half_mm"]
        for hr in v["hours"]:
            pl = lambda k: [(cx + p[0], cy + p[1]) for p in (rot(x, y, hr * 30) for x, y in ((-hw - k, r0 - k), (hw + k, r0 - k), (hw + k, r1 + k), (-hw - k, r1 + k)))]
            frames.append({"outer": [list(p) for p in pl(fw)], "holes": [[list(p) for p in pl(0)][::-1]]})
            lume.prism(pl(0), z0, z1 - ix["lume_recess"])
    add("indices", plate(frames, z0, z1, P + "indices"), "steel_polished", bevel=0.04)
    add("index_lume", lume, "lume")

    # ---- hands at the render's time: traced polygons and circles ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    disc = lambda al_, r, deg, za, zb, n_=48: Geo().lathe([(0, za), (r, za), (r, zb), (0, zb)], segs=n_, m=Matrix.Translation((*rot(0, al_, deg), 0)))
    for name, h in tr["hands"].items():
        z, mat, deg = hs["z"][name], hs["material"][name], h["angle_deg"]
        g = Geo()
        for lp in h["body_mm"]:
            g.prism([rot(x, y, deg) for x, y in lp], z, z + th)
        add("hand_" + name, g, mat, bevel=0.02)
        for i, (al_, r) in enumerate(h["circles_mm"]):
            add("hand_%s_ring%d" % (name, i), disc(al_, r, deg, z, z + th), mat, bevel=0.02)
        lg_ = Geo()
        for lp in h["lume_mm"]:
            lg_.prism([rot(x, y, deg) for x, y in lp], z + th, z + th + hs["lume"])
        for al_, r in h["lume_circles_mm"]:
            m_ = Matrix.Translation((*rot(0, al_, deg), 0))
            lg_.lathe([(0, z + th), (r, z + th), (r, z + th + hs["lume"]), (0, z + th + hs["lume"])], segs=48, m=m_)
        if lg_.v:
            add("hand_%s_lume" % name, lg_, "lume")
        if "spokes_deg" in h:  # polished spokes over the lume disc
            (al_, r), sw = h["lume_circles_mm"][0], h["spoke_half_mm"]
            sp = Geo()
            for a_ in h["spokes_deg"]:
                ox, oy = rot(0, al_, deg)
                sp.prism([(ox + p[0], oy + p[1]) for p in (rot(x, y, deg + a_) for x, y in ((-sw, 0), (sw, 0), (sw, r), (-sw, r)))],
                         z + th, z + th + hs["lume"] + 0.02)
            add("hand_%s_spokes" % name, sp, mat)
    hub = tr["hub_mm"]
    z_top = max(hs["z"].values()) + th
    add("hub", Geo().lathe([(0, d["z"]), (hub["disc"], d["z"]), (hub["disc"], hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=64),
        "steel_polished", smooth=True)
    add("hub_pin", Geo().lathe([(0, d["z"]), (hub["pin"], d["z"]), (hub["pin"], z_top), (hub["pin"] * 0.6, z_top + 0.08), (0, z_top + 0.08)], segs=48),
        "hand_dark", smooth=True)

    # ---- fluted crown on the 3 o'clock axis ----
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

    # ---- case flanks and lugs from the traced silhouette (left edge, top/bottom averaged): brushed top, polished chamfer ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):  # left edge only: the crown widens the right side
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
    out = {"bezel_width": round(2 * rg["rim_out"], 3), "end_link_width": round(2 * xi, 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_end_y_mm": round(end_y, 2), "bracelet_rows": rows,
            "insert_prints": len(tr["insert_prints"]), "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
