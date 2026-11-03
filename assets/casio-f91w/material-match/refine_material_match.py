"""Incremental lookdev; loads the immutable snapshot, never reconstructs the watch.
Modes: --diagnose, --studio, --final, --validate. Run through Blender background.
"""
import bpy,math,json,sys,time,hashlib,struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent
BASE=Path(json.loads((P/'baseline.json').read_text())['directory'])/'casio_f91w.blend'
mode=next((x for x in ['diagnose','correct','studio','final','validate'] if '--'+x in sys.argv),'diagnose')
bpy.ops.wm.open_mainfile(filepath=str(BASE if mode=='diagnose' else P/('casio_f91w.blend' if mode=='validate' else 'material_candidate.blend')))
s=bpy.context.scene;D=bpy.data.objects;root=D['F-91W-1 | SI scale'];asset=bpy.data.collections['CASIO F-91W-1 | manufactured components']
def mat(prefix):return next(m for m in bpy.data.materials if m.name.startswith(prefix))
def bsdf(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def aim(o,pos,target):o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def gpu():
 try:
  p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices()
  for d in p.devices:d.use=True
  s.cycles.device='GPU'
 except Exception:s.cycles.device='CPU'
def render(name,cam,w,h,samples=128,border=None,denoise=True):
 s.camera=D[cam];s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
 s.cycles.samples=samples;s.cycles.adaptive_threshold=.004 if samples>=512 else .01;s.cycles.seed=42;s.cycles.use_denoising=denoise
 s.render.image_settings.file_format='PNG';s.render.image_settings.color_depth='16';s.render.use_border=bool(border);s.render.use_crop_to_border=bool(border)
 if border:s.render.border_min_x,s.render.border_max_x,s.render.border_min_y,s.render.border_max_y=border
 s.render.filepath=str(P/(name+'.png'));t=time.monotonic();bpy.ops.render.render(write_still=True);dt=round(time.monotonic()-t,2)
 print('RENDER_DONE',name,dt,flush=True);return dt
def snapshot_geometry():
 result={}
 for o in asset.objects:
  value={'type':o.type,'matrix':[list(r) for r in o.matrix_world]}
  if o.type=='MESH':value.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(f.vertices) for f in o.data.polygons])
  elif o.type in ['CURVE','FONT']:
   value.update(body=getattr(o.data,'body',''),extrude=o.data.extrude,bevel=o.data.bevel_depth,splines=[[[*p.co] for p in sp.points] for sp in o.data.splines])
  result[o.name]=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
 return result
def molding_mask(o):
 # Per-vertex bend/edge mask affects shaders only, never positions or topology.
 me=o.data;me.update();normals=[[] for v in me.vertices];neighbors=[set() for v in me.vertices]
 for poly in me.polygons:
  for i in poly.vertices:normals[i].append(poly.normal.copy())
 for edge in me.edges:
  a,b=edge.vertices;neighbors[a].add(b);neighbors[b].add(a)
 values=[]
 for ns in normals:
  mean=sum(ns,Vector()).normalized() if ns else Vector((0,0,1));bend=max((1-n.dot(mean) for n in ns),default=0)
  values.append(min(1,max(0,(bend-.003)*15)))
 for _ in range(2):values=[(.5*v+.5*sum(values[j] for j in neighbors[i])/len(neighbors[i])) if neighbors[i] else v for i,v in enumerate(values)]
 a=me.attributes.get('mold_edge') or me.attributes.new('mold_edge','FLOAT','POINT')
 for d,v in zip(a.data,values):d.value=v
def resin_shader(m,spacing,fine_spacing,rough,color,depth):
 # Rounded Voronoi mounds form the mold texture; independent fields vary gloss.
 nt=m.node_tree;n=nt.nodes;l=nt.links;p=bsdf(m)
 for node in list(n):
  if node not in [p] and node.type!='OUTPUT_MATERIAL':n.remove(node)
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=0;p.inputs['IOR'].default_value=1.49;p.inputs['Specular IOR Level'].default_value=.5;p.inputs['Coat Weight'].default_value=0;p.inputs['Sheen Weight'].default_value=0
 def mathnode(kind,a,b=None,label=''):
  q=n.new('ShaderNodeMath');q.operation=kind;q.label=label
  for i,v in enumerate([a,b]):
   if v is None:continue
   if isinstance(v,(int,float)):q.inputs[i].default_value=v
   else:l.new(v,q.inputs[i])
  return q.outputs[0]
 coords=n.new('ShaderNodeTexCoord');coords.object=root
 units=n.new('ShaderNodeVectorMath');units.operation='SCALE';units.inputs['Scale'].default_value=.001;l.new(coords.outputs['Object'],units.inputs[0]);units.label='Millimeters to physical meters'
 vor=n.new('ShaderNodeTexVoronoi');vor.distance='EUCLIDEAN';vor.feature='SMOOTH_F1';vor.inputs['Scale'].default_value=1/spacing;vor.inputs['Smoothness'].default_value=.35;l.new(units.outputs['Vector'],vor.inputs['Vector']);vor.label='Rounded molded grain'
 square=mathnode('MULTIPLY',vor.outputs['Distance'],vor.outputs['Distance']);hill=mathnode('EXPONENT',mathnode('MULTIPLY',square,-8))
 fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=1/fine_spacing;fine.inputs['Detail'].default_value=1;fine.inputs['Roughness'].default_value=.5;l.new(units.outputs['Vector'],fine.inputs['Vector']);fine.label='Secondary fine mold finish'
 height=mathnode('ADD',mathnode('MULTIPLY',hill,.70),mathnode('MULTIPLY',fine.outputs['Fac'],.30))
 attr=n.new('ShaderNodeAttribute');attr.attribute_name='mold_edge';attr.label='Slightly smoother molded edge transitions'
 strength=mathnode('SUBTRACT',.65,mathnode('MULTIPLY',attr.outputs['Fac'],.16))
 bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=depth;l.new(strength,bump.inputs['Strength']);l.new(height,bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 roughfield=n.new('ShaderNodeTexNoise');roughfield.inputs['Scale'].default_value=1600;roughfield.inputs['Detail'].default_value=1.3;roughfield.inputs['Roughness'].default_value=.55;l.new(units.outputs['Vector'],roughfield.inputs['Vector']);roughfield.label='Independent submillimeter gloss variation'
 centered=mathnode('SUBTRACT',roughfield.outputs['Fac'],.5);roughval=mathnode('ADD',rough,mathnode('MULTIPLY',centered,.08))
 # Small uncorrelated cell-to-cell finish variation, not pigment mottling.
 sep=n.new('ShaderNodeSeparateColor');l.new(vor.outputs['Color'],sep.inputs[0]);roughval=mathnode('ADD',roughval,mathnode('MULTIPLY',mathnode('SUBTRACT',sep.outputs[0],.5),.035))
 roughval=mathnode('SUBTRACT',roughval,mathnode('MULTIPLY',attr.outputs['Fac'],.018));l.new(roughval,p.inputs['Roughness'])
 m['material_match']={'mold_spacing_m':spacing,'fine_spacing_m':fine_spacing,'height_bound_m':depth*.65,'roughness_mean':rough}
def materials():
 for o in asset.objects:
  if o.type=='MESH' and any(m and m.name.startswith(('01 |','02 |')) for m in o.data.materials):molding_mask(o)
 resin_shader(mat('01 |'),.00012,.000045,.53,(.006,.0065,.0072),.000006)
 resin_shader(mat('02 |'),.00014,.000060,.59,(.0045,.005,.0055),.000007)
 p=bsdf(mat('08 |'));p.inputs['Base Color'].default_value=(.28,.30,.245,1);p.inputs['Roughness'].default_value=.38;p.inputs['Specular IOR Level'].default_value=.20
 p=bsdf(mat('09 |'));p.inputs['Base Color'].default_value=(.003,.004,.0033,1);p.inputs['Roughness'].default_value=.42;p.inputs['Specular IOR Level'].default_value=.18
 # Keep the actual acrylic slab and refractive index, soften only microfacets.
 p=bsdf(mat('12 |'));p.inputs['Roughness'].default_value=.014;p.inputs['IOR'].default_value=1.49
 m=mat('11 |');p=bsdf(m);nt=m.node_tree
 for link in list(nt.links):
  if link.to_node==p and link.to_socket.name in ['Normal','Roughness']:nt.links.remove(link)
 p.inputs['Metallic'].default_value=1;p.inputs['Roughness'].default_value=.14
 tex=next(n for n in nt.nodes if n.type=='TEX_NOISE');tex.inputs['Scale'].default_value=140000;tex.inputs['Detail'].default_value=1
 ramp=next(n for n in nt.nodes if n.type=='MAP_RANGE');ramp.inputs['To Min'].default_value=.12;ramp.inputs['To Max'].default_value=.16;nt.links.new(ramp.outputs['Result'],p.inputs['Roughness'])
 root['material_match']='Independent rounded mold grain, fine finish and roughness fields; shader-only edge masks; darker LCD electrodes; polished metal micro-roughness.'
def fit_camera(name,occupancy,w,h):
 cam=D[name];s.camera=cam;s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
 dg=bpy.context.evaluated_depsgraph_get();pts=[o.evaluated_get(dg).matrix_world@Vector(v) for o in asset.objects if o.type in ['MESH','CURVE','FONT'] for v in o.evaluated_get(dg).bound_box]
 lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);target=(lo+hi)*.5
 direction=cam.rotation_euler.to_quaternion()@Vector((0,0,-1));distance=(cam.location-target).length
 for _ in range(8):
  cam.location=target-direction*distance;bpy.context.view_layer.update();uv=[world_to_camera_view(s,cam,p) for p in pts];height=max(v.y for v in uv)-min(v.y for v in uv);width=max(v.x for v in uv)-min(v.x for v in uv)
  distance*=max(height/occupancy,width/.9)
 cam.location=target-direction*distance;bpy.context.view_layer.update()
 uv=[world_to_camera_view(s,cam,p) for p in pts];cx=(max(v.x for v in uv)+min(v.x for v in uv))/2;cy=(max(v.y for v in uv)+min(v.y for v in uv))/2
 cam.data.shift_x+=(cx-.5)*w/h;cam.data.shift_y+=cy-.5
 return {'height_fraction':round(max(v.y for v in uv)-min(v.y for v in uv),4),'width_fraction':round(max(v.x for v in uv)-min(v.x for v in uv),4),'focal_length_mm':cam.data.lens}
def studio():
 # Neutral transform preserves shadow detail; the lighting still establishes blacks.
 looks=[i.identifier for i in s.view_settings.bl_rna.properties['look'].enum_items]
 neutral=next((x for x in looks if x.lower() in ['none','agx - none','agx - base contrast']),None)
 try:s.view_settings.look=neutral
 except TypeError as error:
  # Blender's static RNA omits dynamic OCIO look names; the error lists them.
  import ast
  available=ast.literal_eval(str(error).split('not found in ')[-1])
  s.view_settings.look=next(x for x in available if x.lower() in ['none','agx - none','agx - base contrast'])
 s.view_settings.exposure=-.3
 key=D['Key | upper-left tall silk'];aim(key,(-.105,-.11,.125),(0,0,.045));key.data.energy=.65;key.data.size=.045;key.data.size_y=.12
 D['Fill | quiet frontal silk'].data.energy=.15;D['Rim | right vertical strip'].data.energy=.085;D['Upper band | edge strip'].data.energy=.045
 data=bpy.data.lights.new('Lower strap | restrained fill','AREA');data.energy=.035;data.shape='RECTANGLE';data.size=.06;data.size_y=.09
 light=D.new(data.name,data);key.users_collection[0].objects.link(light);aim(light,(.075,-.09,.025),(0,0,.018))
 framing={'hero':fit_camera('CAM | Hero',.80,2048,4438),'front':fit_camera('CAM | Front',.85,2400,2400)}
 (P/'framing.json').write_text(json.dumps(framing,indent=2))
 root['material_match_studio']=True
def settings():
 s.cycles.samples=512;s.cycles.adaptive_threshold=.004;s.cycles.max_bounces=16;s.cycles.transmission_bounces=12;s.cycles.use_denoising=True;s.render.image_settings.color_depth='16';s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_percentage=100
gpu()
if mode=='diagnose':
 (P/'baseline_geometry.json').write_text(json.dumps(snapshot_geometry(),indent=2))
 crop=(.16,.50,.70,.95);strap=(.36,.65,.73,.90)
 render('baseline_case_crop','CAM | Material macro',2400,2400,128,crop)
 render('baseline_strap_crop','CAM | Front',2400,2400,128,strap)
 materials()
 assert snapshot_geometry()==json.loads((P/'baseline_geometry.json').read_text())
 render('candidate_case_crop','CAM | Material macro',2400,2400,128,crop)
 render('candidate_case_raw','CAM | Material macro',2400,2400,128,crop,False)
 render('candidate_strap_crop','CAM | Front',2400,2400,128,strap)
 settings();bpy.ops.wm.save_as_mainfile(filepath=str(P/'material_candidate.blend'))
elif mode in ['correct','studio']:
 if mode=='correct':
  materials()
  render('candidate_case_crop','CAM | Material macro',2400,2400,128,(.16,.50,.70,.95))
  render('candidate_case_raw','CAM | Material macro',2400,2400,128,(.16,.50,.70,.95),False)
  render('candidate_strap_crop','CAM | Front',2400,2400,128,(.36,.65,.73,.90))
 if not root.get('material_match_studio'):studio()
 aim(D['Lower strap | restrained fill'],(.075,-.09,.025),(0,0,.018))
 settings();bpy.ops.wm.save_as_mainfile(filepath=str(P/'material_candidate.blend'))
 render('front_preview','CAM | Front',1200,1200,128)
 render('material_preview','CAM | Material macro',1600,1600,128)
elif mode=='final':
 settings();times={}
 for name,cam,w,h in [('hero','CAM | Hero',2048,4438),('front','CAM | Front',2400,2400),('material_closeup','CAM | Material macro',2400,2400)]:times[name]=render(name,cam,w,h,512)
 settings();s.camera=D['CAM | Hero'];s.render.resolution_x=2048;s.render.resolution_y=4438;s.render.filepath=str(P/'hero.png')
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'casio_f91w.blend'));(P/'render_times.json').write_text(json.dumps(times,indent=2))
elif mode=='validate':
 baseline=json.loads((P/'baseline_geometry.json').read_text());assert snapshot_geometry()==baseline,'Manufactured geometry or graphics changed'
 dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted();pts=[]
 for o in asset.objects:
  if o.type=='MESH' and o.name.startswith(('Case |','Bezel |','Crystal |','Pusher','Gasket','Caseback |','Screw cross','Recessed lug')):
   e=o.evaluated_get(dg);pts.extend(inv@e.matrix_world@Vector(v) for v in e.bound_box)
 bounds=[round(max(v[i] for v in pts)-min(v[i] for v in pts),3) for i in range(3)];assert bounds==[35.2,38.2,8.5],bounds
 images={}
 for name,expected in [('hero',(2048,4438)),('front',(2400,2400)),('material_closeup',(2400,2400))]:
  data=(P/(name+'.png')).read_bytes();wh=struct.unpack('>II',data[16:24]);assert wh==expected and data[24]==16
  images[name]={'resolution':wh,'bit_depth':data[24],'sha256':hashlib.sha256(data).hexdigest()}
 fonts={f.name:bool(f.packed_file) for f in bpy.data.fonts if f.filepath and f.filepath!='<builtin>'};assert all(fonts.values())
 assert s.cycles.samples>=512 and s.render.engine=='CYCLES'
 report={'blender':bpy.app.version_string,'unchanged_manufactured_objects':len(baseline),'case_bounds_mm':bounds,'packed_fonts':fonts,'images':images,'samples':s.cycles.samples,'look':s.view_settings.look,'framing':json.loads((P/'framing.json').read_text()),'render_seconds':json.loads((P/'render_times.json').read_text()),'blend_sha256':hashlib.sha256((P/'casio_f91w.blend').read_bytes()).hexdigest()}
 (P/'validation.json').write_text(json.dumps(report,indent=2));print('VALIDATED',bounds,len(baseline),flush=True)
print('MATERIAL_MATCH_DONE',mode,flush=True)
