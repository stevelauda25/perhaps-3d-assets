"""watch_hamilton_h69439940: build a Hamilton Khaki Field (H69439940 Mechanical 38 mm, H70405710 Murph 38 mm) as a flat-backed
front relief.

Params: spec (config/watches/hamilton-<sku>.json). Same frame, pose, 2.5D depth scale, glass, steel and strap curl as
watch_orient_ra_ac0f06l10b, whose method it follows. Parts from the photo: one lathe for the case flank and one for the
sloped bezel (each with its own steel finish from the spec), a black ring at the crystal edge, the crystal, the dial with
its rehaut (photo map, hands removed), four lugs (outline by depth from the tip, top and bottom averaged, sloping top),
a fluted crown with a smooth end cap, a hub, and the hands built from the traced hand parts (body, then the lume on top)
posed at the photo's time. The strap is the photo strip with the house curl. Rebuild with --force after regenerating the
maps (they are not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    sm = json.loads((ROOT / cfg["strap_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | " + cfg["model"] + " front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d, st = cfg["dial"], cfg["strap"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    mats["strap_photo"] = photo_material("strap_photo", ROOT / cfg["strap_map"], st["roughness"])
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

    def add(name, geo, mat, bevel=None, smooth=None, uv_of=None, polished_bevel=False):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if uv_of:
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co)
        elif mat in textured:  # planar UV in mm / tile, lines along the strap (model Y)
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
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    # ---- case flank and sloped bezel (own finishes), black ring at the crystal edge, crystal ----
    c, bz = cfg["case"], cfg["bezel"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"], smooth=True)
    add("bezel", Geo().lathe([tuple(p) for p in bz["profile_rz"]], segs=192), bz["material"], smooth=True)
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + rehaut to the crystal ring, photo map on a planar UV about the hand pivot ----
    H = dm["half_size_mm"]
    me = Geo().lathe([(0, d["z"]), (tr["rehaut_mm"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H)))

    # ---- applied frame around the date window (the window and its numeral stay in the dial map) ----
    if "date_window" in tr:
        x0, y0, x1, y1 = tr["date_window"]["x0_y0_x1_y1_mm"]
        k = tr["date_window"]["frame_mm"]
        outer = [(x0, y1), (x1, y1), (x1, y0), (x0, y0)]
        inner = [(x0 + k, y1 + k), (x1 - k, y1 + k), (x1 - k, y0 - k), (x0 + k, y0 - k)]
        g = Geo()
        for i in range(4):
            j = (i + 1) % 4
            g.prism([outer[i], outer[j], inner[j], inner[i]], d["z"], d["z"] + cfg["date_frame"]["height"])
        add("date_frame", g, cfg["date_frame"]["material"], bevel=0.03)

    # ---- hands at the photo's time from the traced parts: body (layer 0), lume on top (layer 1) ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name, h in tr["hands"].items():
        z0 = hs["z"][h["z"]]
        for layer, (za, zb) in enumerate(((z0, z0 + th), (z0 + th, z0 + th + hs["lume_height"]))):
            for mat in sorted({p["mat"] for p in h["parts"] if p["layer"] == layer}):
                g = Geo()
                for p in h["parts"]:
                    if p["layer"] == layer and p["mat"] == mat:
                        g.prism([rot(x, y, h["angle_deg"]) for x, y in p["poly_mm"]], za, zb)
                key = hs["material"] if mat == "hand" else mat
                add("hand_%s_%s" % (name, "body" if layer == 0 else mat), g, key, bevel=0.02 if layer == 0 else None)
    collar_r, cap_r = tr["hub_radius_mm"]
    zh = hs["z"]["hour"] + th
    zc = hs["z"]["seconds"] + th
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, zh), (0, zh)], segs=64), hs["material"])
    add("hub_cap", Geo().lathe([(0, zh), (cap_r, zh), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), hs["material"])

    # ---- crown on the 3 o'clock axis: neck, fluted body, smooth rounded end cap ----
    cw_, tc = cfg["crown"], tr["crown"]
    R0, teeth = tc["radius_mm"], tc["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth),
             (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, 0.0, cw_["z"])
    R_case = c["profile_rz"][2][0]
    r1, r2, r3 = tc["from_mm"] + cw_["neck"], tc["cap_from_mm"], tc["to_mm"]
    add("crown_neck", Geo().lathe([(0, R_case - 1.0), (R0 * 0.6, R_case - 1.0), (R0 * 0.6, r1 + 0.1), (0, r1 + 0.1)], segs=48, m=m),
        cw_["material"], smooth=True)
    add("crown", Geo().prism(star, r1, r2, m), cw_["material"], bevel=0.1)
    add("crown_cap", Geo().lathe([(0, r2), (R0 * 0.95, r2), (R0 * 0.9, r2 + (r3 - r2) * 0.6), (R0 * 0.6, r3), (0, r3)], segs=48, m=m),
        cw_["material"], smooth=True)

    # ---- lugs: outline by depth from the tip (top and bottom averaged), mirrored to all four, top sloping to the tip ----
    lg, tl = cfg["lug"], tr["lug"]
    tip, xi = tl["tip_mm"], tl["inner_x_mm"]
    # silhouette points while the lug shows outside the case circle, then one point into the case on the same row
    case_x = lambda y: math.sqrt(max(R_case ** 2 - y * y, 0.0))
    outer = [(w, tip - dd) for dd, w in tl["half_width_by_depth_mm"] if w > xi + 0.2 and w > case_x(tip - dd) + 0.05]
    yl = outer[-1][1]
    outer.append((math.sqrt((R_case - lg["into_case"]) ** 2 - yl * yl), yl))
    inner_end = max(yl, math.sqrt((R_case - lg["into_case"]) ** 2 - xi ** 2))  # stays under the case, out of the crystal
    poly = [(xi, tip)] + outer + [(xi, inner_end)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, slope)
    add("lugs", g, lg["material"], bevel=lg["bevel"], polished_bevel=lg.get("polished_bevel", False))

    # ---- strap: straight between the lugs, house curl from the tips; both sides sample the photo's bottom strap, lug tips
    #      aligned, folded back and forth over its photo rows ----
    hw = xi - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw, hw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
    rows, Sp = sm["rows_px"]["bottom"], sm["scale_px_per_mm"]
    tip_px, n_rows = sm["lug_tips_px"][1], sm["size_px"][1]
    lo, hi = tip + (rows[0] - tip_px) / Sp, tip + (rows[-1] - tip_px) / Sp

    def strap_uv(x, y, z):
        u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
        s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        k_, w = divmod(s - lo, hi - lo)  # folded, not clamped, under the case and past the photo's strap end
        sp = lo + w if int(k_) % 2 == 0 else hi - w
        row = (sp - lo) / (hi - lo) * (len(rows) - 1)
        return 0.5 + 0.5 * u, 1 - (row + 0.5) / n_rows
    add("strap", g, "strap_photo", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3), "strap_width": round(2 * hw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
