import bpy
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'casio_f91w.blend'))
s=bpy.context.scene;s.camera=bpy.data.objects['CAM | Hero'];s.render.resolution_x=2048;s.render.resolution_y=4438;s.render.filepath=str(OUT/'hero.png')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
exec(compile((OUT/'validate.py').read_text(),str(OUT/'validate.py'),'exec'))
print('CASIO_REALISM_OUTPUTS_VALIDATED')
