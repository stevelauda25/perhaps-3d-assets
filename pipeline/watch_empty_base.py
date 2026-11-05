"""Blender script: empty input scene for watch jobs that bring their own kit (no studio, no objects).

    blender -b --factory-startup --python pipeline/watch_empty_base.py -- assets/watches/baseline/empty_base.blend

.blend files are not in git, so run this once on a new machine before the Seiko jobs.
"""
import sys

import bpy

out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.context.scene.render.engine = "CYCLES"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("EMPTY BASE", out, len(bpy.data.objects), "objects")
