"""watch_zeppelin_z76802: build the Zeppelin 100 Jahre chronograph Z76802 (7680-2: steel, black dial, black leather strap)
as a flat-backed front relief.

Params: spec (config/watches/zeppelin-z76802.json). Same watch head as watch_zeppelin_z7680mb2 (brushed case with a low band
around a polished sloped bezel, flat photo dial out to the bezel, steel lollipop hands with lume, white chronograph and
sub-dial hands, fluted crown with a domed end, two pushers, brushed lugs from the silhouette), posed at this photo's time, on
a leather strap from the photo with the house curl (as watch_zeppelin_z96905). One photo map
(pipeline/zeppelin_z76802_dial.py) serves the dial and the strap. Rebuild with --force after regenerating it.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT
from pipeline.steps.watch_zeppelin_z7680mb2 import axis_matrix


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    for key, rough in cfg["photo_roughness"].items():  # one image, two surfaces
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)
    photo_uv = lambda x, y: (0.5 + x / (2 * pm["half_w_mm"]), 0.5 + (y - pm["centre_y_mm"]) / (2 * pm["half_h_mm"]))
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
        if mat in textured:  # planar UV, lines along model Y
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
        if not name.startswith("strap"):
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
    me = Geo().lathe([(0, d["z"]), (rg["bezel_inner"], d["z"]), (rg["bezel_inner"], d["z"] - 0.3)], segs=192).mesh(P + "dial", True)
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

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

    # ---- brushed lugs outside the strap, outline from the traced silhouette (left edge: the pushers sit on the right) ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    left = lambda y: (sil[round(round(y * 4) / 4, 2)][1] + sil[round(-round(y * 4) / 4, 2)][1]) / 2
    lg, st = cfg["lug"], cfg["strap"]
    tip = tr["lug"]["tip_mm"]["mean"]
    inner = tr["lug"]["inner_x_mm"] + st["lug_gap"]
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

    # ---- leather strap: the photo's own strap (grain, stitching) along its length, house curl from the lug tips ----
    hw = tr["lug"]["inner_x_mm"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    ends = pm["strap_end_mm"]  # last straightened strap row; the rolled-under strap past it reuses that row
    box = curl(bend_y, R, zm)
    g = Geo()
    start = math.sqrt(c["profile_rz"][2][0] ** 2 - hw ** 2) - st["under_case"]
    for sy in (1, -1):
        box(g, -hw, hw, start, st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    add("strap", g, "strap_leather", bevel=st["bevel"],
        uv_of=lambda x, y, z: photo_uv(x, math.copysign(min(s_of(y, z), ends["top" if y > 0 else "bottom"]), y)))

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "strap_width": round(2 * tr["lug"]["inner_x_mm"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": st["end_y"], "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
