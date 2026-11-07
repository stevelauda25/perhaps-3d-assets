"""watch_cartier_tankmustxl: build a CARTIER Tank Must (rectangular steel case, brancards, steel bracelet) as a flat-backed front relief (like the Seiko / Tudor GLBs).

Model-specific copy of watch_tudor_bb54 (untouched), adapted for a rectangular case and a photo without alpha (silhouette mask from the JPEG, see
pipeline/cartier_tankmustxl_prep.py). Every Tank Must variant needs only its own spec/measure JSON; later Cartier watches (Santos, ...) copy this approach.
Parts, all from the trace (mm, origin = hand pivot):
  brancards  the two rounded vertical bars of the case: outer edge = silhouette row by row (top/bottom corners follow it), inner edge = trace case.brancard_inner_x_mm
  bars       brushed bars between the brancards above and below the dial opening; core = block under the dial (flat back at z = 0)
  dial       plane over case.dial_rect_mm with the 2x photo map (planar UV by the crop box in dial_photo.json), crystal = flat transparent plate above it
  hands      three blue sword hands from outline profiles in the spec (the photographed hands stay in the dial map), hub = blue ball; hands_photo material
  crown      lathe along the 3 o'clock axis (faceted steel part + sapphire cabochon), spec crown.profile_mm, steel_photo material
  bracelet   outer / centre / outer brushed columns, pieces at the measured joints (trace.bracelet), dark backing for the gaps
Steel parts, hands and crown carry the reference photo projected straight from the front (steel_photo.jpg, planar UV from x, y) plus emission.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the maps (they are not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


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

    il, ir = cw["brancard_inner_x_mm"]
    top, bot = cw["top_mm"], cw["bottom_mm"]
    n_ = int(round((top - bot) / 0.25))
    ys = [bot + (top - bot) * k / n_ for k in range(n_ + 1)]

    # ---- brancards: outer edge from the silhouette (rounded corners), inner edge straight ----
    for side, inner in (("left", il), ("right", ir)):
        k = 0 if side == "left" else 1
        outline = [(edges(y)[k], y) for y in ys] + [(inner, y) for y in reversed(ys)]
        g = Geo()
        slab(g, outline, 0.0, lambda x, y: cs["brancard_z"])
        add("brancard_" + side, g, "steel_photo", bevel=cs["brancard_bevel"], bevel_segments=3)

    # ---- bars above / below the dial opening, core block under the dial ----
    ov = cs["bar_overlap_mm"]
    for key in ("top", "bottom"):
        y_a, y_b = cw["bar_%s_y_mm" % key]
        g = Geo().prism(rect((il + ir) / 2, (y_a + y_b) / 2, ir - il + 2 * ov, abs(y_a - y_b)), 0.0, cs["bar_z"])
        add("bar_" + key, g, "steel_photo", bevel=cs["bar_bevel"])
    dx0, dy0, dx1, dy1 = cw["dial_rect_mm"]  # dial opening: x0 < x1, y0 above y1
    dial_poly = rect((dx0 + dx1) / 2, (dy0 + dy1) / 2, dx1 - dx0, dy0 - dy1)
    add("core", Geo().prism(rect((il + ir) / 2, (dy0 + dy1) / 2, ir - il + 2 * ov, dy0 - dy1), 0.0, cfg["dial"]["z"] - 0.05), "steel_gap")

    # ---- dial (photo map on the opening) and crystal ----
    d, cr = cfg["dial"], cfg["crystal"]
    add("dial", Geo().prism(dial_poly, d["z"] - 0.05, d["z"]).mesh(P + "dial", False), "dial")
    add("crystal", Geo().prism(dial_poly, cr["z0"], cr["z1"]), "crystal")

    # ---- hands at the photographed pose: outlines from the spec (mm along the hand from the pivot, half width), the last point sits at the traced length ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        h = t[name]
        L, deg, z = h["length_mm"], h["angle_deg"], hs["z"][name]
        prof = [list(p) for p in hs["profile"][name]]
        prof[-1][0] = L
        half_outline = [(0, prof[0][0])] + [(w, y) for y, w in prof]
        g_ = Geo()
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g_, [rot(sx * x, y, deg) for x, y in half_outline], z, lambda x, y, z=z, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg))
        add("hand_" + name, g_, hs.get("material", "hands_photo"), bevel=0.02)
    hub_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.7, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.2)], segs=48),
        hs.get("material", "hands_photo"), smooth=True)

    # ---- crown on the 3 o'clock axis: lathe about x (local z -> world x, local x -> world -z), profile [radius, x] ----
    c, cwr = cfg["crown"], tr["crown"]
    m = Matrix(((0, 0, 1), (0, 1, 0), (-1, 0, 0))).to_4x4()
    m.translation = (0, cwr["centre_y_mm"], c["z"])
    add("crown", Geo().lathe([tuple(p) for p in c["profile_mm"]], segs=c["segs"], m=m), "steel_photo", smooth=True)

    # ---- bracelet: outer / centre / outer columns of flat pieces at measured y ranges, top and bottom separately ----
    br, tb = cfg["bracelet"], tr["bracelet"]
    gap, za, ins, bins = br["gap"], ds * br["z0"], br["inset"], br["backing_inset"]

    def clamp_edges(y):  # bracelet outer edges: the silhouette, but never wider than the gap between the brancards
        l, r_ = edges(y)
        return max(l, il), min(r_, ir)

    def centre(y):  # left and right x of the centre column at y: linear in the trace's [|y|, left, right] lists, one per side
        pts = tb["centre_x_mm"]["top" if y > 0 else "bottom"]
        if abs(y) <= pts[0][0]:
            return pts[0][1], pts[0][2]
        for (y0, l0, r0), (y1, l1, r1) in zip(pts, pts[1:]):
            if abs(y) <= y1:
                f = max(0.0, (abs(y) - y0) / (y1 - y0))
                return l0 + (l1 - l0) * f, r0 + (r1 - r0) * f
        return pts[-1][1], pts[-1][2]

    cols = {"left": (lambda y: clamp_edges(y)[0] + ins, lambda y: centre(y)[0] - gap / 2, "outer"),
            "centre": (lambda y: centre(y)[0] + gap / 2, lambda y: centre(y)[1] - gap / 2, "centre"),
            "right": (lambda y: centre(y)[1] + gap / 2, lambda y: clamp_edges(y)[1] - ins, "outer")}
    links, back, pieces = Geo(), Geo(), 0
    for sy, key in ((1, "top"), (-1, "bottom")):
        for xl, xr, ckind in cols.values():
            lst = tb["pieces_mm"][ckind][key]
            for k, (a_, b_) in enumerate(lst):
                y0, y1 = a_ + (gap / 2 if k else 0), b_ - gap / 2
                n_ = max(1, math.ceil((y1 - y0) / 0.5))
                ys_ = [sy * (y0 + j * (y1 - y0) / n_) for j in range(n_ + 1)]  # columns follow the photo's tapering edges
                slab(links, [(xr(y), y) for y in ys_] + [(xl(y), y) for y in reversed(ys_)], za, lambda x, y, k_=ckind: ds * br["z_" + k_])
                pieces += 1
        s0 = min(p[0] for p in tb["pieces_mm"]["outer"][key]) - 0.3  # the backing runs 0.3 mm under the case bar: no see-through line at the first joint
        s1 = max(p[1] for p in tb["pieces_mm"]["outer"][key])
        ys_ = [sy * (s0 + j * (s1 - s0) / round((s1 - s0) / 0.5)) for j in range(round((s1 - s0) / 0.5) + 1)]
        slab(back, [(clamp_edges(y)[1] - bins, y) for y in ys_] + [(clamp_edges(y)[0] + bins, y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    add("bracelet_links", links, "steel_photo", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    out = {"width": round(cw["right_mm"] - cw["left_mm"], 3), "lug_to_lug": round(top - bot, 3)}
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
