"""Product-only GLB utility; production texture baking remains a later phase."""
import bpy

from .geometry.box import set_opened


def export_glb(path):
    set_opened(False)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.get("export_product") or obj.name in ("CTRL | Base", "CTRL | Lid lift-off"):
            obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                              export_apply=True, export_cameras=False, export_lights=False)
