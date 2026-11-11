"""watch_bulova_96b431: build the Bulova 96B431 (Marine Star Precisionist 43 mm, yellow wave dial, black twelve-sided bezel,
black rubber strap) as a flat-backed front relief.

Params: spec (config/watches/bulova-96b431.json). Frame as watch_hamilton_scuba_pioneer: mm, origin = hand pivot, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth
with the house curl. Own construction from the official render: one brushed steel case and lug body from the traced
silhouette (lug gap, crown guards), a twelve-sided bezel (polished rim, black insert from the photo map), house glass, the
photo-mapped wave dial, applied steel indices with lume and the applied logo (traced), polished steel hands with lume, open
windows and flat tails, a seconds hand with a red-framed lume triangle, a fluted crown, and the rubber strap tapering as in the
render with the strap photo map. Maps from pipeline/bulova_96b431_dial.py; rebuild with --force after regenerating them.
"""
import json
import math

import bpy
import numpy as np
from mathutils import Matrix

from pipeline.steps.watch_hamilton_scuba_pioneer import circle, sloped_plate
from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    maps = {}
    for key, pm in cfg["photo_maps"].items():  # dial (+ insert) and strap
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
        if mat in textured:  # planar UV, lines along the watch's 12-6 axis
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
                me.materials.append(mats[polished_bevel])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        elif smooth:
            for poly in me.polygons:
                poly.use_smooth = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    def upward(me):
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg, c, bz, cr, d = tr["rings_mm"], cfg["case"], cfg["bezel"], cfg["crystal"], cfg["dial"]
    lg, tip = cfg["lug"], tr["lug"]["tip_y_mm"]
    xi, yc = tr["lug"]["inner_x_mm"], tr["lug"]["notch_y_mm"]
    n = tr["sides"]
    gon = lambda ap: [rot(0, ap / math.cos(math.pi / n), 360.0 / n * (k + 0.5)) for k in range(n)]  # flats at 12, 1, 2 ...

    # ---- brushed steel case and lugs from the silhouette, straight edge between the lugs, top sloping to the tips ----
    ho = tr["half_outline_mm"]
    ed = {k: (lambda pts: lambda y: float(np.interp(abs(y), [q[0] for q in pts], [q[1] for q in pts])))(v) for k, v in ho.items()}
    ys = [q[0] for q in ho["right"]]
    right = [(ed["right"](y), y) for y in reversed(ys)] + [(ed["right"](y), -y) for y in ys[1:]]
    left = [(-ed["left"](y), -y) for y in reversed(ys)] + [(-ed["left"](y), y) for y in ys[1:]]
    outline = right + [(xi, -tip), (xi, -yc), (-xi, -yc), (-xi, -tip)] + left + [(-xi, tip), (-xi, yc), (xi, yc), (xi, tip)]
    clean = [outline[0]]
    for q in outline[1:]:
        if math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) > 0.05:
            clean.append(q)
    sf = lg["slope_from_y"]
    top = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - sf) / (tip - sf)))
    cuts = [sy * (sf + (tip - sf) * k / 8) for sy in (1, -1) for k in range(8)]
    add("case", sloped_plate(clean, 0.0, top, P + "case", (), cuts), "steel_brushed", bevel=lg["bevel"], polished_bevel="steel_polished")

    # ---- twelve-sided bezel: polished rim, black insert (dial map), crystal ----
    z0 = bz["z0"]
    add("bezel_rim", plate([{"outer": gon(rg["rim_apothem"]), "holes": [gon(rg["insert_apothem"] - 0.05)[::-1]]}], z0, bz["rim_top_z"], P + "bezel_rim"),
        "steel_polished", bevel=bz["rim_bevel"])
    add("bezel_insert", plate([{"outer": gon(rg["insert_apothem"]), "holes": [circle(rg["insert_in"], 192)]}], z0, bz["insert_top_z"], P + "bezel_insert"),
        "dial", smooth=True)
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["insert_in"] + 0.05, cr["z0"]), (rg["insert_in"] + 0.05, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial (photo map) with a short wall up to the insert ----
    add("dial", upward(Geo().lathe([(0, d["z"]), (rg["dial"] + 0.02, d["z"]), (rg["dial"] + 0.02, bz["insert_top_z"] - 0.1)], segs=256).mesh(P + "dial", True)), "dial")

    # ---- applied indices (steel frames, lume) and logo ----
    ix = cfg["indices"]
    frames, lume = Geo(), Geo()
    for sh in tr["indices"].values():
        for hr in sh["hours"]:
            frames.prism([rot(x, y, 30 * hr) for x, y in sh["frame_mm"]], d["z"], d["z"] + ix["height"])
            lume.prism([rot(x, y, 30 * hr) for x, y in sh["lume_mm"]], d["z"] + ix["height"], d["z"] + ix["height"] + ix["lume_height"])
    add("indices", frames, "steel_polished", bevel=0.03)
    add("index_lume", lume, "lume")
    logo = [{"outer": [tuple(q) for q in s_["outer"]], "holes": [[tuple(q) for q in h] for h in s_["holes"]]} for s_ in tr["logo_mm"]]
    add("logo", plate(logo, d["z"], d["z"] + ix["height"], P + "logo"), "steel_polished", bevel=0.03)

    # ---- hands at the render's time ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name in ("hour", "minute"):
        h, z = tr["hands"][name], hs["z"][name]
        add("hand_" + name, plate([{"outer": [tuple(q) for q in h["outline_mm"]], "holes": [[tuple(q) for q in h["window_mm"]]]}], z, z + th, P + "hand_" + name),
            "steel_polished", bevel=0.02)
        add("hand_%s_lume" % name, plate([{"outer": [tuple(q) for q in h["lume_mm"]], "holes": []}], z + th, z + th + hs["lume"], P + "lume_" + name), "lume")
    h, z = tr["hands"]["seconds"], hs["z"]["seconds"]
    add("hand_seconds", Geo().prism([tuple(q) for q in h["needle_mm"]], z, z + th), "steel_polished", bevel=0.01)
    add("hand_seconds_tail", Geo().prism([tuple(q) for q in h["tail_mm"]], z, z + th), "steel_polished", bevel=0.02)
    add("hand_seconds_triangle", Geo().prism([tuple(q) for q in h["triangle_mm"]], z, z + th), "seconds_red", bevel=0.01)
    add("hand_seconds_lume", Geo().prism([tuple(q) for q in h["triangle_lume_mm"]], z + th, z + th + hs["lume"]), "lume")
    add("hand_seconds_stick", Geo().prism([tuple(q) for q in h["stick_mm"]], z, z + th), "seconds_red", bevel=0.01)
    hub = tr["hub_mm"]
    zt = z + th
    add("hub", Geo().lathe([(0, d["z"]), (hub["disc"], d["z"]), (hub["disc"], zt), (hub["disc"] - 0.1, zt + 0.05), (0, zt + 0.05)], segs=64), "steel_polished", smooth=True)
    add("hub_pin", Geo().lathe([(0, zt), (hub["pin"], zt), (hub["pin"], zt + 0.1), (hub["pin"] * 0.6, zt + 0.15), (0, zt + 0.15)], segs=32), "pin_dark", smooth=True)

    # ---- fluted steel crown on the 3 o'clock axis ----
    cw, tc = cfg["crown"], tr["crown"]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, tc["centre_y_mm"], cw["z"])
    R0, (r1, r2) = tc["radius_mm"], tc["r_from_to_mm"]
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / tc["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / tc["teeth"])) for i in range(tc["teeth"] * 2)]
    add("crown_collar", Geo().lathe([(0, tc["collar_mm"] - 1.0), (R0 * 0.6, tc["collar_mm"] - 1.0), (R0 * 0.6, r1 + 0.2), (0, r1 + 0.2)], segs=48, m=m),
        "steel_polished", smooth=True)
    add("crown", Geo().prism(star, r1, r2 - cw["end"], m), "steel_polished", bevel=0.1)
    add("crown_end", Geo().lathe([(0, r2 - cw["end"]), (R0 - 0.15, r2 - cw["end"]), (R0 - 0.5, r2 - cw["end"] * 0.3), (R0 - 1.0, r2), (0, r2)], segs=64, m=m),
        "steel_polished", smooth=True)

    # ---- rubber strap: house curl from the lug tips, the render's taper, the photo's strap rows (tips aligned) ----
    st, sm = cfg["strap"], maps["strap"]
    zm, R = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"]
    bend_y = tip + st["bend_after_tip"]
    end_y = bend_y + R * st["arc_over_radius"]
    hw0 = xi - st["side_gap"]
    taper = tr["strap"]["half_width_by_s_mm"]
    hw = lambda s: min(hw0, float(np.interp(s - tip, [q[0] for q in taper if q[0] >= 1.5], [q[1] for q in taper if q[0] >= 1.5])))
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw0, hw0, yc - st["under_case"], end_y, ds * st["z0"], ds * st["z1"], sy)
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    g.v =[(x * hw(s_of(y, z)) / hw0, y, z) for x, y, z in g.v]  # taper: every vertex moved in to the width at its strap length
    tips_photo = tr["lug"]["tips_photo_mm"]
    rows_h = sm["size_px"][1]

    def strap_uv(x, y, z):
        top_side = y > 0
        side = sm["top"] if top_side else sm["bottom"]
        s = s_of(y, z)
        sp = s - tip + tips_photo[0 if top_side else 1]
        i = (sp - side["first_s_mm"]) * sm["rows_per_mm"]
        i = min(max(i, 0.0), 2 * side["rows"] - 1.0)
        if i > side["rows"] - 1:  # past the photo's edge (rolled under, out of the front view): fold back
            i = 2 * (side["rows"] - 1) - i
        row = i + (0 if top_side else sm["top"]["rows"])
        u = min(max((x / hw(s) + 1) / 2, st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
        return (u, 1 - (row + 0.5) / rows_h)
    add("strap", g, "strap", uv_of=strap_uv, smooth=True)

    # ---- checks against the official anchors ----
    out = {"case_width": round(2 * rg["rim_apothem"], 3), "lug_width": round(2 * xi, 3), "case_length": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 1.0, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "strap_end_y_mm": round(end_y, 2), "strap_half_width_at_end_mm": round(hw(end_y), 2),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
