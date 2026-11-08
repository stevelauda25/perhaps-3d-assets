"""watch_rolex_airking: the ROLEX Air-King 126900 (40 mm steel, black dial, domed polished bezel, Oyster bracelet) build and the Rolex Air-King TEMPLATE (round Oyster-case Rolex variants follow).

Own copy of pipeline/steps/watch_patek_nautilus41.py (untouched; same recipe, same helpers, spec driven) with these changes for the round Oyster case:
  - the bezel is a DOMED polished ring: outer edge (ellipse, trace.bezel_outer_mm, cut back to the silhouette) at bezel_z - bezel_outer_dz, a crest ring `bezel_crest_mm` inside the outer edge at bezel_z, down to the scanned (circle) window
    edge at bezel_z - bezel_inner_dz, then the chamfer ring to the dial window at chamfer_z; there is no flat brushed face and no polished-band step (the Oyster bezel is one polished surface, all texture);
  - the hands are the traced photo OUTLINES (trace.hands[name].outline_mm, x right / y up from the pivot, drawn about the pivot as photographed): flat polygons at their own height (no profile / ridge / lume parts: the photographed
    pixels, lume and Mercedes lines included, are projected on them by the hands_photo material);
  - the case is the alpha silhouette between the end-link tips (lugs, crown guards included); the crown is the fluted-barrel lathe from trace.crowns; the Oyster bracelet = brushed outer-link rows + centre-link pieces from the trace.
A later Air-King variant (another dial colour / bezel) needs only its own spec / measure / job JSON; copy this step only for a code change.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the maps (the maps are not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT


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


def superellipse_rays(cx, cy, ax, ay, n_exp, n):
    """Points of the superellipse |(x-cx)/ax|^e + |(y-cy)/ay|^e = 1 (origin inside) on the same n angles as rays(): bisection along each ray."""
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        dx, dy = math.cos(a), math.sin(a)
        lo, hi = 0.0, 3 * max(ax, ay)
        for _ in range(60):
            t = (lo + hi) / 2
            if abs((t * dx - cx) / ax) ** n_exp + abs((t * dy - cy) / ay) ** n_exp < 1:
                lo = t
            else:
                hi = t
        out.append((lo * dx, lo * dy))
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
        if mat in ("steel_photo", "hands_photo", "bracelet_top", "bracelet_bottom"):
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

    # ---- bezel: domed polished ring (outer edge = measured ellipse cut back to the silhouette, crest bezel_crest_mm inside it, window edge from the fitted circle), polished chamfer down to the window ----
    N, zb = cs["rays"], cs["bezel_z"]
    bo = tr["bezel_outer_mm"]
    se_pts = superellipse_rays(bo["centre"][0], bo["centre"][1], bo["half_axes"][0], bo["half_axes"][1], bo["exponent"], N)
    r_se = [math.hypot(*p) for p in se_pts]
    r_sil = rays(outline, N)
    outer = [(min(ro, rs - cs["silhouette_margin_mm"]) * math.cos(2 * math.pi * k / N), min(ro, rs - cs["silhouette_margin_mm"]) * math.sin(2 * math.pi * k / N))
             for k, (ro, rs) in enumerate(zip(r_se, r_sil))]
    mid = pol(ap["face_edge_r_mm"])
    inner = pol([r - ap["chamfer_mm"] for r in ap["face_edge_r_mm"]])
    crest = [(p[0] * (1 - cs["bezel_crest_mm"] / math.hypot(*p)), p[1] * (1 - cs["bezel_crest_mm"] / math.hypot(*p))) for p in outer]  # radial inset of the dome crest
    add("core", Geo().prism(inner, 0.0, d["z"] - 0.05), "steel_gap")
    g = ring(Geo(), outer, crest, 0.0, zb - cs["bezel_outer_dz"], zb)
    ring(g, crest, mid, 0.0, zb, zb - cs["bezel_inner_dz"])
    ring(g, mid, inner, 0.0, zb - cs["bezel_inner_dz"], cs["chamfer_z"])
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

    # ---- hands: the photographed outlines (mm from the pivot, x right, y up) as flat polygons at their own heights; hands_photo projects the photo (lume, Mercedes lines, green paint) on them ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        z = hs["z"][name]
        add("hand_" + name, slab(Geo(), [tuple(p) for p in t[name]["outline_mm"]], z, lambda x, y, z=z: z + th), hs.get("material", "hands_photo"), bevel=0.02)
    hub_big, hub_small = tr["hub_radius_mm"]  # hour-hand base disc, white seconds hub
    add("hub", Geo().lathe([(0, d["z"]), (hub_big, d["z"]), (hub_big, hs["z"]["hour"] + th), (hub_big * 0.9, hs["z"]["hour"] + th + 0.05), (hub_small, hs["z"]["minute"] + th),
                            (hub_small * 0.92, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.1)], segs=96), hs.get("material", "gold"), smooth=True)

    # ---- crown (3 o'clock): fluted cylinder = lathe about its axis (trace profile [radius, mm along the axis]); local z = along the axis, local y = up ----
    c = cfg["crown"]
    for cw in tr["crowns"]:
        ax, ay = math.sin(math.radians(cw["angle_deg"])), math.cos(math.radians(cw["angle_deg"]))
        m = Matrix(((-ay, 0, ax), (ax, 0, ay), (0, 1, 0))).to_4x4()
        m.translation = (cw["base_mm"][0], cw["base_mm"][1], c["z"])
        add(cw["name"], Geo().lathe([(r, z_) for r, z_ in cw["profile_mm"]], segs=96, m=m), "steel_photo", smooth=True)

    # ---- bracelet: brushed outer-link rows (edges = silhouette) and polished centre pieces (rounded rectangles), top and bottom separately, all from the trace ----
    br, tb_ = cfg["bracelet"], tr["bracelet"]
    gap, za, ins = br["gap"], ds * br["z0"], br["inset"]

    def se(y):  # bracelet outline at y (the silhouette)
        return edges(y)
    links, pieces_g, nrows = {"top": Geo(), "bottom": Geo()}, {"top": Geo(), "bottom": Geo()}, 0
    for sy, key in ((1, "top"), (-1, "bottom")):
        for a_, b_ in tb_["rows_mm"][key]:
            y0, y1 = a_ + gap / 2, b_ - gap / 2
            n_ = max(1, math.ceil((y1 - y0) / 0.25))
            ys_ = [sy * (y0 + j * (y1 - y0) / n_) for j in range(n_ + 1)]
            slab(links[key], [(se(y)[1] - ins, y) for y in ys_] + [(se(y)[0] + ins, y) for y in reversed(ys_)], za, lambda x, y: ds * max(br["z_side"], ramp(0, y) + br["lift"]))
            nrows += 1
        for p in tb_["pieces_mm"]:
            if p["side"] != key:
                continue
            (x0, x1), (n0, f0), r = p["x_mm"], p["y_mm"], p["r_mm"]
            poly = []
            for (cx_, cy_), a0 in (((x1 - r, f0 - r), 0), ((x0 + r, f0 - r), 90), ((x0 + r, n0 + r), 180), ((x1 - r, n0 + r), 270)):
                poly += [(cx_ + r * math.cos(math.radians(a0 + 90 * j / 4)), sy * (cy_ + r * math.sin(math.radians(a0 + 90 * j / 4)))) for j in range(5)]
            slab(pieces_g[key], poly, za, lambda x, y: ds * (max(br["z_side"], ramp(0, y) + br["lift"]) + br["piece_lift"]))
    back = Geo()  # dark backing under the rows: the joints between rows and around the centre pieces read dark, as in the photo (not the white kit background)
    for sy, key in ((1, "top"), (-1, "bottom")):
        s0, s1 = min(r[0] for r in tb_["rows_mm"][key]), max(r[1] for r in tb_["rows_mm"][key])
        n_ = round((s1 - s0) / 0.25)
        ys_ = [sy * (s0 + j * (s1 - s0) / n_) for j in range(n_ + 1)]
        slab(back, [(se(y)[1] - br["backing_inset"], y) for y in ys_] + [(se(y)[0] + br["backing_inset"], y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    add("bracelet_backing", back, "steel_photo")
    mats["bracelet_top"], mats["bracelet_bottom"] = mats["steel_photo"].copy(), mats["steel_photo"].copy()
    for k_ in ("top", "bottom"):
        mats["bracelet_" + k_].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = br.get("emission_" + k_, cfg["steel"]["emission"])
    for key in ("top", "bottom"):
        add("bracelet_links_" + key, links[key], "bracelet_" + key, bevel=br["bevel"])
        add("bracelet_pieces_" + key, pieces_g[key], "bracelet_" + key, bevel=br["piece_bevel"])

    out = {"diameter": round(sorted(p[2] - p[1] for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3)[len([1 for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3]) // 2], 3),
           "lug_to_lug": round(tt + tb, 3)}  # diameter = median silhouette width within 3 mm of the pivot row (left flat to the guard notch wall)
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "bracelet_rows": nrows, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}

