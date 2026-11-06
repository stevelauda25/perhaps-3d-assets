"""watch_seiko_sna411: build the Seiko Pilot's Flight SNA411P1 (NATO variant) as a flat-backed front relief.

Params: spec (config/watches/seiko-sna411p1-var-nato3.json). Same frame, pose and depth scale as the other Seiko front reliefs
(watch_seiko_front helpers), origin = dial centre. Parts: round polished case, coin-edge bezel with the photo's slide-rule
insert, black dial with subdials and their hands from the photo map, raised lume dots textured by the same map, sword hour
and minute hands with lume, yellow chrono seconds hand with a triangular counterweight, fluted crown at 3 and pushers at 2
and 4, four lugs, and a 22 mm NATO strap from the photo atlas with the house curl. The photo was taken turned, so the map
comes from pipeline/seiko_sna411_rectify.py + seiko_sna411_map.py; the insert is mapped around its own photo centre
(parallax). Rebuild with --force after regenerating the maps (they are not part of the stage fingerprint).
"""
import json
import math

import bmesh
import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    meta = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Seiko SNA411P1 NATO front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d, st = cfg["dial"], cfg["strap"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    mats["strap"] = photo_material("strap_photo", ROOT / st["map"], st["roughness"])

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]
    H = meta["half_size_mm"]
    photo_uv = lambda x, y, c=(0.0, 0.0): (0.5 + (x + c[0]) / (2 * H), 0.5 + (y + c[1]) / (2 * H))

    def add(name, geo, mat, bevel=None, flat_depth=True, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if uv_of:
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co[:2])
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if flat_depth:
            o.scale = (1, 1, ds)
        return o

    def upward(me):
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg, pc = tr["rings_mm"], tr["photo_centres_mm"]
    circle = lambda r, n=192: [(r * math.sin(2 * math.pi * k / n), r * math.cos(2 * math.pi * k / n)) for k in range(n)]

    # ---- case, coin-edge bezel ring, slide-rule insert (photo, around its own photo centre), crystal ----
    c, bz = cfg["case"], cfg["bezel"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    n = tr["teeth_count"]
    star = [((rg["bezel_outer"] if i % 2 == 0 else bz["teeth_root_r"]) * math.sin(math.pi * i / n),
             (rg["bezel_outer"] if i % 2 == 0 else bz["teeth_root_r"]) * math.cos(math.pi * i / n)) for i in range(2 * n)]
    add("bezel_ring", plate([{"outer": star, "holes": [circle(rg["insert_outer"])]}], bz["z0"], bz["ring_top_z"], P + "bezel_ring"),
        "steel_polished", bevel=0.12)
    ri, ro = rg["crystal"], rg["insert_outer"]
    cr = cfg["crystal"]
    prof = [(ri, cr["z0"]), (ri, bz["insert_inner_z"]), (ro, bz["insert_top_z"]), (ro, bz["z0"])]
    add("bezel_insert", upward(Geo().lathe(prof, segs=192).mesh(P + "bezel_insert", True)), "dial",
        uv_of=lambda x, y: photo_uv(x, y, pc["bezel"]))
    add("crystal", Geo().lathe([(0, cr["z0"]), (ri, cr["z0"]), (ri, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial (photo map: print, subdials and their hands, date) and raised lume dots textured by the same map ----
    add("dial", upward(Geo().lathe([(0, d["z"]), (ri, d["z"])], segs=192).mesh(P + "dial", True)), "dial", uv_of=photo_uv)
    ld = tr["lume_dots"]
    g = Geo()
    for hr in ld["hours"]:
        x, y = rot(0, ld["ring_mm"], hr * 30)
        g.lathe([(0, d["z"]), (ld["radius_mm"], d["z"]), (ld["radius_mm"], d["z"] + cfg["lume_dots"]["height"]),
                 (0, d["z"] + cfg["lume_dots"]["height"])], segs=32, m=Matrix.Translation((x, y, 0)))
    add("lume_dots", g, "dial", uv_of=photo_uv, smooth=False)

    # ---- hands at the photo's time: sword hour and minute with lume, yellow chrono hand with a triangular counterweight ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        h, z = t[name], hs["z"][name]
        half = [tuple(p) for p in h["half_outline_mm"]]
        outline = half + [(-x, y) for x, y in reversed(half[1:-1])]
        add("hand_" + name, Geo().prism([rot(x, y, h["angle_deg"]) for x, y in outline], z, z + th), "steel_polished", bevel=0.03)
        lu = h["lume"]
        w = lu["half_width_mm"]
        lume = [(-w, lu["from_mm"]), (w, lu["from_mm"]), (w, lu["to_mm"]), (0, lu["to_mm"] + w), (-w, lu["to_mm"])]
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, h["angle_deg"]) for x, y in lume], z + th, z + th + hs["lume_height"]), "lume")
    h, z = t["chrono"], hs["z"]["chrono"]
    nw, rw, L = h["needle_half_mm"], h["root_half_mm"], h["length_mm"]
    ap, tl, bw = h["tail_apex_mm"], h["tail_mm"], h["tail_base_half_mm"]
    outline = [(nw, L), (nw, 3.0), (rw, 0.6), (rw, -ap), (bw, -tl), (-bw, -tl), (-rw, -ap), (-rw, 0.6), (-nw, 3.0), (-nw, L)]
    add("hand_chrono", Geo().prism([rot(x, y, h["angle_deg"]) for x, y in outline], z, z + th), "chrono_yellow", bevel=0.02)
    hub = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub, d["z"]), (hub, z + th), (0, z + th)], segs=48), "chrono_yellow")
    zc, cap = z + th, hs["cap_radius"]
    add("hub_cap", Geo().lathe([(0, zc), (cap, zc), (cap, zc + 0.12), (cap * 0.6, zc + 0.18), (0, zc + 0.18)], segs=32), "steel_polished")

    # ---- crown at 3: short wide fluted barrel with a rounded end; pushers at 2 and 4: fluted collar and a plain domed button ----
    def axis(angle, z_):
        a = math.radians(angle)
        m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
        m.translation = (0, 0, z_)
        return m

    def fluted(name, m, radius, r_from, r_to, teeth, depth, bevel):
        star_ = [((radius if i % 2 == 0 else radius - depth) * math.cos(math.pi * i / teeth),
                  (radius if i % 2 == 0 else radius - depth) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
        add(name, Geo().prism(star_, r_from, r_to, m), "steel_polished", bevel=bevel)

    def dome(name, m, radius, r_from, r_flat, r_to):
        """Plain cylinder along the axis with a rounded end (profile: radius, distance from the dial centre)."""
        prof = [(0, r_from), (radius, r_from), (radius, r_flat)] + \
               [(radius * math.cos(math.pi / 2 * k / 6), r_flat + (r_to - r_flat) * math.sin(math.pi / 2 * k / 6)) for k in range(1, 7)]
        add(name, Geo().lathe(prof, segs=48, m=m), "steel_polished", smooth=True)

    cw = cfg["crown"]
    m = axis(tr["crown"]["angle_deg"], cw["z"])
    fluted("crown", m, cw["radius"], cw["r_from"], cw["flutes_to"], cw["teeth"], cw["flute_depth"], 0.3)
    dome("crown_end", m, cw["radius"] - cw["flute_depth"], cw["flutes_to"] - 0.2, cw["flutes_to"], cw["r_to"])
    pw = cfg["pushers"]
    for k, ang in enumerate(tr["pushers"]["angles_deg"]):
        m = axis(ang, pw["z"])
        fluted("pusher_collar_%d" % k, m, pw["collar_radius"], pw["r_from"], pw["collar_to"], pw["teeth"], pw["flute_depth"], 0.2)
        dome("pusher_button_%d" % k, m, pw["button_radius"], pw["collar_to"] - 0.1, pw["button_to"], pw["r_to"])

    # ---- four lugs from the 6 o'clock outline (mirrored) ----
    lg = cfg["lug"]
    outline = [tuple(p) for p in lg["outline_mm"]]
    y0, tip = min(y for _, y in outline), tr["lug_mm"]["tip_y"]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - y0, 0) / (tip - y0)
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- NATO strap: one band per side, photo atlas mirrored along the strap, straight to the lug tips, then the house curl ----
    lay = json.loads((ROOT / st["map"]).with_suffix(".json").read_text())
    hw, za, zb, ch = st["half_width"], ds * st["z0"], ds * st["z1"], st["edge_chamfer"]
    assert hw < tr["lug_mm"]["inner_x"], "strap wider than the lug gap"
    zm, R, bend_y = (za + zb) / 2, st["bend_radius"], tip + st.get("bend_after_tip", 0.0)
    end_y = bend_y + R * st["arc_over_radius"]

    def bend(s, z_):
        if s <= bend_y:
            return s, z_
        a_, r_ = (s - bend_y) / R, R + z_ - zm
        return bend_y + r_ * math.sin(a_), zm - R + r_ * math.cos(a_)

    period = lay["length_mm"]
    v_of = lambda s: (lambda k: k if k <= 1 else 2 - k)((s / period) % 2)  # mirrored repeat of the atlas rows
    ring = [(-hw, za + ch), (-hw + ch, za), (hw - ch, za), (hw, za + ch), (hw, zb - ch), (hw - ch, zb), (-hw + ch, zb), (-hw, zb - ch)]
    cuts = [st["from_y"] + k * 0.4 for k in range(int((end_y - st["from_y"]) / 0.4) + 1)] + [end_y]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for sy in (1, -1):
        rings = []
        for s in cuts:
            row = []
            for x, z_ in ring:
                y, zz = bend(s, z_)
                row.append((bm.verts.new((x, sy * y, zz)), ((x + hw) / (2 * hw), v_of(s))))
            rings.append(row)
        faces = [[rings[k][i], rings[k][(i + 1) % 8], rings[k + 1][(i + 1) % 8], rings[k + 1][i]] for k in range(len(cuts) - 1) for i in range(8)]
        faces += [rings[0], rings[-1][::-1]]
        for f in faces:
            face = bm.faces.new([v for v, _ in f])
            face.smooth = True
            for loop, (_, uv_) in zip(face.loops, f):
                loop[uvl].uv = uv_
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(P + "strap")
    bm.to_mesh(me)
    bm.free()
    add("strap", me, "strap", flat_depth=False)

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * rg["bezel_outer"], 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    y_end, z_end = bend(end_y, zm)
    return {"measured_mm": out, "lug_tip_y_mm": tip, "strap_front_end_mm": round(y_end, 2), "strap_drop_mm": round(zm - z_end, 2),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
