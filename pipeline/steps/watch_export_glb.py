"""watch_export_glb: export the objects tagged `export_product` as one GLB (modifiers applied, images embedded).

Params: glb (path from the project root, inside the job's output folder). Returns the file name as a stage output.
"""
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]


def run(params):
    dest = ROOT / params["glb"]
    bpy.ops.object.select_all(action="DESELECT")
    chosen = [o for o in bpy.data.objects if o.get("export_product")]
    for o in chosen:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(dest), export_format="GLB", use_selection=True, export_apply=True,
                              export_cameras=False, export_lights=False, export_yup=True)
    return {"outputs": [dest.name], "objects": len(chosen), "bytes": dest.stat().st_size}
