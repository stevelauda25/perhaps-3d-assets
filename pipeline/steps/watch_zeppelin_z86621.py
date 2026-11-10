"""watch_zeppelin_z86621: build the Zeppelin New Captain's Line Z86621 (8662-1: steel, white dial with 24 h and small seconds
sub-dials, brown leather strap) as a flat-backed front relief.

Params: spec (config/watches/zeppelin-z86621.json). Same frame as watch_zeppelin_z96645: mm, origin = dial centre, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth
with the house curl. Own construction: round polished case with a thin polished bezel (one lathe), plain polished lugs from
the traced silhouette, flat white dial with a sloped rehaut (photo map: print, sub-dials, gold 24 h batons, logo), faceted
dark steel dauphine hour and minute hands (two facets meeting at a ridge on the hand's axis) on a grey collet and cap with a
polished ring, black needles on black hubs with steel pins on the 24 h sub-dial at 9 and the small seconds at 4-5, large fluted crown
with a domed end at 3. Two photo maps (pipeline/zeppelin_z86621_dial.py): the dial, and the strap leather from the photo's
12 o'clock strap, used on both sides. Rebuild with --force after regenerating them.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot
from pipeline.steps.watch_zeppelin_z96645 import axis_matrix


def faceted_hand(prof, L, deg, z0, ze, zr):
    """Two facets meeting at a ridge on the hand's axis. prof: (along, half width) from the trace, unposed; the tip at L."""
    prof = [p for p in prof if p[1] > 0.01 and p[0] < L - 0.05]  # the traced tip point is replaced by the ridge tip at L
    g = Geo()
    for sx in (1, -1):
        b = len(g.v)
        n = len(prof)
        for s, w in prof:  # per station: ridge top, edge top, edge bottom, axis bottom
            for x, z in ((0.0, zr), (sx * w, ze), (sx * w, z0), (0.0, z0)):
                g.v.append((*rot(x, s, deg), z))
        tip = len(g.v)
        g.v += [(*rot(0.0, L, deg), ze), (*rot(0.0, L, deg), z0)]
        faces = []
        for i in range(n - 1):
            a, c = b + 4 * i, b + 4 * i + 4
            faces += [(a, a + 1, c + 1, c), (a + 1, a + 2, c + 2, c + 1), (a + 3, c + 3, c + 2, a + 2)]  # facet, edge wall, bottom
        a = b + 4 * (n - 1)
        faces += [(a, a + 1, tip), (a + 1, a + 2, tip + 1, tip), (a + 3, tip + 1, a + 2), (b, b + 3, b + 2, b + 1)]  # tip, root cap
        for f in faces:
            g.f.append(f if sx > 0 else f[::-1])  # mirrored half: flip the winding to keep normals outward
            g.smooth.append(False)
    return g


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Zeppelin Z86621 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    mats["dial"] = photo_material("dial", ROOT / cfg["dial_map"], cfg["photo_roughness"]["dial"])
    mats["strap_leather"] = photo_material("strap_leather", ROOT / cfg["strap_map"], cfg["photo_roughness"]["strap_leather"])

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"].get("depth_scale", 1.0)
    photo_uv = lambda x, y: (0.5 + x / (2 * pm["dial_half_mm"]), 0.5 + y / (2 * pm["dial_half_mm"]))
    s0, s1 = pm["strap_s_from_to_mm"]
    strap_uv = lambda x, s: (0.5 + x / (2 * pm["strap_half_w_mm"]), 1 - min(max((s - s0) / (s1 - s0), 0.0), 1.0))

    def add(name, geo, mat, bevel=None, uv_of=None):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if uv_of:  # photo map: uv_of(x, y, z) -> map coordinates
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co)
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    rg, lg_t = tr["rings_mm"], tr["lug"]
    tip = lg_t["tip_mm"]["mean"]
    ol = lg_t["outline_half_mm"]  # (y, half width) along the lug, traced about the case centre
    half = lambda y: next(h0 + (h1 - h0) * (y - y0_) / (y1_ - y0_) for (y0_, h0), (y1_, h1) in zip(ol, ol[1:]) if y <= y1_ + 1e-6)

    # ---- round polished case with the thin polished bezel, one lathe ----
    c = cfg["case"]
    R_case = max(p[0] for p in c["profile"])
    add("case", Geo().lathe([tuple(p) for p in c["profile"]], segs=192), "steel_polished")

    # ---- plain polished lugs from the traced silhouette, top sloping down to the tip ----
    lg = cfg["lug"]
    inner = lg_t["inner_x_mm"] + lg["gap"]
    y0 = lg_t["from_y_mm"] - lg["into_case"]
    y_sq = tip - lg["square_tip"]  # past this the traced edge is the lug's end bending away: the end is cut square instead
    steps = [lg_t["from_y_mm"] + k * 0.25 for k in range(int((y_sq - lg_t["from_y_mm"]) / 0.25) + 1)]
    outline = [(inner, y0), (math.sqrt(R_case ** 2 - y0 ** 2) - 0.2, y0)] + [(max(half(y), inner + 0.3), y) for y in steps]
    outline += [(half(y_sq) - 0.15, tip), (inner, tip)]
    za, zb = lg["top_z"]
    slope = lambda x, y: za + (zb - za) * max(abs(y) - lg_t["from_y_mm"], 0) / (tip - lg_t["from_y_mm"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- crystal (alpha glass, no transmission) and the dial with the photo map ----
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_inner"], cr["z0"]), (rg["bezel_inner"], cr["z1"]), (rg["bezel_inner"] * 0.7, cr["z1"] + cr["dome"] * 0.5),
                                (0, cr["z1"] + cr["dome"])], segs=192), "crystal")
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["dial_edge"], d["z"]), (rg["bezel_inner"] + 0.05, d["flange_z"]), (rg["bezel_inner"] + 0.05, d["z"] - 0.3)],
                     segs=192).mesh(P + "dial", True)  # flat dial and the sloped rehaut, one photo map
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

    # ---- faceted hour and minute hands at the photo's time, collet and polished cap ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name in ("hour", "minute"):
        h, z = tr["hands"][name], hs["z"][name]
        add("hand_" + name, faceted_hand(h["half_profile_mm"], h["length_mm"], h["angle_deg"], z, z + th, z + th + hs["ridge"]), "hand_dark")
    hub, (cr0, cr1, ct) = tr["hub_mm"], hs["cap"]
    zc = hs["collet_top"]  # over the hand roots, as in the photo
    add("hub", Geo().lathe([(0, d["z"]), (hub["collet"], d["z"]), (hub["collet"], zc), (0, zc)], segs=64), "hub_grey")
    add("hub_cap", Geo().lathe([(0, zc), (cr1, zc), (cr1, ct - 0.03), (0, ct - 0.03)], segs=48), "hub_grey")
    add("hub_ring", Geo().lathe([(cr1, zc), (cr0, zc), (cr0, ct - 0.03), (cr0 - 0.04, ct), (cr1 + 0.04, ct), (cr1, ct - 0.03)], segs=48), "steel_polished")

    # ---- sub-dial needles (24 h at 9, small seconds) on black hubs with steel pins ----
    zs = hs["z"]["sub"]
    for k, sd in tr["subdials"].items():
        cx, cy = sd["centre_mm"]
        add("sub_hand_" + k, Geo().prism([(cx + x, cy + y) for x, y in sd["outline_mm"]], zs, zs + th), "hand_black", bevel=0.02)
        m = Matrix.Translation((cx, cy, 0))
        sr = sd["hub_radius_mm"]
        add("sub_hub_" + k, Geo().lathe([(0, d["z"]), (sr, d["z"]), (sr, zs + th + 0.08), (0, zs + th + 0.08)], segs=48, m=m), "hand_black")
        add("sub_pin_" + k, Geo().lathe([(0, zs + th + 0.08), (hs["sub_pin"], zs + th + 0.08), (hs["sub_pin"], zs + th + 0.22), (0, zs + th + 0.26)], segs=24, m=m),
            "steel_polished")

    # ---- crown: neck, fluted body, domed end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(tc["angle_deg"], cw["z"])
    r1, r2, r3 = tc["r_from_to_mm"]
    R0 = tc["radius_mm"]
    add("crown_neck", Geo().lathe([(0, r1 - 1.6), (cw["neck_radius"], r1 - 1.6), (cw["neck_radius"], r1), (0, r1)], segs=48, m=m), "steel_polished")
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2, m), "steel_polished", bevel=0.15)
    dome, Rd = r3 - r2, tc["dome_radius_mm"]
    add("crown_end", Geo().lathe([(0, r2 - 0.05)] + [(Rd * math.cos(a), r2 + dome * math.sin(a)) for a in [k * math.pi / 24 for k in range(12)]]
                                 + [(0, r3)], segs=48, m=m), "steel_polished")

    # ---- leather strap: the photo's 12 o'clock strap (grain, stitching) on both sides, house curl from the lug tips ----
    st = cfg["strap"]
    hw = lg_t["inner_x_mm"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    box = curl(bend_y, R, zm)
    g = Geo()
    start = math.sqrt(R_case ** 2 - hw ** 2) - st["under_case"]
    for sy in (1, -1):
        box(g, -hw, hw, start, st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    add("strap", g, "strap_leather", bevel=st["bevel"],
        uv_of=lambda x, y, z: strap_uv(x if y > 0 else -x, s_of(y, z)))  # 6 o'clock side: the map turned round, past its end the last row

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * R_case, 3), "strap_width": round(2 * lg_t["inner_x_mm"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": st["end_y"],
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
