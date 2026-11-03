import bpy
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'realism_preview.blend'))
m=bpy.data.materials['12 | Clear acrylic resin crystal • IOR 1.49'];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for l in list(m.node_tree.links):
 if l.to_node==p and l.to_socket.name=='Roughness':m.node_tree.links.remove(l)
p.inputs['Roughness'].default_value=.008
s=bpy.context.scene;s.camera=bpy.data.objects['CAM | Hero'];s.cycles.samples=512;s.cycles.adaptive_threshold=.004;s.render.resolution_x=2048;s.render.resolution_y=4438;s.render.image_settings.color_depth='16';s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.30;s.render.border_max_x=.71;s.render.border_min_y=.52;s.render.border_max_y=.70;s.render.filepath=str(OUT/'hero_face_test.png');bpy.ops.render.render(write_still=True)
s.render.use_border=False;s.render.resolution_x=804;s.render.resolution_y=1742;s.cycles.samples=256;s.render.filepath=str(OUT/'realism_hero_preview.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'realism_preview.blend'));print('HERO_CLEAR_CRYSTAL_TEST_COMPLETE')
