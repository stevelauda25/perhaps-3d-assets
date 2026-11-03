"""Small geometry checks, run in Blender before any delivery is saved."""
import hashlib
import json
import bmesh
import bpy


def validate(config):
    report = {"components": {}, "blender": bpy.app.version_string,
              "assumptions": config["assumptions"]}
    product = [o for o in bpy.data.objects if o.get("export_product")]
    assert len(product) == 4, "Expected lid, base, collar, and tray floor"
    fingerprint = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in sorted(product, key=lambda o: o.name):
        assert tuple(obj.scale) == (1, 1, 1), obj.name + " has unapplied scale"
        assert all(abs(v) < 1e-8 for v in obj.rotation_euler), obj.name + " has unapplied rotation"
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        assert all(e.is_manifold for e in bm.edges), obj.name + " is not manifold"
        volume = bm.calc_volume(signed=True)
        assert volume > 0, obj.name + " has reversed normals or zero volume"
        bm.free()
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        assert all(e.is_manifold for e in bm.edges), obj.name + " bevel is not manifold"
        assert bm.calc_volume(signed=True) > 0, obj.name + " evaluated volume is invalid"
        bm.free()
        evaluated.to_mesh_clear()
        report["components"][obj.name] = {"vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons), "volume_mm3": round(volume * 1e9, 3),
            "manifold": True, "evaluated_manifold": True, "origin_m": list(obj.matrix_world.translation)}
        fingerprint.append({"name": obj.name, "vertices": [list(v.co) for v in obj.data.vertices],
                            "faces": [list(p.vertices) for p in obj.data.polygons]})
    report["mesh_sha256"] = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
    points = [o.matrix_world @ v.co for o in product for v in o.data.vertices]
    dimensions = [(max(p[i] for p in points) - min(p[i] for p in points))*1000 for i in range(3)]
    expected = [config["geometry_mm"][k] for k in ("width", "depth", "height")]
    assert all(abs(a-b) < 0.001 for a, b in zip(dimensions, expected)), (dimensions, expected)
    report["closed_bounds_mm"] = dimensions
    g = config["geometry_mm"]
    base = bpy.data.objects["Box | Base shell"]
    lid = bpy.data.objects["Box | Lid shell"]
    for i in range(4, 8):
        base_point = base.matrix_world @ base.data.vertices[i].co
        lid_point = lid.matrix_world @ lid.data.vertices[i].co
        assert abs((lid_point.z - base_point.z)*1000 - g["reveal"]) < 0.001, "Reveal is discontinuous"
        endpoint = g["base_front"] if i < 6 else g["base_rear"]
        assert abs(base_point.z*1000 - endpoint) < 0.001, "Seam endpoint differs from configuration"
    report["seam_mm"] = {"front": g["base_front"], "rear": g["base_rear"],
                         "vertical_reveal": g["reveal"], "continuous_corner_checks": True}
    report["nominal_collar_clearance_mm"] = g["collar_clearance"]
    report["tier"] = config["selected_tier"]
    report["tier_changes_geometry"] = False
    return report
