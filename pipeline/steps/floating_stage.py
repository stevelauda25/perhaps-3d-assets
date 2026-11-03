"""Shared floating presentation: pose controller + low-angle camera + dramatic studio rig, from two preset files.

Params: camera_preset, studio_preset (config/presets/*.json), tier: {<group>_mult} per-tier energy multipliers only (groups: key, edge, side, bounce).
Product parts keep their own transforms: both CTRL empties are parented to `PRESENT | pose` (a yaw about the box centre) so the
presentation can be removed by clearing the parent. Cameras/lights are new; old lights, floor and reflection cards are switched off.
World stays pure black. Materials, geometry and branding are not modified.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(params):
    import bpy
    from mathutils import Matrix, Vector
    from pipeline.studio import aim
    cam_p = json.loads((ROOT / params["camera_preset"]).read_text())
    studio = json.loads((ROOT / params["studio_preset"]).read_text())
    mult = params.get("tier", {})
    scene = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            o.hide_render = True
        elif o.type == "MESH" and (o.name.startswith("Studio | Ground") or (o.name.startswith("PE6 | ") and "wrap" not in o.name and "stitching" not in o.name)):
            o.hide_render = True
    # pose controller
    pose = bpy.data.objects.new("PRESENT | pose", None)
    scene.collection.objects.link(pose)
    pose.location = cam_p["pose"]["pivot_m"]
    bpy.context.view_layer.update()
    inverse = pose.matrix_world.inverted()
    for name in ("CTRL | Base", "CTRL | Lid lift-off"):
        o = bpy.data.objects[name]
        assert o.parent is None, name
        o.parent, o.matrix_parent_inverse = pose, inverse
    pose.rotation_euler.z = math.radians(cam_p["pose"]["yaw_deg"])
    # camera
    c = cam_p["camera"]
    t, az, el = Vector(c["target_m"]), math.radians(c["azimuth_deg"]), math.radians(c["elevation_deg"])
    pos = t + Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * c["distance_m"]
    cam = bpy.data.objects.new("CAM | floating_hero_low_angle", bpy.data.cameras.new("CAM | floating_hero_low_angle"))
    scene.collection.objects.link(cam)
    cam.data.lens, cam.data.sensor_width, cam.data.clip_end = c["lens_mm"], 36, 20
    cam.matrix_world = Matrix.Translation(pos) @ (t - pos).to_track_quat("-Z", "Y").to_matrix().to_4x4() @ Matrix.Rotation(math.radians(c["roll_deg"]), 4, "Z")
    cam.data.shift_x, cam.data.shift_y = c["shift"]
    # lights: the rig is defined in the product frame and follows the pose yaw, so it keeps its relation to the box
    yaw, pivot = math.radians(cam_p["pose"]["yaw_deg"]), Vector(cam_p["pose"]["pivot_m"])
    turn = Matrix.Rotation(yaw, 3, "Z")
    made = []
    for spec in studio["lights"]:
        data = bpy.data.lights.new(spec["name"], "AREA")
        data.shape, data.size, data.size_y = "RECTANGLE", spec["size"][0], spec["size"][1]
        data.energy, data.color = spec["power_w"] * mult.get(spec.get("group", "key") + "_mult", 1.0), spec["color"]
        if "spread_deg" in spec:
            data.spread = math.radians(spec["spread_deg"])  # narrower beam: the light pools on one side of the face and falls off across it
        o = bpy.data.objects.new(spec["name"], data)
        scene.collection.objects.link(o)
        if "mirror" in spec:
            # edge strip: sits on the mirror direction of the camera about the edge bevel normal, so the bevel reflects it (thin real highlight)
            m = spec["mirror"]
            point, normal = pivot + turn @ (Vector(m["point"]) - pivot), (turn @ Vector(m["normal"])).normalized()
            view = (pos - point).normalized()
            refl = (2 * normal.dot(view) * normal - view).normalized()
            aim(o, point + refl * m["distance"], point)
        else:
            aim(o, pivot + turn @ (Vector(spec["position"]) - pivot), pivot + turn @ (Vector(spec["target"]) - pivot))
        o.visible_camera = False
        made.append(o.name)
    scene.camera = cam
    return {"camera": cam.name, "lights": made, "pose_yaw_deg": cam_p["pose"]["yaw_deg"], "tier": mult}
