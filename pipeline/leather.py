"""Physically scaled leather, lining and brushed-metal node materials."""
import copy
import bpy
from .config import ROOT


class Graph:
    def __init__(self, name):
        self.material = bpy.data.materials.new(name)
        self.material.use_nodes = True
        self.nodes = self.material.node_tree.nodes
        self.links = self.material.node_tree.links
        self.shader = self.nodes.get("Principled BSDF")
        self.shader.location = (1050, 100)
        self.nodes.get("Material Output").location = (1350, 100)

    def node(self, kind, label, location=(0, 0), **properties):
        node = self.nodes.new(kind)
        node.label = node.name = label
        node.location = location
        for name, value in properties.items():
            setattr(node, name, value)
        return node

    def connect(self, output, node, socket):
        self.links.new(output, node.inputs[socket])

    def remap(self, source, limits, output, label, location):
        node = self.node("ShaderNodeMapRange", label, location, clamp=True, interpolation_type="SMOOTHERSTEP")
        self.connect(source, node, "Value")
        for key, value in zip(("From Min", "From Max", "To Min", "To Max"), (*limits, *output)):
            node.inputs[key].default_value = value
        return node.outputs["Result"]

    def noise(self, vector, scale, label, location, detail=2):
        node = self.node("ShaderNodeTexNoise", label, location)
        self.connect(vector, node, "Vector")
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
        node.inputs["Roughness"].default_value = 0.65
        return node

    def coordinates(self, anchor):
        node = self.node("ShaderNodeTexCoord", "Meters in component control space", (-1400, 0))
        node.object = anchor
        return node.outputs["Object"]


def leather(name, params, anchor, pressed=False):
    p = copy.deepcopy(params)
    g = Graph(name)
    xyz = g.coordinates(anchor)
    source = p["source_maps"]
    scaled = g.node("ShaderNodeVectorMath", "Physical scan tile in meters", (-1150, 500), operation="SCALE")
    g.connect(xyz, scaled, 0)
    scaled.inputs["Scale"].default_value = 1000/source["tile_width_mm"]
    maps = {}
    for key, location in (("height", (-800, 520)), ("roughness", (-800, -100))):
        texture = g.node("ShaderNodeTexImage", "CC0 leather scan - "+key, location)
        texture.image = bpy.data.images.load(str(ROOT/source[key]), check_existing=True)
        texture.image.colorspace_settings.name = "Non-Color"
        if not texture.image.packed_file:
            texture.image.pack()
        texture.projection = "BOX"
        texture.projection_blend = source["box_blend"]
        texture.extension = "REPEAT"
        g.connect(scaled.outputs[0], texture, "Vector")
        maps[key] = texture.outputs["Color"]
    height = g.remap(maps["height"], source["height_range"], (0, 1), "Natural scan grain and pores", (350, 520))
    if p.get("seam_pressure_um") and anchor.name == "CTRL | Lid lift-off":
        split = g.node("ShaderNodeSeparateXYZ", "Wrap coordinates", (-1200, -650))
        g.connect(xyz, split, 0)
        distances = []
        for axis in ("X", "Y"):
            absolute = g.node("ShaderNodeMath", "Absolute "+axis, (-1000, -650-len(distances)*150), operation="ABSOLUTE")
            g.connect(split.outputs[axis], absolute, 0)
            distance = g.node("ShaderNodeMath", "Distance to stitch channel "+axis, (-800, -650-len(distances)*150), operation="SUBTRACT")
            g.connect(absolute.outputs[0], distance, 0)
            distance.inputs[1].default_value = p["stitch_track_mm"][axis.lower()]/1000
            positive = g.node("ShaderNodeMath", "Channel distance "+axis, (-600, -650-len(distances)*150), operation="ABSOLUTE")
            g.connect(distance.outputs[0], positive, 0)
            distances.append(positive.outputs[0])
        nearest = g.node("ShaderNodeMath", "Nearest pressure track", (-400, -650), operation="MINIMUM")
        for i, distance in enumerate(distances):
            g.connect(distance, nearest, i)
        depression = g.remap(nearest.outputs[0], (0, p["seam_pressure_width_mm"]/1000),
                            (-p["seam_pressure_um"]/p["grain_height_um"], 0), "Soft stitch seating pressure", (-180, -650))
        seated = g.node("ShaderNodeMath", "Hide grain plus wrap pressure", (520, 620), operation="ADD")
        g.connect(height, seated, 0)
        g.connect(depression, seated, 1)
        height = seated.outputs[0]
    bump = g.node("ShaderNodeBump", "Micron-scale leather relief", (700, 500))
    g.connect(height, bump, "Height")
    bump.inputs["Distance"].default_value = p["grain_height_um"]*1e-6*(p.get("pressed_relief_factor", 0.2) if pressed else 1)
    bump.inputs["Strength"].default_value = p["bump_strength"]
    fine = g.noise(xyz, 1000/p["micro_spacing_mm"], "Subgrain surface finish", (-650, -340), detail=1)
    finish = g.node("ShaderNodeBump", "Very fine finish normal", (900, 450))
    g.connect(fine.outputs["Fac"], finish, "Height")
    g.connect(bump.outputs["Normal"], finish, "Normal")
    finish.inputs["Distance"].default_value = p["micro_height_um"]*1e-6
    finish.inputs["Strength"].default_value = 0.20
    g.connect(finish.outputs["Normal"], g.shader, "Normal")
    value = g.remap(maps["roughness"], source["roughness_range"],
                    (p["roughness"]-p["roughness_variation"], p["roughness"]+p["roughness_variation"]),
                    "Narrow roughness range", (150, -340))
    if p.get("roughness_mottle", 0):
        mottle = g.noise(xyz, 1000/p["roughness_mottle_mm"], "Low-amplitude finish variation", (-600, -400), detail=1)
        variation = g.remap(mottle.outputs["Fac"], (0.1, 0.9), (-p["roughness_mottle"], p["roughness_mottle"]),
                            "Independent finish variation", (-200, -400))
        combine = g.node("ShaderNodeMath", "Natural finish plus scanned roughness", (450, -320), operation="ADD")
        g.connect(value, combine, 0)
        g.connect(variation, combine, 1)
        value = combine.outputs[0]
    g.connect(value, g.shader, "Roughness")
    broad = g.noise(xyz, 45, "Subtle hide tonal variation", (-950, -850), detail=1)
    color = g.node("ShaderNodeMixRGB", "Near-black espresso undertone", (680, -200), blend_type="MIX")
    g.connect(broad.outputs["Fac"], color, 0)
    color.inputs[1].default_value = tuple(c*(1-p["color_variation"]) for c in p["color_linear"]) + (1,)
    color.inputs[2].default_value = tuple(c*(1+p["color_variation"]) for c in p["color_linear"]) + (1,)
    g.connect(color.outputs[0], g.shader, "Base Color")
    for key, value in {"IOR": p["ior"], "Specular IOR Level": p["specular_level"],
                       "Sheen Weight": p["sheen"], "Sheen Roughness": 0.7, "Diffuse Roughness": 0.15}.items():
        g.shader.inputs[key].default_value = value
    g.material["scan_tile_width_mm"] = source["tile_width_mm"]
    g.material["texture_source"] = source["source_url"]
    g.material["relief_height_bound_um"] = p["grain_height_um"]
    g.material["coordinate_anchor"] = anchor.name
    return g.material


def metal(params, anchor):
    g = Graph("PE | Dark graphite brushed inlay")
    xyz = g.coordinates(anchor)
    scale = g.node("ShaderNodeVectorMath", "Horizontal circumferential brush scale", (-1100, 200), operation="MULTIPLY")
    g.connect(xyz, scale, 0)
    scale.inputs[1].default_value = (1000/params["brush_length_mm"], 1000/params["brush_length_mm"], 1e6/params["brush_spacing_um"])
    noise = g.noise(scale.outputs[0], 1, "Fine directional machining", (-850, 180), detail=1)
    rough = g.remap(noise.outputs["Fac"], (0.1, 0.9),
                    (params["roughness"]-params["roughness_variation"], params["roughness"]+params["roughness_variation"]),
                    "Controlled brushed roughness", (-550, 200))
    g.connect(rough, g.shader, "Roughness")
    bump = g.node("ShaderNodeBump", "Submicron brush normal", (550, 250))
    g.connect(noise.outputs["Fac"], bump, "Height")
    bump.inputs["Distance"].default_value = params["brush_height_um"]*1e-6
    bump.inputs["Strength"].default_value = params.get("bump_strength", 0.3)
    g.connect(bump.outputs["Normal"], g.shader, "Normal")
    normal = g.node("ShaderNodeNewGeometry", "Vertical side normal", (-400, -200))
    tangent = g.node("ShaderNodeVectorMath", "Brushing follows horizontal perimeter", (0, -100), operation="CROSS_PRODUCT")
    tangent.inputs[0].default_value = (0, 0, 1)
    g.connect(normal.outputs["Normal"], tangent, 1)
    g.connect(tangent.outputs[0], g.shader, "Tangent")
    g.shader.inputs["Base Color"].default_value = (*params["color_linear"], 1)
    g.shader.inputs["Metallic"].default_value = 1
    g.shader.inputs["Anisotropic"].default_value = params["anisotropy"]
    return g.material


def lining(params, anchor):
    g = Graph("PE | Dark soft interior lining")
    xyz = g.coordinates(anchor)
    fiber = g.noise(xyz, 1000/params["fiber_spacing_mm"], "Fine interior nap", (-750, 200), detail=1)
    bump = g.node("ShaderNodeBump", "Restrained textile nap", (550, 250))
    g.connect(fiber.outputs["Fac"], bump, "Height")
    bump.inputs["Distance"].default_value = params["fiber_height_um"]*1e-6
    bump.inputs["Strength"].default_value = 0.25
    g.connect(bump.outputs["Normal"], g.shader, "Normal")
    g.shader.inputs["Base Color"].default_value = (*params["color_linear"], 1)
    g.shader.inputs["Roughness"].default_value = params["roughness"]
    g.shader.inputs["Sheen Weight"].default_value = params["sheen"]
    return g.material


def apply(config):
    base, lid = (bpy.data.objects[name] for name in ("CTRL | Base", "CTRL | Lid lift-off"))
    lidskin = leather("PE | Fine-grain black leather - lid", config["leather"], lid)
    baseskin = leather("PE | Fine-grain black leather - base", config["leather"], base)
    interior = lining(config["interior"], base)
    band = metal(config["metal"], base)
    pressed_params = copy.deepcopy(config["leather"])
    pressed_params["color_linear"] = [v*config["branding"]["pressed_color_factor"] for v in pressed_params["color_linear"]]
    pressed_params["roughness"] = config["branding"]["pressed_roughness"]
    pressed = leather("PE | Compressed leather letter floors", pressed_params, lid, pressed=True)
    for obj in bpy.data.objects:
        if obj.get("export_product"):
            replacements = {"exterior": lidskin if obj.parent == lid else baseskin,
                            "interior": interior, "band": band, "branding": pressed}
            if len(obj.material_slots) != 4:
                raise ValueError("Canonical material-slot layout changed: "+obj.name)
            for i, key in enumerate(("exterior", "interior", "band", "branding")):
                obj.data.materials[i] = replacements[key]
    return {"lid": lidskin, "base": baseskin, "interior": interior, "band": band, "pressed": pressed}
