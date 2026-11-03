"""PERHAPS_CINEMATIC_STUDIO_V2: replace every existing light with a new four-light rig on an already-posed floating scene.

Params: studio_preset (config/presets/*.json), tier: {<group>_mult} energy multipliers (groups: key, edge, side, bounce) and optional key_spread_deg (per-tier cone width override).
Input scene must already hold `PRESENT | pose` and the floating camera (icon-float-v00x stage.blend). Camera, pose, product
transforms, materials, world and colour management are not touched. Old lights move to an excluded collection (they stay in
the file for comparison but cannot reach the depsgraph). The rig is defined in the product frame and follows the pose yaw.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RIG, OLD = "PERHAPS_CINEMATIC_STUDIO_V2", "PERHAPS_PREVIOUS_LIGHTS_DISABLED"


def run(params):
    import bpy
    from mathutils import Matrix, Vector
    from pipeline.studio import aim
    studio = json.loads((ROOT / params["studio_preset"]).read_text())
    mult = params.get("tier", {})
    scene, view_layer = bpy.context.scene, bpy.context.view_layer
    pose, cam = bpy.data.objects["PRESENT | pose"], scene.camera
    assert cam and cam.name == "CAM | floating_hero_low_angle", "expected the floating camera"
    old_collection = bpy.data.collections.new(OLD)
    scene.collection.children.link(old_collection)
    disabled = []
    for o in list(bpy.data.objects):
        if o.type == "LIGHT":
            for c in list(o.users_collection):
                c.objects.unlink(o)
            old_collection.objects.link(o)
            o.hide_render = o.hide_viewport = True
            disabled.append(o.name)
    view_layer.layer_collection.children[OLD].exclude = True
    rig = bpy.data.collections.new(RIG)
    rig["preset"] = studio["name"]
    scene.collection.children.link(rig)
    pivot, yaw = Vector(pose.location), pose.rotation_euler.z
    turn = Matrix.Rotation(yaw, 3, "Z")
    cam_pos = cam.matrix_world.translation.copy()
    made = []
    for spec in studio["lights"]:
        data = bpy.data.lights.new(spec["name"], "AREA")
        data.shape, data.size, data.size_y = "RECTANGLE", spec["size"][0], spec["size"][1]
        data.energy = spec["power_w"] * mult.get(spec["group"] + "_mult", 1.0)
        data.color = spec["color"]
        if "spread_deg" in spec:
            data.spread = math.radians(mult.get(spec["group"] + "_spread_deg", spec["spread_deg"]))
        o = bpy.data.objects.new(spec["name"], data)
        rig.objects.link(o)
        if "mirror" in spec:  # strip sits on the camera's mirror direction about the bevel normal, so the bevel reflects it
            m = spec["mirror"]
            point, normal = pivot + turn @ (Vector(m["point"]) - pivot), (turn @ Vector(m["normal"])).normalized()
            view = (cam_pos - point).normalized()
            aim(o, point + (2 * normal.dot(view) * normal - view).normalized() * m["distance"], point)
        else:
            aim(o, pivot + turn @ (Vector(spec["position"]) - pivot), pivot + turn @ (Vector(spec["target"]) - pivot))
        o.visible_camera = False
        made.append(o.name)
    bpy.context.view_layer.update()
    return {"rig": RIG, "preset": studio["name"], "lights": made, "disabled_previous": len(disabled), "tier": mult}
