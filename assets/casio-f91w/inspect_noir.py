import bpy,json,os
from pathlib import Path
OUT=Path(__file__).resolve().parent
r={'file':bpy.data.filepath,'version':bpy.app.version_string,'scenes':[],'materials':[],'images':[]}
def val(v):
 try:return list(v)
 except:return v
for s in bpy.data.scenes:
 d={'name':s.name,'engine':s.render.engine,'camera':s.camera.name if s.camera else None,'resolution':[s.render.resolution_x,s.render.resolution_y],'exposure':s.view_settings.exposure,'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'compositor':s.use_nodes,'units':s.unit_settings.scale_length,'objects':[]}
 for o in s.objects:
  x={'name':o.name,'type':o.type,'dimensions':list(o.dimensions),'location':list(o.location)}
  if o.type=='LIGHT':x.update({'power':o.data.energy,'shape':getattr(o.data,'shape',None),'size':getattr(o.data,'size',None),'size_y':getattr(o.data,'size_y',None)})
  if o.type=='CAMERA':x.update({'lens':o.data.lens,'dof':o.data.dof.use_dof})
  d['objects'].append(x)
 r['scenes'].append(d)
for m in bpy.data.materials:
 if m.node_tree:r['materials'].append({'name':m.name,'nodes':[{'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked}} for n in m.node_tree.nodes],'links':[(a.from_node.type,a.from_socket.name,a.to_node.type,a.to_socket.name) for a in m.node_tree.links]})
for i in bpy.data.images:r['images'].append({'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'exists':os.path.exists(bpy.path.abspath(i.filepath))})
(OUT/'noir_reference_inspection.json').write_text(json.dumps(r,indent=2,default=str))
s=bpy.data.scenes.get('NOIR | Product Studio') or bpy.context.scene;bpy.context.window.scene=s
s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100;s.cycles.samples=48;s.cycles.use_denoising=True
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
 for d in p.devices:d.use=True
 s.cycles.device='GPU'
except:pass
s.render.filepath=str(OUT/'noir_reference_preview.png');bpy.ops.render.render(write_still=True)
print('REFERENCE_INSPECTION_COMPLETE')
