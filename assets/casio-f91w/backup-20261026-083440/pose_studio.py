# Upright, closed wrist-loop pose and photographic studio.
import bpy, math, bisect, sys, json
from pathlib import Path
from mathutils import Vector, Matrix
OUT=Path(__file__).resolve().parent
PREVIEW='--preview' in sys.argv
scene=bpy.context.scene
root=bpy.data.objects['F-91W-1 | SI scale']
asset=bpy.data.collections['CASIO F-91W-1 | manufactured components']
# Preserve every manufactured part; replace only the photographic set.
for o in list(bpy.data.collections['STUDIO | cameras and softboxes'].objects) if bpy.data.collections.get('STUDIO | cameras and softboxes') else []:bpy.data.objects.remove(o,do_unlink=True)
studio=bpy.data.collections.get('STUDIO | cameras and softboxes')
if not studio:studio=bpy.data.collections.new('STUDIO | cameras and softboxes');scene.collection.children.link(studio)

# Resample actual arclength around an asymmetric wrist ellipse, in local mm.
# The closed loop has a longer downward sweep and shorter upper turn, as reference.
def ellipse(t):
 a=32.0 if math.sin(t)>=0 else 40.0
 return Vector((a*math.sin(t),-17.7+25.0*math.cos(t)))
paths={}
for side in (1,-1):
 t0=math.asin(19.1/(32 if side==1 else 40))
 ts=[side*(t0+i*2*math.pi/12000) for i in range(12001)]
 ds=[0.0]
 for a,b in zip(ts,ts[1:]):ds.append(ds[-1]+(ellipse(b)-ellipse(a)).length)
 paths[side]=(ts,ds,3.0-ellipse(ts[0]).y)
def path(s,side):
 ts,ds,adjust=paths[side];s=max(0,s);i=min(len(ds)-2,max(0,bisect.bisect_right(ds,s)-1));f=(s-ds[i])/(ds[i+1]-ds[i]);t=ts[i]*(1-f)+ts[i+1]*f
 p=ellipse(t);p.y+=adjust*math.exp(-s/12)
 return p

def oldcenter(y):return -7+10*math.exp(-max(abs(y)-19.1,0)/18)
def deform_band(o,side):
 for v in o.data.vertices:
  y=v.co.y;s=abs(y)-19.1;offset=v.co.z-oldcenter(y);p=path(s,side)
  tangent=(path(s+.02,side)-path(max(0,s-.02),side)).normalized()*side
  normal=Vector((-tangent.y,tangent.x));v.co.y=p.x+normal.x*offset;v.co.z=p.y+normal.y*offset
 # Smooth the flexible molded surface, retain precise groove edges with normals.
 for f in o.data.polygons:f.use_smooth=True
 mod=o.modifiers.new('Flexible molded surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True
for side,n in [(1,'Buckle band | flexible tapered resin'),(-1,'Perforated band | flexible tapered resin')]:deform_band(bpy.data.objects[n],side)
# Rigid buckle / keeper assemblies follow the band tangent at the back.
def rigid_on_band(o,anchor):
 s=anchor-19.1;p=path(s,1);t=(path(s+.02,1)-path(s-.02,1)).normalized();angle=math.atan2(t.y,t.x)
 o.matrix_basis=Matrix.Translation((0,p.x,p.y)) @ Matrix.Rotation(angle,4,'X') @ Matrix.Translation((0,-anchor,-oldcenter(anchor))) @ o.matrix_basis
for o in list(asset.objects):
 if o.name.startswith('Buckle |') or o.name=='Buckle molded CASIO':rigid_on_band(o,83)
 elif o.name.startswith('Keeper |'):rigid_on_band(o,69)
# Soften the existing rounded molded bezel shoulder across its small edge facets.
for f in bpy.data.objects['Bezel | inclined inner shoulder'].data.polygons:f.use_smooth=True
root.rotation_euler=(math.pi/2,0,math.radians(-8))
root.location=(.0018,0,0)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
minz=min((o.evaluated_get(dg).matrix_world@Vector(v)).z for o in asset.objects if o.type in {'MESH','FONT','CURVE'} for v in o.evaluated_get(dg).bound_box)
root.location.z=.0002-minz
root['model']='Casio F-91W-1';root['verified_case_dimensions_mm']='38.2 × 35.2 × 8.5';root['references']='../../references/casio-f91w/sources.md'
root['pose']='Upright closed wrist loop; 8 degree yaw; buckle hidden behind case'
root['studio_reference']='../../references/casio-f91w/studio-pose-reference.png'
bpy.context.view_layer.update()

# Near-black studio with a physically reflected floor and low grazing strip.
def material(name,color,rough,metal=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
floor=material('Studio | black polished acrylic ground',(.002,.0025,.003),.16)
n=floor.node_tree.nodes;l=floor.node_tree.links;p=next(n for n in n if n.type=='BSDF_PRINCIPLED');geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');ab=n.new('ShaderNodeMath');ab.operation='ABSOLUTE';ramp=n.new('ShaderNodeMapRange');ramp.clamp=True;ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=.045;ramp.inputs['To Min'].default_value=.09;ramp.inputs['To Max'].default_value=.14;l.new(geo.outputs['Position'],sep.inputs[0]);l.new(sep.outputs['Y'],ab.inputs[0]);l.new(ab.outputs[0],ramp.inputs['Value']);l.new(ramp.outputs['Result'],p.inputs['Roughness'])
# A polished contact zone transitions to black matte foreground, preventing
# off-camera softboxes from filling the large portrait foreground with gray.
mask=n.new('ShaderNodeMapRange');mask.clamp=True;mask.interpolation_type='SMOOTHSTEP';mask.inputs['From Min'].default_value=.02;mask.inputs['From Max'].default_value=.48;mask.inputs['To Min'].default_value=1;mask.inputs['To Max'].default_value=0;l.new(ab.outputs[0],mask.inputs['Value'])
velvet=n.new('ShaderNodeBsdfDiffuse');velvet.inputs['Color'].default_value=(.00005,.00006,.00007,1);velvet.inputs['Roughness'].default_value=1
mix=n.new('ShaderNodeMixShader');l.new(mask.outputs['Result'],mix.inputs[0]);l.new(velvet.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],next(q for q in n if q.type=='OUTPUT_MATERIAL').inputs['Surface'])
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));o=bpy.context.object;o.name='Studio | reflective black ground'
for c in list(o.users_collection):c.objects.unlink(o)
studio.objects.link(o);o.data.materials.append(floor)
scene.world=bpy.data.worlds.new('Upright studio | near-black environment');scene.world.use_nodes=True
p=scene.world.node_tree.nodes.get('Background');p.inputs[0].default_value=(.01,.012,.014,1);p.inputs[1].default_value=.04

def area(name,pos,target,power,w,h,color=(1,1,1)):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='RECTANGLE';d.size=w;d.size_y=h;d.color=color;o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Key | upper-left tall silk',(-.055,-.075,.107),(0,0,.041),.12,.045,.080,(.95,.98,1))
area('Fill | quiet frontal silk',(.055,-.12,.075),(0,0,.042),.040,.060,.050,(1,.98,.95))
area('Rim | right vertical strip',(.052,.025,.068),(0,-.004,.042),.055,.014,.065,(.90,.95,1))
area('Upper band | edge strip',(-.025,.02,.12),(0,-.012,.055),.02,.055,.014)
area('Ground | grazing horizontal glow',(0,.022,.004),(0,0,0),.00025,.22,.0018,(.78,.84,.85))

# Long-lens near-front portrait. Horizontal view and low target preserve reference placement.
def camera(name,pos,target,scale):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='PERSP';d.lens=100;d.sensor_fit='VERTICAL';d.sensor_height=24;d.clip_start=.001;d.clip_end=20;return o
cz=root.location.z
cams={
 'hero':camera('CAM | Hero',(.0,-.867,.0166),(0,0,.0166),.208),
 'front':camera('CAM | Front',(.0018,-.42,.036),(.0018,.010,.036),.1032),
 'three_quarter':camera('CAM | Three-quarter',tuple(Vector((.0018,.015,.036))+Vector((.18,-.29,.025)).normalized()*.46),(.0018,.015,.036),.1104),
 'material_closeup':camera('CAM | Material macro',(.023,-.17,cz+.014),(0,-.004,cz+.001),.041)}
scene.render.engine='CYCLES';scene.cycles.samples=64 if PREVIEW else 256;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.025 if PREVIEW else .008;scene.cycles.max_bounces=12;scene.cycles.transmission_bounces=8
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=True
 scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.6
scene.camera=cams['hero'];bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
for name in (['hero'] if PREVIEW else cams):
 scene.camera=cams[name]
 if name=='hero':scene.render.resolution_x=804 if PREVIEW else 2048;scene.render.resolution_y=1742 if PREVIEW else 4438
 else:scene.render.resolution_x=2400;scene.render.resolution_y=2400
 scene.render.filepath=str(OUT/('upright_preview.png' if PREVIEW else name+'.png'));bpy.ops.render.render(write_still=True)
scene.camera=cams['hero'];scene.render.resolution_x=2048;scene.render.resolution_y=4438;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'casio_f91w.blend'))
print('UPRIGHT_STUDIO_COMPLETE',root.location[:])
