"""watch_zeppelin_z7680mb2: build the Zeppelin 100 Jahre chronograph Z7680MB2 (steel, black dial, three-column steel bracelet)
as a flat-backed front relief.

Params: spec (config/watches/zeppelin-z7680mb2.json). Same frame and house values as watch_zeppelin_z70363: mm, origin = hand
pivot, dial faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet
built at final depth with the smooth curl. Own construction (from the photo): brushed round case with a low band around a polished sloped bezel,
flat photo dial out to the bezel (flange, telemeter ring, sub-dials, date), steel lollipop hour and minute hands with a lume
leaf and a lume disc, white chronograph needle with a long tail, white sub-dial hands, fluted crown with a domed end, two
pushers, brushed lugs from the silhouette, and a three-column bracelet: the end link spans all columns from under the case,
outer links start at the lug tips, centre links (brushed with polished sides) at the first centre joint half a row later.
Rebuild with --force after regenerating the dial map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT


def axis_matrix(angle_deg, z):
    """Local z -> radial direction at a clock angle (dial plane), local origin at height z."""
    a = math.radians(angle_deg)
    m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
    m.translation = (0, 0, z)
    return m


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
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
    ds = cfg["pose"].get("depth_scale", 1.0)

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

    def disc(r, za, zb, c, segs=48):
        return Geo().lathe([(0, za), (r, za), (r, zb), (0, zb)], segs=segs, m=Matrix.Translation((c[0], c[1], 0)))

    rg = tr["rings_mm"]
    # ---- brushed case with the low band that carries the crown and pushers, polished sloped bezel, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_brushed")
    add("bezel", Geo().lathe([tuple(p) for p in cfg["bezel"]["profile_rz"]], segs=192), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_inner"], cr["z0"]), (rg["bezel_inner"], cr["z1"]), (rg["bezel_inner"] * 0.7, cr["z1"] + cr["dome"] * 0.5),
                                (0, cr["z1"] + cr["dome"])], segs=192), "crystal")

    # ---- flat dial with the photo map, out to the bezel ----
    H = dm["half_mm"]
    me = Geo().lathe([(0, d["z"]), (rg["bezel_inner"], d["z"]), (rg["bezel_inner"], d["z"] - 0.3)], segs=192).mesh(P + "dial", True)
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H)))

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        h, z = t[name], hs["z"][name]
        g = Geo().prism([tuple(p) for p in h["outline_mm"]], z, z + th)
        g.lathe([(0, z), (h["disc_ring_r_mm"], z), (h["disc_ring_r_mm"], z + th), (0, z + th)], segs=40,
                m=Matrix.Translation((*h["disc_centre_mm"], 0)))
        add("hand_" + name, g, "steel_polished", bevel=0.03)
        g = Geo().prism([tuple(p) for p in h["leaf_mm"]], z + th, z + th + 0.04)
        g.lathe([(0, z + th), (h["disc_lume_r_mm"], z + th), (h["disc_lume_r_mm"], z + th + 0.04), (0, z + th + 0.04)], segs=40,
                m=Matrix.Translation((*h["disc_centre_mm"], 0)))
        add("hand_%s_lume" % name, g, "lume")
    z = hs["z"]["chrono"]
    add("hand_chrono", Geo().prism([tuple(p) for p in t["chrono"]["outline_mm"]], z, z + th), "hand_white", bevel=0.02)
    hub = t["chrono"]["hub_r_mm"]
    add("hub", disc(hub * 1.8, d["z"], hs["z"]["hour"], (0, 0)), "steel_polished")
    add("hub_cap", Geo().lathe([(0, d["z"]), (hub, d["z"]), (hub, z + th + 0.1), (hub * 0.4, z + th + 0.2), (0, z + th + 0.2)], segs=48), "hand_white")
    zs = hs["z"]["sub"]
    for k, sd in tr["subdials"].items():
        g = Geo().prism([tuple(p) for p in sd["outline_mm"]], zs, zs + th)
        if "tail_disc_mm" in sd:
            g.lathe([(0, zs), (sd["tail_disc_mm"][2], zs), (sd["tail_disc_mm"][2], zs + th), (0, zs + th)], segs=32,
                    m=Matrix.Translation((*sd["tail_disc_mm"][:2], 0)))
        add("sub_hand_" + k, g, "hand_white", bevel=0.02)
        if sd["hub_r_mm"]:
            add("sub_hub_" + k, Geo().lathe([(0, d["z"]), (sd["hub_r_mm"], d["z"]), (sd["hub_r_mm"], zs + th + 0.08), (sd["hub_r_mm"] * 0.3, zs + th + 0.15),
                                             (0, zs + th + 0.15)], segs=40, m=Matrix.Translation((*sd["centre_mm"], 0))), "hand_white")

    # ---- crown: collar, fluted cylinder, domed end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(tc["angle_deg"], cw["z"])
    r0, r1, r2, r3 = tc["r_mm"]
    R0 = tc["radius_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 0.6), (R0 * 0.62, r0 - 0.6), (R0 * 0.62, r1), (0, r1)], segs=48, m=m), "steel_polished")
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2, m), "steel_polished", bevel=0.12)
    dome = [(R0 * math.cos(a), r2 + (r3 - r2) * math.sin(a)) for a in [k * math.pi / 16 for k in range(9)]]
    add("crown_end", Geo().lathe([(0, r2)] + dome, segs=48, m=m), "steel_polished")

    # ---- pushers at 2 and 4: stem and head ----
    for i, pu in enumerate(tr["pushers"]):
        m = axis_matrix(pu["angle_deg"], cfg["pusher"]["z"])
        p0, p1, p2 = pu["r_from_to_mm"]
        add("pusher_%d" % i, Geo().lathe([(0, p0 - 0.6), (pu["stem_radius_mm"], p0 - 0.6), (pu["stem_radius_mm"], p1), (pu["head_radius_mm"], p1),
                                          (pu["head_radius_mm"], p2 - 0.3), (pu["head_radius_mm"] - 0.3, p2), (0, p2)], segs=48, m=m), "steel_polished")

    # ---- brushed lugs outside the bracelet, outline from the traced silhouette (left edge: the pushers sit on the right) ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    left = lambda y: (sil[round(round(y * 4) / 4, 2)][1] + sil[round(-round(y * 4) / 4, 2)][1]) / 2
    lg, br = cfg["lug"], cfg["bracelet"]
    tip = tr["lug"]["tip_mm"]["mean"]
    bhw = tr["bracelet_half_width_mm"]
    inner = bhw + br["gap"] / 2
    from_y = tr["lug"]["from_y_mm"]
    y0 = from_y - lg["into_case"]
    steps = [from_y + k * 0.25 for k in range(int((tip - from_y) / 0.25) + 1)]
    outline = [(inner, y0), (math.sqrt(c["profile_rz"][2][0] ** 2 - y0 ** 2) - 0.2, y0)] + [(max(left(y), inner + 0.3), y) for y in steps] + [(inner, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - from_y, 0) / (tip - from_y)
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- bracelet: end link across all columns from under the case; outer links from the lug tips, centre links from the first centre joint ----
    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip, br["bend_radius"], zm)  # links bend with the curve (approved on SUR419P1)
    za, zb = ds * br["z0"], ds * br["z1"]
    end_y = tip + br["bend_radius"] * 2.2
    pitch, gap = tr["bracelet_pitch_mm"], br["gap"]
    centre_first = tr["bracelet_centre_first_joint_mm"]
    groups, back, rows = {}, Geo(), 0
    for sy in (1, -1):
        y_ = br["end_link_from_y"]
        while y_ < end_y - 0.5:  # backing plate per row, under every column
            y1 = min(tip if y_ < tip else y_ + pitch, end_y)
            box(back, -(bhw - 0.3), bhw - 0.3, y_, y1, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
            y_ = y1
            rows += 1
        for f0, f1, mat, col in br["columns"]:
            g = groups.setdefault(mat, Geo())
            x0, x1 = f0 * bhw + (gap / 2 if f0 else 0), f1 * bhw - gap / 2
            first = tip if col == "outer" else centre_first
            spans = [(br["end_link_from_y"], first - gap)]
            y_ = first + gap
            while y_ < end_y - 0.5:
                spans.append((y_, min(y_ + pitch - gap, end_y)))
                y_ += pitch
            for a_, b_ in spans:
                if b_ - a_ > 0.5:
                    if f0:
                        box(g, x0, x1, a_, b_, za, zb, sy)
                        box(g, -x1, -x0, a_, b_, za, zb, sy)
                    else:
                        box(g, -x1, x1, a_, b_, za, zb, sy)
    for mat, g in groups.items():
        add("bracelet_links_" + mat.split("_")[1], g, mat, bevel=br["bevel"], polished_bevel=mat == "steel_brushed")
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "bracelet_width": round(2 * bhw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "centre_first_joint_y_mm": centre_first, "lug_to_lug_mm": round(2 * tip, 2),
            "end_y_mm": round(end_y, 2), "bracelet_rows": rows, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
