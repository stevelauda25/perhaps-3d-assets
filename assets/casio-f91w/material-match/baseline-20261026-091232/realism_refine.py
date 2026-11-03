# Reference-driven Casio manufacturing and material refinement, native millimeters.
import bpy, math
from mathutils import Vector
root=bpy.data.objects['F-91W-1 | SI scale'];asset=bpy.data.collections['CASIO F-91W-1 | manufactured components']
D=bpy.data.objects
resin=bpy.data.materials.get('01 | Black molded resin • 40 micron grain');strapmat=bpy.data.materials.get('02 | Flexible black urethane • satin micrograin')
white=bpy.data.materials['04 | Warm white screen printing'];blue=bpy.data.materials['05 | Casio cobalt blue print'];black=bpy.data.materials['03 | Under-crystal black printed mask'];ink=bpy.data.materials['09 | Non-emissive liquid crystal segments'];glass=bpy.data.materials['12 | Clear acrylic resin crystal • IOR 1.49']

def remove(name):
 if D.get(name):bpy.data.objects.remove(D[name],do_unlink=True)
def poly(name,xy,z,mat):
 me=bpy.data.meshes.new(name);me.from_pydata([(x,y,z) for x,y in xy],[],[tuple(range(len(xy)))]);me.update();o=bpy.data.objects.new(name,me);asset.objects.link(o);o.parent=root;o.data.materials.append(mat);return o

def rr(w,h,r,n=16):
 points=[]
 for cx,cy,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for j in range(n):
   t=math.radians(a+90*j/(n-1));points.append((cx+r*math.cos(t),cy+r*math.sin(t)))
 return points

def chamfer(w,h,c):
 p=[(-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)];r=[]
 for i,b in enumerate(p):
  a=Vector(p[i-1]);b=Vector(b);d=Vector(p[(i+1)%len(p)]);radius=min(.85,c*.45);q=b+(a-b).normalized()*radius;t=b+(d-b).normalized()*radius
  for j in range(8):
   f=j/7;r.append(tuple((1-f)**2*q+2*f*(1-f)*b+f*f*t))
 return r

def flatline(name,pts,width,z,ma,closed=False):
 n=len(pts);verts=[];faces=[]
 for j in range(n if closed else n-1):
  a=Vector(pts[j]);b=Vector(pts[(j+1)%n]);v=b-a
  if v.length<.00001:continue
  normal=Vector((-v.y,v.x)).normalized()*width/2;k=len(verts)
  verts.extend([(a.x+normal.x,a.y+normal.y,z),(a.x-normal.x,a.y-normal.y,z),(b.x-normal.x,b.y-normal.y,z),(b.x+normal.x,b.y+normal.y,z)]);faces.append((k,k+1,k+2,k+3))
 # Flat circular joins avoid any tubular or embossed appearance.
 for x,y in pts:
  k=len(verts)
  for j in range(12):t=j*math.tau/12;verts.append((x+width/2*math.cos(t),y+width/2*math.sin(t),z))
  faces.append(tuple(range(k,k+12)))
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);asset.objects.link(o);o.parent=root;me.materials.append(ma);return o

def ringmesh(name,outer,inner,z,ma):
 n=len(outer);v=[(x,y,z) for x,y in outer+inner];f=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(name,me);asset.objects.link(o);o.parent=root;me.materials.append(ma);return o

# A genuine printed black mask on the underside of the physical resin crystal.
outer=chamfer(28.54,28.54,3.05);n=len(outer)
me=bpy.data.meshes.new('Under-crystal mask');me.from_pydata([(x,y,z) for z in [7.982,7.993] for x,y in outer],[],[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]);me.update();mask=bpy.data.objects.new('Dial | printed opaque aperture mask',me);asset.objects.link(mask);mask.parent=root;me.materials.append(black)
# Real rectangular LCD opening, cut through the opaque printing layer.
pts=rr(22.13,11.55,1.15);nn=len(pts);me=bpy.data.meshes.new('mask aperture cutter');me.from_pydata([(x,y,z) for z in [7.8,8.1] for x,y in pts],[],[tuple(reversed(range(nn))),tuple(range(nn,2*nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]);me.update();cut=bpy.data.objects.new('mask aperture cutter',me);asset.objects.link(cut);cut.parent=root
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=mask;mod=mask.modifiers.new('Printed LCD aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# All ink sits on the same underside face, with no raised wire rims.
for o in list(asset.objects):
 if o.type=='FONT' and o.name!='Buckle molded CASIO':o.location.z=7.995
 if o.name in ['Blue upper divider','Lower blue rule','Lower blue rule.001','Light arrow','Mode arrow','Alarm arrow']:
  if o.name.endswith('arrow'):
   for v in o.data.vertices:v.co.z=7.995
  else:o.location.z=7.995
# Screen-printed rules are planar films, not small extruded boxes.
for name,x,y,w,h in [('Blue upper divider',0,8.5,24.9,.25),('Lower blue rule',-8.1,-8.15,7.8,.20),('Lower blue rule.001',8.1,-8.15,7.8,.20)]:
 remove(name);poly(name,[(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)],7.995,blue)
for name,x,y,sgn in [('Light arrow',-11.2,7.05,-1),('Mode arrow',-11.2,-7.05,-1),('Alarm arrow',11.7,-7.05,1)]:
 remove(name);poly(name,[(x+sgn*.65,y),(x-sgn*.65,y+.19),(x-sgn*.65,y-.19)],7.995,bpy.data.materials['07 | Deep red screen printing'])
for o in list(asset.objects):
 if o.name.startswith('Dial perimeter |') or o.name=='WR shield outline' or o.name=='LCD | double white aperture border':bpy.data.objects.remove(o,do_unlink=True)
flatline('Print | cobalt perimeter',chamfer(27.75,27.75,2.75),.26,7.995,blue,True)
flatline('Print | white perimeter',chamfer(26.6,26.6,2.6),.075,7.995,white,True)
flatline('Print | WR shield',[(x,y-10.12) for x,y in chamfer(7.3,2.8,.7)],.13,7.995,blue,True)
flatline('Print | LCD aperture keyline',rr(22.65,12.05,1.5),.075,7.995,white,True)

# Squared rounded CASIO logotype traced as flat graphic geometry from official face.
remove('CASIO brand')
letters=[('C',1.40),('A',1.45),('S',1.35),('I',.38),('O',1.42)];gap=.30;total=sum(w for c,w in letters)+4*gap;x=-5.45-total/2;cy=10.5;h=1.45;th=.245
for ch,w in letters:
 cx=x+w/2
 if ch in ['C','O']:
  outer=rr(w,h,.25,12);inner=rr(w-2*th,h-2*th,.11,12)
  if ch=='O':ringmesh('Print | CASIO '+ch,[(xx+cx,yy+cy) for xx,yy in outer],[(xx+cx,yy+cy) for xx,yy in inner],7.995,white)
  else:
   # Continuous rounded-rect C, including top and lower right terminals.
   p=[]
   for xx,yy in outer:
    if not (xx>w/2-.02 and abs(yy)<.23):p.append((xx+cx,yy+cy))
   # Build each ring quad, omitting the right central opening.
   n=len(outer);vs=[(xx+cx,yy+cy,7.995) for xx,yy in outer+inner];fs=[]
   for i in range(n):
    j=(i+1)%n
    if max(outer[i][0],outer[j][0])>w/2-.01 and min(outer[i][1],outer[j][1])<.24 and max(outer[i][1],outer[j][1])>-.24:continue
    fs.append((i,j,j+n,i+n))
   me=bpy.data.meshes.new('CASIO C');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Print | CASIO C',me);asset.objects.link(o);o.parent=root;me.materials.append(white)
 elif ch=='A':
  for p in [[(-w/2,-h/2),(-w/2+.27,-h/2),(-.04,h/2-.03),(-.23,h/2)],[(w/2,-h/2),(w/2-.27,-h/2),(.04,h/2-.03),(.23,h/2)],[(-.38,-.1),(.38,-.1),(.46,-.34),(-.46,-.34)],[(-.22,h/2),(.22,h/2),(.30,h/2-.24),(-.30,h/2-.24)]]:poly('Print | CASIO A',[(xx+cx,yy+cy) for xx,yy in p],7.995,white)
 elif ch=='I':poly('Print | CASIO I',[(cx-w/2,cy-h/2),(cx+w/2,cy-h/2),(cx+w/2,cy+h/2),(cx-w/2,cy+h/2)],7.995,white)
 else:
  # Broad geometric S with gently rounded corners and square terminals.
  p=[(w/2-th*.5,h/2-th*.5),(-w/2+th,h/2-th*.5),(-w/2+th*.5,h/2-th),(-w/2+th*.5,th*.55),(-w/2+th,0),(w/2-th,0),(w/2-th*.5,-th*.55),(w/2-th*.5,-h/2+th),(w/2-th,-h/2+th*.5),(-w/2+th*.5,-h/2+th*.5)]
  flatline('Print | CASIO S',[(xx+cx,yy+cy) for xx,yy in p],th,7.995,white)
 x+=w+gap

# Recessed reflective LCD, with non-overlapping flat cell electrodes.
for v in D['Dial backing'].data.vertices:v.co.z=min(v.co.z,7.35)
for v in D['LCD | polarizer plate'].data.vertices:v.co.z-=.17
for o in list(asset.objects):
 if o.name.startswith('LCD cell ') or o.name.startswith('LCD colon') or o.name in ['LCD alarm bell','LCD bell crown','LCD bell clapper','Signal indicator']:bpy.data.objects.remove(o,do_unlink=True)
segments={'0':'abcdef','1':'bc','3':'abgcd','5':'afgcd','8':'abcdefg','S':'afgcd','U':'fbcde'}
def digit(ch,x,y,w,h):
 t=w*.16
 a=[(t*.45,h),(w-t*.45,h),(w-t,h-t),(t,h-t)]
 b=[(w,h-t*.45),(w,h/2+t*.30),(w-t,h/2+t*.65),(w-t,h-t)]
 g=[(t*.75,h/2+t*.45),(w-t*.75,h/2+t*.45),(w-t*.25,h/2),(w-t*.75,h/2-t*.45),(t*.75,h/2-t*.45),(t*.25,h/2)]
 shapes={'a':a,'b':b,'f':[(w-xx,yy) for xx,yy in b],'c':[(xx,h-yy) for xx,yy in b],'e':[(w-xx,h-yy) for xx,yy in b],'d':[(xx,h-yy) for xx,yy in a],'g':g}
 for k in segments[ch]:
  p=shapes[k];cx=sum(xx for xx,yy in p)/len(p);cy=sum(yy for xx,yy in p)/len(p)
  p=[(cx+(xx-cx)*.945,cy+(yy-cy)*.945) for xx,yy in p]
  poly('LCD electrode | '+ch+' '+k,[(x+xx+.15*yy/h,y+yy) for xx,yy in p],7.565,ink)
for ch,x in [('1',-10.8),('0',-7.0),('5',-1.8),('8',1.5)]:digit(ch,x,-4.52,2.8,4.9)
for ch,x in [('5',5),('0',7.65)]:digit(ch,x,-4.52,2.18,3.7)
for ch,x in [('S',-3.6),('U',-.9),('3',6),('0',8.15)]:digit(ch,x,1.25,1.7,2.55)
for yy in [-3.2,-1.25]:poly('LCD electrode | colon',[( -2.65+.23*math.cos(a*math.tau/32),yy+.23*math.sin(a*math.tau/32)) for a in range(32)],7.565,ink)
D['PM indicator'].location.z=7.565
flatline('LCD electrode | bell',[(-6.3,3.1),(-6,3.5),(-6,4.1),(-5.7,4.4),(-5.3,4.4),(-5,4.1),(-5,3.5),(-4.7,3.1),(-6.3,3.1)],.11,7.565,ink)
poly('LCD electrode | clapper',[(-5.62,3.0),(-5.38,3.0),(-5.38,2.85),(-5.62,2.85)],7.565,ink)
poly('LCD electrode | bell crown',[(-5.58,4.4),(-5.42,4.4),(-5.42,4.6),(-5.58,4.6)],7.565,ink)
for i in range(4):
 p=[(-9.5+i*.35+.28*math.cos(t),3.85+.45*math.sin(t)) for t in [(-1+j/12*2)*1.05 for j in range(13)]];flatline('LCD electrode | signal',p,.10,7.565,ink)

# Convex molded shoulder profile replaces broad straight chamfer facets.
remove('Bezel | inclined inner shoulder')
profiles=[(31.8,32,4,7.15),(31.2,31.4,3.8,7.45),(30.5,30.7,3.55,7.69),(29.6,29.8,3.3,7.86),(28.2,28.2,3.0,7.95)]
v=[]
for w,h,c,z in profiles:v.extend((x,y,z) for x,y in chamfer(w,h,c))
n=len(chamfer(31.8,32,4));f=[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for k in range(len(profiles)-1) for i in range(n)]
me=bpy.data.meshes.new('Convex molded bezel');me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('Bezel | inclined inner shoulder',me);asset.objects.link(o);o.parent=root;me.materials.append(resin)
for p in me.polygons:p.use_smooth=True
m=o.modifiers.new('Molded bezel thickness','SOLIDIFY');m.thickness=.25
for name in ['Case | tapered lugs and shell','Bezel | lower chamfer']:
 o=D[name]
 for p in o.data.polygons:p.use_smooth=True
 for m in o.modifiers:
  if m.type=='BEVEL':m.segments=6;m.harden_normals=True
# Thin black gasket at the actual back/case manufacturing boundary.
ringmesh('Caseback | compressed black perimeter gasket',chamfer(29.8,31.0,3.9),chamfer(29.0,30.2,3.65),.98,black)

# Reference-informed material separation: resin remains dielectric and satin.
for ma,rough,col in [(resin,.48,(.014,.016,.019)),(strapmat,.54,(.009,.011,.013))]:
 p=next(n for n in ma.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=0;p.inputs['IOR'].default_value=1.48;p.inputs['Specular IOR Level'].default_value=.35
 for n in ma.node_tree.nodes:
  if n.type=='MAP_RANGE':n.inputs['To Min'].default_value=rough-.035;n.inputs['To Max'].default_value=rough+.035
  if n.type=='BUMP':n.inputs['Strength'].default_value=.22;n.inputs['Distance'].default_value=.000008
# Polished acrylic uses a controlled uniform microfacet finish to avoid frosted glare.
p=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Roughness'].default_value=.008
n=glass.node_tree.nodes;l=glass.node_tree.links;geo=n.new('ShaderNodeNewGeometry');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3500;tex.inputs['Detail'].default_value=2;l.new(geo.outputs['Position'],tex.inputs['Vector']);r=n.new('ShaderNodeMapRange');r.inputs['To Min'].default_value=.008;r.inputs['To Max'].default_value=.008;l.new(tex.outputs['Fac'],r.inputs['Value']);l.new(r.outputs['Result'],p.inputs['Roughness'])
# Long shaped reflection gradients derived from the real Noir studio ratios.
def aim(o,pos,target):o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
o=D['Key | upper-left tall silk'];aim(o,(-.095,-.16,.11),(0,0,.041));o.data.energy=.75;o.data.size=.055;o.data.size_y=.12
o=D['Fill | quiet frontal silk'];aim(o,(.10,-.17,.07),(0,0,.041));o.data.energy=.085;o.data.size=.075;o.data.size_y=.10
o=D['Rim | right vertical strip'];aim(o,(.075,.020,.08),(0,0,.042));o.data.energy=.18;o.data.size=.012;o.data.size_y=.095
D['Upper band | edge strip'].data.energy=.028
bpy.context.scene.view_settings.exposure=-.40
root['realism_refinement']='Flat underside printing; recessed LCD with clean flat electrodes; reconstructed squared CASIO mark; convex molded shoulder; dielectric satin resin and shaped studio gradients.'
print('REALISM_REFINEMENT_APPLIED')
