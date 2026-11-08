"""watch_rolex_daydate40: build a ROLEX Day-Date 40 (228235 Everose gold / chocolate dial / President bracelet; the 228238 yellow row is skipped, no later variants queued) as a flat-backed
front relief (like the other Rolex / Tudor / Omega GLBs in models/watches/).

Model-specific copy of watch_rolex_datejust41 (the fluted-bezel template, untouched), spec driven:
  - the case and lugs are cut from the photo silhouette (the 40 mm flank shows as a smooth band outside the fluted bezel; no crown guards: the crown rows take the mirrored left flank, done in the prep);
  - the bezel is a polished flange, a chamfer and a FLUTED face of `bezel.flutes` flutes (76: 152 flat facets, boundaries at 12 / 3 / 6 / 9 o'clock): every boundary has its own inner / outer radius (long
    boundaries reach further in and out than the short ones, as in the photo's zig-zag outline) and its own height (crest = long, valley = short), the outer zig-zag edge drops to the case;
  - a Cyclops date lens at 3 o'clock built from the measured outline (`lens` section); the date numeral, the day-of-week arc window at 12 (MONDAY), the Roman numerals / baton indices and the print
    stay in the dial photo (texture);
  - the gold baton hands are DRAWN outlines from edge scans (trace.hands[name].outline_mm, mm from the pivot, x right / y up): flat polygons at their own heights (hands_photo projects the photographed
    pixels on them); the photographed hands also stay in the dial map;
  - a fluted crown with neck and rounded cap on the 3 o'clock axis (no guards);
  - the PRESIDENT bracelet: columns outer / centre / outer from the spec (`strap.bracelet.columns`, `bounds_x_mm`, `pieces_mm`, one `z_<kind>` and one `round_<kind>` per column kind). The outer links are
    brushed semicircular barrels (each piece rises like a sine arch by `round_outer` mm, so the joints are real grooves), the centre links are polished flat pieces separated by the measured dark gaps
    (`shave.centre` false: the piece ranges already exclude the gaps); the silhouette gives each outer link's own width.
Native-size maps (prep: pipeline/rolex_daydate40_prep.py): the maps carry a `scale` (map px per photo px, 1.0 unless the 2048 cap bites).
Spec: config/watches/rolex-daydate40-<key>.json.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the maps (the maps are not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT


def ribbon(g, outer, inner):
    """Top face between two equal-length counter-clockwise lists of (x, y, z) points (outer ring first); every quad is one flat facet."""
    n, base = len(outer), len(g.v)
    g.v += list(outer) + list(inner)
    for k in range(n):
        j = (k + 1) % n
        g.f.append((base + k, base + j, base + n + j, base + n + k))
        g.smooth.append(False)
    return g


def link(g, xl, xr, ys, za, zt):
    """Bracelet link as strips of quads along y (no n-gon caps, so smooth shading cannot crease the top diagonally): left / right edge functions xl(y), xr(y), bottom za, top zt (a number or a function of y: barrel)."""
    base = len(g.v)
    for y in ys:
        z = zt(y) if callable(zt) else zt
        g.v += [(xl(y), y, z), (xr(y), y, z), (xl(y), y, za), (xr(y), y, za)]  # per row: top left, top right, bottom left, bottom right
    q = []
    for j in range(len(ys) - 1):
        a, b = base + 4 * j, base + 4 * j + 4
        q += [(a, a + 1, b + 1, b), (a + 2, b + 2, b + 3, a + 3), (a, b, b + 2, a + 2), (a + 1, a + 3, b + 3, b + 1)]
    a, b = base, base + 4 * (len(ys) - 1)
    q += [(a, a + 2, a + 3, a + 1), (b, b + 1, b + 3, b + 2)]
    for f in q:
        g.f.append(f if ys[-1] > ys[0] else f[::-1])
        g.smooth.append(True)
    return g


def wall3(g, pts, zb):
    """Vertical outer wall under a counter-clockwise outline of (x, y, z) points down to zb."""
    n, base = len(pts), len(g.v)
    g.v += list(pts) + [(x, y, zb) for x, y, _ in pts]
    for k in range(n):
        j = (k + 1) % n
        g.f.append((base + n + k, base + n + j, base + j, base + k))
        g.smooth.append(False)
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
    dn.links.new(next(n for n in dn.nodes if n.type == "TEX_IMAGE").outputs["Color"], db.inputs["Emission Color"])  # the printed dial as photographed
    db.inputs["Emission Strength"].default_value = cfg["dial"]["emission"]
    steel_meta = json.loads((ROOT / cfg["steel_map"]).with_suffix(".json").read_text())
    mats["steel_photo"] = photo_material("steel_photo", ROOT / cfg["steel_map"], cfg["steel"]["roughness"])
    nt = mats["steel_photo"].node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Specular IOR Level"].default_value = cfg["steel"]["specular"]
    nt.links.new(next(n for n in nt.nodes if n.type == "TEX_IMAGE").outputs["Color"], bs.inputs["Emission Color"])  # the photo's own shading, not re-lit away
    bs.inputs["Emission Strength"].default_value = cfg["steel"]["emission"]
    mats["hands_photo"] = mats["steel_photo"].copy()  # same projected photo; own emission so the photographed hand brightness can be matched
    mats["hands_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["hands"].get("emission", cfg["steel"]["emission"])
    mats["lens_photo"] = mats["steel_photo"].copy()  # the Cyclops shows the photographed lens; its own emission (a dial region, not steel)
    mats["lens_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["lens"]["emission"]
    if "bezel_emission" in cfg["steel"]:  # the ceramic insert and the coin ring can need their own emission (black ceramic with a baked sheen)
        mats["bezel_photo"] = mats["steel_photo"].copy()
        mats["bezel_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["steel"]["bezel_emission"]
    S_px, (px0, py0) = tr["scale_px_per_mm"], tr["origin_px"]
    cx0, cy0 = steel_meta["crop_px"][:2]
    mw, mh = steel_meta["size_px"]
    k_map = steel_meta.get("scale", 1.0)  # map px per photo px

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
        if mat in ("steel_photo", "hands_photo", "bezel_photo", "lens_photo"):
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

    rg, cs, bz, d = tr["rings_mm"], cfg["case"], cfg["bezel"], cfg["dial"]
    rc = cfg.get("ring_centre_mm", tr["ring_centre_mm"])  # dial / rehaut / crystal circle (the camera sees it a few px lower than the hub...)
    bc = cfg.get("bezel_centre_mm", tr["bezel_centre_mm"])  # ... and the fluted bezel circle

    def at_ring(g):
        g.v = [(x + rc[0], y + rc[1], z) for x, y, z in g.v]
        return g
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    y_lo, y_hi = min(sil), max(sil)

    def edges(y):  # left and right silhouette x at y
        p = sil[round(round(max(y_lo, min(y_hi, y)) * 4) / 4, 2)]
        return p[1], p[2]

    # ---- case and lugs from the silhouette (own length top and bottom), sloping toward the bracelet; the crown guards are part of the outline ----
    tt, tb = cs["tip_top"], cs["tip_bottom"]
    ys = [-tb + k * 0.25 for k in range(int(round((tt + tb) / 0.25)) + 1)]
    outline = [(edges(y)[1], y) for y in ys] + [(edges(y)[0], y) for y in reversed(ys)]
    ramp = lambda x, y: cs["body_z"] - (cs["body_z"] - cs["tip_z"]) * min(1.0, max(0.0, (abs(y) - cs["ramp_from_y"]) / ((tt if y > 0 else tb) - cs["ramp_from_y"])))
    g = Geo()
    slab(g, outline, 0.0, ramp)
    add("case", g, "steel_photo", bevel=cs["bevel"])

    # ---- bezel: polished flange, grey chamfer, fluted face (flat facets between N = 2 x flutes boundaries, each with its own radii and heights), zig-zag outer wall ----
    N = 2 * bz["flutes"]
    th = [2 * math.pi * k / N for k in range(N)]  # counter-clockwise from 12 o'clock (parity is the same clockwise: N is even)
    pol = lambda r, t, c: (c[0] + r * math.cos(math.pi / 2 + t), c[1] + r * math.sin(math.pi / 2 + t))
    is_long = [k % 2 == bz["long_parity"] for k in range(N)]
    is_crest = [(lg if bz["crest_is_long"] else not lg) for lg in is_long]
    r_in = [rg["flute_in_long" if lg else "flute_in_short"] for lg in is_long]
    r_out = [rg["flute_out_long" if lg else "flute_out_short"] for lg in is_long]
    z_in = [bz["z_crest_in" if cr_ else "z_valley_in"] for cr_ in is_crest]
    z_out = [bz["z_crest_out" if cr_ else "z_valley_out"] for cr_ in is_crest]
    P3 = lambda r, t, c, z: pol(r, t, c) + (z,)
    ring_in = [P3(rg["crystal_edge"], t, rc, bz["z_flange_in"]) for t in th]  # flange inner edge at the crystal / rehaut circle
    ring_fl = [P3(rg["flange_out"], t, bc, bz["z_flange_out"]) for t in th]  # flange outer edge = start of the chamfer
    zig_in = [P3(r_in[k], th[k], bc, z_in[k]) for k in range(N)]
    zig_out = [P3(r_out[k], th[k], bc, z_out[k]) for k in range(N)]
    gb = Geo()
    ribbon(gb, ring_fl, ring_in)  # polished flange
    ribbon(gb, zig_in, ring_fl)  # chamfer up to the flutes' inner zig-zag
    ribbon(gb, zig_out, zig_in)  # the flutes: one flat facet between neighbouring boundaries
    wall3(gb, zig_out, bz["z0"])  # outer zig-zag wall down to the case
    add("bezel", gb, "bezel_photo" if "bezel_photo" in mats else "steel_photo")

    # ---- crystal and dial ----
    cr = cfg["crystal"]
    ce = rg["crystal_edge"]
    dome = [(ce * f, cr["z1"] + cr["dome"] * (1 - f * f)) for f in (1.0, 0.85, 0.65, 0.4, 0.0)]  # shallow dome
    add("crystal", at_ring(Geo().lathe([(0, cr["z0"]), (ce, cr["z0"]), (ce, cr["z1"])] + dome[1:], segs=192)), "crystal")
    add("dial", photo_uv(at_ring(Geo().lathe([(0, d["z"]), (rg["dial_flat"], d["z"]), (rg["crystal_edge"], d["rehaut_z"])], segs=192)).mesh(P + "dial", True)), "dial")

    # ---- Cyclops date lens: the measured outline, chamfered rim and a flat top, over the dial's window ----
    ln = cfg["lens"]
    pts = [tuple(p) for p in tr["lens_mm"]]
    if sum(a_[0] * b_[1] - b_[0] * a_[1] for a_, b_ in zip(pts, pts[1:] + pts[:1])) < 0:
        pts = pts[::-1]  # counter-clockwise
    lc = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    inset = lambda p, dd: (lc[0] + (p[0] - lc[0]) * (1 - dd / math.hypot(p[0] - lc[0], p[1] - lc[1])), lc[1] + (p[1] - lc[1]) * (1 - dd / math.hypot(p[0] - lc[0], p[1] - lc[1])))
    gl = Geo()
    levels = [[inset(p, dd) + (zz,) for p in pts] for dd, zz in ln["levels"]]
    wall3(gl, levels[0], ln["z_base"])
    for outer_, inner_ in zip(levels, levels[1:]):
        ribbon(gl, outer_, inner_)
    top = len(gl.v)
    gl.v += levels[-1]
    gl.f.append(tuple(range(top, top + len(pts))))
    gl.smooth.append(False)
    add("cyclops", gl, "lens_photo")

    # ---- hands: the traced photo outlines as flat polygons at their own heights ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        z = hs["z"][name]
        add("hand_" + name, slab(Geo(), [tuple(p) for p in t[name]["outline_mm"]], z, lambda x, y, z=z: z + th), hs.get("material", "hands_photo"), bevel=0.02)
    hub_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.55, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.1)], segs=48),
        hs.get("material", "hands_photo"), smooth=True)

    # ---- crown on the 3 o'clock axis: neck, fluted cylinder, rounded cap (the coronet is texture) ----
    c, cw = cfg["crown"], tr["crown"]
    rad, r_from, r_to, r_fl = cw["radius_mm"], cw["x_mm"][0], cw["x_mm"][1], cw["fluted_to_mm"]
    star_c = [((rad if i % 2 == 0 else rad - c["flute_depth"]) * math.cos(math.pi * i / c["teeth"]),
               (rad if i % 2 == 0 else rad - c["flute_depth"]) * math.sin(math.pi * i / c["teeth"])) for i in range(c["teeth"] * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()
    m.translation = (0, cw["centre_y_mm"], c["z"])
    add("crown", Geo().prism(star_c, r_from, r_fl, m), "steel_photo", bevel=c.get("bevel", 0.15))
    add("crown_neck", Geo().lathe([(0, rg["case_flank"] - 1.0), (rad * c["neck_radius_fraction"], rg["case_flank"] - 1.0), (rad * c["neck_radius_fraction"], r_from + 0.1), (0, r_from + 0.1)], segs=48, m=m),
        "steel_photo", smooth=True)
    cap = [(0, r_fl), (rad - 0.1, r_fl), (rad * c["cap_radius_fraction"], r_to - 0.3), (rad * c["cap_radius_fraction"] * 0.6, r_to), (0, r_to)]
    add("crown_cap", Geo().lathe(cap, segs=48, m=m), "steel_photo", smooth=True)

    # ---- bracelet: columns left to right (strap.bracelet.columns), each a chain of flat pieces at measured y ranges, top and bottom separately ----
    kind = cfg["strap"]["kind"]
    assert kind == "bracelet", "strap.kind %r" % kind
    br = cfg["strap"][kind]
    gap, za, ins, bins = br["gap"], ds * br["z0"], br["inset"], br["backing_inset"]
    seq = br["columns"]

    def bounds(y):  # x of the vertical joint lines between the columns at y: linear in the spec's [|y|, x1, x2, ...] lists, one per side
        pts = br["bounds_x_mm"]["top" if y > 0 else "bottom"]
        for p0, p1 in zip(pts, pts[1:]):
            if abs(y) <= p1[0]:
                f = max(0.0, (abs(y) - p0[0]) / (p1[0] - p0[0]))
                return [a_ + (b_ - a_) * f for a_, b_ in zip(p0[1:], p1[1:])]
        return pts[-1][1:]

    cols = [((lambda y: edges(y)[0] + ins) if i == 0 else (lambda y, i=i: bounds(y)[i - 1] + gap / 2),
             (lambda y: edges(y)[1] - ins) if i == len(seq) - 1 else (lambda y, i=i: bounds(y)[i] - gap / 2), ck) for i, ck in enumerate(seq)]
    first = seq[0]
    links, back, pieces = Geo(), Geo(), 0
    for sy, key in ((1, "top"), (-1, "bottom")):
        for xl, xr, ckind in cols:
            shave = br.get("shave", {}).get(ckind, True)
            for k, (a_, b_) in enumerate(br["pieces_mm"][ckind][key]):
                y0, y1 = (a_ + (gap / 2 if k else 0), b_ - gap / 2) if shave else (a_, b_)
                n_ = max(1, math.ceil((y1 - y0) / (0.25 if br.get("round_" + ckind, 0) == 0 else 0.15)))
                ys_ = [sy * (y0 + j * (y1 - y0) / n_) for j in range(n_ + 1)]  # columns follow the photo's tapering edges
                rise = br.get("round_" + ckind, 0.0)
                zt = ds * br["z_" + ckind]
                if rise:  # semicircular barrel: sine arch along the link, z_<kind> at the crest, joints lower by `round_<kind>`
                    zt = lambda y, y0=y0, y1=y1, zc=ds * br["z_" + ckind], r_=ds * rise: zc - r_ * (1 - math.sin(math.pi * (abs(y) - y0) / (y1 - y0)) ** 0.5)
                link(links, xl, xr, ys_, za, zt)
                pieces += 1
        s0, s1 = min(p[0] for p in br["pieces_mm"][first][key]), max(p[1] for p in br["pieces_mm"][first][key])
        ys_ = [sy * (s0 + j * (s1 - s0) / round((s1 - s0) / 0.5)) for j in range(round((s1 - s0) / 0.5) + 1)]
        slab(back, [(edges(y)[1] - bins, y) for y in ys_] + [(edges(y)[0] + bins, y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    add("bracelet_links", links, "steel_photo", bevel=br["bevel"])
    add("bracelet_backing", back, br.get("backing_material", "steel_gap"))  # steel_photo: the gaps between the centre links show the photo's own dark red-brown

    out = {"diameter": round(2 * rg["case_flank"], 3), "lug_to_lug": round(tt + tb, 3)}  # the case flank is the 40 mm anchor
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "strap": kind, "strap_pieces": pieces, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
