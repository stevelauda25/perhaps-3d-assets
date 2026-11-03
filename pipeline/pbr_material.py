"""Image-based PBR material builder for library presets (Blender side).

build(preset, overrides=None, pack=False) -> bpy.types.Material. Texture checksums are verified first.
Mapping: `box` = object-space box projection (any mesh, no UVs), `uv` = a named UV map in mm/unit.
Normal map (OpenGL) and/or height bump are chained; optional `micro` adds a noise bump on top.
"""
import copy

from . import material_library


def merged(preset, overrides):
    p = copy.deepcopy(preset)
    for key, value in (overrides or {}).items():
        p[key] = {**p[key], **value} if isinstance(p.get(key), dict) and isinstance(value, dict) else value
    return p


def build(preset, overrides=None, pack=False, name=None):
    import bpy
    p = merged(preset, overrides)
    paths = material_library.verify(p)
    mat = bpy.data.materials.new(name or p["id"])
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    def node(kind, label, xy):
        n = nodes.new(kind); n.name = n.label = label; n.location = xy
        return n

    def image(channel, xy, vector, color):
        im = bpy.data.images.load(paths[channel], check_existing=True)
        im.colorspace_settings.name = "sRGB" if color else "Non-Color"
        if pack:
            im.pack()
        n = node("ShaderNodeTexImage", "Source | " + channel, xy)
        n.image, n.interpolation, n.extension = im, "Cubic", "REPEAT"
        links.new(vector, n.inputs["Vector"])
        return n, im

    m = p["mapping"]
    k = 1 if m.get("object_unit_mm") else 1000  # object coordinates are metres (box scenes) unless the mesh is modelled in mm
    first = next((c for c in ("color", "roughness", "normal", "height") if p["maps"].get(c)), None)
    w, h = bpy.data.images.load(paths[first], check_existing=True).size if first else (1, 1)  # map-free presets are parametric
    # square texels: u spans tile_width_mm, v spans tile_width_mm * h / w
    sx, sy = 1.0 / m["tile_width_mm"], w / (h * m["tile_width_mm"])
    mapping = node("ShaderNodeMapping", "Physical scale (mm to tile)", (-900, 0))
    if m["mode"] == "uv":
        uv = node("ShaderNodeUVMap", "Metric UV", (-1150, 0)); uv.uv_map = m["uv_map"]
        links.new(uv.outputs["UV"], mapping.inputs["Vector"])
        mapping.inputs["Scale"].default_value = (m["uv_mm_per_unit"] * sx, m["uv_mm_per_unit"] * sy, 1)
    else:
        coord = node("ShaderNodeTexCoord", "Object space", (-1150, 0))
        links.new(coord.outputs["Object"], mapping.inputs["Vector"])
        mapping.inputs["Scale"].default_value = (k * sx, k * sx, k * sx)
    vec = mapping.outputs["Vector"]

    def tex(channel, xy, color=False):
        n, _ = image(channel, xy, vec, color)
        if m["mode"] == "box":
            n.projection, n.projection_blend = "BOX", 0.15
            fix = node("ShaderNodeMapping", "Texel aspect | " + channel, (xy[0] - 200, xy[1]))
            fix.inputs["Scale"].default_value = (1, h / w, 1)
            links.new(vec, fix.inputs["Vector"])
            links.new(fix.outputs["Vector"], n.inputs["Vector"])
        return n

    bsdf = node("ShaderNodeBsdfPrincipled", "Paperboard BSDF", (600, 0))
    out = node("ShaderNodeOutputMaterial", "Material Output", (900, 0))
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    c = p["color"]
    if p["maps"].get("color"):
        base = tex("color", (-500, 400), True)
    else:  # no colour map: plain pigment (tint_linear) so the stock adds relief/roughness only, no flecks
        base = node("ShaderNodeRGB", "Plain stock", (-500, 400)); base.outputs["Color"].default_value = (1, 1, 1, 1)
    if c.get("contrast"):  # optional: lift the source tonal variation (nap streaks) before hue/value scaling
        bc = node("ShaderNodeBrightContrast", "Tonal contrast", (-400, 400)); bc.inputs["Contrast"].default_value = c["contrast"]
        links.new(base.outputs["Color"], bc.inputs["Color"]); base = bc
    hsv = node("ShaderNodeHueSaturation", "Colour adjust", (-250, 400))
    hsv.inputs["Hue"].default_value, hsv.inputs["Saturation"].default_value, hsv.inputs["Value"].default_value = c["hue"], c["saturation"], c["value"]
    links.new(base.outputs["Color"], hsv.inputs["Color"])
    tint = node("ShaderNodeMix", "Pigment tint (linear)", (0, 400)); tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs["Factor"].default_value = 1
    tint.inputs["B"].default_value = (*c["tint_linear"], 1)
    links.new(hsv.outputs["Color"], tint.inputs["A"])
    colour = tint.outputs["Result"]
    if p.get("tone"):  # optional soft pigment depth: very low-frequency, low-amplitude tonal variation (multiplies the pigment)
        t = p["tone"]
        tn = node("ShaderNodeTexNoise", "Pigment depth", (-250, 700)); tn.noise_dimensions = "3D"
        tn.inputs["Scale"].default_value, tn.inputs["Detail"].default_value, tn.inputs["Roughness"].default_value = t["scale_per_mm"], 2.0, 0.5
        tm = node("ShaderNodeMapping", "Depth mm", (-450, 700)); tm.inputs["Scale"].default_value = (k, k, k)
        links.new(coord.outputs["Object"], tm.inputs["Vector"]); links.new(tm.outputs["Vector"], tn.inputs["Vector"])
        tr = node("ShaderNodeMapRange", "Depth range", (0, 700)); tr.clamp = True
        tr.inputs["From Min"].default_value, tr.inputs["From Max"].default_value = 0.35, 0.65
        tr.inputs["To Min"].default_value, tr.inputs["To Max"].default_value = 1 - t["amount"], 1 + t["amount"]
        links.new(tn.outputs["Fac"], tr.inputs["Value"])
        td = node("ShaderNodeMix", "Pigment x depth", (250, 500)); td.data_type, td.blend_type = "RGBA", "MULTIPLY"
        td.inputs["Factor"].default_value = 1
        links.new(tint.outputs["Result"], td.inputs["A"]); links.new(tr.outputs["Result"], td.inputs["B"])
        colour = td.outputs["Result"]
    links.new(colour, bsdf.inputs["Base Color"])
    r = p["roughness"]
    if p["maps"].get("roughness"):
        rough = tex("roughness", (-500, 100))
        rm = node("ShaderNodeMapRange", "Calibrated roughness", (-250, 100)); rm.clamp = True
        for k, v in zip(("From Min", "From Max", "To Min", "To Max"), (*r["source_range"], *r["range"])):
            rm.inputs[k].default_value = v
        links.new(rough.outputs["Color"], rm.inputs["Value"])
        links.new(rm.outputs["Result"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = r["value"]
    normal_socket = None
    if p["maps"].get("normal"):
        nm = node("ShaderNodeNormalMap", "Normal (OpenGL)", (-250, -200)); nm.inputs["Strength"].default_value = p["normal"]["strength"]
        links.new(tex("normal", (-500, -200)).outputs["Color"], nm.inputs["Color"])
        normal_socket = nm.outputs["Normal"]
    if p["maps"].get("height") and p.get("height"):
        bump = node("ShaderNodeBump", "Height bump", (0, -300))
        bump.inputs["Strength"].default_value = p["height"]["bump_strength"]
        bump.inputs["Distance"].default_value = p["height"]["bump_distance_mm"] / 1000
        links.new(tex("height", (-500, -500)).outputs["Color"], bump.inputs["Height"])
        if normal_socket:
            links.new(normal_socket, bump.inputs["Normal"])
        normal_socket = bump.outputs["Normal"]
    if p.get("micro"):
        mi = p["micro"]
        nz = node("ShaderNodeTexNoise", "Micro detail", (-250, -600))
        nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = mi["scale_per_mm"], 6.0
        mp = node("ShaderNodeMapping", "Micro mm", (-450, -650)); mp.inputs["Scale"].default_value = (k, k, k)
        links.new(coord.outputs["Object"], mp.inputs["Vector"]); links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        mb = node("ShaderNodeBump", "Micro bump", (250, -300))
        mb.inputs["Strength"].default_value, mb.inputs["Distance"].default_value = mi["strength"], mi["distance_mm"] / 1000
        links.new(nz.outputs["Fac"], mb.inputs["Height"])
        if normal_socket:
            links.new(normal_socket, mb.inputs["Normal"])
        normal_socket = mb.outputs["Normal"]
    if p.get("nap"):
        # Directional fibre layer (suede/velvet): noise stretched along object Z reads as short brushed fibres.
        # Drives both a fine bump and a tonal streak; a coarser stretched patch layer gives the plush brushed-nap light/dark.
        nap = p["nap"]
        def stretched(label, per_mm, stretch, detail, xy):
            mp = node("ShaderNodeMapping", label + " axes", (xy[0] - 250, xy[1]))
            mp.inputs["Scale"].default_value = (k, k, k / stretch)
            links.new(coord.outputs["Object"], mp.inputs["Vector"])
            nz = node("ShaderNodeTexNoise", label, xy); nz.noise_dimensions = "3D"
            nz.inputs["Scale"].default_value, nz.inputs["Detail"].default_value = per_mm, detail
            nz.inputs["Roughness"].default_value, nz.inputs["Distortion"].default_value = 0.6, nap.get("distortion", 0.25)
            links.new(mp.outputs["Vector"], nz.inputs["Vector"])
            return nz.outputs["Fac"]
        fibre = stretched("Nap fibres", nap["scale_per_mm"], nap["stretch"], 5.0, (-250, -900))
        patch = stretched("Nap patches", nap["patch_per_mm"], nap.get("patch_stretch", nap["stretch"] / 2), 2.0, (-250, -1150))
        nb = node("ShaderNodeBump", "Nap bump", (250, -900))
        nb.inputs["Strength"].default_value, nb.inputs["Distance"].default_value = nap["bump"], nap["distance_mm"] / 1000
        links.new(fibre, nb.inputs["Height"])
        if normal_socket:
            links.new(normal_socket, nb.inputs["Normal"])
        normal_socket = nb.outputs["Normal"]
        def tone(src, amount, xy, label):
            r = node("ShaderNodeMapRange", label, xy); r.clamp = True
            r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = 0.3, 0.7
            r.inputs["To Min"].default_value, r.inputs["To Max"].default_value = 1 - amount, 1 + amount
            links.new(src, r.inputs["Value"]); return r.outputs["Result"]
        for src, amt, lbl, xy in ((fibre, nap["tone"], "Fibre tone", (0, -900)), (patch, nap["patch_tone"], "Patch tone", (0, -1150))):
            mx = node("ShaderNodeMix", lbl + " x pigment", (xy[0] + 250, xy[1] + 400)); mx.data_type, mx.blend_type = "RGBA", "MULTIPLY"
            mx.inputs["Factor"].default_value = 1
            links.new(colour, mx.inputs["A"]); links.new(tone(src, amt, xy, lbl + " range"), mx.inputs["B"])
            colour = mx.outputs["Result"]
        links.new(colour, bsdf.inputs["Base Color"])
    if normal_socket:
        links.new(normal_socket, bsdf.inputs["Normal"])
    if p.get("tangent"):  # brushed direction for anisotropy: radial about an axis (circumferential brushing on lathes)
        tn = node("ShaderNodeTangent", "Brush tangent", (300, -400)); tn.direction_type, tn.axis = "RADIAL", p["tangent"]["axis"]
        links.new(tn.outputs["Tangent"], bsdf.inputs["Tangent"])
    for k, v in p["bsdf"].items():
        if k == "sheen_tint":  # RGB: keeps the nap glint in the pigment hue instead of a pale veil
            bsdf.inputs["Sheen Tint"].default_value = (*v, 1); continue
        if k == "emission_color":
            bsdf.inputs["Emission Color"].default_value = (*v, 1); continue
        bsdf.inputs[{"ior": "IOR", "specular_ior_level": "Specular IOR Level", "sheen_weight": "Sheen Weight",
                     "sheen_roughness": "Sheen Roughness", "metallic": "Metallic", "anisotropic": "Anisotropic",
                     "anisotropic_rotation": "Anisotropic Rotation", "transmission_weight": "Transmission Weight",
                     "emission_strength": "Emission Strength",
                     "coat_weight": "Coat Weight", "coat_roughness": "Coat Roughness"}[k]].default_value = v
    mat["library_id"], mat["library_version"] = p["id"], p["version"]
    return mat
