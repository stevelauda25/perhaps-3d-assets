"""watch_rolex_daytona40: build a ROLEX Cosmograph Daytona 40 (126500LN steel / ceramic / Oyster first; 126503, 126505, 126518LN, 126508 yellow / green, 126519LN, 126506, 126506A reuse this file read-only with their own spec / trace / maps)
as a flat-backed front relief (like the other Rolex / Tudor / Omega GLBs in models/watches/).

Variant-named copy of watch_rolex_gmtmaster40 (untouched; rotating coin-edge bezel + Cyclops lens + column-driven bracelet) and of the crown / pusher / sub-dial-disc code of watch_tudor_bbchrono (untouched), spec driven:
  - case: ONE slab from trace.case_outline_mm (the clipped contour of the photo silhouette between the lug tip rows: horns, crown guards, pusher barrels, crown and the slits between horn and bracelet all follow the photo
    to a pixel), sloping toward the bracelet; the steel parts show the photo projected from the front (planar UV from x, y), so every part that sits at the same x, y shows the same photographed pixels;
  - bezel (fixed, no coin edge): ceramic ring (flat top, ellipse outer edge `bezel_ellipse.ceramic_out`, the engraved tachymetre scale / numerals are texture), bright inner chamfer ring, steel outer edge ring sloping down to
    `bezel_ellipse.case_ring`; crystal and dial plane as the template (dial = native photo map, sub-dials, printing and the photographed hands included);
  - hands = every name in spec hands.z (hour, minute, chronograph seconds, three sub-dial hands) as flat polygons from trace.hands[name].outline_mm at their own heights, `hands_photo` projects the photographed pixels on them;
    hub disc and three small sub-dial hub screws (trace.subdials_mm) on top;
  - crown on the 3 o'clock axis and TWO screw-down chronograph pushers (spec `pushers` + trace.pushers: radial axes through origin_mm at +-angle, neck / fluted ring / cylindrical cap, same build as the crown) as fluted parts;
  - strap: any column layout in strap.bracelet.columns, each column kind with its own height z_<kind> and piece chain pieces_mm[kind][top|bottom]; vertical joint lines bounds_x_mm (one boundary less than columns):
    Oyster ("outer", "centre", "outer"), Jubilee / President (five columns) and a one-piece rubber strap such as the Oysterflex (columns ["strap"], pieces_mm.strap.top / bottom).
A variant (other metal, dial, Oyster or Oysterflex strap) only needs its own spec / measure / job JSON and maps. Spec per variant: config/watches/rolex-daytona40-<key>.json.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the maps (the maps are not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT


def strip(g, outer, inner, zo, zi):
    """Top face of an annulus between two equal-length counter-clockwise point lists, height zo at the outer and zi at the inner edge (no walls)."""
    n, base = len(outer), len(g.v)
    g.v += [(x, y, zo) for x, y in outer] + [(x, y, zi) for x, y in inner]
    for k in range(n):
        j = (k + 1) % n
        g.f.append((base + k, base + j, base + n + j, base + n + k))
        g.smooth.append(False)
    return g


def wall(g, pts, zt, zb):
    """Vertical outer wall under a counter-clockwise outline, from zt down to zb."""
    n, base = len(pts), len(g.v)
    g.v += [(x, y, zt) for x, y in pts] + [(x, y, zb) for x, y in pts]
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
    if "bezel_emission" in cfg["steel"]:  # the ceramic ring needs its own emission (black ceramic with a baked sheen)
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
        if mat in ("steel_photo", "hands_photo", "bezel_photo"):
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
    rc = cfg.get("ring_centre_mm", tr["ring_centre_mm"])  # the photo's dial / flange circle sits a px off the hub: bezel, crystal and dial are centred there

    def at_ring(g):
        g.v = [(x + rc[0], y + rc[1], z) for x, y, z in g.v]
        return g
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    y_lo, y_hi = min(sil), max(sil)

    def edges(y):  # left and right silhouette x at y (bracelet edges)
        p = sil[round(round(max(y_lo, min(y_hi, y)) * 4) / 4, 2)]
        return p[1], p[2]

    # ---- case and lugs: the photo outline between the lug tip rows (horns, crown guards, pusher barrels, crown), sloping toward the bracelet ----
    tt, tb = cs["tip_top"], cs["tip_bottom"]
    outline = [tuple(p) for p in tr["case_outline_mm"]]
    ramp = lambda x, y: cs["body_z"] - (cs["body_z"] - cs["tip_z"]) * min(1.0, max(0.0, (abs(y) - cs["ramp_from_y"]) / ((tt if y > 0 else tb) - cs["ramp_from_y"])))
    g = Geo()
    slab(g, outline, 0.0, ramp)
    add("case", g, "steel_photo", bevel=cs["bevel"])

    # ---- bezel: bright inner chamfer ring, flat ceramic ring out to an ellipse, steel outer edge ring sloping down to the case; all strips use the same N angles ----
    N = bz["segments"]
    ang = [2 * math.pi * k / N for k in range(N)]
    circ = lambda r: [(r * math.cos(a), r * math.sin(a)) for a in ang]

    def ell(name):  # absolute mm (relative to the origin), NOT shifted by the ring centre
        e = tr["bezel_ellipse_mm"][name]
        return [(e["centre_mm"][0] + e["rx_mm"] * math.cos(a), e["centre_mm"][1] + e["ry_mm"] * math.sin(a)) for a in ang]
    unshift = lambda pts: [(x - rc[0], y - rc[1]) for x, y in pts]  # at_ring adds the ring centre back
    gi, gb, ge = Geo(), Geo(), Geo()
    strip(gi, circ(rg["insert_in"]), circ(rg["bezel_in"]), bz["z_insert"], bz["z_inner"])  # bright chamfer toward the dial
    strip(gb, unshift(ell("ceramic_out")), circ(rg["insert_in"]), bz["z_insert"], bz["z_insert"])  # ceramic top (tachymetre scale, numerals are texture)
    strip(ge, unshift(ell("case_ring")), unshift(ell("ceramic_out")), bz["z_edge"], bz["z_insert"] - bz["round_mm"])  # polished edge sloping down to the case flank
    wall(ge, unshift(ell("case_ring")), bz["z_edge"], bz["z0"])
    wall(ge, unshift(ell("ceramic_out")), bz["z_insert"], bz["z_insert"] - bz["round_mm"])  # small shoulder between the ceramic top and the polished edge
    bm = "bezel_photo" if "bezel_photo" in mats else "steel_photo"
    add("bezel_chamfer", at_ring(gi), "steel_photo")
    add("bezel", at_ring(gb), bm)
    add("bezel_edge", at_ring(ge), "steel_photo")

    # ---- crystal and dial ----
    cr = cfg["crystal"]
    ce = rg["crystal_edge"]
    dome = [(ce * f, cr["z1"] + cr["dome"] * (1 - f * f)) for f in (1.0, 0.85, 0.65, 0.4, 0.0)]  # shallow dome
    add("crystal", at_ring(Geo().lathe([(0, cr["z0"]), (ce, cr["z0"]), (ce, cr["z1"])] + dome[1:], segs=192)), "crystal")
    add("dial", photo_uv(at_ring(Geo().lathe([(0, d["z"]), (rg["dial_flat"], d["z"]), (rg["crystal_edge"], d["rehaut_z"])], segs=192)).mesh(P + "dial", True)), "dial")

    # ---- hands: the traced / picked photo outlines as flat polygons at their own heights ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in hs["z"]:  # hour, minute, seconds (chronograph), sub-dial hands
        z = hs["z"][name]
        add("hand_" + name, slab(Geo(), [tuple(p) for p in t[name]["outline_mm"]], z, lambda x, y, z=z: z + th), hs.get("material", "hands_photo"), bevel=0.02)
    hx, hy = tr.get("hub_offset_mm", [0.0, 0.0])
    hub_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.55, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.1)], segs=48,
                          m=Matrix.Translation((hx, hy, 0))), hs.get("material", "hands_photo"), smooth=True)
    for sd in tr.get("subdials_mm", []):  # small sub-dial hub screws on top of the sub-dial hands
        zs = max(hs["z"][n] for n in hs["z"] if n.startswith("sub")) + th
        add(sd["name"], Geo().lathe([(0, zs), (sd["r_mm"], zs), (sd["r_mm"] * 0.6, zs + 0.06), (0, zs + 0.08)], segs=24, m=Matrix.Translation((sd["x_mm"], sd["y_mm"], 0))),
            hs.get("material", "hands_photo"), smooth=True)

    # ---- crown and pushers: a fluted cylinder plus plain neck and cap along an axis (crown: the 3 o'clock axis, pushers: radial at +-angle) ----
    def crown_parts(name, ox, oy, phi, rad, neck_from, r_from, r_fl, r_to, c):
        star = [((rad if i % 2 == 0 else rad - c["flute_depth"]) * math.cos(math.pi * i / c["teeth"]),
                 (rad if i % 2 == 0 else rad - c["flute_depth"]) * math.sin(math.pi * i / c["teeth"])) for i in range(c["teeth"] * 2)]
        a_ = math.radians(phi)  # local z = along the axis, local y = up (world z), local x = across (world xy)
        m = Matrix(((math.sin(a_), -math.cos(a_), 0), (0, 0, 1), (math.cos(a_), math.sin(a_), 0))).transposed().to_4x4()
        m.translation = (ox, oy, c["z"])
        add(name, Geo().prism(star, r_from, r_fl, m), "steel_photo", bevel=c.get("bevel", 0.15))
        if "neck_radius_fraction" in c:  # narrower tube between the case and the fluted part
            add(name + "_neck", Geo().lathe([(0, neck_from), (rad * c["neck_radius_fraction"], neck_from), (rad * c["neck_radius_fraction"], r_from + 0.1), (0, r_from + 0.1)], segs=48, m=m),
                "steel_photo", smooth=True)
        cap = [(0, r_fl), (rad - 0.1, r_fl), (rad * c["cap_radius_fraction"], r_to - 0.3), (rad * c["cap_radius_fraction"] * 0.6, r_to), (0, r_to)]
        if c.get("cap_cylinder"):  # pushers: a plain cylinder narrower than the fluted ring, rounded only at the end face
            rcap = rad * c["cap_radius_fraction"]
            cap = [(0, r_fl - 0.1), (rcap, r_fl - 0.1), (rcap, r_to - 0.25), (rcap * 0.85, r_to), (0, r_to)]
        add(name + "_cap", Geo().lathe(cap, segs=48, m=m), "steel_photo", smooth=True)

    c, cw = cfg["crown"], tr["crown"]
    crown_parts("crown", 0.0, cw["centre_y_mm"], 0.0, cw["radius_mm"], c["neck_from_mm"], cw["x_mm"][0], cw["fluted_to_mm"], cw["x_mm"][1], c)
    pu, pw = cfg.get("pushers"), tr.get("pushers")
    for k, phi in enumerate(pw["angles_deg"] if pw else []):
        pc = dict(pu, neck_radius_fraction=pw["neck_radius_fraction"], cap_radius_fraction=pw["cap_radius_fraction"])
        crown_parts("pusher%d" % (k + 1), pw["origin_mm"][0], pw["origin_mm"][1], phi, pw["radius_mm"], pw["neck_from_mm"], pw["r_from_mm"], pw["fluted_to_mm"], pw["r_to_mm"], pc)

    # ---- strap: columns left to right (strap.bracelet.columns), each a chain of flat pieces at measured y ranges, top and bottom separately ----
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
            for k, (a_, b_) in enumerate(br["pieces_mm"][ckind][key]):
                y0, y1 = a_ + (gap / 2 if k else 0), b_ - gap / 2
                n_ = max(1, math.ceil((y1 - y0) / 0.5))
                ys_ = [sy * (y0 + j * (y1 - y0) / n_) for j in range(n_ + 1)]  # columns follow the photo's tapering edges
                slab(links, [(xr(y), y) for y in ys_] + [(xl(y), y) for y in reversed(ys_)], za, lambda x, y, k_=ckind: ds * br["z_" + k_])
                pieces += 1
        s0, s1 = min(p[0] for p in br["pieces_mm"][first][key]), max(p[1] for p in br["pieces_mm"][first][key])
        ys_ = [sy * (s0 + j * (s1 - s0) / round((s1 - s0) / 0.5)) for j in range(round((s1 - s0) / 0.5) + 1)]
        slab(back, [(edges(y)[1] - bins, y) for y in ys_] + [(edges(y)[0] + bins, y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    add("bracelet_links", links, "steel_photo", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    near = [p for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 2.0]
    out = {"diameter": round(-2 * min(p[1] for p in near), 3), "lug_to_lug": round(tt + tb, 3)}  # the flank left of the bezel is the 40 mm anchor
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "strap": kind, "strap_pieces": pieces, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
