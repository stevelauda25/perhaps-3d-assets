"""Casio F-91W-1. Run with Blender --background --python build.py.
Reference reconstruction from eight official Casio images. Dimensions in mm,
asset parent scales them to SI meters. No unrelated scenes are opened/modified.
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parent
PREVIEW='--preview' in sys.argv
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.length_unit='MILLIMETERS'
asset=bpy.data.collections.new('CASIO F-91W-1 | manufactured components');scene.collection.children.link(asset)
root=bpy.data.objects.new('F-91W-1 | SI scale',None);asset.objects.link(root);root.scale=(.001,)*3

def own(o,mat=None):
 for c in list(o.users_collection):c.objects.unlink(o)
 asset.objects.link(o);o.parent=root
 if mat:o.data.materials.append(mat)
 return o

def mat(name,color,rough=.4,metal=0,grain=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
 p=next(x for x in n if x.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if grain:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=16000;tex.inputs['Detail'].default_value=2;tex.inputs['Roughness'].default_value=.72
  coord=n.new('ShaderNodeNewGeometry');l.new(coord.outputs['Position'],tex.inputs['Vector'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.30;bump.inputs['Distance'].default_value=.000008;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
  ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=rough-.045;ramp.inputs['To Max'].default_value=rough+.045;l.new(tex.outputs['Fac'],ramp.inputs['Value']);l.new(ramp.outputs['Result'],p.inputs['Roughness'])
 return m
resin=mat('01 | Black molded resin • 40 micron grain',(.012,.014,.017),.39,grain=True)
strapmat=mat('02 | Flexible black urethane • satin micrograin',(.009,.011,.013),.46,grain=True)
black=mat('03 | Under-crystal black printed mask',(.002,.003,.005),.25)
white=mat('04 | Warm white screen printing',(.68,.73,.72),.4)
blue=mat('05 | Casio cobalt blue print',(.014,.135,.40),.4)
yellow=mat('06 | Gold yellow screen printing',(.72,.50,.075),.42)
red=mat('07 | Deep red screen printing',(.52,.014,.029),.42)
lcd=mat('08 | Reflective gray-green LCD polarizer',(.32,.36,.30),.31)
ink=mat('09 | Non-emissive liquid crystal segments',(.018,.023,.021),.38)
steel=mat('10 | Brushed stainless steel',(.45,.48,.50),.28,1,True)
p=next(x for x in steel.node_tree.nodes if x.type=='BSDF_PRINCIPLED');next((i for i in p.inputs if 'Anisotropic' in i.name and i.type=='VALUE'),p.inputs['Roughness']).default_value=.65
chrome=mat('11 | Polished steel button caps',(.58,.62,.65),.18,1,True)
glass=mat('12 | Clear acrylic resin crystal • IOR 1.49',(.99,.995,1),.025)
p=next(x for x in glass.node_tree.nodes if x.type=='BSDF_PRINCIPLED');p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.49

def mesh(name,verts,faces,ma):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);asset.objects.link(o);o.parent=root
 if ma:me.materials.append(ma)
 return o

def bevel(o,width=.15,seg=3):
 m=o.modifiers.new('Manufacturing edge radius','BEVEL');m.width=width;m.segments=seg
 m=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');m.keep_sharp=True
 return o

def outline(w,h,c):
 p=[(-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)]
 result=[]
 for i,b in enumerate(p):
  a=Vector(p[i-1]);b=Vector(b);d=Vector(p[(i+1)%len(p)]);r=min(.85,c*.45)
  q=b+(a-b).normalized()*r;t=b+(d-b).normalized()*r
  for j in range(6):
   f=j/5;v=(1-f)**2*q+2*f*(1-f)*b+f*f*t;result.append(tuple(v))
 return result

def solid(name,pts,z0,z1,ma,bev=0):
 n=len(pts);v=[(x,y,z) for z in (z0,z1) for x,y in pts];f=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh(name,v,f,ma)
 if bev:bevel(o,bev)
 return o

def box(name,loc,dim,ma,bev=.12):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=own(bpy.context.object,ma);o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bev:bevel(o,bev)
 return o

def ring(name,outer,inner,z,ma,thick=.015):
 n=len(outer);v=[(x,y,z) for x,y in outer+inner];f=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh(name,v,f,ma)
 if thick:m=o.modifiers.new('Ink film thickness','SOLIDIFY');m.thickness=thick
 return o

def line(name,pts,ma,r=.045,cyclic=False):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=r;c.bevel_resolution=3
 s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,co in zip(s.points,pts):p.co=(*co,1)
 s.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,c);asset.objects.link(o);o.parent=root;c.materials.append(ma);return o

def rounded(w,h,r,n=10):
 pts=[]
 for cx,cy,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for i in range(n+1):
   t=math.radians(a+i*90/n);pts.append((cx+r*math.cos(t),cy+r*math.sin(t)))
 return pts

def text(name,body,x,y,z,w,h,ma,font='Arial.ttf'):
 c=bpy.data.curves.new(name,'FONT');c.body=body;c.align_x='CENTER';c.align_y='CENTER';c.size=1;c.resolution_u=6
 fp='/System/Library/Fonts/Supplemental/'+font
 if os.path.exists(fp):c.font=bpy.data.fonts.load(fp,check_existing=True)
 o=bpy.data.objects.new(name,c);asset.objects.link(o);o.parent=root;c.materials.append(ma);o.location=(x,y,z);bpy.context.view_layer.update();o.scale=(.001*w/o.dimensions.x,.001*h/o.dimensions.y,1);return o

# Case silhouette. Overall specified width including pushers = 35.2 mm.
casepts=[(-11.4,-19.1),(11.4,-19.1),(13.1,-14.6),(16.55,-9.8),(16.55,9.8),(13.1,14.6),(11.4,19.1),(-11.4,19.1),(-13.1,14.6),(-16.55,9.8),(-16.55,-9.8),(-13.1,-14.6)]
solid('Case | tapered lugs and shell',casepts,1.0,6.1,resin,.30)
# Bezel stepped shoulder outline, octagonal rounded inset crystal.
solid('Bezel | lower chamfer',outline(32.4,32.9,4.2),5.9,7.3,resin,.35)
o=ring('Bezel | inclined inner shoulder',outline(31.8,32.0,4),outline(28.2,28.2,3.0),7.15,resin,.30)
for v in list(o.data.vertices)[len(o.data.vertices)//2:]:v.co.z=7.95
bevel(o,.12,3)
# Main resin panel lies behind physical crystal, aperture is separate LCD.
solid('Dial backing',outline(28.6,28.6,3),7.1,7.61,black,.25)
solid('LCD | polarizer plate',rounded(22.1,11.5,1.1),7.62,7.72,lcd,.08)
ring('LCD | double white aperture border',rounded(22.65,12.05,1.5),rounded(22.49,11.89,1.42),7.76,white)
# Physical acrylic cap, thin front plate over all graphics.
solid('Crystal | solid molded acrylic',outline(28.55,28.55,3.05),8.00,8.50,glass,.16)
for w,h,c,r,ma,z in [(27.75,27.75,2.75,.14,blue,7.84),(26.6,26.6,2.6,.044,white,7.85)]:
 line('Dial perimeter | '+ma.name,[(x,y,z) for x,y in outline(w,h,c)],ma,r,True)
text('CASIO brand','CASIO',-5.45,10.5,7.87,7.2,1.45,white,'Arial Bold.ttf')
text('F-91W model','F-91W',6.1,10.5,7.87,6.55,1.28,yellow,'Arial Bold Italic.ttf')
box('Blue upper divider',(0,8.5,7.86),(24.9,.25,.014),blue,0)
text('Alarm chronograph','ALARM CHRONOGRAPH',4.0,7.05,7.86,15.25,1.03,yellow,'Arial Narrow Bold.ttf')
text('Light legend','LIGHT',-8.45,7.05,7.86,3.1,.65,white)
text('Mode legend','MODE',-8.5,-7.05,7.86,3.4,.67,white)
text('Alarm legend','ALARM ON·OFF/24HR',3.5,-7.05,7.86,12.5,.65,white)
for name,x,y,sgn in [('Light arrow',-11.2,7.05,-1),('Mode arrow',-11.2,-7.05,-1),('Alarm arrow',11.7,-7.05,1)]:
 solid(name,[(x+sgn*.65,y),(x-sgn*.65,y+.19),(x-sgn*.65,y-.19)],7.86,7.875,red)
for x in [-8.1,8.1]:box('Lower blue rule',(x,-8.15,7.86),(7.8,.20,.014),blue,0)
text('Water','WATER',-8,-10.05,7.86,6.0,1.13,white,'Arial Bold.ttf')
text('Resist','RESIST',8.1,-10.05,7.86,6.1,1.13,white,'Arial Bold.ttf')
line('WR shield outline',[(x,y-10.12,7.86) for x,y in outline(7.3,2.8,.7)],blue,.07,True)
text('WR logo','WR',0,-10.05,7.86,5.6,1.74,red,'Arial Bold Italic.ttf')
# Segmented LCD characters are actual planar, non-emissive cell geometry.
segments={'0':'abcedf','1':'bc','2':'abged','3':'abgcd','4':'fgbc','5':'afgcd','6':'afgecd','7':'abc','8':'abcdefg','9':'abfgcd','S':'afgcd','U':'fbcde'}
def digit(ch,x,y,w,h):
 t=w*.16; gap=w*.055
 shapes={
 'a':[(t*.55,h-t*.4),(t,h),(w-t*.15,h),(w-t*.95,h-t),(t*.95,h-t)],
 'g':[(t*.35,h/2),(t*.95,h/2+t*.48),(w-t*.85,h/2+t*.48),(w-t*.15,h/2),(w-t*.85,h/2-t*.48),(t*.95,h/2-t*.48)],
 'd':[(t*.55,t*.4),(t*.95,t),(w-t*.95,t),(w-t*.15,0),(t,0)],
 'f':[(0,h-t*.65),(t*.46,h-t*.28),(t,h-t*.98),(t,h/2+t*.65),(t*.45,h/2+t*.15),(0,h/2+t*.65)],
 'b':[(w,h-t*.65),(w,h/2+t*.65),(w-t*.48,h/2+t*.15),(w-t,h/2+t*.65),(w-t,h-t*.98),(w-t*.48,h-t*.28)],
 'e':[(0,h/2-t*.65),(t*.45,h/2-t*.15),(t,h/2-t*.65),(t,t*.98),(t*.46,t*.28),(0,t*.65)],
 'c':[(w,h/2-t*.65),(w,t*.65),(w-t*.48,t*.28),(w-t,t*.98),(w-t,h/2-t*.65),(w-t*.48,h/2-t*.15)]}
 for k in segments[ch]:solid('LCD cell '+ch+' '+k,[(x+px+.19*py/h,y+py) for px,py in shapes[k]],7.775,7.785,ink)
for ch,x in [('1',-10.8),('0',-7.0),('5',-1.8),('8',1.5)]:digit(ch,x,-4.52,2.8,4.9)
for ch,x in [('5',5.0),('0',7.65)]:digit(ch,x,-4.52,2.18,3.7)
for y in [-3.2,-1.25]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.25,depth=.014,location=(-2.65,y,7.79));own(bpy.context.object,ink).name='LCD colon'
for ch,x in [('S',-3.6),('U',-.9),('3',6),('0',8.15)]:digit(ch,x,1.25,1.7,2.55)
text('PM indicator','PM',-8.3,1.65,7.78,2.2,1.1,ink,'Arial Bold.ttf')
line('LCD alarm bell', [(-6.3,3.1,7.79),(-6.0,3.5,7.79),(-6.0,4.1,7.79),(-5.7,4.4,7.79),(-5.3,4.4,7.79),(-5.0,4.1,7.79),(-5.0,3.5,7.79),(-4.7,3.1,7.79),(-6.3,3.1,7.79)],ink,.07)
box('LCD bell crown',(-5.5,4.55,7.79),(.15,.3,.01),ink,0)
box('LCD bell clapper',(-5.5,2.95,7.79),(.25,.25,.01),ink,0)
text('Signal indicator','))))',-8.9,3.9,7.78,2.0,.9,ink,'Arial Narrow Bold.ttf')
# Three steel pushers, gasket collars and molded protective side pads.
for side,y in [(-1,5.6),(-1,-5.6),(1,-5.6)]:
 box('Pusher protective resin shoulder',(side*16.35,y,4.45),(1.0,5.5,4.4),resin,.18)
 for rad,length,xx,ma,nm in [(1.04,.35,16.75,black,'Gasket'),(.88,1.30,16.95,chrome,'Pusher')]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=rad,depth=length,location=(side*xx,y,4.7),rotation=(0,math.pi/2,0));o=own(bpy.context.object,ma);o.name=nm;bevel(o,.085)
# Lug transverse pins and recessed pin holes.
for y in [-17.8,17.8]:
 for side in [-1,1]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.44,depth=.15,location=(side*11.9,y,3.0),rotation=(0,math.pi/2,0));own(bpy.context.object,black).name='Recessed lug pin hole'
# Back plate and four screws. No invented serial or unreadable engraving.
solid('Caseback | stamped steel',outline(29.4,30.6,3.9),0,.9,steel,.28)
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=12.5,depth=.18,location=(0,0,.18));own(bpy.context.object,steel).name='Caseback | circular stamped relief'
for x in [-12.1,12.1]:
 for y in [-11.9,11.9]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(x,y,.30));o=own(bpy.context.object,steel);o.name='Caseback | crosshead screw';o.scale=(.83,.83,.25)
  for a in [0,math.pi/2]:
   o=box('Screw cross recess',(x,y,.05),(1.0,.16,.018),black,.04);o.rotation_euler.z=a
# Bands: booleans in flat construction space, then gentle flexible deformation.
def applymods(o):
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
def cut(o,c):
 bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Molded recess / perforation','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
def strapbend(o,side):
 bm=bmesh.new();bm.from_mesh(o.data)
 for step in range(20,127):
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,side*step,0),plane_no=(0,1,0),clear_outer=False,clear_inner=False)
 bm.to_mesh(o.data);bm.free()
 # Flat local band z is surface offset about center. Curve settles naturally.
 for v in o.data.vertices:
  s=side*v.co.y-19.1
  z=-7+10*math.exp(-max(s,0)/18)
  v.co.z+=z
  end=83 if side==1 else 126
  if side<0 and -v.co.y>end-3:
   t=min(1,max(0,(-v.co.y-end+3)/3));old=7.65-1.45*t;new=4.65+3*math.sqrt(max(0,1-t*t));v.co.x*=new/old
for side,end in [(1,83),(-1,126)]:
 pts=[(-10.7,side*19.1),(10.7,side*19.1),(8.1,side*43),(7.65,side*(end-3)),(6.2,side*end),(-6.2,side*end),(-7.65,side*(end-3)),(-8.1,side*43)]
 if side<0:pts.reverse()
 o=solid(('Buckle' if side==1 else 'Perforated')+' band | flexible tapered resin',pts,-.9,.9,strapmat,.3);applymods(o)
 if side<0:
  for i in range(12):
   y=-(54+i*6.25)
   c=solid('hole cutter',[(x,y+yy) for x,yy in rounded(3.65,2.05,.93)],-3,3,None);cut(o,c)
 # Relief bands near case, elongated middle depression.
 for s in [6.0,11.2,16.4]:
  y=side*(19.1+s)
  c=box('Transverse relief cutter',(0,y,.89),(22,.38,.40),None,.14);applymods(c);cut(o,c)
  c=solid('Elongated relief cutter',[(x,y+yy) for x,yy in rounded(9,.75,.36)],.55,1.5,None);cut(o,c)
 # Pair of parallel longitudinal molded channels.
 for x in [-2.9,2.9]:
  c=box('Longitudinal relief cutter',(x,side*(end+46)/2,.95),(.22,end-46,.35),None,.09);applymods(c);cut(o,c)
 bevel(o,.07,2);applymods(o);strapbend(o,side)
# Black molded buckle and sliding keeper on shorter half.
z=-7+10*math.exp(-(76-19.1)/18)
outer=rounded(18.0,15.0,1.0);inner=rounded(14.4,11.0,.55)
o=ring('Buckle | black resin frame',[(x,y+83) for x,y in outer],[(x,y+83) for x,y in inner],z+1.9,resin,1.4);bevel(o,.3)
box('Buckle | central tongue',(0,83,z+1.1),(1.55,12.0,1.1),resin,.3)
o=text('Buckle molded CASIO','CASIO',0,89.5,z+1.96,8.0,.85,resin,'Arial Bold.ttf');o.data.extrude=.06;o.data.bevel_depth=.015
z=-7+10*math.exp(-(69-19.1)/18)
box('Keeper | top',(0,69,z+2.0),(19.0,7.0,1.55),strapmat,.5)
for x in [-8.7,8.7]:box('Keeper | side',(x,69,z), (1.6,7,3.5),strapmat,.4)

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
