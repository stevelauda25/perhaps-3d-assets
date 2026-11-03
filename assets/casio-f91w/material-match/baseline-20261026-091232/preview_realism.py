import bpy,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'previous-upright/casio_f91w.blend'))
exec(compile((OUT/'realism_refine.py').read_text(),str(OUT/'realism_refine.py'),'exec'))
s=bpy.context.scene;s.cycles.samples=80;s.cycles.adaptive_threshold=.02
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'realism_preview.blend'))
for name,cam,w,h in [('macro','CAM | Material macro',1300,1300),('hero','CAM | Hero',804,1742)]:
 s.camera=bpy.data.objects[cam];s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(OUT/('realism_'+name+'_preview.png'));bpy.ops.render.render(write_still=True)
print('REALISM_PREVIEWS_COMPLETE')
