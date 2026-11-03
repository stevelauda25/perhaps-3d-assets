"""Lighting-only Casio reference match. Modes: --preview, --final, --validate."""
import bpy, json, hashlib, sys, time, struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent
mode='validate' if '--validate' in sys.argv else 'final' if '--final' in sys.argv else 'preview'
source=P/'source-snapshot/casio_f91w_scene_match.blend'
dest=P/'casio_f91w_scene_match.blend'
bpy.ops.wm.open_mainfile(filepath=str(dest if mode=='validate' else P/'preview_scene.blend' if mode=='final' else source))
s=bpy.context.scene;D=bpy.data.objects;asset=bpy.data.collections['CASIO F-91W-1 | manufactured components']
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def val(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except:return str(v)
def fingerprints():
 objects={};materials={}
 for o in asset.objects:
  data={'type':o.type,'matrix':[list(r) for r in o.matrix_world],'materials':[m.name if m else None for m in getattr(o.data,'materials',[])]}
  if o.type=='MESH':data.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(f.vertices) for f in o.data.polygons])
  elif o.type in ['FONT','CURVE']:data.update(body=getattr(o.data,'body',''),extrude=o.data.extrude,bevel=o.data.bevel_depth,splines=[[[*p.co] for p in sp.points] for sp in o.data.splines])
  objects[o.name]=digest(data)
  for m in getattr(o.data,'materials',[]):
   if not m or m.name in materials:continue
   nodes=[]
   for n in m.node_tree.nodes:
    nd={'name':n.name,'type':n.bl_idname,'inputs':[(i.identifier,val(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]}
    for k in ['operation','attribute_name','feature','distance','noise_dimensions','normalize','interpolation_type','blend_type','clamp','object','image']:
     if hasattr(n,k):nd[k]=getattr(n,k).name if k in ['object','image'] and getattr(n,k) else val(getattr(n,k))
    if hasattr(n,'color_ramp'):nd['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
    nodes.append(nd)
   materials[m.name]=digest({'nodes':nodes,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]})
 return {'objects':objects,'materials':materials}
def aim(o,pos,target):o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,pos,target,power,w,h,color=(1,1,1)):
 o=D.get(name)
 if not o:
  d=bpy.data.lights.new(name,'AREA');o=D.new(name,d);D['Key | upper-left tall silk'].users_collection[0].objects.link(o)
 aim(o,pos,target);o.data.energy=power;o.data.shape='RECTANGLE';o.data.size=w;o.data.size_y=h;o.data.color=color
 return o
def points():
 dg=bpy.context.evaluated_depsgraph_get()
 return [o.evaluated_get(dg).matrix_world@Vector(v) for o in asset.objects if o.type in ['MESH','CURVE','FONT'] for v in o.evaluated_get(dg).bound_box]
def framing():
 uv=[world_to_camera_view(s,s.camera,p) for p in points()]
 return {'height':max(v.y for v in uv)-min(v.y for v in uv),'top':1-max(v.y for v in uv),'bottom':1-min(v.y for v in uv),'center_x':(max(v.x for v in uv)+min(v.x for v in uv))/2,'lens_mm':s.camera.data.lens}
def configure():
 (P/'baseline_fingerprints.json').write_text(json.dumps(fingerprints(),indent=2))
 s.render.resolution_x=2400;s.render.resolution_y=2872;s.render.resolution_percentage=100
 cam=D['CAM | Hero'];s.camera=cam;cam.data.lens=100;cam.data.shift_x=0;cam.data.shift_y=0
 pts=points();cx=(min(p.x for p in pts)+max(p.x for p in pts))/2;cz=(min(p.z for p in pts)+max(p.z for p in pts))/2
 distance=.5
 for _ in range(8):
  aim(cam,(cx,-distance,cz),(cx,0,cz));bpy.context.view_layer.update();distance*=framing()['height']/.655
 aim(cam,(cx,-distance,cz),(cx,0,cz));bpy.context.view_layer.update()
 f=framing();cam.data.shift_y=((1-f['top'])+(1-f['bottom']))/2-.6205
 cam.data.shift_x=(f['center_x']-.5)*2400/2872;bpy.context.view_layer.update()
 # Dark void, no room illumination or atmospheric effects.
 for n in s.world.node_tree.nodes:
  if n.type=='BACKGROUND':n.inputs['Strength'].default_value=0
 s.view_settings.exposure=-.65
 for o in s.objects:
  if o.type=='LIGHT':o.data.energy=0
 key=area('Key | upper-left tall silk',(.001,-.07,.095),(.001,0,.044),.0055,.003,.075,(.96,.98,1));key.data.spread=.11
 area('Fill | quiet frontal silk',(.025,-.13,.055),(0,0,.04),.035,.05,.055,(.96,.98,1))
 area('Rim | right vertical strip',(.05,-.025,.065),(0,0,.04),.055,.012,.055,(.96,.98,1))
 area('Upper band | edge strip',(-.045,-.025,.07),(0,0,.04),.045,.012,.055,(.96,.98,1))
 card=D['Studio | feathered diffusion reflection'];card.visible_camera=False;card.scale=(.10,.75,1);aim(card,(-.006,-.12,.13),(0,-.005,.045))
 for n in card.active_material.node_tree.nodes:
  if n.type=='MATH' and n.operation=='MULTIPLY' and abs(n.inputs[1].default_value-.65)<.001:n.inputs[1].default_value=.38
 floor=D['Studio | reflective black ground'];floor.location.z=-.0005
 m=floor.active_material;principled=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 for n in m.node_tree.nodes:
  if n.type=='MAP_RANGE' and n.inputs['To Min'].default_value>0 and n.inputs['To Min'].default_value<.2:
   n.inputs['To Min'].default_value=.15;n.inputs['To Max'].default_value=.21
  if n.type=='MAP_RANGE' and n.inputs['To Min'].default_value==1 and n.inputs['To Max'].default_value==0:n.inputs['From Max'].default_value=.28
 principled.inputs['Base Color'].default_value=(.001,.0012,.0014,1)
 area('Ground | grazing horizontal glow',(0,.022,.001),(0,.002,-.0005),.00005,.13,.0008,(.86,.91,.93))
 red=area('Accent | shielded lower red',(.004,-.005,.002),(.004,.017,.0005),.00012,.012,.0005,(1,.008,.002))
 # Narrow emitter spread confines the accent to the underside, away from the face.
 red.data.spread=.55
 assert fingerprints()==json.loads((P/'baseline_fingerprints.json').read_text())
 (P/'framing.json').write_text(json.dumps(framing(),indent=2))
def settings(final):
 s.render.engine='CYCLES';s.cycles.samples=1536 if final else 128;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.0007 if final else .015;s.cycles.use_denoising=True;s.cycles.seed=42
 s.cycles.max_bounces=16;s.cycles.transmission_bounces=12;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_percentage=100
 s.render.resolution_x=2400 if final else 804;s.render.resolution_y=2872 if final else 962
 s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='16';s.render.film_transparent=False
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
  for d in prefs.devices:d.use=True
  s.cycles.device='GPU'
 except Exception:s.cycles.device='CPU'
if mode=='validate':
 assert fingerprints()==json.loads((P/'baseline_fingerprints.json').read_text()),'Product changed'
 root=D['F-91W-1 | SI scale'];inv=root.matrix_world.inverted();dg=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in asset.objects:
  if o.type=='MESH' and o.name.startswith(('Case |','Bezel |','Crystal |','Pusher','Gasket','Caseback |','Screw cross','Recessed lug')):
   e=o.evaluated_get(dg);pts.extend(inv@e.matrix_world@Vector(v) for v in e.bound_box)
 bounds=[round(max(v[i] for v in pts)-min(v[i] for v in pts),3) for i in range(3)];assert bounds==[35.2,38.2,8.5]
 data=(P/'hero.png').read_bytes();assert struct.unpack('>II',data[16:24])==(2400,2872) and data[24]==16
 fonts={f.name:bool(f.packed_file) for f in bpy.data.fonts if f.filepath and f.filepath!='<builtin>'};assert all(fonts.values())
 report={'geometry_and_product_shaders_unchanged':True,'case_bounds_mm':bounds,'packed_fonts':fonts,'framing':framing(),'samples':s.cycles.samples,'engine':s.render.engine,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'lights':[{'name':o.name,'watts':o.data.energy,'position':list(o.location),'size':[o.data.size,o.data.size_y]} for o in s.objects if o.type=='LIGHT'],'blend_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'hero_sha256':hashlib.sha256(data).hexdigest()}
 (P/'validation.json').write_text(json.dumps(report,indent=2));print('VALIDATED',bounds,flush=True)
else:
 if mode=='preview':configure()
 final=mode=='final';settings(final);name='hero' if final else 'preview'
 if not final:bpy.ops.wm.save_as_mainfile(filepath=str(P/'preview_scene.blend'))
 s.render.filepath=str(P/(name+'.png'));t=time.monotonic();bpy.ops.render.render(write_still=True);elapsed=round(time.monotonic()-t,2)
 (P/(name+'_time.json')).write_text(json.dumps({'render_seconds':elapsed}));print('RENDER_DONE',name,elapsed,flush=True)
 if final:bpy.ops.wm.save_as_mainfile(filepath=str(dest))
