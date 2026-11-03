"""Incremental refinement of the recovered scene; never runs build.py.
Blender --background --disable-autoexec --python refine_photography.py [-- --final]
Default: save candidate and render focused previews. --final: render saved candidate.
Verified graphic contours are traced from the existing official F-91W-1_06.jpg.
"""
import bpy, json, math, sys, time
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
BASE=P/'backup-20261026-083440/casio_f91w.blend1'
FINAL='--final' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(P/'photography_candidate.blend' if FINAL else BASE))
s=bpy.context.scene;D=bpy.data.objects;root=D['F-91W-1 | SI scale']
asset=bpy.data.collections['CASIO F-91W-1 | manufactured components']
def principled(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def remove(o):bpy.data.objects.remove(o,do_unlink=True)
def flatcurve(name,paths,mat,z):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='2D';c.resolution_u=2;c.fill_mode='BOTH';c.extrude=0;c.bevel_depth=0
 for pts in paths:
  sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
  for q,(x,y) in zip(sp.points,pts):q.co=(x,y,0,1)
  sp.use_cyclic_u=True
 o=D.new(name,c);asset.objects.link(o);o.parent=root;o.location.z=z;c.materials.append(mat);return o
def aim(o,pos,target):o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
if not FINAL:
 # Root-local coordinates measured in meters: micrograin follows the watch pose.
 for prefix,rough,scale,depth,color in [('01 |',.455,14500,0.000010,(.009,.010,.012)),('02 |',.515,11500,0.000012,(.007,.008,.009))]:
  m=next(m for m in bpy.data.materials if m.name.startswith(prefix));n=m.node_tree.nodes;l=m.node_tree.links;p=principled(m)
  p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=0;p.inputs['IOR'].default_value=1.49;p.inputs['Specular IOR Level'].default_value=.5
  tex=next(q for q in n if q.type=='TEX_NOISE');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=1.5;tex.inputs['Roughness'].default_value=.6
  tc=n.new('ShaderNodeTexCoord');tc.object=root;tc.label='Stable molded grain coordinates'
  unit=n.new('ShaderNodeVectorMath');unit.operation='SCALE';unit.inputs['Scale'].default_value=.001;unit.label='Native millimeters to meters'
  l.new(tc.outputs['Object'],unit.inputs[0]);l.new(unit.outputs['Vector'],tex.inputs['Vector'])
  ramp=next(q for q in n if q.type=='MAP_RANGE');ramp.inputs['To Min'].default_value=rough-.065;ramp.inputs['To Max'].default_value=rough+.065
  bump=next(q for q in n if q.type=='BUMP');bump.inputs['Strength'].default_value=.38;bump.inputs['Distance'].default_value=depth
  m['grain_spacing_m']=1/scale;m['height_bound_m']=depth*.38
 # Closed, continuous ink outlines remove coplanar disk/quad overlaps at joins.
 for o in list(asset.objects):
  if o.name in ['Print | cobalt perimeter','Print | white perimeter','Print | LCD aperture keyline','Print | WR shield']:
   me=o.data;faces=[f for f in me.polygons if len(f.vertices)==4]
   outside=[];inside=[]
   for f in faces:
    a,b,c,d=[me.vertices[i].co.copy() for i in f.vertices];outside.append((a.x,a.y));inside.append((b.x,b.y))
   ma=me.materials[0];name=o.name;remove(o);flatcurve(name,[outside,list(reversed(inside))],ma,7.995)
 # Correct the faceted acrylic sidewall while retaining the cap dimensions.
 crystal=D['Crystal | solid molded acrylic']
 for f in crystal.data.polygons:f.use_smooth=len(f.vertices)==4
 for mod in crystal.modifiers:
  if mod.type=='BEVEL':mod.segments=8;mod.harden_normals=True
  if mod.type=='WEIGHTED_NORMAL':mod.keep_sharp=True;mod.weight=50
 glass=crystal.data.materials[0];p=principled(glass)
 for link in list(glass.node_tree.links):
  if link.to_node==p and link.to_socket.name=='Roughness':glass.node_tree.links.remove(link)
 p.inputs['Roughness'].default_value=.012;p.inputs['IOR'].default_value=1.49
 # Extracted outlines contain silhouette only: no photographic shading is baked in.
 colors={k:next(m for m in bpy.data.materials if m.name.startswith(v)) for k,v in [('white','04 |'),('yellow','06 |'),('red','07 |'),('lcd','09 |')]}
 for name,info in json.loads((P/'verified_graphics_contours.json').read_text()).items():
  for o in list(asset.objects):
   match=o.name==name or (name=='CASIO' and o.name.startswith('Print | CASIO')) or (name=='signal' and o.name.startswith('LCD electrode | signal')) or (name=='bell' and o.name.startswith(('LCD electrode | bell','LCD electrode | clapper')))
   if match:remove(o)
  paths=[[(info['x']+x*info['w'],info['y']+y*info['h']) for x,y in path] for path in info['contours']]
  flatcurve('Verified print | '+name,paths,colors[info['color']],7.565 if info['color']=='lcd' else 7.995)
 # Broader LCD electrodes with softly clipped manufactured corners, no extrusion.
 for o in asset.objects:
  if not o.name.startswith('LCD electrode | ') or o.type!='MESH' or 'colon' in o.name:continue
  vs=[v.co.copy() for v in o.data.vertices]
  if not vs:continue
  minx=min(v.x for v in vs);maxx=max(v.x for v in vs);miny=min(v.y for v in vs);maxy=max(v.y for v in vs)
  cx=(minx+maxx)/2;cy=(miny+maxy)/2;horizontal=maxx-minx>maxy-miny
  pts=[Vector((cx+(v.x-cx)*(1 if horizontal else 1.16),cy+(v.y-cy)*(1.16 if horizontal else 1),v.z)) for v in vs]
  rounded=[]
  for i,b in enumerate(pts):
   a=pts[i-1];c=pts[(i+1)%len(pts)];radius=min(.055,(a-b).length*.12,(c-b).length*.12)
   rounded.extend([tuple(b+(a-b).normalized()*radius),tuple(b+(c-b).normalized()*radius)])
  me=bpy.data.meshes.new(o.name+' refined');me.from_pydata(rounded,[],[tuple(range(len(rounded)))]);me.materials.append(o.data.materials[0]);o.data=me
 lcd=next(m for m in bpy.data.materials if m.name.startswith('08 |'));p=principled(lcd);p.inputs['Base Color'].default_value=(.30,.325,.29,1);p.inputs['Roughness'].default_value=.34
 # Wide overhead silk and restrained fill reveal molded grain without luminous rims.
 key=D['Key | upper-left tall silk'];aim(key,(-.085,-.125,.135),(0,0,.045));key.data.energy=.62;key.data.size=.065;key.data.size_y=.13
 fill=D['Fill | quiet frontal silk'];fill.data.energy=.105;fill.data.size=.09;fill.data.size_y=.13
 rim=D['Rim | right vertical strip'];rim.data.energy=.115;rim.data.size=.025
 D['Upper band | edge strip'].data.energy=.04
 # A low-luminance silk panel gives a feathered reflection instead of a clipped
 # rectangle across the face. Its UV luminance falls smoothly to zero at edges.
 me=bpy.data.meshes.new('Diffusion silk panel');me.from_pydata([(-.045,-.08,0),(.045,-.08,0),(.045,.08,0),(-.045,.08,0)],[],[(0,1,2,3)])
 uv=me.uv_layers.new()
 for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=co
 card=D.new('Studio | feathered diffusion reflection',me);key.users_collection[0].objects.link(card);aim(card,(-.08,-.16,.105),(0,0,.045))
 m=bpy.data.materials.new('Studio | silk luminance falloff');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
 coord=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs['UV'],sep.inputs[0]);axes=[]
 def op(kind,a,b=None):
  q=n.new('ShaderNodeMath');q.operation=kind
  if isinstance(a,(int,float)):q.inputs[0].default_value=a
  else:l.new(a,q.inputs[0])
  if b is not None:
   if isinstance(b,(int,float)):q.inputs[1].default_value=b
   else:l.new(b,q.inputs[1])
  return q.outputs[0]
 for axis in [sep.outputs['X'],sep.outputs['Y']]:
  v=op('SUBTRACT',op('MULTIPLY',axis,2),1);fall=op('SUBTRACT',1,op('MULTIPLY',v,v));axes.append(op('MULTIPLY',fall,fall))
 emission=n.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(.97,.985,1,1);l.new(op('MULTIPLY',op('MULTIPLY',axes[0],axes[1]),1.5),emission.inputs['Strength'])
 output=n.new('ShaderNodeOutputMaterial');l.new(emission.outputs[0],output.inputs['Surface']);me.materials.append(m)
 s.view_settings.exposure=-.30
 root['photography_refinement']='2026-10-26: stable physically scaled mold grain, continuous ink borders, acrylic side normals, official-photo vector lettering and LCD indicators, broader LCD electrodes, broad silk lighting.'
 s.cycles.samples=512;s.cycles.adaptive_threshold=.004;s.cycles.max_bounces=16;s.cycles.transmission_bounces=12
 s.render.image_settings.color_depth='16';s.render.use_border=False;s.render.resolution_percentage=100
 s.camera=D['CAM | Hero'];s.render.resolution_x=2048;s.render.resolution_y=4438
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'photography_candidate.blend'))
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=True
 s.cycles.device='GPU'
except Exception:s.cycles.device='CPU'
s.cycles.use_denoising=True;s.render.image_settings.color_depth='16';s.render.use_border=False
views=[('hero','CAM | Hero',2048,4438),('front','CAM | Front',2400,2400),('three_quarter','CAM | Three-quarter',2400,2400),('material_closeup','CAM | Material macro',2400,2400)]
times={}
for name,cam,w,h in (views if FINAL else ([views[3]] if '--detail-only' in sys.argv else [views[3],views[0]])):
 s.camera=D[cam];s.render.resolution_x=w;s.render.resolution_y=h
 s.render.resolution_percentage=100 if FINAL else (67 if name=='material_closeup' else 40)
 s.cycles.samples=512 if FINAL else 128;s.cycles.adaptive_threshold=.004 if FINAL else .012
 s.render.filepath=str(P/(name+'.png' if FINAL else 'photography_'+name+'_preview.png'))
 start=time.monotonic();bpy.ops.render.render(write_still=True);times[name]=round(time.monotonic()-start,2);print('VIEW_DONE',name,times[name],flush=True)
if FINAL:
 s.camera=D['CAM | Hero'];s.render.resolution_x=2048;s.render.resolution_y=4438;s.render.resolution_percentage=100
 s.render.filepath=str(P/'hero.png');bpy.ops.wm.save_as_mainfile(filepath=str(P/'casio_f91w.blend'))
 (P/'photography_render_times.json').write_text(json.dumps(times,indent=2))
print('PHOTOGRAPHY_COMPLETE',flush=True)
