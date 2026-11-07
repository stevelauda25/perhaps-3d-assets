"""watch_cartier_santoslarge: build a CARTIER Santos de Cartier Large (square steel case with a screwed bezel, angular crown, steel bracelet) as a flat-backed
front relief (like the Seiko / Tudor / Cartier Tank GLBs).

Model-specific copy of watch_cartier_tankmustxl (untouched), with the bezel / flank rings of the Tudor Black Bay steps instead of brancards and bars, and a
single-column bracelet. The photo has no alpha: silhouette mask from the JPEG, see pipeline/cartier_santoslarge_prep.py. Every Santos Large variant (WSSA0018
silver, WSSA0071 blue, WSSA0062 green) needs only its own spec / measure JSON. Parts, all from the trace (mm, origin = hand pivot):
  core       block under the bezel opening (flat back at z = 0), steel_gap material
  flank      ring from the photo silhouette (horns, crown guards; rows between the horn top and bottom) up to the bezel outline, sloping
  bezel      polished face ring from the traced outline to the opening, then a chamfer ring down to the dial outline; eight screw heads
  dial       plane over the dial outline with the 2x photo map (planar UV by the crop box in dial_photo.json), crystal = flat transparent plate above it
  hands      three blue sword hands from outline profiles in the spec (the photographed hands stay in the dial map), hub = blue ball; hands_photo material
  crown      lathe along the 3 o'clock axis from the traced [radius, x] profile (angular steel part + sapphire cabochon), steel_photo material
  bracelet   one brushed column in pieces at the measured joints (trace.bracelet), the first piece is the end link between the horns, dark backing for the gaps
Steel parts, hands and crown carry the reference photo projected straight from the front (steel_photo.jpg, planar UV from x, y) plus emission.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the maps (they are not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def radial(poly, n, c=(0.0, 0.0)):
    """Sample a closed polygon star-shaped about c at n equal angles (counter-clockwise from +x): rings with equal point counts for ring()."""
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
            t = ((x1 - c[0]) * ey - (y1 - c[1]) * ex) / den
            u = ((x1 - c[0]) * dy - (y1 - c[1]) * dx) / den
            if t > 0 and -1e-9 <= u <= 1 + 1e-9:
                best = max(best, t)
        out.append((c[0] + best * dx, c[1] + best * dy))
    return out


def ring(g, outer, inner, z0, zo, zi):
    """Annulus between two equal-length counter-clockwise point lists: top sloping from zo (outer edge) to zi (inner edge), walls down to z0, flat bottom."""
    n, base = len(outer), len(g.v)
    g.v += [(x, y, z0) for x, y in outer] + [(x, y, zo) for x, y in outer] + [(x, y, z0) for x, y in inner] + [(x, y, zi) for x, y in inner]
    ob, ot, ib, it = base, base + n, base + 2 * n, base + 3 * n
    for k in range(n):
        j = (k + 1) % n
        g.f += [(ot + k, ot + j, it + j, it + k),  # top, +z
                (ob + k, ob + j, ot + j, ot + k),  # outer wall, outward
                (it + k, it + j, ib + j, ib + k),  # inner wall, toward the hole
                (ib + k, ib + j, ob + j, ob + k)]  # bottom, -z
        g.smooth += [False] * 4
    return g


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"].split(" (")[0])
    scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}

    def photo(name, path_key, roughness, specular, emission):
        m = photo_material(name, ROOT / cfg[path_key], roughness)
        nt = m.node_tree
        bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        bs.inputs["Specular IOR Level"].default_value = specular
        nt.links.new(next(n for n in nt.nodes if n.type == "TEX_IMAGE").outputs["Color"], bs.inputs["Emission Color"])  # the photo's own shading, not re-lit away
        bs.inputs["Emission Strength"].default_value = emission
        return m, bs.name

    mats["dial"], _ = photo("dial_photo", "dial_map", cfg["dial"]["roughness"], cfg["dial"]["specular"], cfg["dial"]["emission"])
    mats["steel_photo"], bsdf = photo("steel_photo", "steel_map", cfg["steel"]["roughness"], cfg["steel"]["specular"], cfg["steel"]["emission"])
    mats["hands_photo"] = mats["steel_photo"].copy()  # same projected photo; own emission so the photographed blue can be matched
    mats["hands_photo"].node_tree.nodes[bsdf].inputs["Emission Strength"].default_value = cfg["hands"].get("emission", cfg["steel"]["emission"])
    S_px, (px0, py0) = tr["scale_px_per_mm"], tr["origin_px"]

    def px_uv(me, meta_path):  # the photo projected straight from the front: a part shows the photographed pixels at its x, y (pixel centres at integers, 2x map)
        meta = json.loads((ROOT / meta_path).with_suffix(".json").read_text())
        cx0, cy0 = meta["crop_px"][:2]
        mw, mh = meta["size_px"]
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = ((px0 + x * S_px + 0.5 - cx0) * 2 / mw, 1 - (py0 - y * S_px + 0.5 - cy0) * 2 / mh)

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, smooth=None, bevel_segments=2):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in ("steel_photo", "hands_photo"):
            px_uv(me, cfg["steel_map"])
        elif mat == "dial":
            px_uv(me, cfg["dial_map"])
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, bevel_segments, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    cs, cw = cfg["case"], tr["case"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    y_lo, y_hi = min(sil), max(sil)

    def edges(y):  # left and right silhouette x at y (row nearest on the 0.25 mm grid)
        p = sil[round(round(max(y_lo, min(y_hi, y)) * 4) / 4, 2)]
        return p[1], p[2]

    top, bot = cw["top_mm"], cw["bottom_mm"]
    n_ = int(round((top - bot) / 0.25))
    ys = [bot + (top - bot) * k / n_ for k in range(n_ + 1)]
    N = cs["rays"]
    case_poly = [(edges(y)[1], y) for y in ys] + [(edges(y)[0], y) for y in reversed(ys)]  # horn bottom -> horn top on the right, back down on the left (counter-clockwise)
    r_sil, r_bez = radial(case_poly, N), radial(cw["bezel_outline_mm"], N)
    r_open, r_dial = radial(cw["opening_mm"]["outline"], N), radial(cw["dial_outline_mm"], N)
    dz = cfg["dial"]["z"]

    # ---- core under the opening, flank ring (horns, crown guards), bezel face ring and chamfer ----
    add("core", Geo().prism(r_open, 0.0, dz - 0.05), "steel_gap")
    add("flank", ring(Geo(), r_sil, r_bez, 0.0, cs["flank_outer_z"], cs["flank_z"]), "steel_photo", bevel=cs["flank_bevel"], bevel_segments=3)
    g = ring(Geo(), r_bez, r_open, 0.0, cs["bezel_z"], cs["bezel_z"])
    ring(g, r_open, r_dial, 0.0, cs["bezel_z"], dz)
    add("bezel", g, "steel_photo", bevel=cs["bezel_bevel"], bevel_segments=3)
    sr = cw["screw_radius_mm"]
    zb = cs["bezel_z"]
    for k, (sx, sy) in enumerate(cw["screws_mm"]):  # shallow domed heads; the slots come from the projected photo
        m_ = Matrix.Translation((sx, sy, 0))
        add("screw_%d" % k, Geo().lathe([(0, zb + cs["screw_z"]), (sr * 0.8, zb + cs["screw_z"]), (sr, zb + cs["screw_z"] * 0.3), (sr, zb - 0.05), (0, zb - 0.05)], segs=24, m=m_), "steel_photo", smooth=True)

    # ---- dial (photo map on the dial outline) and crystal ----
    d, cr = cfg["dial"], cfg["crystal"]
    add("dial", Geo().prism(r_dial, dz - 0.05, dz).mesh(P + "dial", False), "dial")
    add("crystal", Geo().prism(r_dial, cr["z0"], cr["z1"]), "crystal")

    # ---- hands at the photographed pose: outlines from the spec (mm along the hand from the pivot, half width), the last point sits at the traced length ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        h = t[name]
        L, deg, z = h["length_mm"], h["angle_deg"], hs["z"][name]
        prof = [list(p) for p in hs["profile"][name]]
        prof[-1][0] = L
        if name == "seconds":
            prof[0][0] = -h["tail_mm"]
        half_outline = [(0, prof[0][0])] + [(w, y) for y, w in prof]
        g_ = Geo()
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g_, [rot(sx * x, y, deg) for x, y in half_outline], z, lambda x, y, z=z, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg))
        add("hand_" + name, g_, hs.get("material", "hands_photo"), bevel=0.02)
    hub_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, dz), (hub_r, dz), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.7, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.2)], segs=48),
        hs.get("material", "hands_photo"), smooth=True)

    # ---- crown on the 3 o'clock axis: lathe about x (local z -> world x, local x -> world -z), profile [radius, x] from the trace ----
    c, cwr = cfg["crown"], tr["crown"]
    m = Matrix(((0, 0, 1), (0, 1, 0), (-1, 0, 0))).to_4x4()
    m.translation = (0, cwr["centre_y_mm"], c["z"])
    add("crown", Geo().lathe([tuple(p) for p in cwr["profile_mm"]], segs=c["segs"], m=m), "steel_photo", smooth=True)

    # ---- bracelet: one column of flat pieces at measured y ranges, top and bottom separately; the end link between the horns has its own edges ----
    br, tb = cfg["bracelet"], tr["bracelet"]
    gap, za, ins, bins = br["gap"], ds * br["z0"], br["inset"], br["backing_inset"]
    links, back, pieces = Geo(), Geo(), 0
    for sy, key in ((1, "top"), (-1, "bottom")):
        lst = tb["pieces_mm"][key]
        for k, (a_, b_) in enumerate(lst):
            y0, y1 = a_ + (gap / 2 if k else 0), b_ - gap / 2
            n_ = max(1, math.ceil((y1 - y0) / 0.5))
            ys_ = [sy * (y0 + j * (y1 - y0) / n_) for j in range(n_ + 1)]  # the column follows the photo's tapering edges
            if k == 0:
                el, er = tr["end_link_x_mm"][key]
                xl, xr = (lambda y: el + ins), (lambda y: er - ins)
            else:
                xl, xr = (lambda y: edges(y)[0] + ins), (lambda y: edges(y)[1] - ins)
            slab(links, [(xr(y), y) for y in ys_] + [(xl(y), y) for y in reversed(ys_)], za, lambda x, y, z_=ds * br["z_pieces"][k]: z_)
            pieces += 1
        s0, s1 = lst[0][0] - 0.3, lst[-1][1]  # the backing runs 0.3 mm under the case: no see-through line at the first joint
        ys_ = [sy * (s0 + j * (s1 - s0) / round((s1 - s0) / 0.5)) for j in range(round((s1 - s0) / 0.5) + 1)]
        slab(back, [(edges(y)[1] - bins, y) for y in ys_] + [(edges(y)[0] + bins, y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    add("bracelet_links", links, "steel_photo", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    out = {"width": round(cw["right_mm"] - cw["left_mm"], 3), "horn_to_horn": round(top - bot, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "strap_pieces": pieces, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
