"""watch_omega_snoopy: the OMEGA Speedmaster Silver Snoopy Award 50th Anniversary Co-Axial Master Chronometer Chronograph 42 mm (310.32.42.50.02.001, white / silver dial, blue bezel,
blue NYLON strap) build. Own copy of pipeline/steps/watch_omega_moonwatch.py (the Moonwatch template, untouched) with the three things a fabric strap needs (BASELINE.md of the Moonwatch,
"Template for the next Moonwatch variants"):
  - material `strap_photo`: the same projected photo with its own emission / roughness (0.8) / specular 0 (`strap.nylon.emission|roughness|specular`), a non-metallic fabric;
  - strap kind "nylon" (a one-piece strap = ONE column `columns` ["strap"], pieces `pieces_mm.strap.top|bottom` = [y0, y1(, x_left, x_right)], `edge_from` = the strap-wide silhouette row at
    the lug tops, `lift` over the case ramp); the weave, stripes and stitching stay flat photo texture; links and backing use `strap_photo` (`backing_material`);
  - `case.notch` {"top"|"bottom": [x_left, x_right], "ring_r_mm"} (optional): the gap between the strap end and the steel case ring (background in the photo, between the lug inner edges x_left .. x_right) is cut out of the case slab, its floor is the case ring circle of radius ring_r_mm about the ring centre; `strap.nylon.sample_mm`;
  - `pushers.cap_round_mm` (optional): the end face of the push buttons is a quarter arc of that radius instead of the 0.25 mm chamfer;
  - `hub_centre_mm` (optional, spec): the photographed hub dome sits a few px off the hand pivot (tilt parallax), the 3D hub is centred there; hands, rings, pushers and crown as in the template.
The chrono seconds hand of this model is free polygons (`hands.polygons`: tail + shaft, diamond, needle, `lume_mm` for the white diamond): its needle is bent 1.3 deg against the shaft in the render.
Everything model specific is in the spec / trace.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the dial map (the map is not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    meta = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"].split(" (")[0])
    scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for k, v in cfg["materials"].items():  # optional per-material specular (the dark backing must stay black)
        if "specular" in v:
            next(n for n in mats[k].node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Specular IOR Level"].default_value = v["specular"]
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
    mats["strap_photo"] = mats["steel_photo"].copy()  # nylon: same projected photo, own emission and roughness, non-metallic, no specular
    sb = mats["strap_photo"].node_tree.nodes[bs.name]
    sn = cfg["strap"].get("nylon", {})
    sb.inputs["Emission Strength"].default_value = sn.get("emission", cfg["steel"]["emission"])
    sb.inputs["Roughness"].default_value = sn.get("roughness", cfg["steel"]["roughness"])
    sb.inputs["Specular IOR Level"].default_value = sn.get("specular", 0.0)
    mats["hands_photo"] = mats["steel_photo"].copy()  # same projected photo; own emission (hands.emission) so the photographed gold/lume brightness can be matched
    mats["hands_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["hands"].get("emission", cfg["steel"]["emission"])
    S_px, (px0, py0) = tr["scale_px_per_mm"], tr["origin_px"]
    cx0, cy0 = steel_meta["crop_px"][:2]
    mw, mh = steel_meta["size_px"]

    def steel_uv(me):  # the photo projected straight from the front: every steel part shows the photographed pixels at its x, y
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = ((px0 + x * S_px - cx0) * 2 / mw, 1 - (py0 - y * S_px - cy0) * 2 / mh)

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
        if mat in ("steel_photo", "hands_photo", "strap_photo"):
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
    rc = cfg.get("ring_centre_mm", [0.0, 0.0])  # the photo's dial / bezel circle can sit a few px off the hub hole: bezel, crystal and dial lathes are centred there

    def at_ring(g):
        g.v = [(x + rc[0], y + rc[1], z) for x, y, z in g.v]
        return g
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    y_lo, y_hi = min(sil), max(sil)

    def edges(y):  # left and right silhouette x at y (the photo is not exactly centred on the pivot)
        p = sil[round(round(max(y_lo, min(y_hi, y)) * 4) / 4, 2)]
        return p[1], p[2]

    # ---- integrated case and lugs from the silhouette (own length top and bottom), top sloping into the bracelet ----
    tt, tb = cs["tip_top"], cs["tip_bottom"]
    ys = [-tb + k * 0.25 for k in range(int(round((tt + tb) / 0.25)) + 1)]
    outline = [(edges(y)[1], y) for y in ys]
    nt = cs.get("notch", {}).get("top")  # [x_left, x_right]: the gap between the strap end and the bezel is background in the photo (alpha 0), not case: cut it out of the slab
    arc = lambda x, s: rc[1] + s * math.sqrt(max(0.0, cs["notch"]["ring_r_mm"] ** 2 - (x - rc[0]) ** 2))  # notch floor = the steel case ring circle (notch.ring_r_mm about the ring centre)
    if nt:
        xs_ = [nt[1] + (nt[0] - nt[1]) * k / 12 for k in range(13)]  # right to left (the outline runs counter-clockwise: right side up, top edge to the left)
        outline += [(nt[1], tt)] + [(x, arc(x, 1)) for x in xs_] + [(nt[0], tt)]
    outline += [(edges(y)[0], y) for y in reversed(ys)]
    nb = cs.get("notch", {}).get("bottom")  # same at 6 o'clock
    if nb:
        xs_ = [nb[0] + (nb[1] - nb[0]) * k / 12 for k in range(13)]
        outline += [(nb[0], -tb)] + [(x, arc(x, -1)) for x in xs_] + [(nb[1], -tb)]
    ramp = lambda x, y: cs["body_z"] - (cs["body_z"] - cs["tip_z"]) * min(1.0, max(0.0, (abs(y) - cs["ramp_from_y"]) / ((tt if y > 0 else tb) - cs["ramp_from_y"])))
    g = Geo()
    slab(g, outline, 0.0, ramp)
    add("case", g, "steel_photo", bevel=cs["bevel"])

    # ---- bezel: one black ring (flat top, inner chamfer, rounded outer edge); a steel coin ring only when insert_out < bezel_out ----
    ri, ro, rins = rg["bezel_in"], rg["bezel_out"], rg["insert_out"]
    prof_b = [(ri, bz["z_inner"]), (ri + bz["chamfer_mm"], bz["z_insert"])]
    if rins < ro - 1e-6:
        prof_b += [(rins, bz["z_insert"]), (rins, bz["z_coin"])]
    top_b = bz["z_coin"] if rins < ro - 1e-6 else bz["z_insert"]
    prof_b += [(ro - bz["round_mm"], top_b), (ro, top_b - bz["round_mm"]), (ro, bz["z0"]), (ri, bz["z0"])]
    add("bezel_ring", at_ring(Geo().lathe(prof_b, segs=192)), "steel_photo")

    # ---- crystal and dial ----
    cr = cfg["crystal"]
    ce = rg["crystal_edge"]
    dome = [(ce * f, cr["z1"] + cr["dome"] * (1 - f * f)) for f in (1.0, 0.85, 0.65, 0.4, 0.0)]  # shallow dome
    add("crystal", at_ring(Geo().lathe([(0, cr["z0"]), (ce, cr["z0"]), (ce, cr["z1"])] + dome[1:], segs=192)), "crystal")
    add("dial", photo_uv(at_ring(Geo().lathe([(0, d["z"]), (rg["dial_flat"], d["z"]), (rg["crystal_edge"], d["rehaut_z"])], segs=192)).mesh(P + "dial", True)), "dial")

    # ---- hands at the photographed pose: outlines from the spec (mm along the hand from the pivot, half width), the last point sits at the traced length ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in hs["profile"]:  # minute, seconds (symmetric profile hands)
        h = t[name]
        L, deg, z = h["length_mm"], h["angle_deg"], hs["z"][name]
        prof = [list(p) for p in hs["profile"][name]]
        prof[-1][0] = L
        half_outline = [(0, prof[0][0])] + [(w, y) for y, w in prof] if prof[-1][1] == 0 else [(0, prof[0][0])] + [(w, y) for y, w in prof] + [(0, L)]
        g_ = Geo()
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g_, [rot(sx * x, y, deg) for x, y in half_outline], z, lambda x, y, z=z, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg))
        add("hand_" + name, g_, hs.get("material", "gold"), bevel=0.02)
        if name in hs.get("lume", {}):  # lume: +w side outline [s, w] in mm along the hand, mirrored about the axis; polygon extruded over the hand ridge
            half = [(w, y) for y, w in hs["lume"][name]]
            poly = half + [(-w, y) for w, y in reversed(half) if w > 0]
            add("lume_" + name, Geo().prism([rot(x, y, deg) for x, y in poly], z + th + hs["ridge"] * 0.4, z + th + hs["ridge"] + hs["lume_height"]), hs.get("lume_material", "lume"))
    for name, pg in hs.get("polygons", {}).items():  # free-form hand parts: outline and lume polygon in mm, flat top (lume_only: no hand body)
        if pg["outline_mm"]:
            add("hand_" + name, Geo().prism([tuple(q) for q in pg["outline_mm"]], pg["z"], pg["z"] + pg.get("thick", th)), hs.get("material", "gold"), bevel=0.02)
        if "lume_mm" in pg:
            add("lume_" + name, Geo().prism([tuple(q) for q in pg["lume_mm"]], pg["z"] + th * 0.5, pg["z"] + th + hs["lume_height"]), hs.get("lume_material", "lume"))
    for dsc in hs.get("discs", []):  # sub-dial hubs
        mdl = Matrix.Translation((dsc["x_mm"], dsc["y_mm"], 0))
        add(dsc["name"], Geo().lathe([(0, dsc["z0"]), (dsc["r_mm"], dsc["z0"]), (dsc["r_mm"], dsc["z1"]), (dsc["r_mm"] * 0.5, dsc["z1"] + 0.05), (0, dsc["z1"] + 0.05)], segs=40, m=mdl),
            hs.get("material", "gold"), smooth=True)
    hub_r = tr["hub_radius_mm"]
    hc = cfg.get("hub_centre_mm", [0.0, 0.0])  # the photographed hub dome (parallax), not the hand pivot
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.55, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.1)], segs=48,
                            m=Matrix.Translation((hc[0], hc[1], 0))), hs.get("material", "gold"), smooth=True)

    # ---- crown and pushers: a fluted cylinder plus plain neck and cap along an axis (crown: the 3 o'clock axis, pushers: radial at +-angle) ----
    def crown_parts(name, ox, oy, phi, rad, neck_from, r_from, r_fl, r_to, c):
        star = [((rad if i % 2 == 0 else rad - c["flute_depth"]) * math.cos(math.pi * i / c["teeth"]),
                 (rad if i % 2 == 0 else rad - c["flute_depth"]) * math.sin(math.pi * i / c["teeth"])) for i in range(c["teeth"] * 2)]
        a_ = math.radians(phi)  # local z = along the axis, local y = up (world z), local x = across (world xy)
        m = Matrix(((math.sin(a_), -math.cos(a_), 0), (0, 0, 1), (math.cos(a_), math.sin(a_), 0))).transposed().to_4x4()
        m.translation = (ox, oy, c["z"])
        add(name, Geo().prism(star, r_from, r_fl, m), "steel_photo", bevel=c.get("bevel", 0.15))
        if "base_chamfer_mm" in c:  # chamfered shoulder on the case side of the fluted part
            bc = c["base_chamfer_mm"]
            add(name + "_base", Geo().lathe([(0, r_from), (rad * 0.8, r_from), (rad - 0.02, r_from + bc), (0, r_from + bc)], segs=48, m=m), "steel_photo", smooth=True)
        if "neck_radius_fraction" in c:  # narrower tube between the case and the fluted part
            add(name + "_neck", Geo().lathe([(0, neck_from), (rad * c["neck_radius_fraction"], neck_from), (rad * c["neck_radius_fraction"], r_from + 0.1), (0, r_from + 0.1)], segs=48, m=m),
                "steel_photo", smooth=True)
        cap = [(0, r_fl), (rad * c.get("cap_start_fraction", 1.0 - 0.1 / rad), r_fl), (rad * c["cap_radius_fraction"], r_to - 0.3), (rad * c["cap_radius_fraction"] * 0.6, r_to), (0, r_to)]
        if c.get("cap_cylinder"):  # pushers: a plain cylinder narrower than the fluted ring, rounded only at the end face
            rc = rad * c["cap_radius_fraction"]
            cap = [(0, r_fl - 0.1), (rc, r_fl - 0.1), (rc, r_to - 0.25), (rc * 0.85, r_to), (0, r_to)]
            if "cap_round_mm" in c:  # rounder end face (quarter arc of this radius), as the photographed buttons
                R_ = c["cap_round_mm"]
                cap = [(0, r_fl - 0.1), (rc, r_fl - 0.1)] + [(rc - R_ + R_ * math.cos(math.radians(a_)), r_to - R_ + R_ * math.sin(math.radians(a_))) for a_ in (0, 30, 60, 90)] + [(0, r_to)]
        add(name + "_cap", Geo().lathe(cap, segs=48, m=m), "steel_photo", smooth=True)

    c, cw = cfg["crown"], tr["crown"]
    crown_parts("crown", 0.0, cw["centre_y_mm"], 0.0, cw["radius_mm"], rg["bezel_out"] - 0.5, cw["x_mm"][0], c["fluted_to_mm"], cw["x_mm"][1], c)
    pu = cfg.get("pushers")
    for k, it in enumerate(pu["items"] if pu else []):  # common keys of `pushers` plus the per-pusher keys of the item
        p_ = {**pu, **it}
        crown_parts("pusher%d" % (k + 1), p_["origin_mm"][0], p_["origin_mm"][1], p_["angle_deg"], p_["radius_mm"], p_["neck_from_mm"], p_["r_from_mm"], p_["fluted_to_mm"], p_["r_to_mm"], p_)

    # ---- strap: strap.kind "nylon" = one-piece fabric strap (columns ["strap"]; the template's "bracelet" five-column chain still works); every kind is a chain of flat pieces at measured y ranges ----
    kind = cfg["strap"]["kind"]
    assert kind in ("nylon", "bracelet"), "strap.kind %r" % kind
    fab = kind == "nylon"
    br = cfg["strap"][kind]
    gap, za, ins, bins = br["gap"], ds * br["z0"], br["inset"], br["backing_inset"]
    groove = br.get("groove", gap)  # x gap between the columns; y gap between the pieces of a column is `gap`
    seq, full = br["columns"], br.get("full", [])
    ef = br["edge_from"]

    def se(y):  # strap outline: lug-wide silhouette rows nearer than edge_from take the strap-wide row at edge_from
        return edges(math.copysign(max(abs(y), ef["top" if y > 0 else "bottom"]), y))

    def bounds(y):  # x of the vertical joint lines between the five columns at y: linear in the spec's [|y|, x1, x2, ...] lists, one per side
        pts = br["bounds_x_mm"]["top" if y > 0 else "bottom"]
        for p0, p1 in zip(pts, pts[1:]):
            if abs(y) <= p1[0]:
                f = max(0.0, (abs(y) - p0[0]) / (p1[0] - p0[0]))
                return [a_ + (b_ - a_) * f for a_, b_ in zip(p0[1:], p1[1:])]
        return pts[-1][1:]

    cols = [((lambda y: se(y)[0] + ins) if i == 0 else (lambda y, i=i: bounds(y)[i - 1] + groove / 2),
             (lambda y: se(y)[1] - ins) if i == len(seq) - 1 else (lambda y, i=i: bounds(y)[i] - groove / 2), ck, i) for i, ck in enumerate(seq)]
    cols += [((lambda y: se(y)[0] + ins), (lambda y: se(y)[1] - ins), ck, -1) for ck in full]
    links, back, pieces = Geo(), Geo(), 0
    allp = lambda key: [p for ck in set(seq) | set(full) for p in br["pieces_mm"][ck][key]]
    for sy, key in ((1, "top"), (-1, "bottom")):
        for xl, xr, ckind, ci in cols:
            for pc in br["pieces_mm"][ckind][key]:
                y0, y1 = pc[0] + gap / 2, pc[1] - gap / 2
                lim = (pc[2], pc[3]) if len(pc) > 2 else None  # rows between the lugs: the outermost columns end at these x
                n_ = max(1, math.ceil((y1 - y0) / br.get("sample_mm", 0.5)))  # sample_mm: row spacing of the strap pieces (0.25 = the silhouette grid, follows the arched strap ends)
                ys_ = [sy * (y0 + j * (y1 - y0) / n_) for j in range(n_ + 1)]  # columns follow the photo's tapering edges
                xr_ = (lambda y, xr=xr: min(xr(y), lim[1])) if lim and ci == len(seq) - 1 else xr
                xl_ = (lambda y, xl=xl: max(xl(y), lim[0])) if lim and ci == 0 else xl
                slab(links, [(xr_(y), y) for y in ys_] + [(xl_(y), y) for y in reversed(ys_)], za, lambda x, y, k_=ckind: ds * max(br["z_" + k_], ramp(0, y) + br["lift"]))
                pieces += 1
        s0, s1 = min(p[0] for p in allp(key)), max(p[1] for p in allp(key))
        ys_ = [sy * (s0 + j * (s1 - s0) / round((s1 - s0) / 0.5)) for j in range(round((s1 - s0) / 0.5) + 1)]
        slab(back, [(se(y)[1] - bins, y) for y in ys_] + [(se(y)[0] + bins, y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    add("bracelet_links", links, "strap_photo" if fab else "steel_photo", bevel=br["bevel"])
    add("bracelet_backing", back, br.get("backing_material", "steel_gap"))  # steel_photo / strap_photo: the joint gaps stay as photographed

    out = {"diameter": round(2 * max(abs(p[1] - rc[0]) for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3), 3),  # left silhouette about the ring centre (the right side carries the crown)
           "lug_to_lug": round(tt + tb, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "strap": kind, "strap_pieces": pieces, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
