import bpy,math
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'casio_f91w.blend'))
o=bpy.data.objects['Perforated band | flexible tapered resin']
for v in o.data.vertices:
 if -v.co.y>123:
  t=min(1,max(0,(-v.co.y-123)/3));old=7.65-1.45*t;new=4.65+3*math.sqrt(max(0,1-t*t));v.co.x*=new/old
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
s=bpy.context.scene
for name,cam in [('front','CAM | Front'),('three_quarter','CAM | Three-quarter')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['CAM | Hero'];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
exec(compile((OUT/'validate.py').read_text(),str(OUT/'validate.py'),'exec'))
print('FINAL_PACK_VALIDATE_COMPLETE')
