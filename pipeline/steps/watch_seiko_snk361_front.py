"""watch_seiko_snk361_front: build the Seiko 5 SNK361K1 as a flat-backed front relief (like the other GLBs in models/watches/).

Params: spec (config/watches/seiko-snk361k1-v1.json). Same frame, pose, 2.5D depth scale and materials as watch_seiko_front
(SNK607K1), whose helpers it reuses; this model differs in the parts: hollow batons with lume blocks, hands with wide tails, a
five-column bracelet (mid columns half a row offset) and a five-part end link running under the case. Plan sizes come from config/watches/seiko-snk361k1-trace.json; heights from the spec. The dial is the photo map from
pipeline/seiko_snk361_dial.py. Rebuild with --force after regenerating the dial map (the map is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Seiko 5 SNK361K1 front relief")
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

    # ---- dial + rehaut, photo map on a planar UV ----
    g = Geo().lathe([(0, d["z"]), (tr["dial_edge_radius_mm"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192)
    me = g.mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    H = tr["crystal_ring"]["radius_mm"]
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied batons: polished outline, black centre, white lume block at the outer end; double at 12, lume only at 3 ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    r0, rl, r1 = ti["inner_mm"], ti["lume_from_mm"], ti["outer_mm"]
    baton, centre, lume = Geo(), Geo(), Geo()
    wall = ix["wall"]
    for hour in range(1, 13):
        turn = lambda poly: [rot(x, y, hour * 30) for x, y in poly]
        if hour == 3:
            baton.prism(turn(rect(0, (rl + r1) / 2, ti["width_mm"], r1 - rl + 2 * wall)), z0, top)
            lume.prism(turn(rect(0, (rl + r1) / 2, ti["width_mm"] - 2 * wall, r1 - rl)), top, top + 0.03)
            continue
        w = ti["width_12_mm"] if hour == 12 else ti["width_mm"]
        baton.prism(turn(rect(0, (r0 + r1) / 2, w, r1 - r0)), z0, top)
        lume.prism(turn(rect(0, (rl + r1) / 2 - wall / 2, w - 2 * wall, r1 - rl - wall)), top, top + 0.03)
        holes = [(-(w - wall) / 4, (w - 3 * wall) / 2), ((w - wall) / 4, (w - 3 * wall) / 2)] if hour == 12 else [(0, w - 2 * wall)]
        for hx, hw in holes:
            centre.prism(turn(rect(hx, (r0 + rl) / 2, hw, rl - r0 - 2 * wall)), top, top + 0.02)
    add("indices", baton, "steel_polished", bevel=0.05)
    add("index_centres", centre, "index_line")
    add("index_lume", lume, "lume")
    fr, box = cfg["daydate_frame"], tr["daydate_frame"]
    (fx, fy), (fw, fh), wl = box["centre_mm"], box["size_mm"], fr["wall"]
    g = Geo()
    for cx_, cy_, w_, h_ in ((fx, fy + fh / 2 - wl / 2, fw, wl), (fx, fy - fh / 2 + wl / 2, fw, wl),
                             (fx - fw / 2 + wl / 2, fy, wl, fh - 2 * wl), (fx + fw / 2 - wl / 2, fy, wl, fh - 2 * wl)):
        g.prism(rect(cx_, cy_, w_, h_), d["z"], d["z"] + fr["height"])
    add("daydate_frame", g, "steel_polished", bevel=0.05)

    # ---- hands at the photo's time: polished rim around a black centre (skeleton, as photographed), rounded ends,
    #      wide tails, lume inserts on hour and minute ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    rim = hs["rim"]

    def arc(cx, cy, r, a0, a1, n=5):
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    def outline(L, hw, tail, tw, root):
        """Blade to a rounded tip at L, wide tail with a rounded end at -tail; hand-local, pivot at 0, counter-clockwise."""
        rt, rb = hw * hs["tip_round"], tw * hs["tip_round"]
        return (arc(tw - rb, -tail + rb, rb, -90, 0) + [(tw, -root), (hw, root)] + arc(hw - rt, L - rt, rt, 0, 90)
                + arc(-hw + rt, L - rt, rt, 90, 180) + [(-hw, root), (-tw, -root)] + arc(-tw + rb, -tail + rb, rb, 180, 270))

    def plate(name, poly, deg, z0, z1, mat, bevel=None):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z0, z1), mat, bevel=bevel)

    for name in ("hour", "minute"):
        h = t[name]
        L, tail, hw, tw, deg, z = h["length_mm"], h["tail_mm"], h["half_width_mm"], h["tail_half_width_mm"], h["angle_deg"], hs["z"][name]
        plate("hand_" + name, outline(L, hw, tail, tw, 0.7), deg, z, z + th, "steel_polished", bevel=0.03)
        plate("hand_%s_centre" % name, outline(L - rim, hw - rim, tail - rim, tw - rim, 0.7), deg, z + th, z + th + 0.01, "index_line")
        a, b = h["lume_from_to_mm"]
        plate("hand_%s_lume" % name, rect(0, (a + b) / 2, 2 * (hw - rim), b - a), deg, z + th, z + th + 0.03, "lume")
    h = t["seconds"]
    L, tail, tw, deg, z = h["length_mm"], h["tail_mm"], h["tail_half_width_mm"], h["angle_deg"], hs["z"]["seconds"]
    plate("hand_seconds", outline(L, hs["seconds_half_width"], tail, tw, 0.9), deg, z, z + th, "steel_polished", bevel=0.03)
    w, r = tw - rim, (tw - rim) * hs["tip_round"]  # black centre of the tail paddle, from beside the hub to its rounded end
    plate("hand_seconds_centre", arc(w - r, -tail + rim + r, r, -90, 0) + [(w, -1.0), (-w, -1.0)] + arc(-w + r, -tail + rim + r, r, 180, 270),
          deg, z + th, z + th + 0.01, "index_line")
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, z), (0, z)], segs=48), "steel_polished")
    zc = z + th
    add("hub_ring", Geo().lathe([(0, zc), (hub_r * 0.8, zc), (hub_r * 0.8, zc + 0.02), (0, zc + 0.02)], segs=48), "index_line")
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.15), (cap_r * 0.6, zc + 0.25), (0, zc + 0.25)], segs=48), "steel_polished")

    # ---- crown: fluted cylinder on a radial axis at the traced angle (4 o'clock) ----
    cw = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, cw["r_from"], cw["r_to"], m), "steel_polished", bevel=0.15)

    # ---- lugs from the traced silhouette (left/right and top/bottom averaged) ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    tip = tr["lug_tip_mm"]["mean"]
    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- five columns: centre and outer links in step, mid links half a row offset (as in the photo) ----
    br, el, col = cfg["bracelet"], cfg["end_link"], tr["bracelet_columns"]
    sil_max = min(max(sil), -min(sil)) - 0.25  # the photo ends here; links further out keep the last traced width
    hw_at = lambda y: half(round(min(max(y, tip + 0.5), sil_max) * 4) / 4)  # past the lug tips: bracelet only, both ends
    gap = br["gap"]

    def columns(hw):
        """x ranges (x0, x1) of the right half: centre (from 0), mid, outer."""
        c_, m0, m1 = col["centre_half"] * hw, col["mid_from_to"][0] * hw, col["mid_from_to"][1] * hw
        return {"centre": (0.0, c_), "mid": (m0, m1), "outer": (m1 + gap, hw)}

    def piece(geo, kind, x0, x1, ylen, za, zb, M=None):
        if kind == "centre":
            geo.prism(rect(0, 0, 2 * x1, ylen), za, zb, M)
        else:
            for sx in (1, -1):
                geo.prism(rect(sx * (x0 + x1) / 2, 0, x1 - x0, ylen), za, zb, M)

    # end link: same five columns between the lugs, from under the case to the lug tips
    end_brushed, end_polished = Geo(), Geo()
    yc, ylen = (el["from_y"] + tip) / 2, tip - el["from_y"]
    for kind, (x0, x1) in columns(lg["inner_x"]).items():
        x1 = min(x1, lg["inner_x"])
        for sy in (1, -1):
            piece(end_polished if kind == "mid" else end_brushed, kind, x0, x1, ylen, 0.0, el["top_z"], Matrix.Translation((0, sy * yc, 0)))
    add("end_links", end_brushed, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_links_mid", end_polished, "steel_polished", bevel=el["bevel"])

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]  # bracelet built at final depth: flattened thickness, unflattened curve

    def place(s, sy):
        """Rigid placement of a link whose centre sits at distance s along the bracelet: straight up to bend_y, then
        rolled back over a circle of radius R (away from the viewer), so the ends curve out of sight."""
        over = s - br["bend_y"]
        if over <= 0:
            return Matrix.Translation((0, sy * s, zm))
        th_ = over / R
        m_ = Matrix.Translation((0, sy * (br["bend_y"] + R * math.sin(th_)), zm - R * (1 - math.cos(th_))))
        return m_ @ Matrix.Rotation(-sy * th_, 4, "X")

    pitch = tr["bracelet_pitch_mm"]
    brushed, polished, back = Geo(), Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for kinds, first in ((("centre", "outer"), tip), (("mid",), tip + pitch / 2)):
            y0 = tip
            y1s = [first] + [first + k * pitch for k in range(1, 40)]
            for y1 in y1s:
                if y0 >= br["end_y"] - 0.5:
                    break
                y1 = min(y1 - gap, br["end_y"])
                ym, M = (y0 + y1) / 2, place((y0 + y1) / 2, sy)
                cols = columns(hw_at(ym))
                for kind in kinds:
                    piece(polished if kind == "mid" else brushed, kind, *cols[kind], y1 - y0, ds * br["z0"] - zm, ds * br["z1"] - zm, M)
                if kinds[0] == "centre":
                    back.prism(rect(0, 0, 2 * (hw_at(ym) - 0.3), y1 - y0 + gap), ds * br["backing_z"][0] - zm, ds * br["backing_z"][1] - zm, M)
                    rows += 1
                y0 = y1 + gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links_mid", polished, "steel_polished", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    near = sorted(p[2] - p[1] for y, p in sil.items() if 22 <= abs(y) <= 24)  # same rows as the trace's check
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "bracelet_next_to_case": round(near[len(near) // 2], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
