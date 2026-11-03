"""Tier material presets -> Blender materials. One builder per surface family.

A preset (config/tiers/<tier>.json) names a `builder`; roles (exterior/branding/interior/band)
override shared `defaults`. `extends` inherits another preset's keys (roles merge per role).
Add a surface family = add a function to BUILDERS; presets stay data-only.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_preset(ref):
    p = Path(ref) if Path(ref).is_absolute() else ROOT / ref
    preset = json.loads(p.read_text())
    if "extends" in preset:
        base = load_preset("config/tiers/%s.json" % preset["extends"])
        roles = {**base.get("roles", {}), **{k: {**base.get("roles", {}).get(k, {}), **v} for k, v in preset.get("roles", {}).items()}}
        preset = {**base, **preset, "roles": roles}
    return preset


def role_params(preset, role):
    r = dict(preset["roles"][role])
    if "from" in r:
        base = role_params(preset, r.pop("from"))
        factor, offset = r.pop("color_factor", 1), r.pop("roughness_offset", 0)
        r = {**base, **r}
        r["color_linear"] = [c * factor for c in base["color_linear"]]
        r["roughness_range"] = [v + offset for v in base["roughness_range"]]
    return {**preset.get("defaults", {}), **r}


def paperboard(name, p):
    """Uncoated paperboard: object-space (mm) fibre noise drives bump, roughness and tone."""
    import bpy
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    def node(kind, label, xy):
        n = nodes.new(kind); n.name = n.label = label; n.location = xy
        return n

    def noise(label, per_mm, detail, xy, roughness=0.62, distortion=0.4):
        n = node("ShaderNodeTexNoise", label, xy)
        n.noise_dimensions, n.normalize = "3D", True
        n.inputs["Scale"].default_value, n.inputs["Detail"].default_value = per_mm, detail
        n.inputs["Roughness"].default_value, n.inputs["Distortion"].default_value = roughness, distortion
        links.new(mm.outputs["Vector"], n.inputs["Vector"])
        return n.outputs["Fac"]

    def remap(src, lo, hi, xy, label):
        n = node("ShaderNodeMapRange", label, xy); n.clamp = True
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = 0.3, 0.7
        n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = lo, hi
        links.new(src, n.inputs["Value"])
        return n.outputs["Result"]

    coord = node("ShaderNodeTexCoord", "Object space", (-1100, 0))
    mm = node("ShaderNodeMapping", "Metres to mm", (-900, 0))
    mm.inputs["Scale"].default_value = (1000, 1000, 1000)
    links.new(coord.outputs["Object"], mm.inputs["Vector"])
    fiber = noise("Paper fibre", p["fiber_scale_per_mm"], p["fiber_detail"], (-650, 300))
    felt = noise("Felting", p["fiber_scale_per_mm"] * 0.25, 4.0, (-650, 100), 0.55, 0.9)
    mottle = noise("Pulp mottling", p["mottle_scale_per_mm"], 3.0, (-650, -100), 0.5, 0.2)
    mix = node("ShaderNodeMix", "Fibre + felting relief", (-400, 250)); mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.35
    links.new(fiber, mix.inputs["A"]); links.new(felt, mix.inputs["B"])
    bump = node("ShaderNodeBump", "Fibre relief", (-150, 250))
    bump.inputs["Strength"].default_value = p["bump_strength"]
    bump.inputs["Distance"].default_value = p["bump_distance_mm"] / 1000
    links.new(mix.outputs["Result"], bump.inputs["Height"])
    tone = remap(mottle, 1 - p["mottle_amount"], 1 + p["mottle_amount"], (-400, -100), "Mottle tone")
    speck = remap(fiber, 1 - p["speckle_amount"], 1 + p["speckle_amount"], (-400, -300), "Fibre speckle tone")
    tint = node("ShaderNodeMix", "Pigment x tone", (-150, -100)); tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs["Factor"].default_value = 1
    tint.inputs["A"].default_value = (*p["color_linear"], 1)
    t2 = node("ShaderNodeMath", "Tone x speckle", (-150, -300)); t2.operation = "MULTIPLY"
    links.new(tone, t2.inputs[0]); links.new(speck, t2.inputs[1])
    links.new(t2.outputs[0], tint.inputs["B"])
    rough = remap(fiber, *p["roughness_range"], (100, -300), "Matte roughness")
    bsdf = node("ShaderNodeBsdfPrincipled", "Paperboard", (400, 0))
    for k, v in {"IOR": p["ior"], "Specular IOR Level": p["specular_ior_level"], "Sheen Weight": p["sheen_weight"],
                 "Sheen Roughness": p["sheen_roughness"], "Coat Weight": 0.0}.items():
        bsdf.inputs[k].default_value = v
    links.new(tint.outputs["Result"], bsdf.inputs["Base Color"])
    links.new(rough, bsdf.inputs["Roughness"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    out = node("ShaderNodeOutputMaterial", "Material Output", (700, 0))
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def metal(name, p):
    """Plain Principled metal (champagne gold etc.): colour, roughness and an optional fine isotropic brush bump."""
    import bpy
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.name = bsdf.label = "Metal"
    out = nodes.new("ShaderNodeOutputMaterial"); out.location = (300, 0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Base Color"].default_value = (*p["color_linear"], 1)
    bsdf.inputs["Roughness"].default_value = p["roughness"]
    if p.get("brush_bump"):
        coord = nodes.new("ShaderNodeTexCoord"); coord.location = (-900, -200)
        mp = nodes.new("ShaderNodeMapping"); mp.location = (-700, -200); mp.inputs["Scale"].default_value = (1000, 1000, 1000)
        nz = nodes.new("ShaderNodeTexNoise"); nz.location = (-500, -200); nz.inputs["Scale"].default_value = p["brush_bump"]["scale_per_mm"]
        nz.inputs["Detail"].default_value = 4.0
        bp = nodes.new("ShaderNodeBump"); bp.location = (-250, -200)
        bp.inputs["Strength"].default_value, bp.inputs["Distance"].default_value = p["brush_bump"]["strength"], p["brush_bump"]["distance_mm"] / 1000
        links.new(coord.outputs["Object"], mp.inputs["Vector"]); links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        links.new(nz.outputs["Fac"], bp.inputs["Height"]); links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


BUILDERS = {"paperboard": paperboard}


def apply(preset_ref, tier_label=None):
    """Build one material per role and swap every mesh slot per preset['slot_map']. Returns a summary."""
    import bpy
    preset = load_preset(preset_ref)
    if preset["builder"] not in BUILDERS:
        raise NotImplementedError("tier %s: no builder %r yet" % (preset["tier"], preset["builder"]))
    from . import material_library, pbr_material
    built = {}
    for r, spec in preset["roles"].items():
        if "library" in spec:  # approved/candidate library material, referenced by id
            built[r] = pbr_material.build(material_library.load(spec["library"]), spec.get("overrides"), pack=True,
                                          name="%s | %s" % (preset["tier"].title(), r))
        elif "metal" in spec:  # plain metal role, e.g. champagne-gold band
            built[r] = metal("%s | %s" % (preset["tier"].title(), r), spec["metal"])
        else:
            built[r] = BUILDERS[preset["builder"]]("%s | %s" % (preset["tier"].title(), r), role_params(preset, r))
    swapped = 0
    for obj in bpy.data.objects:
        for slot in obj.material_slots:
            role = preset["slot_map"].get(slot.material.name) if slot.material else None
            if role:
                slot.material = built[role]; swapped += 1
    for name in preset.get("hide_render", []):
        bpy.data.objects[name].hide_render = True
    return {"tier": preset["tier"], "materials": sorted(m.name for m in built.values()), "slots_swapped": swapped}
