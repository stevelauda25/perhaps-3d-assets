"""watch_emporio_armani_ar11327: build the Emporio Armani Matteo AR11327 (matte gold aluminium, teal dial, gold mesh
bracelet) as a flat-backed front relief.

Params: spec (config/watches/emporio-armani-ar11327.json). Same frame as watch_fossil_fs4735: mm, origin = hand pivot, dial
faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at
final depth with the house curl. Own construction: round case with a thick domed bezel (one lathe), open wire lugs (one arm
per side from the case flank to the end cap, window between arm and case), rectangular end caps that clamp the mesh, flat
dial and sloped flange with the photo map, applied gold hour bars, gold stick hands and hub, black knurled crown at 3, mesh
bracelet from a repeating photo tile (pipeline/emporio_armani_ar11327_dial.py). Rebuild with --force after regenerating it.
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
    map_path = ROOT / cfg["photo_map"]
    pm = json.loads(map_path.with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Emporio Armani AR11327 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    mats["dial"] = photo_material("dial", map_path, cfg["photo_roughness"]["dial"])
    mats["strap_mesh"] = photo_material("strap_mesh", map_path.with_name(pm["mesh"]["file"]), cfg["photo_roughness"]["strap_mesh"])

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"].get("depth_scale", 1.0)

    def add(name, geo, mat, bevel=None, uv_of=None):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if uv_of:
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

    # ---- case and domed bezel, one lathe ----
    c = cfg["case"]
    R_case = max(p[0] for p in c["profile"])
    add("case", Geo().lathe([tuple(p) for p in c["profile"]], segs=192), "gold_matte")

    # ---- dial and sloped flange (photo map), crystal ----
    d, rg = cfg["dial"], tr["rings_mm"]
    dial = Geo().lathe([(0, d["z"]), (d["flange_r"], d["z"]), (rg["groove"] + 0.03, d["flange_z"]), (rg["groove"] + 0.03, d["z"] - 0.3), (0, d["z"] - 0.3)], segs=192)
    add("dial", dial.mesh(P + "dial", True), "dial",
        uv_of=lambda x, y, z: (0.5 + x / (2 * pm["half_w_mm"]), 0.5 + y / (2 * pm["half_h_mm"])))
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["groove"], cr["z0"]), (rg["groove"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- applied hour bars (traced rectangles) ----
    hb = cfg["hour_bars"]
    g = Geo()
    for bar in tr["hour_bars"]:
        g.prism([tuple(p) for p in bar["corners_mm"]], d["z"] - 0.05, d["z"] + hb["height"])
    add("hour_bars", g, "gold_polished", bevel=hb["bevel"])

    # ---- gold stick hands at the photo's time, hub with a pin ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name, h in tr["hands"].items():
        a, w, L = math.radians(h["angle_deg"]), h["half_width_mm"], h["length_mm"]
        u, n = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
        poly = [(u[0] * s + n[0] * k * w, u[1] * s + n[1] * k * w) for s, k in ((-hs["root"], -1), (L, -1), (L, 1), (-hs["root"], 1))]
        z = hs["z"][name]
        add("hand_" + name, Geo().prism(poly, z, z + th), "gold_polished", bevel=0.02)
    hub, zt = tr["hub_mm"], hs["z"]["seconds"] + th
    # the photo's hub ring sits over all three hands, the pin just under the crystal
    add("hub", Geo().lathe([(0, d["z"]), (hub["radius"], d["z"]), (hub["radius"], zt + 0.03), (hub["pin"], zt + 0.03),
                            (hub["pin"], zt + 0.07), (0, zt + 0.08)], segs=64), "gold_polished")

    # ---- open wire lugs: outer edge from the left silhouette, arm width inward, bottom end sunk into the case ----
    ar, at = cfg["arm"], tr["arm"]
    outer = [(x, y) for y, x in at["outer_y_x_mm"] if y >= at["from_y_mm"]]
    y_in = at["from_y_mm"] - ar["into_case"]
    outer = [(math.sqrt((R_case - 0.4) ** 2 - y_in ** 2), y_in)] + outer
    w = at["width_mm"]
    inner = []
    for k, (x, y) in enumerate(outer):
        a, b = outer[max(k - 1, 0)], outer[min(k + 1, len(outer) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        inner.append((x - dy / ln * w, y + dx / ln * w))  # left normal of the upward run points into the window
    (ox, oy), (ix, iy) = outer[-1], inner[-1]
    cx_, cy_ = (ox + ix) / 2, (oy + iy) / 2
    a0 = math.atan2(oy - cy_, ox - cx_)
    cap = [(cx_ + w / 2 * math.cos(a0 + math.pi * k / 8), cy_ + w / 2 * math.sin(a0 + math.pi * k / 8)) for k in range(1, 8)]
    outline = outer + cap + inner[::-1]
    span = at["top_y_mm"] - at["from_y_mm"]
    slope = lambda x, y: ar["top_z_at_case"] + (ar["top_z_at_tip"] - ar["top_z_at_case"]) * min(max(abs(y) - at["from_y_mm"], 0) / span, 1)
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "gold_matte", bevel=ar["bevel"])

    # ---- end caps clamping the mesh ----
    ec, et = cfg["end_cap"], tr["end_cap_mm"]
    hw_cap = et["half_width"]
    g = Geo()
    for sy in (1, -1):
        g.prism([(-hw_cap, sy * et["inner"]), (hw_cap, sy * et["inner"]), (hw_cap, sy * et["outer"]), (-hw_cap, sy * et["outer"])], ec["z0"], ec["z1"])
    add("end_caps", g, "gold_matte", bevel=ec["bevel"])

    # ---- black knurled crown at 3 ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(90.0, cw["z"])
    r1, r2 = tc["r_start_end_mm"]
    R0 = tc["radius_mm"]
    add("crown_tube", Geo().lathe([(0, R_case - 1.0), (cw["tube_radius"], R_case - 1.0), (cw["tube_radius"], r1 + 0.1), (0, r1 + 0.1)], segs=48, m=m), "gold_matte")
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / tc["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / tc["teeth"])) for i in range(tc["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2 - 0.35, m), "crown_black", bevel=0.1)
    add("crown_end", Geo().lathe([(0, r2 - 0.35), (R0 - 0.15, r2 - 0.35), (R0 - 0.6, r2), (0, r2)], segs=48, m=m), "crown_black")

    # ---- mesh bracelet: repeating photo tile along the band, house curl from the end caps' outer edge ----
    st, mt = cfg["strap"], pm["mesh"]
    hw = st["half_width"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], et["outer"] + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw, hw, st["start_y"], st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    add("strap_mesh", g, "strap_mesh", bevel=st["bevel"],
        uv_of=lambda x, y, z: (0.5 + x / (2 * hw), math.copysign(s_of(y, z), y) / mt["tile_mm"]))

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * R_case, 3), "end_cap_width": round(2 * hw_cap, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "end_cap_outer_y_mm": et["outer"], "lug_to_lug_mm": round(2 * et["outer"], 2), "strap_end_y_mm": st["end_y"],
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
