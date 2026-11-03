"""Fingerprint approved product data and original camera presets, excluding materials."""
import hashlib
import json
import bpy


def values(block):
    result = {}
    for prop in block.bl_rna.properties:
        if prop.is_readonly or prop.type not in {"BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"}:
            continue
        value = getattr(block, prop.identifier)
        result[prop.identifier] = sorted(value) if isinstance(value, set) else (list(value) if getattr(prop, "is_array", False) else value)
    return result


def snapshot(names=None):
    if names is None:
        names = [o.name for o in bpy.data.collections["PRODUCT | Perhaps canonical box"].objects]
        names += [o.name for o in bpy.data.objects if o.type == "CAMERA"]
    result = {}
    for name in sorted(names):
        obj = bpy.data.objects[name]
        record = {"type": obj.type, "parent": obj.parent.name if obj.parent else None,
                  "matrix_basis": [list(row) for row in obj.matrix_basis],
                  "parent_inverse": [list(row) for row in obj.matrix_parent_inverse],
                  "modifiers": [values(m) for m in obj.modifiers]}
        if obj.type == "MESH":
            record["vertices"] = [list(v.co) for v in obj.data.vertices]
            record["faces"] = [list(p.vertices) for p in obj.data.polygons]
            record["face_settings"] = [(p.material_index, p.use_smooth) for p in obj.data.polygons]
        if obj.type == "CAMERA":
            record["camera"] = values(obj.data)
        result[name] = record
    return result


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def verify(expected):
    current = snapshot(expected.keys())
    changed = [name for name in expected if digest(expected[name]) != digest(current[name])]
    if changed:
        raise RuntimeError("Approved geometry/camera data changed: " + ", ".join(changed))
    return digest(current)
