"""Cinematic floating presentation on top of an approved scene: new cameras + new studio lights, no product change.

Params:
  cameras: {name: {azimuth_deg, elevation_deg, distance_m, lens_mm, roll_deg, shift: [x, y], target: [x, y, z]}}  (az 0 = camera on -Y, +az toward +X... see below)
  lights:  [{name, size: [w, h] (m), position: [x, y, z], target: [x, y, z], power_w, color: [r, g, b]}]  area lights, invisible to camera
  hide:    object-name prefixes to switch off for render (old floor / reflection cards)
Floating comes from composition (low/high angle + roll + off-centre shift) and a pure black void: world strength 0, floor and
old cards hidden, no product transform touched (geometry lock stays valid). Old lights stay off. Materials are not modified.
"""
import math


def run(params):
    import bpy
    from mathutils import Matrix, Vector
    from pipeline.studio import aim
    scene = bpy.context.scene
    off = []
    for o in bpy.data.objects:
        if any(o.name.startswith(p) for p in params.get("hide", ["Studio | Ground", "PE6 | "])) and o.type in ("MESH", "LIGHT") and "leather wrap" not in o.name \
                and "stitching" not in o.name:
            o.hide_render = True; off.append(o.name)
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            o.hide_render = True
    made = []
    for spec in params["lights"]:
        data = bpy.data.lights.new(spec["name"], "AREA")
        data.shape, data.size, data.size_y = "RECTANGLE", spec["size"][0], spec["size"][1]
        data.energy, data.color = spec["power_w"], spec.get("color", (1, 1, 1))
        data.cycles.is_portal = False
        o = bpy.data.objects.new(spec["name"], data)
        scene.collection.objects.link(o)
        aim(o, spec["position"], spec["target"])
        o.visible_camera = False
        made.append(o.name)
    cams = []
    for name, c in params["cameras"].items():
        t = Vector(c.get("target", (0, 0, 0.07)))
        az, el, d = math.radians(c["azimuth_deg"]), math.radians(c["elevation_deg"]), c["distance_m"]
        # azimuth 0 = camera on the -Y axis looking +Y; positive azimuth swings toward -X (matches the production hero side)
        pos = t + Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * d
        cam = bpy.data.objects.new("CAM | " + name, bpy.data.cameras.new("CAM | " + name))
        scene.collection.objects.link(cam)
        cam.data.lens, cam.data.sensor_width = c.get("lens_mm", 110), 36
        cam.data.clip_end = 20
        q = (t - pos).to_track_quat("-Z", "Y")
        cam.matrix_world = Matrix.Translation(pos) @ q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(c.get("roll_deg", 0)), 4, "Z")
        cam.data.shift_x, cam.data.shift_y = c.get("shift", (0, 0))
        cams.append(cam.name)
    scene.camera = bpy.data.objects[cams[0]]
    return {"cameras": cams, "lights": made, "hidden": len(off), "world_strength": 0}
