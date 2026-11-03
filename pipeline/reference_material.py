"""Scanned PBR leather on metric wrap UVs, without procedural grain substitution."""
import bpy
from .config import ROOT
from .leather import Graph, metal, lining
from .grain_compare import grain_multiplier, SCALE_NODE


def set_grain_scale(material, multiplier):
    """Scale all aligned scan channels together without editing mesh UVs."""
    multiplier = grain_multiplier(multiplier)
    tree = material.node_tree
    maps = [tree.nodes.get("Photometric scan | "+key) for key in ("color", "roughness", "normal", "height")]
    if any(node is None or node.type != "TEX_IMAGE" for node in maps):
        raise ValueError("Expected four aligned photometric scan maps in "+material.name)
    scale = tree.nodes.get(SCALE_NODE)
    if scale is None:
        sources = [[(link.from_node.name, link.from_socket.identifier) for link in node.inputs["Vector"].links] for node in maps]
        if any(source != sources[0] for source in sources) or len(sources[0]) != 1:
            raise ValueError("PBR maps do not share a single coordinate source")
        source = maps[0].inputs["Vector"].links[0].from_socket
        if source.node.type != "UVMAP" or source.node.uv_map != "PE metric wrap":
            raise ValueError("Expected original metric leather wrap UVs")
        scale = tree.nodes.new("ShaderNodeVectorMath")
        scale.name = scale.label = SCALE_NODE
        scale.operation = "SCALE"
        scale.location = (-1050, 300)
        tree.links.new(source, scale.inputs[0])
    if scale.type != "VECT_MATH" or scale.operation != "SCALE":
        raise ValueError("Unexpected grain coordinate node")
    scale.inputs["Scale"].default_value = 1.0/multiplier
    for node in maps:
        tree.links.new(scale.outputs["Vector"], node.inputs["Vector"])
    material["leather_grain_scale_multiplier"] = multiplier
    material["effective_tile_width_mm"] = material["tile_width_mm"]*multiplier
    return scale


def leather(config, pressed=False):
    p = config["leather"]
    g = Graph("PE6 | Pressed leather" if pressed else "PE6 | Scanned obsidian leather")
    uv = g.node("ShaderNodeUVMap", "Metric leather wrap UV", (-1100, 100), uv_map="PE metric wrap")
    maps = {}
    for i, key in enumerate(("color", "roughness", "normal", "height")):
        texture = g.node("ShaderNodeTexImage", "Photometric scan | "+key, (-850, 550-i*300))
        image = bpy.data.images.load(str(ROOT/p["source_maps"][key]), check_existing=True)
        image.colorspace_settings.name = "sRGB" if key == "color" else "Non-Color"
        if not image.packed_file:
            image.pack()
        texture.image = image
        texture.interpolation = "Linear"
        texture.extension = "REPEAT"
        g.connect(uv.outputs["UV"], texture, "Vector")
        maps[key] = texture.outputs["Color"]
    luminance = g.node("ShaderNodeRGBToBW", "Scanned pigmentation variation", (-550, 600))
    g.connect(maps["color"], luminance, 0)
    variation = g.remap(luminance.outputs[0], p["albedo_range"], p["albedo_factors"],
                        "Preserve subtle albedo variation", (-300, 600))
    tint = g.node("ShaderNodeMixRGB", "Obsidian dye with espresso undertone", (0, 600), blend_type="MULTIPLY")
    tint.inputs[0].default_value = 1
    factor = config["branding"]["pressed_color_factor"] if pressed else 1
    tint.inputs[1].default_value = tuple(c*factor for c in p["color_linear"]) + (1,)
    g.connect(variation, tint, 2)
    g.connect(tint.outputs[0], g.shader, "Base Color")
    rough = g.node("ShaderNodeMath", "Scanned roughness gain", (-500, 150), operation="MULTIPLY_ADD")
    g.connect(maps["roughness"], rough, 0)
    rough.inputs[1].default_value = p["roughness_gain"]
    rough.inputs[2].default_value = p["roughness_offset"] - (0.025 if pressed else 0)
    g.connect(rough.outputs[0], g.shader, "Roughness")
    normal = g.node("ShaderNodeNormalMap", "OpenGL tangent normal", (-100, -150), space="TANGENT")
    normal.uv_map = "PE metric wrap"
    normal.inputs["Strength"].default_value = p["normal_strength"]*(0.55 if pressed else 1)
    g.connect(maps["normal"], normal, "Color")
    pores = g.node("ShaderNodeBump", "Restrained scan height microdepth", (500, -120))
    g.connect(maps["height"], pores, "Height")
    g.connect(normal.outputs["Normal"], pores, "Normal")
    pores.inputs["Distance"].default_value = p["grain_height_um"]*1e-6
    pores.inputs["Strength"].default_value = 0.15 if pressed else p["bump_strength"]
    g.connect(pores.outputs["Normal"], g.shader, "Normal")
    for name, value in {"IOR": p["ior"], "Specular IOR Level": p["specular_level"],
                         "Coat Weight": p["coat_weight"], "Coat Roughness": p["coat_roughness"],
                         "Coat IOR": 1.46, "Sheen Weight": p["sheen"], "Diffuse Roughness": 0.2}.items():
        g.shader.inputs[name].default_value = value
    g.connect(pores.outputs["Normal"], g.shader, "Coat Normal")
    g.material["source"] = p["source_maps"]["source_url"]
    g.material["tile_width_mm"] = p["source_maps"]["tile_width_mm"]
    g.material["normal_convention"] = "OpenGL +Y, metric wrap UV, no structural displacement"
    set_grain_scale(g.material, p.get("leather_grain_scale_multiplier", 1.0))
    return g.material


def apply(config):
    base = bpy.data.objects["CTRL | Base"]
    skin = leather(config)
    pressed = leather(config, pressed=True)
    band = metal(config["metal"], base)
    interior = lining(config["interior"], base)
    slots = [skin, interior, band, pressed]
    for obj in bpy.data.objects:
        if obj.get("export_product"):
            if len(obj.data.materials) != 4:
                raise RuntimeError("Canonical material slot layout changed")
            for i, value in enumerate(slots):
                obj.data.materials[i] = value
    return {"skin": skin, "pressed": pressed, "interior": interior, "band": band}


def refine_surface(config):
    """Layer pores/finish over the approved scan without rebuilding its shader."""
    from .grain_compare import MATERIALS, scale_report
    scale_report(3.0)
    p, detail = config["leather"], config["leather"]["surface_refinement"]
    for name in MATERIALS:
        material = bpy.data.materials[name]
        tree = material.node_tree
        if tree.nodes.get("PE9 | Metric pore coordinates"):
            raise ValueError("Secondary surface detail is already installed")
        pressed = name == "PE6 | Pressed leather"
        attenuation = detail["pressed_micro_factor"] if pressed else 1.0
        start_count = len(tree.nodes)

        def node(kind, label, **properties):
            result = tree.nodes.new(kind)
            result.name = result.label = "PE9 | "+label
            for key, value in properties.items():
                setattr(result, key, value)
            index = len(tree.nodes)-start_count-1
            result.location = (1500+(index%4)*260, -300-(index//4)*330)
            return result

        def remap(source, label, limits, output):
            result = node("ShaderNodeMapRange", label, clamp=True, interpolation_type="SMOOTHERSTEP")
            tree.links.new(source, result.inputs["Value"])
            for socket, value in zip(("From Min", "From Max", "To Min", "To Max"), (*limits,*output)):
                result.inputs[socket].default_value = value
            return result.outputs["Result"]

        uv = tree.nodes["Metric leather wrap UV"].outputs["UV"]
        metres = node("ShaderNodeVectorMath", "Metric pore coordinates", operation="SCALE")
        tree.links.new(uv, metres.inputs[0])
        metres.inputs["Scale"].default_value = p["source_maps"]["tile_width_mm"]/1000
        shape = node("ShaderNodeVectorMath", "Subtle pore elongation", operation="MULTIPLY")
        shape.inputs[1].default_value = (1, 0.86, 1)
        tree.links.new(metres.outputs["Vector"], shape.inputs[0])
        pores = node("ShaderNodeTexVoronoi", "Sparse microscopic follicle pits",
                     voronoi_dimensions="2D", feature="F1", distance="EUCLIDEAN")
        pores.inputs["Scale"].default_value = 1000/detail["pore_spacing_mm"]
        pores.inputs["Randomness"].default_value = 1.0
        tree.links.new(shape.outputs[0], pores.inputs["Vector"])
        pit = remap(pores.outputs["Distance"], "Soft shallow pore profile", (0.035,0.19), (-1,0))
        bump = node("ShaderNodeBump", "Pores perturb the scanned leather normal")
        tree.links.new(pit, bump.inputs["Height"])
        tree.links.new(tree.nodes["Restrained scan height microdepth"].outputs["Normal"], bump.inputs["Normal"])
        bump.inputs["Distance"].default_value = detail["pore_depth_um"]*1e-6
        bump.inputs["Strength"].default_value = detail["pore_strength"]*attenuation
        shader = tree.nodes["Principled BSDF"]
        for socket in ("Normal", "Coat Normal"):
            tree.links.new(bump.outputs["Normal"], shader.inputs[socket])

        rough = tree.nodes["Scanned roughness gain"]
        rough.inputs[1].default_value = p["roughness_gain"]
        rough.inputs[2].default_value = p["roughness_offset"]-(0.025 if pressed else 0)
        summit = remap(tree.nodes["Photometric scan | height"].outputs["Color"],
                       "Restrained summit polish", (0.18,0.82),
                       (detail["summit_polish"]*attenuation,-detail["summit_polish"]*attenuation))
        finish = node("ShaderNodeTexNoise", "Low amplitude finish variation", noise_dimensions="2D")
        tree.links.new(metres.outputs[0], finish.inputs["Vector"])
        finish.inputs["Scale"].default_value = 1000/detail["finish_spacing_mm"]
        finish.inputs["Detail"].default_value = 2
        finish.inputs["Roughness"].default_value = 0.6
        variation = node("ShaderNodeMath", "Centered finish roughness", operation="MULTIPLY_ADD")
        tree.links.new(finish.outputs["Fac"], variation.inputs[0])
        variation.inputs[1].default_value = 2*detail["roughness_variation"]*attenuation
        variation.inputs[2].default_value = -detail["roughness_variation"]*attenuation
        cavity = node("ShaderNodeMath", "Pore cavity roughness", operation="MULTIPLY")
        tree.links.new(pit, cavity.inputs[0])
        cavity.inputs[1].default_value = -detail["pore_roughness"]*attenuation
        total = rough.outputs[0]
        for label, addition in (("Summit finish",summit), ("Hide finish",variation.outputs[0]),
                                ("Pore finish",cavity.outputs[0])):
            combine = node("ShaderNodeMath", label, operation="ADD")
            tree.links.new(total, combine.inputs[0])
            tree.links.new(addition, combine.inputs[1])
            total = combine.outputs[0]
        bounded = node("ShaderNodeClamp", "Physically restrained finish range")
        bounded.inputs["Min"].default_value, bounded.inputs["Max"].default_value = 0.30,0.60
        tree.links.new(total, bounded.inputs["Value"])
        tree.links.new(bounded.outputs[0], shader.inputs["Roughness"])
        shader.inputs["Coat Weight"].default_value = p["coat_weight"]
        shader.inputs["Sheen Weight"].default_value = p["sheen"]
    return scale_report(3.0)
