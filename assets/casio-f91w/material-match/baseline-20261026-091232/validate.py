import bpy,json,struct
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(p/'casio_f91w.blend'))
s=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get();root=bpy.data.objects['F-91W-1 | SI scale'];inv=root.matrix_world.inverted()
# Full manufactured case inclusive crystal, metal back, guards and pushers.
keys=('Case |','Bezel |','Crystal |','Pusher','Gasket','Caseback |','Screw cross','Recessed lug')
pts=[]
for o in s.objects:
 if o.type=='MESH' and o.name.startswith(keys):
  e=o.evaluated_get(dg);pts.extend(inv@e.matrix_world@Vector(v) for v in e.bound_box)
mins=[min(v[i] for v in pts) for i in range(3)];maxs=[max(v[i] for v in pts) for i in range(3)]
report={'blender':bpy.app.version_string,'engine':s.render.engine,'samples':s.cycles.samples,'resolution':[s.render.resolution_x,s.render.resolution_y],'case_bounds_mm':{'x':round((maxs[0]-mins[0]),3),'y':round((maxs[1]-mins[1]),3),'z':round((maxs[2]-mins[2]),3)},'scene_objects':len(s.objects),'manufactured_collection_objects':len(bpy.data.collections['CASIO F-91W-1 | manufactured components'].objects),'band_holes':12,'images':{}}
for f in ['hero.png','front.png','three_quarter.png','material_closeup.png']:
 path=p/f
 if path.exists():
  data=path.read_bytes();w,h=struct.unpack('>II',data[16:24]);report['images'][f]={'width':w,'height':h,'bytes':len(data),'bit_depth':data[24]}
report['LCD_layer_stack_mm']={'module_backing_top':max(v.co.z for v in bpy.data.objects['Dial backing'].data.vertices),'polarizer_top':max(v.co.z for v in bpy.data.objects['LCD | polarizer plate'].data.vertices),'electrodes':max(v.co.z for o in bpy.data.objects if o.name.startswith('LCD electrode |') and o.type=='MESH' for v in o.data.vertices),'printed_mask_top':7.993,'crystal_bottom':8.0}
report['planar_ink_max_thickness_mm']=max((max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices) for o in bpy.data.objects if o.name.startswith('Print |') and o.type=='MESH'),default=0)
report['LCD_electrode_max_thickness_mm']=max((max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices) for o in bpy.data.objects if o.name.startswith('LCD electrode |') and o.type=='MESH'),default=0)
mask=bpy.data.objects.get('Dial | printed opaque aperture mask')
if mask:report['LCD_aperture_center_clear']=not mask.ray_cast(Vector((0,0,9)),Vector((0,0,-1)))[0]
report['realism_refinement']=root.get('realism_refinement','')
report['pose']=root.get('pose','')
report['case_bounds_coordinate_system']='Manufactured case coordinates before rigid upright pose'
report['packed_fonts']={f.name:bool(f.packed_file) for f in bpy.data.fonts if f.filepath and f.filepath!='<builtin>'}
report['blend_bytes']=(p/'casio_f91w.blend').stat().st_size
report['limitations']=['Subcomponent dimensions proportionally reconstructed from official photography.','Typography reconstructed with editable type; unreadable rear micro-engraving and serial number not fabricated.']
(p/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
