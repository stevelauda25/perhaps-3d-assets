"""copy_look: copy materials, lights and light-path settings verbatim from a finished .blend (e.g. Final Blender/Perhaps_Select_Box.blend).

Params: source (.blend, project-relative), materials {our slot material name: source material name},
lights_prefix (source light objects whose name starts with this replace same-named lights here; others with the prefix are removed).
Resolution and sampling stay with the render profile.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CYCLES = ("max_bounces", "diffuse_bounces", "glossy_bounces", "transmission_bounces", "volume_bounces",
          "transparent_max_bounces", "sample_clamp_direct", "sample_clamp_indirect", "caustics_reflective",
          "caustics_refractive", "blur_glossy")


def run(params):
    import bpy
    scene = bpy.context.scene
    src = str(ROOT / params["source"])
    prefix = params["lights_prefix"]
    with bpy.data.libraries.load(src, link=False) as (have, want):
        missing = set(params["materials"].values()) - set(have.materials)
        assert not missing, "source has no material %s" % sorted(missing)
        mat_names = sorted(set(params["materials"].values()))
        names = [n for n in have.objects if n.startswith(prefix)]
        want.materials, want.scenes, want.objects = list(mat_names), [have.scenes[0]], list(names)
    src_scene = want.scenes[0]
    lights = [o for o in want.objects if o.type == "LIGHT" and not o.hide_render]
    assert lights, "source has no render lights named %r*" % prefix

    mats = dict(zip(mat_names, want.materials))
    swapped = 0
    for o in scene.objects:
        for slot in getattr(o, "material_slots", []):
            if slot.material and slot.material.name in params["materials"]:
                slot.material = mats[params["materials"][slot.material.name]]
                swapped += 1
    assert swapped or not params["materials"], "no slot matched %s" % sorted(params["materials"])  # {} = lights only

    for o in [o for o in scene.objects if o.name.startswith(prefix)]:
        bpy.data.objects.remove(o)
    for o, name in zip(want.objects, names):
        o.name = name  # appended next to ours as "<name>.001"; take the source name back
        if o in lights:
            scene.collection.objects.link(o)
        else:
            bpy.data.objects.remove(o)

    for k in CYCLES:
        setattr(scene.cycles, k, getattr(src_scene.cycles, k))
    for k in ("view_transform", "look", "exposure", "gamma"):
        setattr(scene.view_settings, k, getattr(src_scene.view_settings, k))
    scene.render.filter_size = src_scene.render.filter_size
    world = src_scene.world
    bpy.data.scenes.remove(src_scene)
    if world and not world.users:
        bpy.data.worlds.remove(world)

    others = [o.name for o in scene.objects if not o.hide_render and (o.type == "LIGHT" and o not in lights)]
    assert not others, "other render lights left in the scene: %s" % others
    return {"slots_swapped": swapped, "lights": sorted(o.name for o in lights)}
