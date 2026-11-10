"""watch_armani_ax1903: build the Armani Exchange AX1903 (16-sided steel case, white dial with black batons, brown leather
strap) as a flat-backed front relief.

Params: spec (config/watches/armani-ax1903.json). Same frame as watch_fossil_fs4735: mm, origin = hand pivot, dial faces +z,
back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth with
the house curl. Own construction: 16-sided case (8 long and 8 short flats) lofted from polygon rings into the round crystal
opening (wide sloped bezel top, inner bevel), crown guard shoulder from the right silhouette, wide sloped lugs from the left
silhouette, two red stripes on the bezel at 12, flat dial with the photo map, white sword hands with grey edges and black
tips, the black AX fork around the pivot (traced outline with holes), black seconds needle with a white stripe and red tip,
fluted crown with a smooth collar. One photo map (pipeline/armani_ax1903_dial.py) serves the dial and the strap.
Rebuild with --force after regenerating it.
"""
import json
import math

import bpy

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT
from pipeline.steps.watch_zeppelin_z70363 import axis_matrix


def case_outline(long, short, inset=0.0):
    """16-gon from support distances: long flats at k * 45 deg (0 = 12 o'clock, clockwise), short flats between them; moved
    in by inset. Same as pipeline/armani_ax1903_trace.case_outline (that module needs OpenCV)."""
    d = [(long if k % 2 == 0 else short) - inset for k in range(16)]
    pts = []
    for k in range(16):
        a1, a2 = math.radians(22.5 * k), math.radians(22.5 * (k + 1))
        d1, d2 = d[k], d[(k + 1) % 16]
        det = math.sin(a1) * math.cos(a2) - math.cos(a1) * math.sin(a2)
        pts.append(((d1 * math.cos(a2) - d2 * math.cos(a1)) / det, (d2 * math.sin(a1) - d1 * math.sin(a2)) / det))
    return pts


def ray(long, short, inset, a):
    """Distance from the centre to the inset 16-gon along clock angle a (rad)."""
    return min(((long if k % 2 == 0 else short) - inset) / c for k in range(16)
               for c in [math.cos(a - math.radians(22.5 * k))] if c > 1e-6)


def x_extent(poly, y):
    """Largest x where the horizontal line y crosses the convex polygon."""
    xs = [a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(poly, poly[1:] + poly[:1])
          if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]]
    return max(xs)


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Armani Exchange AX1903 front relief")
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
    long, short = tr["case_support_mm"]["long"], tr["case_support_mm"]["short"]
    outline = case_outline(long, short)
    tip = lg_t["tip_mm"]["mean"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    tips, y_from = lg_t["tip_mm"], lg_t["from_y_mm"]
    q = lambda v: round(round(v * 4) / 4, 2)  # silhouette rows are 0.25 mm apart
    half = lambda y: sum(sil[k][1] for k in (q(y_from + (y - y_from) * (tips["top"] - y_from) / (tip - y_from)),
                                              -q(y_from + (y - y_from) * (tips["bottom"] - y_from) / (tip - y_from)))) / 2

    # ---- 16-sided case: loft of polygon rings (inset from the outline) into round rings (crystal opening) ----
    c = cfg["case"]
    rings = c["rings"]  # [kind, inset mm (poly) or radius mm (round), z]
    angles = set()
    for kind, v, _ in rings:
        if kind == "poly":
            angles.update(round(math.atan2(x, y) % (2 * math.pi), 6) for x, y in case_outline(long, short, v))
    angles = sorted(angles)
    samples = []
    for a0, a1 in zip(angles, angles[1:] + [angles[0] + 2 * math.pi]):
        n = max(1, round(math.degrees(a1 - a0) / c["step_deg"]))
        samples += [a0 + (a1 - a0) * i / n for i in range(n)]
    ring_pts = lambda kind, v, z: [((ray(long, short, v, a) if kind == "poly" else v) * math.sin(a),
                                    (ray(long, short, v, a) if kind == "poly" else v) * math.cos(a), z) for a in samples]
    N = len(samples)
    g = Geo()
    for lo, hi in zip(rings, rings[1:]):  # own vertices per band: hard edges between bands; flat facets, smooth round bands
        base = len(g.v)
        g.v += ring_pts(*lo) + ring_pts(*hi)
        for k in range(N):  # outer ring first, so (k+1, k) on the lower ring keeps the normals outward/up
            kk = (k + 1) % N
            g.f.append((base + kk, base + k, base + N + k, base + N + kk))
            g.smooth.append(not (lo[0] == hi[0] == "poly"))
    g.v += ring_pts(*rings[0])
    g.f.append(tuple(range(len(g.v) - N, len(g.v))))  # flat back
    g.smooth.append(False)
    add("case", g, "steel_brushed")
    top_z = lambda d: next(z0 + (z1 - z0) * (d - d0) / (d1 - d0) for (k0, d0, z0), (k1, d1, z1) in zip(rings, rings[1:])
                           if k0 == k1 == "poly" and d0 <= d <= d1 and d1 > d0)  # bezel height over the long flats

    # ---- crown guard shoulder: right silhouette past the case, sloping down to the crown ----
    gd = cfg["guard"]
    side = tr["guard_mm"]
    side = side + [(x, -y) for x, y in reversed(side[:-1])]
    inner_edge = [(x_extent(outline, y) - gd["into_case"], y) for _, y in side]
    x_in = side[0][0]
    g = Geo()
    slab(g, list(reversed(inner_edge)) + [tuple(p) for p in side], 0.0, lambda x, y: gd["z"] - gd["slope"] * max(x - x_in, 0))
    add("guard", g, "steel_brushed", bevel=gd["bevel"])

    # ---- red stripes at 12 on the sloped bezel top ----
    g = Geo()
    for yt, yb, ht, hb in tr["marker_mm"]:
        slab(g, [(-hb, yb), (hb, yb), (ht, yt), (-ht, yt)], top_z(long - yb) - 0.4, lambda x, y: top_z(long - y) + cfg["marker"]["raise"])
    add("marker", g, "marker_red")

    # ---- wide sloped lugs: outline from the traced silhouette ----
    lg = cfg["lug"]
    inner = lg_t["inner_x_mm"] + lg["gap"]
    y0 = y_from - lg["into_case"]
    steps = [y_from + k * 0.25 for k in range(int((tip - y_from) / 0.25) + 1)]
    edge = [max(half(y), inner + 0.3) for y in steps]
    edge = [min(edge[:k + 1]) for k in range(len(edge))]
    edge = [sum(edge[max(k - 2, 0):k + 3]) / len(edge[max(k - 2, 0):k + 3]) for k in range(len(edge))]
    lug_poly = [(inner, y0), (x_extent(outline, y0) - 0.2, y0)] + list(zip(edge, steps)) + [(inner, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - y_from, 0) / (tip - y_from)
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in lug_poly], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"])

    # ---- crystal (alpha glass, no transmission); flat dial with the photo map ----
    cr = cfg["crystal"]
    R_open = rg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (R_open, cr["z0"]), (R_open, cr["z1"]), (R_open * 0.7, cr["z1"] + cr["dome"] * 0.5),
                                (0, cr["z1"] + cr["dome"])], segs=192), "crystal")
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["dial_flat"], d["z"]), (R_open + 0.05, d["track_z"]), (R_open + 0.05, d["z"] - 0.3)],
                     segs=192).mesh(P + "dial", True)
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

    # ---- hands at the photo's time: white swords with grey edges and black tips, the black AX fork, seconds needle ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["body_mm"]], z, z + th), "steel_polished", bevel=0.03)
        add("lume_" + name, Geo().prism([tuple(p) for p in t[name]["lume_mm"]], z + th - 0.02, z + th + hs["lume_raise"]), "lume")
        add("tip_" + name, Geo().prism([tuple(p) for p in t[name]["tip_mm"]], z, z + th + hs["lume_raise"]), "paint_black")
    z = hs["z"]["fork"]
    add("hand_fork", plate(t["fork"], z, z + th, P + "hand_fork"), "paint_black")
    z = hs["z"]["seconds"]
    sc = t["seconds"]
    add("hand_seconds", Geo().prism([tuple(p) for p in sc["outline_mm"]], z, z + th), "paint_black")
    add("seconds_stripe", Geo().prism([tuple(p) for p in sc["stripe_mm"]], z + th - 0.02, z + th + 0.02), "lume")
    add("seconds_red", Geo().prism([tuple(p) for p in sc["red_mm"]], z + th - 0.02, z + th + 0.02), "marker_red")
    hub_r = tr["hub_mm"]
    zt = z + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt + 0.06), (hub_r * 0.7, zt + 0.1), (0, zt + 0.11)], segs=48), "steel_polished")

    # ---- crown: smooth collar, fluted body, chamfered end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(tc["angle_deg"], cw["z"])
    r0, r1, r2 = tc["r_collar_knurl_end_mm"]
    R0, Rc = tc["radius_mm"], tc["collar_radius_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 1.0), (Rc, r0 - 1.0), (Rc, r1 + 0.1), (0, r1 + 0.1)], segs=64, m=m), "steel_polished")
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / tc["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / tc["teeth"])) for i in range(tc["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2 - 0.35, m), "steel_polished", bevel=0.06)
    add("crown_end", Geo().lathe([(0, r2 - 0.35), (R0 - 0.15, r2 - 0.35), (R0 - 0.7, r2), (0, r2)], segs=64, m=m), "steel_polished")

    # ---- leather strap: the photo's own strap along its length, house curl from the lug tips ----
    st = cfg["strap"]
    hw = lg_t["inner_x_mm"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    ends = pm["strap_end_mm"]  # last straightened strap row; the rolled-under strap past it reuses that row
    box = curl(bend_y, R, zm)
    g = Geo()
    start = x_extent([(y, x) for x, y in outline], hw) - st["under_case"]  # case top edge above the strap edge
    for sy in (1, -1):
        box(g, -hw, hw, start, st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    add("strap", g, "strap_leather", bevel=st["bevel"],
        uv_of=lambda x, y, z: photo_uv(x, math.copysign(min(s_of(y, z), ends["top" if y > 0 else "bottom"]), y)))

    # ---- checks against the anchors ----
    out = {"across_flats": round(2 * x_extent(outline, 0.0), 3), "strap_width": round(2 * lg_t["inner_x_mm"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": st["end_y"],
            "case_segments": N, "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
