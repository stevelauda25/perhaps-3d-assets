import bpy, json
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'casio_f91w.blend'))
scene=bpy.context.scene
for o in bpy.data.objects:
 if o.name.startswith('LCD cell 1 '):
  for v in o.data.vertices:v.co.x-=1.7
 if o.name.startswith('LCD cell 0 ') and o.type=='MESH' and max(v.co.x for v in o.data.vertices)<0:
  for v in o.data.vertices:v.co.x-=.6
for m in bpy.data.materials:
 if m.node_tree:
  for n in m.node_tree.nodes:
   if n.type=='TEX_NOISE':n.inputs['Scale'].default_value=16000
   if n.type=='BUMP':n.inputs['Strength'].default_value=.30;n.inputs['Distance'].default_value=.000008
frame=bpy.data.objects.get('Buckle | black resin frame')
for v in frame.data.vertices:v.co.z+=1.4
text=bpy.data.objects.get('Buckle molded CASIO');text.data.extrude=.06;text.data.bevel_depth=.015
cams={'hero':'CAM | Hero','front':'CAM | Front','three_quarter':'CAM | Three-quarter','material_closeup':'CAM | Material macro'}
for name,cn in cams.items():
 c=bpy.data.objects[cn]
 if name!='front':
  target=Vector((0,-.002,.006) if name=='material_closeup' else ((0,-.002,.004) if name=='hero' else (0,-.018,0)))
  direction=(c.location-target).normalized();distance=c.data.ortho_scale*100/36;c.location=target+direction*distance;c.data.type='PERSP';c.data.lens=100
scene.render.resolution_x=2400;scene.render.resolution_y=2400;scene.cycles.samples=256
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
for name,cn in cams.items():
 scene.camera=bpy.data.objects[cn];scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['CAM | Hero'];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
print('FINAL_REFINEMENT_COMPLETE')
