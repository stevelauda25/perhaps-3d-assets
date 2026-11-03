"""Controlled edits to an already-lit floating scene: re-place/re-aim named existing lights and add faint extra lights. No new rig.

Params:
  edit: {light name: {position?, target?, power_w?, size?, spread_deg?}}  position/target in the product frame (as in the studio presets);
        the PRESENT | pose yaw is applied exactly like floating_stage does. Unlisted fields keep their saved values.
  add:  [{name, size, position, target, power_w, color?, spread_deg?}]  new area lights, product frame, hidden from camera.
Everything else (camera, pose, product, materials, world, colour management) is untouched. Returns before/after values for the report.
"""
import math


def run(params):
    import bpy
    from mathutils import Matrix, Vector
    from pipeline.studio import aim
    scene = bpy.context.scene
    pose = bpy.data.objects["PRESENT | pose"]
    pivot, turn = Vector(pose.location), Matrix.Rotation(pose.rotation_euler.z, 3, "Z")
    world = lambda p: pivot + turn @ (Vector(p) - pivot)

    def state(o):
        d = o.data
        return {"loc_m": [round(x, 4) for x in o.matrix_world.translation], "rot_deg": [round(math.degrees(a), 1) for a in o.matrix_world.to_euler()],
                "energy_w": round(d.energy, 4), "size_m": [round(d.size, 4), round(d.size_y, 4)], "spread_deg": round(math.degrees(d.spread), 1)}
    report = {"before": {}, "after": {}}
    for name, e in params.get("edit", {}).items():
        o = bpy.data.objects[name]
        assert o.type == "LIGHT" and not o.hide_render, name + " must be an active light"
        report["before"][name] = state(o)
        if "power_w" in e:
            o.data.energy = e["power_w"]
        if "size" in e:
            o.data.size, o.data.size_y = e["size"]
        if "spread_deg" in e:
            o.data.spread = math.radians(e["spread_deg"])
        if "position" in e or "target" in e:
            # unspecified end keeps its current world value: derive the missing one from the light's current pose
            cur = o.matrix_world.translation
            facing = o.matrix_world.to_quaternion() @ Vector((0, 0, -1))
            pos = world(e["position"]) if "position" in e else cur
            tgt = world(e["target"]) if "target" in e else cur + facing
            aim(o, pos, tgt)
        bpy.context.view_layer.update()
        report["after"][name] = state(o)
    for spec in params.get("add", []):
        data = bpy.data.lights.new(spec["name"], "AREA")
        data.shape, data.size, data.size_y = "RECTANGLE", spec["size"][0], spec["size"][1]
        data.energy, data.color = spec["power_w"], spec.get("color", [1, 1, 1])
        if "spread_deg" in spec:
            data.spread = math.radians(spec["spread_deg"])
        o = bpy.data.objects.new(spec["name"], data)
        scene.collection.objects.link(o)
        aim(o, world(spec["position"]), world(spec["target"]))
        o.visible_camera = False
        bpy.context.view_layer.update()
        report["after"][spec["name"]] = state(o)
    return report
