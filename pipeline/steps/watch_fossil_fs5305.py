"""watch_fossil_fs5305: build the Fossil The Minimalist FS5305 (black IP steel, black dial, light brown leather strap) as a
flat-backed front relief.

Params: spec (config/watches/fossil-fs5305.json). Same frame as watch_zeppelin_z96903: mm, origin = hand pivot, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth
with the house curl. Own construction: thin round black polished case with a wide sloped bezel (one lathe), plain sloped
black lugs from the traced silhouette, flat dial and minute track with the photo map, black hour and minute hands (needle
tips) with raised beige lume inserts, orange seconds needle with a spear counterweight on an orange hub over a black collar,
knurled black crown at 3. One photo map (pipeline/fossil_fs5305_dial.py) serves the dial and the strap. Rebuild with
--force after regenerating it.
"""
import json
import math

import bpy

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT
from pipeline.steps.watch_zeppelin_z70363 import axis_matrix


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Fossil FS5305 front relief")
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
    # lug rows: both edges, top and bottom lug each stretched to the mean tip
    half = lambda y: sum((sil[k][1] + sil[k][2]) / 2 for k in (q(y_from + (y - y_from) * (tips["top"] - y_from) / (tip - y_from)),
                                                               -q(y_from + (y - y_from) * (tips["bottom"] - y_from) / (tip - y_from)))) / 2

    # ---- thin round case with the wide sloped polished bezel, one lathe ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile"]], segs=192), "black_polished")

    # ---- plain sloped lugs: outline from the traced silhouette ----
    lg = cfg["lug"]
    inner = lg_t["inner_x_mm"] + lg["gap"]
    y0 = lg_t["from_y_mm"] - lg["into_case"]
    steps = [lg_t["from_y_mm"] + k * 0.25 for k in range(int((tip - lg_t["from_y_mm"]) / 0.25) + 1)]
    # running minimum and a 1.25 mm mean drop the strap and stitching noise from the outer edge
    edge = [max(half(y), inner + 0.3) for y in steps]
    edge = [min(edge[:k + 1]) for k in range(len(edge))]
    edge = [sum(edge[max(k - 2, 0):k + 3]) / len(edge[max(k - 2, 0):k + 3]) for k in range(len(edge))]
    outline = [(inner, y0), (math.sqrt(c["profile"][2][0] ** 2 - y0 ** 2) - 0.2, y0)] + list(zip(edge, steps)) + [(inner, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - lg_t["from_y_mm"], 0) / (tip - lg_t["from_y_mm"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "black_polished", bevel=lg["bevel"])

    # ---- crystal (alpha glass, no transmission); flat dial and the minute track with the photo map ----
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_inner"], cr["z0"]), (rg["bezel_inner"], cr["z1"]), (rg["bezel_inner"] * 0.7, cr["z1"] + cr["dome"] * 0.5),
                                (0, cr["z1"] + cr["dome"])], segs=192), "crystal")
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["track_inner"], d["z"]), (rg["bezel_inner"] + 0.05, d["track_z"]), (rg["bezel_inner"] + 0.05, d["z"] - 0.3)],
                     segs=192).mesh(P + "dial", True)
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

    # ---- hands at the photo's time (traced, posed outlines): black frames with raised lume, orange seconds ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "hand_black", bevel=0.03)
        add("lume_" + name, Geo().prism([tuple(p) for p in t[name]["lume_mm"]], z + th, z + th + hs["lume_raise"]), "lume", bevel=0.03)
    z = hs["z"]["seconds"]
    add("hand_seconds", Geo().prism([tuple(p) for p in t["seconds"]["outline_mm"]], z, z + th), "hand_orange", bevel=0.02)
    add("hand_seconds_tail", Geo().prism([tuple(p) for p in t["seconds"]["tail_mm"]], z, z + th), "hand_orange", bevel=0.02)
    hub_r, collar_r = tr["hub_mm"]["radius"], tr["hub_mm"]["collar"]
    zt = z + th
    add("hub_collar", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=64), "hand_black")
    add("hub", Geo().lathe([(0, z - 0.05), (hub_r, z - 0.05), (hub_r, zt + 0.1), (hub_r * 0.8, zt + 0.2), (0, zt + 0.22)], segs=64), "hand_orange")

    # ---- knurled crown: short neck, fluted body with a flat chamfered end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(tc["angle_deg"], cw["z"])
    r0, r1 = tc["r_from_to_mm"]
    R0 = tc["radius_mm"]
    add("crown_neck", Geo().lathe([(0, r0 - 0.8), (cw["neck_radius"], r0 - 0.8), (cw["neck_radius"], r0 + 0.1), (0, r0 + 0.1)], segs=48, m=m), "black_polished")
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / tc["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / tc["teeth"])) for i in range(tc["teeth"] * 2)]
    add("crown", Geo().prism(star, r0, r1 - 0.25, m), "black_polished", bevel=0.08)
    add("crown_end", Geo().lathe([(0, r1 - 0.25), (R0 - 0.15, r1 - 0.25), (R0 - 0.45, r1), (0, r1)], segs=48, m=m), "black_polished")

    # ---- leather strap: the photo's own strap (grain, stitching) along its length, house curl from the lug tips ----
    st = cfg["strap"]
    hw = lg_t["inner_x_mm"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    ends = pm["strap_end_mm"]  # last straightened strap row; the rolled-under strap past it reuses a row uv_end_inset before it (the last rows touch the photo edge)
    box = curl(bend_y, R, zm)
    g = Geo()
    start = math.sqrt(c["profile"][2][0] ** 2 - hw ** 2) - st["under_case"]
    for sy in (1, -1):
        box(g, -hw, hw, start, st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    xin = hw - st["uv_edge_inset"]  # the photo's strap edge columns are pale (background): the strap sides use leather just inside
    add("strap", g, "strap_leather", bevel=st["bevel"],
        uv_of=lambda x, y, z: photo_uv(max(-xin, min(x, xin)), math.copysign(min(s_of(y, z), ends["top" if y > 0 else "bottom"] - st["uv_end_inset"]), y)))

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(p[0] for p in c["profile"]), 3), "strap_width": round(2 * lg_t["inner_x_mm"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": st["end_y"],
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
