"""watch_tissot_t127407: build the Tissot T127.407.11.081.00 (Gentleman Powermatic 80 Open Heart, 40 mm, steel bracelet) as a
flat-backed front relief.

Params: spec (config/watches/tissot-t127.407.11.081.00.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_hamilton_h70515137, whose case, crown, lug and bracelet methods it follows. Parts from the official render: a polished
round case with a wide curved bezel down to the crystal; twelve applied batons (polished frame sloping into a brushed centre channel);
faceted hour and minute hands with a lume strip and a kite tail; a thin polished seconds hand; a fluted crown at 3; brushed
lugs; a bracelet with brushed outer links and polished centre pieces. The dial (sunray, prints, lume dots, open-heart
movement) is the photo map from pipeline/tissot_t127407_dial.py. Rebuild with --force after regenerating the map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_orient_ra_ak0705r10b import ridge
from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | " + cfg["model"] + " front relief")
    bpy.context.scene.collection.children.link(coll)
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

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile; lines along the bracelet (model Y), across the dial on the index centres
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
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

    # ---- polished case with the wide curved bezel down to the crystal, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished", smooth=True)
    cr = cfg["crystal"]
    ri = tr["rings_mm"]["bezel_in"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (ri, cr["z0"]), (ri, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial with the dark flange, photo map on a planar UV about the hand pivot ----
    me = Geo().lathe([(0, d["z"]), (tr["rings_mm"]["dial"], d["z"]), (ri, d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    H = dm["half_size_mm"]
    for loop_ in me.loops:
        x, y, _ = me.vertices[loop_.vertex_index].co
        uv.data[loop_.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied batons: polished frame whose walls slope down into a brushed centre channel ----
    ix, ti = cfg["indices"], tr["index"]
    z0, top = d["z"], d["z"] + ix["height"]
    zc = top - ix["channel_depth"]
    frame, channel = Geo(), Geo()
    fr = ti["frame"]
    k = (ti["half_outer"] - ti["half_inner"]) / (ti["outer"] - ti["inner"])  # side slope: the channel keeps the frame width
    hi_c = max(ti["half_inner"] + k * fr - fr, 0.06)
    for hour in range(12):
        q = [(ti["half_inner"], ti["inner"]), (ti["half_outer"], ti["outer"]), (-ti["half_outer"], ti["outer"]), (-ti["half_inner"], ti["inner"])]
        qc = [(hi_c, ti["inner"] + fr), (ti["half_outer"] - fr, ti["outer"] - fr), (-(ti["half_outer"] - fr), ti["outer"] - fr), (-hi_c, ti["inner"] + fr)]
        i = len(frame.v)
        frame.v += [(*rot(x, y, hour * 30), z) for z, pts in ((z0, q), (top, q), (zc, qc)) for x, y in pts]
        for j in range(4):
            n = (j + 1) % 4
            frame.f += [(i + j, i + n, i + 4 + n, i + 4 + j), (i + 4 + j, i + 4 + n, i + 8 + n, i + 8 + j)]  # outer wall, sloped wall
        frame.f.append((i + 3, i + 2, i + 1, i))
        frame.smooth += [False] * 9
        channel.prism([rot(x, y, hour * 30) for x, y in qc], z0, zc)
    add("indices", frame, "steel_polished", bevel=ix["bevel"])
    add("indices_channel", channel, "steel_channel")

    # ---- hands at the render's time: faceted hour and minute with lume strips, thin seconds hand ----
    hs, t = cfg["hands"], tr["hands"]
    th, ridge_h = hs["thickness"], hs["ridge"]
    lh = tr["lume_half_mm"]
    for name in ("hour", "minute"):
        h, z = t[name], hs["z"][name]
        st = [(r, w) for r, w in h["outline_mm"]]
        st[0], st[-1] = (st[0][0], 0.0), (st[-1][0], 0.0)
        g = Geo()
        ridge(g, st, z, th + ridge_h, th / (th + ridge_h), h["angle_deg"])  # edges at z + th, ridge on the axis
        add("hand_" + name, g, "steel_polished", bevel=0.015)
        l0, l1 = h["lume_mm"]
        zl = z + th + ridge_h + hs["lume_raise"]
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, h["angle_deg"]) for x, y in [(lh, l0), (lh, l1), (-lh, l1), (-lh, l0)]], z + th * 0.5, zl), "lume")
    h = t["seconds"]
    L, deg, z = h["length_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, tl = h["half_width_mm"], h["tail_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in [(-nw * 1.4, -tl), (nw * 1.4, -tl), (nw, L - 0.3), (0, L), (-nw, L - 0.3)]], z, z + th),
        "steel_polished", bevel=0.01)
    collar_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=64), "steel_polished", bevel=0.02)
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown at 3: collar and fluted cylinder on a radial axis ----
    cw_, crn = cfg["crown"], tr["crown"]
    a = math.radians(crn["angle_deg"])
    R0, teeth = crn["radius_mm"], crn["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth), (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth))
            for i in range(teeth * 2)]
    u_, dr_ = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u_, (0, 0, 1), dr_)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    r0, r1 = crn["r_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 0.8), (R0 * 0.6, r0 - 0.8), (R0 * 0.6, r0 + 0.6), (0, r0 + 0.6)], segs=48, m=m), "steel_polished", bevel=0.08)
    add("crown", Geo().prism(star, r0 + 0.6, r1, m), "steel_polished", bevel=0.15)

    # ---- lugs from the render's silhouette (left edge, top and bottom averaged): brushed top, polished chamfer ----
    lg, tl_ = cfg["lug"], tr["lug"]
    tip, xi = tl_["tip_mm"], tl_["inner_x_mm"]
    sil = {round(p[0], 2): p[1] for p in tr["silhouette_left_mm"]}
    half = lambda y: (sil[round(y, 2)] + sil[round(-y, 2)]) / 2
    steps = [lg["from_y"] + k_ * 0.25 for k_ in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(xi, lg["from_y"])] + [(half(y), y) for y in steps] + [(xi, tip)]
    outline = [(max(x, xi), y) for x, y in outline]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- bracelet: brushed outer links from the lug tips, polished centre pieces from just past the tips ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, gap = tr["bracelet_centre_half_mm"], br["gap"]
    pitches = tr["bracelet_pitch_mm"]
    hw_ = xi
    c_start = tip + tr["bracelet_centre_start_past_tip_mm"]
    end, end_c = Geo(), Geo()
    for sy in (1, -1):
        M = Matrix.Translation((0, sy * (el["from_y"] + tip) / 2, 0))
        for sx in (1, -1):
            end.prism(rect(sx * (ch + gap + hw_) / 2, 0, hw_ - ch - gap, tip - el["from_y"]), 0.0, el["top_z"], M)
        y1 = c_start - gap
        end_c.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"] + br["centre_raise"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_links_centre", end_c, "steel_polished", bevel=el["bevel"])

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    outer, centre, back = Geo(), Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", c_start)):
            y0 = start
            pitch = pitches[kind]
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw_))
                        bent_box(outer, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(centre, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", outer, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_centre", centre, "steel_polished", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
