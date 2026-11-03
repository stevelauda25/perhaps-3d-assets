import bpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'casio_f91w.blend'))
s=bpy.context.scene
for name,pos,target in [('front',(.0018,-.42,.036),(.0018,.010,.036)),('three_quarter',tuple(Vector((.0018,.015,.036))+Vector((.18,-.29,.025)).normalized()*.46),(.0018,.015,.036))]:
 cam=bpy.data.objects['CAM | Front' if name=='front' else 'CAM | Three-quarter'];cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
for name,cam in [('front','CAM | Front'),('three_quarter','CAM | Three-quarter')]:
 s.camera=bpy.data.objects[cam];s.render.resolution_x=2400;s.render.resolution_y=2400;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['CAM | Hero'];s.render.resolution_x=2048;s.render.resolution_y=4438;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
exec(compile((OUT/'validate.py').read_text(),str(OUT/'validate.py'),'exec'))
print('UPRIGHT_ALL_OUTPUTS_VALIDATED')
