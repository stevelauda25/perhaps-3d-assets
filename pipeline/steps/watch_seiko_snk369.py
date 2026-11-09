"""watch_seiko_snk369: build the Seiko 5 SNK369K1 as a flat-backed front relief (like the other GLBs in models/watches/).

Params: spec (config/watches/seiko-snk369k1.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_seiko_snk361_front, whose structure it follows; this model differs in the parts: polished batons with a lume fill (wide
at 12, none at 3), a black open-arrow hour hand, a black stick minute hand with a lume window, a red seconds hand with a wide
tail and a red hub cap, and a seven-part bracelet row (outer, narrow polished strip, mid links half a row offset, centre).
Plan sizes come from config/watches/seiko-snk369k1-trace.json; heights from the spec. The dial is the photo map from
pipeline/seiko_snk369_dial.py. Rebuild with --force after regenerating the dial map (the map is not part of the stage fingerprint).
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
    scene = bpy.context.scene
    coll = bpy.data.collections.new(f"WATCH | {cfg['model']} front relief")
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

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"])
    pose.scale = (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, polished_bevel=False):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
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

    # ---- case (full circle: the end links sit lower and run under it), gasket, crystal ----
    c, lg = cfg["case"], cfg["lug"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + rehaut, photo map on a planar UV (the map is a square of whole pixels out to the crystal ring) ----
    g = Geo().lathe([(0, d["z"]), (d["edge_r"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192)
    me = g.mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    S = tr["scale_px_per_mm"]
    H = math.ceil(tr["crystal_ring"]["radius_mm"] * S) / S
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied batons: polished, lume fill; wide at 12, none at 3 (day-date) ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    r0, r1, wall = ti["inner_mm"], ti["outer_mm"], ix["wall"]
    baton, lume = Geo(), Geo()
    for hour in range(1, 13):
        if hour == 3:
            continue
        turn = lambda poly: [rot(x, y, hour * 30) for x, y in poly]
        w = ti["width_12_mm"] if hour == 12 else ti["width_mm"]
        baton.prism(turn(rect(0, (r0 + r1) / 2, w, r1 - r0)), z0, top)
        lume.prism(turn(rect(0, (r0 + r1) / 2, w - 2 * wall, r1 - r0 - 2 * wall)), top, top + 0.03)
    add("indices", baton, "steel_polished", bevel=0.05)
    add("index_lume", lume, "lume")
    fr, box = cfg["daydate_frame"], tr["daydate_frame"]
    (fx, fy), (fw, fh), wl = box["centre_mm"], box["size_mm"], fr["wall"]
    g = Geo()
    for cx_, cy_, w_, h_ in ((fx, fy + fh / 2 - wl / 2, fw, wl), (fx, fy - fh / 2 + wl / 2, fw, wl),
                             (fx - fw / 2 + wl / 2, fy, wl, fh - 2 * wl), (fx + fw / 2 - wl / 2, fy, wl, fh - 2 * wl)):
        g.prism(rect(cx_, cy_, w_, h_), d["z"], d["z"] + fr["height"])
    add("daydate_frame", g, fr.get("material", "steel_polished"), bevel=0.05)

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    hub_r, cap_r, pin_r = tr["hub_radius_mm"]
    hand_mat = {"outline": "hand_black", "hour_shaft": "lume", "seconds": "hand_red", "hub": "steel_polished", **hs.get("materials", {})}  # SNK369 defaults

    def plate(name, poly, deg, z0, z1, mat, bevel=None):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z0, z1), mat, bevel=bevel)

    # hour: open arrow, black outline; lume in the head, white between the shaft rails
    h = t["hour"]
    L, hb, hhw, hw, o, deg, z = h["length_mm"], h["head_base_mm"], h["head_half_width_mm"], h["half_width_mm"], h["outline_mm"], h["angle_deg"], hs["z"]["hour"]
    plate("hand_hour", [(-hw, -0.4), (hw, -0.4), (hw, hb), (hhw, hb), (0, L), (-hhw, hb), (-hw, hb)], deg, z, z + th, hand_mat["outline"], bevel=0.03)
    if hs.get("hour_collar_mm"):  # round collar of the hour hand showing around the hub
        rc = hub_r + hs["hour_collar_mm"]
        add("hand_hour_collar", Geo().lathe([(0, z), (rc, z), (rc, z + th), (0, z + th)], segs=48), hand_mat["outline"])
    side = math.hypot(hhw, L - hb)
    r_in = hhw * (L - hb) / (hhw + side)  # inradius of the head triangle; the lume is the triangle shrunk by the outline width
    k, cy = (r_in - o) / r_in, hb + r_in
    head = [(x * k, cy + (y - cy) * k) for x, y in ((-hhw, hb), (hhw, hb), (0, L))]
    plate("hand_hour_lume", head, deg, z + th, z + th + 0.03, "lume")
    plate("hand_hour_centre", rect(0, (hub_r + hb) / 2, 2 * (hw - o), hb - hub_r), deg, z + th, z + th + 0.02, hand_mat["hour_shaft"])
    # minute: black stick, square tip, lume window
    h = t["minute"]
    L, hw, o, deg, z = h["length_mm"], h["half_width_mm"], h["outline_mm"], h["angle_deg"], hs["z"]["minute"]
    a, b = h["lume_from_to_mm"]
    tip = hs.get("minute_tip_mm")  # pointed tip: taper length; square tip when unset
    if tip:
        f, wl = hs.get("minute_tip_flat_mm", 0.0), hw - o
        plate("hand_minute", [(-hw, -0.4), (hw, -0.4), (hw, L - tip), (f, L), (-f, L), (-hw, L - tip)], deg, z, z + th, hand_mat["outline"], bevel=0.03)
        plate("hand_minute_lume", [(-wl, a), (wl, a), (wl, L - tip), (0, b), (-wl, L - tip)], deg, z + th, z + th + 0.03, "lume")
    else:
        plate("hand_minute", rect(0, (L - 0.4) / 2, 2 * hw, L + 0.4), deg, z, z + th, hand_mat["outline"], bevel=0.03)
        plate("hand_minute_lume", rect(0, (a + b) / 2, 2 * (hw - o), b - a), deg, z + th, z + th + 0.03, "lume")
    # seconds: thin red needle, wide red tail
    h = t["seconds"]
    L, tail, tw, sw, deg, z = h["length_mm"], h["tail_mm"], h["tail_half_width_mm"], max(h["half_width_mm"], 0.07), h["angle_deg"], hs["z"]["seconds"]
    plate("hand_seconds", [(-tw, -tail), (tw, -tail), (tw, 0.6), (sw, 1.6), (sw, L), (-sw, L), (-sw, 1.6), (-tw, 0.6)], deg, z, z + th, hand_mat["seconds"], bevel=0.02)
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, z), (0, z)], segs=48), hand_mat["hub"])
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (0, zc + 0.1)], segs=48), hand_mat["seconds"])
    add("hub_pin", Geo().lathe([(0, zc), (pin_r, zc), (pin_r, zc + 0.2), (0, zc + 0.25)], segs=24), "steel_polished")

    # ---- crown: fluted cylinder on a radial axis at the traced angle (4 o'clock) ----
    cw = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, cw["r_from"], cw["r_to"], m), "steel_polished", bevel=0.15)

    # ---- lugs from the traced silhouette (top and bottom averaged; mirrored from the left edge in the trace) ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    tips = tr["lug_tip_mm"]
    tip = tips["mean"]

    def lug_half(y):
        """Top and bottom lug outlines averaged after stretching each to the mean tip (the photo's tips differ by 2 mm)."""
        return sum((sil[k][2] - sil[k][1]) / 2 for k in (round(y * tips["top"] / tip * 4) / 4, -round(y * tips["bottom"] / tip * 4) / 4)) / 2

    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(lug_half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- bracelet: centre, narrow strip and outer links in step, mid links half a row offset (as in the photo) ----
    br, el, col = cfg["bracelet"], cfg["end_link"], tr["bracelet_columns"]
    sil_max = min(max(sil), -min(sil)) - 0.25  # the photo ends here; links further out keep the last traced width
    hw_at = lambda y: half(round(min(max(y, tip + 0.5), sil_max) * 4) / 4)  # past the lug tips: bracelet only, both ends
    gap = br["gap"]
    polished_kinds = ("mid", "narrow")

    def columns(hw):
        """x ranges (x0, x1) of the right half: centre (from 0), mid, narrow strip, outer."""
        c_, m1, n1 = col["centre_half"] * hw, col["mid_from_to"][1] * hw, col["narrow_from_to"][1] * hw
        return {"centre": (0.0, c_), "mid": (c_ + gap, m1), "narrow": (m1 + gap, n1), "outer": (n1 + gap, hw)}

    def piece(geo, kind, x0, x1, ylen, za, zb, M=None):
        if kind == "centre":
            geo.prism(rect(0, 0, 2 * x1, ylen), za, zb, M)
        else:
            for sx in (1, -1):
                geo.prism(rect(sx * (x0 + x1) / 2, 0, x1 - x0, ylen), za, zb, M)

    # end link: the same columns between the lugs, from under the case to the lug tips
    end_brushed, end_polished = Geo(), Geo()
    yc, ylen = (el["from_y"] + tip) / 2, tip - el["from_y"]
    for kind, (x0, x1) in columns(lg["inner_x"]).items():
        x1 = min(x1, lg["inner_x"])
        for sy in (1, -1):
            piece(end_polished if kind in polished_kinds else end_brushed, kind, x0, x1, ylen, 0.0, el["top_z"], Matrix.Translation((0, sy * yc, 0)))
    add("end_links", end_brushed, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_links_polished", end_polished, "steel_polished", bevel=el["bevel"])

    zm = ds * (br["z0"] + br["z1"]) / 2  # bracelet built at final depth: flattened thickness, unflattened curve
    box = curl(br["bend_y"], br["bend_radius"], zm)
    za, zb = ds * br["z0"], ds * br["z1"]

    def bent_piece(geo, kind, x0, x1, y0, y1, sy):
        if kind == "centre":
            box(geo, -x1, x1, y0, y1, za, zb, sy)
        else:
            box(geo, x0, x1, y0, y1, za, zb, sy)
            box(geo, -x1, -x0, y0, y1, za, zb, sy)

    pitch = tr["bracelet_pitch_mm"]
    brushed, polished, back = Geo(), Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for kinds, first in ((("centre", "narrow", "outer"), tip + pitch), (("mid",), tip + pitch / 2)):
            y0 = tip
            for y1 in [first + k * pitch for k in range(40)]:
                if y0 >= br["end_y"] - 0.5:
                    break
                y1 = min(y1 - gap, br["end_y"])
                ym = (y0 + y1) / 2
                cols = columns(hw_at(ym))
                for kind in kinds:
                    bent_piece(polished if kind in polished_kinds else brushed, kind, *cols[kind], y0, y1, sy)
                if kinds[0] == "centre":
                    hb_ = hw_at(ym) - 0.3
                    box(back, -hb_, hb_, y0 - gap / 2, y1 + gap / 2, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                y0 = y1 + gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links_polished", polished, "steel_polished", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_gap": round(2 * lg["inner_x"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
