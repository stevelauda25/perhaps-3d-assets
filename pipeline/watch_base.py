"""Blender script: lean watch studio base = the Casio F-91W scene without the watch.

    blender -b --factory-startup --python pipeline/watch_base.py -- assets/casio-f91w/casio_f91w.blend OUT.blend

Keeps the Casio upright studio exactly as is (collection `STUDIO | cameras and softboxes`: ground, softboxes,
reflection card, 4 cameras; near-black world; AgX / 16 bounces). Deletes the watch collection and every datablock
only it used. The source file is opened and never saved. Source md5 697c36af1d0d4f070e4889ff119e11b9.
"""
import sys

import bpy

src, out = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=src, load_ui=False, use_scripts=False)
watch = bpy.data.collections["CASIO F-91W-1 | manufactured components"]
for o in list(watch.objects):
    bpy.data.objects.remove(o)
bpy.data.collections.remove(watch)
for _ in range(3):  # recursive purge: meshes/curves/fonts/materials only the watch used
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("BASE", {k: len(getattr(bpy.data, k)) for k in ("objects", "meshes", "materials", "lights", "cameras", "fonts", "curves")})
