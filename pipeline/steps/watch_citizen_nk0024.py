"""watch_citizen_nk0024: build the Citizen NK0024-54X (Tsuyosa 60 automatic, 40 mm, green patterned dial, gold-tone bezel,
two-tone Jubilee-style bracelet) as a flat-backed front relief.

Params: spec (config/watches/citizen-nk0024-54x.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_tissot_t120410; origin = the dial centre (the trace measures the hands about their own pivot and they are placed here).
Parts from the photo: one brushed steel case from the traced silhouette with the lower end pieces at 12 and 6, a domed
polished gold bezel, a sloped gold rehaut, applied gold-framed lume bars (pairs at 12 and 6), a cyclops over the date at 3,
gold baton hands with lume and stub tails, a gold seconds needle, a fluted gold crown at 4, and a five-column bracelet
(brushed steel outer links, polished gold semi and centre links, the centre row half a link off). The dial (pattern, prints,
date, printed minute track) is the photo map from pipeline/citizen_nk0024_dial.py. Rebuild with --force after regenerating
the map (it is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def rrect(cx, cy, w, h, r, n=6):
    """Rounded rectangle outline (counterclockwise)."""
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + qx * (w / 2 - r), cy + qy * (h / 2 - r)
        pts += [(ox + r * math.cos(math.radians(a0 + 90 * k / n)), oy + r * math.sin(math.radians(a0 + 90 * k / n))) for k in range(n + 1)]
    return pts


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Citizen NK0024-54X front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    textured = cfg.get("brushed_textures", {})
    for key, tx in textured.items():  # brushed lines as a tangent-space normal map: a plain image link, so the GLB keeps it
        nodes, links = mats[key].node_tree.nodes, mats[key].node_tree.links
        b = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        im = bpy.data.images.load(str(ROOT / tx["normal"]), check_existing=True)
        im.colorspace_settings.name = "Non-Color"
        im.pack()
        tex, nm = nodes.new("ShaderNodeTexImage"), nodes.new("ShaderNodeNormalMap")
        tex.image, tex.location, nm.location = im, (-600, -300), (-250, -300)
        nm.inputs["Strength"].default_value = tx["strength"]
        links.new(tex.outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], b.inputs["Normal"])

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, bevel_mat=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile, lines along the bracelet (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if bevel:
            if bevel_mat:
                me.materials.append(mats[bevel_mat])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if bevel_mat:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    rg = tr["rings_mm"]
    bx, by = tr["bezel_offset_mm"]
    centred = Matrix.Translation((bx, by, 0))

    # ---- case: brushed top from the silhouette (mean of both edges, the left edge alone where the crown sits), lower end
    # pieces at 12 and 6 past the step, polished chamfer ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    cr_ = cfg["crown"]

    def half(y):
        y = round(y * 4) / 4  # the silhouette is sampled every 0.25 mm
        ys = [sil[k_] for k_ in (round(y, 2), round(-y, 2)) if k_ in sil]
        crown_band = lambda p: cr_["band_y"][0] < p[0] < cr_["band_y"][1]
        return sum(-p[1] if crown_band(p) else (p[2] - p[1]) / 2 for p in ys) / len(ys)

    cs = cfg["case"]
    tip = tr["lug_tip_mm"]["mean"]
    step_y = cs["step_y"]
    grid = lambda y0, y1: [y0 + k_ * 0.25 for k_ in range(int(round((y1 - y0) / 0.25)) + 1)]
    body = [(half(y), y) for y in grid(-step_y, step_y)]
    g = Geo()
    slab(g, body + [(-x, y) for x, y in body[::-1]], 0.0, lambda x, y: cs["top_z"])
    add("case", g, "steel_brushed", bevel=cs["bevel"], bevel_mat="steel_polished")
    g = Geo()
    for sy in (1, -1):
        side = [(half(y), sy * y) for y in grid(step_y, tip)]
        slab(g, side + [(-x, y) for x, y in side[::-1]], 0.0,
             lambda x, y: cs["end_z_at_step"] + (cs["end_z_at_tip"] - cs["end_z_at_step"]) * (abs(y) - step_y) / (tip - step_y))
    add("case_ends", g, "steel_brushed", bevel=cs["end_bevel"], bevel_mat="steel_polished")

    # ---- bezel (domed, polished gold), rehaut, crystal, cyclops ----
    add("bezel", Geo().lathe([tuple(p) for p in cfg["bezel"]["profile_rz"]], segs=256, m=centred), "gold_polished", smooth=True)
    rh = cfg["rehaut"]
    add("rehaut", Geo().lathe([(rg["dial_out"], d["z"]), (rh["r_top"], rh["z_top"]), (rh["r_top"], rh["z_top"] - 0.3), (rg["dial_out"], d["z"] - 0.3)], segs=192),
        "gold_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")
    cy_ = cfg["cyclops"]
    (cx0, cy0), (cw, chh) = tr["cyclops"]["centre_mm"], tr["cyclops"]["size_mm"]
    # one solid with a rounded top edge: every extra cap over the date is another alpha layer that greys it
    add("cyclops", Geo().prism(rrect(cx0, cy0, cw, chh, cy_["corner_r"]), cr["z1"], cy_["z_top"]), "crystal", bevel=cy_["chamfer"])

    # ---- dial, photo map on a planar UV (map centre = dial centre, half a pixel off) ----
    me = Geo().lathe([(0, d["z"]), (rg["dial_out"] + 0.05, d["z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    H, S = dm["half_size_mm"], tr["scale_px_per_mm"]
    ox, oy = dm["centre_offset_px"][0] / S, -dm["centre_offset_px"][1] / S
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + (x + ox) / (2 * H), 0.5 + (y + oy) / (2 * H))
    add("dial", me, "dial")

    # ---- applied indices: gold frame round a recessed lume bar, each at its traced centre and angle ----
    ix, ti = cfg["indices"], tr["indices"]
    fw, z0, z1 = ti["frame_mm"], d["z"], d["z"] + ix["height"]
    L = sorted(b["half_len_mm"] for b in ti["bars"])[len(ti["bars"]) // 2]  # one size for all: hands cover parts of some
    W = sorted(b["half_w_mm"] for b in ti["bars"])[len(ti["bars"]) // 2]
    frames, lume = Geo(), Geo()
    for b in ti["bars"]:
        m = Matrix.Translation((*b["centre_mm"], 0)) @ Matrix.Rotation(-math.radians(b["angle_deg"]), 4, "Z")
        frames.prism(rect(0, 0, 2 * (W + fw), 2 * (L + fw)), z0, z1, m)
        lume.prism(rect(0, 0, 2 * W, 2 * L), z0, z1 + ix["lume_raise"], m)  # the frame is a solid plate: the lume sits just above it
    add("indices", frames, "gold_polished", bevel=0.03)
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time, gold, about the origin ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, poly, deg, z, mat="gold_polished", h=th):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=0.02 if mat == "gold_polished" else None)

    for key in ("hour", "minute"):
        h = t[key]
        (tl, tw), hw = h["tail"], h["half"]
        hand("hand_" + key, [(-tw, -tl), (tw, -tl), (tw, 0.0), (hw, 0.0), (hw, h["tip"]), (-hw, h["tip"]), (-hw, 0.0), (-tw, 0.0)], h["angle_deg"], hs["z"][key])
        l0, l1, lw = h["lume"]
        hand("hand_%s_lume" % key, [(-lw, l0), (lw, l0), (lw, l1), (-lw, l1)], h["angle_deg"], hs["z"][key] + th, "lume", 0.04)
    h, z = t["seconds"], hs["z"]["seconds"]
    (tl, tw), nw = h["tail"], h["half"]
    hand("hand_seconds", [(-tw, -tl), (tw, -tl), (nw, 0.0), (nw, h["tip"] - 0.3), (0, h["tip"]), (-nw, h["tip"] - 0.3), (-nw, 0.0)], h["angle_deg"], z)
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub_boss", Geo().lathe([(0, hs["z"]["minute"]), (hub_r, hs["z"]["minute"]), (hub_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=48),
        "gold_polished", bevel=0.02)
    add("hub_post", Geo().lathe([(0, d["z"]), (cap_r * 1.4, d["z"]), (cap_r * 1.4, z), (0, z)], segs=48), "gold_polished")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "gold_polished")

    # ---- crown: collar and fluted gold cylinder on a radial axis at the traced angle (4 o'clock) ----
    tc = tr["crown"]
    a = math.radians(tc["angle_deg"])
    teeth, rad = tc["teeth"], tc["radius_mm"]
    star = [((rad if i % 2 == 0 else rad - cr_["flute_depth"]) * math.cos(math.pi * i / teeth),
             (rad if i % 2 == 0 else rad - cr_["flute_depth"]) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
    u_, dr_ = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u_, (0, 0, 1), dr_)).transposed().to_4x4()
    m.translation = (0, 0, cr_["z"])
    r0, r1 = tc["r_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 0.6), (cr_["collar_r"], r0 - 0.6), (cr_["collar_r"], r0 + 0.3), (0, r0 + 0.3)], segs=48, m=m), "gold_polished", bevel=0.1)
    add("crown", Geo().prism(star, r0 + 0.3, r1, m), "gold_polished", bevel=0.15)

    # ---- five-column bracelet: steel outer links, gold semi links, gold centre links half a link off ----
    br, el, tb = cfg["bracelet"], cfg["end_link"], tr["bracelet"]
    gh, ch, gap, pitch = tb["gold_half_mm"], tb["centre_half_mm"], br["gap"], tb["pitch_mm"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), el["half_width"])
    end_s, end_g = Geo(), Geo()
    for sy in (1, -1):
        M = Matrix.Translation((0, sy * (el["from_y"] + tip) / 2, 0))
        for sx in (1, -1):
            end_s.prism(rect(sx * (gh + gap + el["half_width"]) / 2, 0, el["half_width"] - gh - gap, tip - el["from_y"]), 0.0, el["top_z"], M)
        end_g.prism(rect(0, 0, 2 * gh, tip - el["from_y"]), 0.0, el["top_z"] + br["gold_raise"], M)
    add("end_links", end_s, "steel_brushed", bevel=el["bevel"], bevel_mat="steel_polished")
    add("end_links_gold", end_g, "gold_polished", bevel=el["bevel"])

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    outer, gold, back = Geo(), Geo(), Geo()
    za, zb, zg = ds * br["z0"], ds * br["z1"], ds * (br["z1"] + br["gold_raise"])
    rows = 0
    for sy in (1, -1):
        for kind in ("outer", "semi", "centre"):
            first = tb["first_joint_mm"][kind]
            joints = [first + k_ * pitch for k_ in range(-3, 12)]
            edges = [tip] + [j_ for j_ in joints if tip + 0.5 < j_ < br["end_y"] - 0.5] + [br["end_y"]]
            for y0, y1 in zip(edges[:-1], edges[1:]):
                y1g = y1 - gap if y1 < br["end_y"] else y1
                hw_ = hw_at((y0 + y1) / 2)
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (gh + gap), sx * hw_))
                        bent_box(outer, x0, x1, y0, y1g, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                elif kind == "semi":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * gh))
                        bent_box(gold, x0, x1, y0, y1g, za, zg, sy)
                else:
                    bent_box(gold, -ch, ch, y0, y1g, za, zg, sy)
    add("bracelet_links", outer, "steel_brushed", bevel=br["bevel"], bevel_mat="steel_polished")
    add("bracelet_gold_links", gold, "gold_polished", bevel=br["gold_bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(half(k_ * 0.25) for k_ in range(-4, 5)), 3), "case_to_case": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "indices": len(ti["bars"]),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
