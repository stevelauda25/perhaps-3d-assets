"""watch_fossil_fs4735: build the Fossil Grant Chronograph FS4735 (polished steel, cream chronograph dial with Roman
numerals, brown leather strap) as a flat-backed front relief.

Params: spec (config/watches/fossil-fs4735.json). Same frame as watch_fossil_fs5305: mm, origin = hand pivot, dial faces +z,
back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth with
the house curl. Own construction: round polished case with the wide sloped bezel (one lathe), crown guard shoulders above
and below the crown from the right silhouette, wide sloped lugs from the left silhouette, flat dial and minute track with the
photo map, polished steel hour and minute hands with raised white lume, steel chronograph seconds with a round
counterweight, three steel subdial needles with hubs, round pushers at 2 and 4, large knurled crown at 3.
One photo map (pipeline/fossil_fs4735_dial.py) serves the dial and the strap. Rebuild with --force after regenerating it.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT
from pipeline.steps.watch_zeppelin_z70363 import axis_matrix


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Fossil FS4735 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():  # one image, two surfaces
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"].get("depth_scale", 1.0)
    photo_uv = lambda x, y: (0.5 + x / (2 * pm["half_w_mm"]), 0.5 + (y - pm["centre_y_mm"]) / (2 * pm["half_h_mm"]))

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
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    tips, y_from = lg_t["tip_mm"], lg_t["from_y_mm"]
    q = lambda v: round(round(v * 4) / 4, 2)  # silhouette rows are 0.25 mm apart
    # lug rows: left edge only (the crown side shows the lug flank), top and bottom lug each stretched to the mean tip
    half = lambda y: sum(sil[k][1] for k in (q(y_from + (y - y_from) * (tips["top"] - y_from) / (tip - y_from)),
                                              -q(y_from + (y - y_from) * (tips["bottom"] - y_from) / (tip - y_from)))) / 2

    # ---- round case with the wide sloped polished bezel, one lathe ----
    c = cfg["case"]
    R_case = c["profile"][2][0]
    add("case", Geo().lathe([tuple(p) for p in c["profile"]], segs=192), "steel_polished")

    # ---- crown guard shoulders: right silhouette past the case circle, above and below the crown ----
    gd = cfg["guard"]
    rows = sorted((y, x) for y, x in tr["guard_y_right_mm"] if gd["from_y"] + 0.4 <= abs(y) <= gd["to_y"])
    g = Geo()
    for sy in (1, -1):
        side = [(abs(y), x) for y, x in rows if y * sy > 0]
        side = [(gd["from_y"], side[0][1])] + side
        inner_edge = [(math.sqrt(R_case ** 2 - y * y) - gd["into_case"], y) for y, _ in side]
        slab(g, [(x, sy * y) for x, y in inner_edge] + [(x, sy * y) for y, x in reversed(side)], 0.0, lambda x, y: gd["z"])
    add("guard", g, "steel_polished", bevel=gd["bevel"])

    # ---- wide sloped lugs: outline from the traced silhouette ----
    lg = cfg["lug"]
    inner = lg_t["inner_x_mm"] + lg["gap"]
    y0 = y_from - lg["into_case"]
    steps = [y_from + k * 0.25 for k in range(int((tip - y_from) / 0.25) + 1)]
    # running minimum and a 1.25 mm mean drop the strap and stitching noise from the outer edge
    edge = [max(half(y), inner + 0.3) for y in steps]
    edge = [min(edge[:k + 1]) for k in range(len(edge))]
    edge = [sum(edge[max(k - 2, 0):k + 3]) / len(edge[max(k - 2, 0):k + 3]) for k in range(len(edge))]
    outline = [(inner, y0), (math.sqrt(R_case ** 2 - y0 ** 2) - 0.2, y0)] + list(zip(edge, steps)) + [(inner, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - y_from, 0) / (tip - y_from)
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- crystal (alpha glass, no transmission); flat dial and the minute track with the photo map ----
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_inner"], cr["z0"]), (rg["bezel_inner"], cr["z1"]), (rg["bezel_inner"] * 0.7, cr["z1"] + cr["dome"] * 0.5),
                                (0, cr["z1"] + cr["dome"])], segs=192), "crystal")
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["track_inner"], d["z"]), (rg["bezel_inner"] + 0.05, d["track_z"]), (rg["bezel_inner"] + 0.05, d["z"] - 0.3)],
                     segs=192).mesh(P + "dial", True)
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

    # ---- hands at the photo's time (traced, posed outlines) ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "steel_polished", bevel=0.03)
        add("lume_" + name, Geo().prism([tuple(p) for p in t[name]["lume_mm"]], z + th - 0.02, z + th + hs["lume_raise"]), "lume")
    z = hs["z"]["seconds"]
    add("hand_seconds", Geo().prism([tuple(p) for p in t["seconds"]["outline_mm"]], z, z + th), "steel_polished", bevel=0.02)
    hub_r, collar_r = tr["hub_mm"]["radius"], tr["hub_mm"]["collar"]
    zt = z + th
    add("hub_collar", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=64), "steel_polished")
    add("hub", Geo().lathe([(0, z - 0.05), (hub_r, z - 0.05), (hub_r, zt + 0.1), (hub_r * 0.8, zt + 0.2), (0, zt + 0.22)], segs=64), "steel_polished")
    zs = hs["z"]["subdial"]
    for k, sh in tr["subdial_hands"].items():
        (cx, cy), r = sh["centre_mm"], sh["hub_radius_mm"]
        add("subhand_" + k, Geo().prism([tuple(p) for p in sh["outline_mm"]], zs, zs + th), "steel_polished", bevel=0.02)
        add("subhub_" + k, Geo().lathe([(0, d["z"]), (r, d["z"]), (r, zs + th + 0.06), (r * 0.7, zs + th + 0.12), (0, zs + th + 0.13)], segs=48,
                                       m=Matrix.Translation((cx, cy, 0))), "steel_polished")

    # ---- round pushers at 2 and 4: short tube, chamfered cap ----
    pu, pr = cfg["pusher"], tr["pusher_radius_mm"]
    for k, p in tr["pushers"].items():
        m = axis_matrix(p["angle_deg"], pu["z"])
        e = p["end_r_mm"]
        add("pusher_" + k, Geo().lathe([(0, R_case - 1.0), (pu["tube_radius"], R_case - 1.0), (pu["tube_radius"], pu["cap_from"]), (pr, pu["cap_from"]),
                                        (pr, e - 0.25), (pr - 0.25, e), (0, e)], segs=48, m=m), "steel_polished")

    # ---- large knurled crown: tube, fluted body with a chamfered end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(tc["angle_deg"], cw["z"])
    r0, r1, r2 = tc["r_tube_body_end_mm"]
    R0 = tc["radius_mm"]
    add("crown_tube", Geo().lathe([(0, r0 - 0.8), (tc["tube_radius_mm"], r0 - 0.8), (tc["tube_radius_mm"], r1 + 0.1), (0, r1 + 0.1)], segs=48, m=m), "steel_polished")
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / tc["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / tc["teeth"])) for i in range(tc["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2 - 0.3, m), "steel_polished", bevel=0.08)
    add("crown_end", Geo().lathe([(0, r2 - 0.3), (R0 - 0.15, r2 - 0.3), (R0 - 0.6, r2), (0, r2)], segs=48, m=m), "steel_polished")

    # ---- leather strap: the photo's own strap (grain, stitching) along its length, house curl from the lug tips ----
    st = cfg["strap"]
    hw = lg_t["inner_x_mm"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    ends = pm["strap_end_mm"]  # last straightened strap row; the rolled-under strap past it reuses that row
    box = curl(bend_y, R, zm)
    g = Geo()
    start = math.sqrt(R_case ** 2 - hw ** 2) - st["under_case"]
    for sy in (1, -1):
        box(g, -hw, hw, start, st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    add("strap", g, "strap_leather", bevel=st["bevel"],
        uv_of=lambda x, y, z: photo_uv(x, math.copysign(min(s_of(y, z), ends["top" if y > 0 else "bottom"]), y)))

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * R_case, 3), "strap_width": round(2 * lg_t["inner_x_mm"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": st["end_y"],
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
