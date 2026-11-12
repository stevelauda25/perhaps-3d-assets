"""delete_objects: remove named objects (and their meshes) from the scene, e.g. a part a later version drops.

Params: names (list). Fails if a name is missing.
"""


def run(params):
    import bpy
    missing = [n for n in params["names"] if n not in bpy.data.objects]
    assert not missing, "no object %s" % missing
    for n in params["names"]:
        o = bpy.data.objects[n]
        data = o.data
        bpy.data.objects.remove(o)
        if data is not None and not data.users:
            bpy.data.meshes.remove(data)
    return {"removed": params["names"]}
