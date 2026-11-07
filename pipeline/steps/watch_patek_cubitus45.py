"""watch_patek_cubitus45: the PATEK PHILIPPE Cubitus 5821/1A (45 mm steel, green embossed dial, steel bracelet) build; the Cubitus TEMPLATE (other Cubitus references follow with their own spec / measure / job JSON).

Own copy of pipeline/steps/watch_patek_aquanaut40.py (untouched; same recipe, same helpers, spec driven) with these changes for the squarish Cubitus case and its steel bracelet:
  - the bezel outer edge is the MEASURED rounded-octagon polygon (trace.bezel_outer_mm.polygon_mm, rays from the pivot) cut back to the case silhouette (less case.silhouette_margin_mm), instead of a superellipse;
  - the window edge is the traced polygon sampled on the same rays (trace.aperture.face_edge_r_mm; the prep copy patek_cubitus45_prep writes it), a flat recessed rim ring of chamfer_mm slopes to the dial;
  - the strap is a STEEL BRACELET: strap.bracelet.pieces_mm = link pieces between the measured joints (top and bottom separately, outline = the silhouette at every 0.25 mm row, so the shingled link edges follow the photo), gaps between
    them show a dark backing; emission top / bottom separately; material strap_photo (steel_photo projection, non-metallic with specular as in the spec);
  - no lug inner walls (the case slab is the silhouette between the case shoulders, trace silhouette = strap outline).
Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the maps (the maps are not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def rays(poly, n):
    """Distance from the origin to the closed polygon (furthest hit) along n equal angles, counter-clockwise from +x."""
    segs = list(zip(poly, poly[1:] + poly[:1]))
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        dx, dy = math.cos(a), math.sin(a)
        best = 0.0
        for (x1, y1), (x2, y2) in segs:
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = (x1 * ey - y1 * ex) / den
            u = (x1 * dy - y1 * dx) / den
            if t > 0 and -1e-9 <= u <= 1 + 1e-9:
                best = max(best, t)
        out.append(best)
    return out


def ring(g, outer, inner, z0, zo, zi):
    """Annulus between two equal-length counter-clockwise point lists: top sloping from zo (outer edge) to zi (inner edge), walls down to z0, flat bottom."""
    n, base = len(outer), len(g.v)
    g.v += [(x, y, z0) for x, y in outer] + [(x, y, zo) for x, y in outer] + [(x, y, z0) for x, y in inner] + [(x, y, zi) for x, y in inner]
    ob, ot, ib, it = base, base + n, base + 2 * n, base + 3 * n
    for k in range(n):
        j = (k + 1) % n
        g.f += [(ot + k, ot + j, it + j, it + k), (ob + k, ob + j, ot + j, ot + k), (it + k, it + j, ib + j, ib + k), (ib + k, ib + j, ob + j, ob + k)]
        g.smooth += [False] * 4
    return g


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    meta = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"].split(" (")[0])
    scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], cfg["dial"]["roughness"])
    dn = mats["dial"].node_tree
    db = next(n for n in dn.nodes if n.type == "BSDF_PRINCIPLED")
    db.inputs["Specular IOR Level"].default_value = cfg["dial"]["specular"]
    dn.links.new(next(n for n in dn.nodes if n.type == "TEX_IMAGE").outputs["Color"], db.inputs["Emission Color"])  # keeps the printed gold as photographed
    db.inputs["Emission Strength"].default_value = cfg["dial"]["emission"]
    steel_meta = json.loads((ROOT / cfg["steel_map"]).with_suffix(".json").read_text())
    mats["steel_photo"] = photo_material("steel_photo", ROOT / cfg["steel_map"], cfg["steel"]["roughness"])
    nt = mats["steel_photo"].node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Specular IOR Level"].default_value = cfg["steel"]["specular"]
    nt.links.new(next(n for n in nt.nodes if n.type == "TEX_IMAGE").outputs["Color"], bs.inputs["Emission Color"])  # the photo's own shading, not re-lit away
    bs.inputs["Emission Strength"].default_value = cfg["steel"]["emission"]
    mats["strap_photo"] = mats["steel_photo"].copy()  # bracelet: same projected photo, own emission and roughness, no specular
    sb = mats["strap_photo"].node_tree.nodes[bs.name]
    sr = cfg["strap"]["bracelet"]
    sb.inputs["Emission Strength"].default_value = sr.get("emission", cfg["steel"]["emission"])
    sb.inputs["Roughness"].default_value = sr.get("roughness", cfg["steel"]["roughness"])
    sb.inputs["Specular IOR Level"].default_value = sr.get("specular", 0.0)
    mats["hands_photo"] = mats["steel_photo"].copy()  # same projected photo; own emission (hands.emission) so the photographed gold/lume brightness can be matched
    mats["hands_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["hands"].get("emission", cfg["steel"]["emission"])
    S_px, (px0, py0) = tr["scale_px_per_mm"], tr["origin_px"]
    cx0, cy0 = steel_meta["crop_px"][:2]
    mw, mh = steel_meta["size_px"]
    k_map = steel_meta.get("scale", 2)  # map pixels per photo pixel (native Patek maps: 1)

    def steel_uv(me):  # the photo projected straight from the front: every steel part shows the photographed pixels at its x, y
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = ((px0 + x * S_px - cx0) * k_map / mw, 1 - (py0 - y * S_px - cy0) * k_map / mh)

    H = meta["half_size_mm"]
    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in ("steel_photo", "hands_photo", "strap_photo", "strap_photo_bottom"):
            steel_uv(me)
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    def photo_uv(me):  # planar, centred on the pivot; faces up
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
        return me

    cs, d, ap = cfg["case"], cfg["dial"], tr["aperture"]
    NA = ap["n"]
    assert NA == cs["rays"], "aperture rays and case rays must match"
    pol = lambda rs: [(r * math.cos(2 * math.pi * k / NA), r * math.sin(2 * math.pi * k / NA)) for k, r in enumerate(rs)]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    y_lo, y_hi = min(sil), max(sil)

    def edges(y):  # left and right silhouette x at y (the photo is not exactly centred on the pivot)
        p = sil[round(round(max(y_lo, min(y_hi, y)) * 4) / 4, 2)]
        return p[1], p[2]

    # ---- integrated case and lugs from the silhouette (own length top and bottom), top sloping into the bracelet ----
    tt, tb = cs["tip_top"], cs["tip_bottom"]
    ys = [-tb + k * 0.25 for k in range(int(round((tt + tb) / 0.25)) + 1)]
    outline = [(edges(y)[1], y) for y in ys] + [(edges(y)[0], y) for y in reversed(ys)]
    ramp = lambda x, y: cs["body_z"] - (cs["body_z"] - cs["tip_z"]) * min(1.0, max(0.0, (abs(y) - cs["ramp_from_y"]) / ((tt if y > 0 else tb) - cs["ramp_from_y"])))
    g = Geo()
    slab(g, outline, 0.0, ramp)
    add("case", g, "steel_photo", bevel=cs["bevel"])

    # ---- bezel: superellipse ring (outer edge = measured superellipse cut back to the silhouette), flat brushed face at bezel_z out to the scanned window edge, polished chamfer down to the window ----
    N, zb = cs["rays"], cs["bezel_z"]
    r_se = rays([tuple(p) for p in tr["bezel_outer_mm"]["polygon_mm"]], N)  # measured rounded octagon
    r_sil = rays(outline, N)
    outer = [(min(ro, rs - cs["silhouette_margin_mm"]) * math.cos(2 * math.pi * k / N), min(ro, rs - cs["silhouette_margin_mm"]) * math.sin(2 * math.pi * k / N))
             for k, (ro, rs) in enumerate(zip(r_se, r_sil))]
    mid = pol(ap["face_edge_r_mm"])
    inner = pol([r - ap["chamfer_mm"] for r in ap["face_edge_r_mm"]])
    if not cs.get("omit_core"):  # hidden under the opaque dial: dropped for the mobile triangle budget
        add("core", Geo().prism(inner, 0.0, d["z"] - 0.05), "steel_gap")
    g = ring(Geo(), outer, mid, 0.0, zb, zb)
    ring(g, mid, inner, 0.0, zb, cs["chamfer_z"])
    add("bezel", g, "steel_photo", bevel=cs["bezel_bevel"])

    # ---- crystal and dial: flat polygons on the window outline; the dial carries the native photo map ----
    cr = cfg["crystal"]
    add("crystal", Geo().prism(pol([r - ap["chamfer_mm"] - 0.05 for r in ap["face_edge_r_mm"]]), cr["z0"], cr["z1"]), "crystal")
    dme = Geo().prism(inner, d["z"] - 0.2, d["z"]).mesh(P + "dial", False)
    uv = dme.uv_layers.new(name="UVMap")  # planar, centred on the pivot (top and side faces: only the top is seen)
    for loop in dme.loops:
        x, y, _ = dme.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", dme, "dial")

    # ---- hands at the photographed pose: outlines from the spec (mm along the hand from the pivot, half width), the last point sits at the traced length ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        h = t[name]
        L, deg, z, off = h["length_mm"], h["angle_deg"], hs["z"][name], h.get("offset_mm", 0.0)  # off: the hand's centre line sits off the pivot by this much (clockwise side +)
        prof = [list(p) for p in hs["profile"][name]]
        prof[-1][0] = L
        half_outline = [(0, prof[0][0])] + [(w, y) for y, w in prof] if prof[-1][1] == 0 else [(0, prof[0][0])] + [(w, y) for y, w in prof] + [(0, L)]
        g_ = Geo()
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g_, [rot(sx * x + off, y, deg) for x, y in half_outline], z, lambda x, y, z=z, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg))
        add("hand_" + name, g_, hs.get("material", "gold"), bevel=0.02)
        if name in hs["lume"]:  # lume: +w side outline [s, w] in mm along the hand, mirrored about the axis; polygon extruded over the hand ridge
            half = [(w, y) for y, w in hs["lume"][name]]
            poly = half + [(-w, y) for w, y in reversed(half) if w > 0]
            add("lume_" + name, Geo().prism([rot(x + off, y, deg) for x, y in poly], z + th + hs["ridge"] * 0.4, z + th + hs["ridge"] + hs["lume_height"]), hs.get("lume_material", "lume"))
    hub_big, hub_small = tr["hub_radius_mm"]  # hour-hand base disc, white seconds hub
    add("hub", Geo().lathe([(0, d["z"]), (hub_big, d["z"]), (hub_big, hs["z"]["hour"] + th), (hub_big * 0.9, hs["z"]["hour"] + th + 0.05), (hub_small, hs["z"]["minute"] + th),
                            (hub_small * 0.92, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.1)], segs=hs.get("hub_segs", 96)), hs.get("material", "gold"), smooth=True)

    # ---- crown (3 o'clock): fluted cylinder = lathe about its axis (trace profile [radius, mm along the axis]); local z = along the axis, local y = up ----
    c = cfg["crown"]
    for cw in tr["crowns"]:
        ax, ay = math.sin(math.radians(cw["angle_deg"])), math.cos(math.radians(cw["angle_deg"]))
        m = Matrix(((-ay, 0, ax), (ax, 0, ay), (0, 1, 0))).to_4x4()
        m.translation = (cw["base_mm"][0], cw["base_mm"][1], c["z"])
        add(cw["name"], Geo().lathe([(r, z_) for r, z_ in cw["profile_mm"]], segs=c.get("segs", 96), m=m), "steel_photo", smooth=True)

    # ---- steel bracelet: link pieces between the measured joints (top and bottom separately); outline = trace.strap_y_left_right_mm (the silhouette) ----
    br = cfg["strap"]["bracelet"]
    gap, za, ins, bins = br["gap"], ds * br["z0"], br["inset"], br["backing_inset"]
    sp = {round(p[0], 2): p for p in tr["strap_y_left_right_mm"]}

    def se(y):  # strap outline at y (silhouette outside the lug zone, lug inner walls inside it)
        p = sp[round(round(max(y_lo, min(y_hi, y)) * 4) / 4, 2)]
        return p[1], p[2]
    links, back, pieces = {"top": Geo(), "bottom": Geo()}, Geo(), 0  # one links part per side: the photo's top and bottom bracelet differ in brightness (emission_top / emission_bottom)
    for sy, key in ((1, "top"), (-1, "bottom")):
        lst = br["pieces_mm"]["full"][key]
        for k, (a_, b_) in enumerate(lst):
            y0, y1 = a_ + (gap / 2 if k else 0), b_ - gap / 2
            n_ = max(1, math.ceil((y1 - y0) / 0.5))
            ys_ = [sy * (y0 + j * (y1 - y0) / n_) for j in range(n_ + 1)]  # the piece follows the photo's edges
            slab(links[key], [(se(y)[1] - ins, y) for y in ys_] + [(se(y)[0] + ins, y) for y in reversed(ys_)], za, lambda x, y: ds * max(br["z_side"], ramp(0, y) + br["lift"]))
            pieces += 1
        s0 = min(p[0] for p in lst)
        s1 = br.get("backing_to_mm", {}).get(key, max(p[1] for p in lst))
        ys_ = [sy * (s0 + j * (s1 - s0) / round((s1 - s0) / 0.5)) for j in range(round((s1 - s0) / 0.5) + 1)]
        slab(back, [(se(y)[1] - bins, y) for y in ys_] + [(se(y)[0] + bins, y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    mats["strap_photo_bottom"] = mats["strap_photo"].copy()
    mats["strap_photo_bottom"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = br.get("emission_bottom", sr.get("emission", cfg["steel"]["emission"]))
    mats["strap_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = br.get("emission_top", sr.get("emission", cfg["steel"]["emission"]))
    add("bracelet_links_top", links["top"], "strap_photo", bevel=br["bevel"])
    add("bracelet_links_bottom", links["bottom"], "strap_photo_bottom", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    out = {"diameter": round(sorted(p[2] - p[1] for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3)[len([1 for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3]) // 2], 3),
           "lug_to_lug": round(tt + tb, 3)}  # diameter = median silhouette width within 3 mm of the pivot row (left flat to the guard notch wall)
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "strap": "steel bracelet", "strap_pieces": pieces, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
