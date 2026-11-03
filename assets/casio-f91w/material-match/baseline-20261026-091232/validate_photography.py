"""Reopen and validate the exact delivered file, extending existing checks."""
import bpy,runpy,json,hashlib,struct
from pathlib import Path
P=Path(__file__).resolve().parent
def protected_geometry():
 result={}
 for o in bpy.data.objects:
  if o.type=='MESH' and (o.name.startswith(('Case |','Caseback |','Buckle','Keeper','Perforated','Pusher','Recessed lug')) or o.name.startswith('Bezel |')):
   data={'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons],'matrix':[list(r) for r in o.matrix_world]}
   result[o.name]=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
 return result
bpy.ops.wm.open_mainfile(filepath=str(P/'backup-20261026-083440/casio_f91w.blend1'))
baseline=protected_geometry()
baseline_cameras={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects if o.type=='CAMERA'}
runpy.run_path(str(P/'validate.py'))
report=json.loads((P/'validation.json').read_text());s=bpy.context.scene
assert baseline==protected_geometry(),'Protected manufactured geometry changed'
assert baseline_cameras=={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects if o.type=='CAMERA'},'Camera pose changed'
report['unchanged_manufactured_geometry']=list(baseline)
report['camera_transforms_preserved']=True
report['photography_refinement']=bpy.data.objects['F-91W-1 | SI scale'].get('photography_refinement')
report['saved_file']=bpy.data.filepath
report['blend_sha256']=hashlib.sha256((P/'casio_f91w.blend').read_bytes()).hexdigest()
report['source_baseline']='backup-20261026-083440/casio_f91w.blend1'
report['verified_graphics_source']='references/casio-f91w/F-91W-1_06.jpg'
report['traced_graphics']=[o.name for o in s.objects if o.name.startswith('Verified print |')]
report['microtexture']={m.name:{k:m[k] for k in ['grain_spacing_m','height_bound_m']} for m in bpy.data.materials if 'grain_spacing_m' in m}
report['render_seconds']=json.loads((P/'photography_render_times.json').read_text())
report['limitations']=['Subcomponent dimensions reconstructed from official photography; no manufacturer CAD available.','Selected lettering and indicator outlines traced from a product photograph, with finite reference resolution.','Unreadable rear micro-engraving and serial number omitted rather than invented.']
assert report['case_bounds_mm']=={'x':35.2,'y':38.2,'z':8.5},report['case_bounds_mm']
assert report['samples']>=512 and report['engine']=='CYCLES'
assert report['LCD_aperture_center_clear']
assert all(report['packed_fonts'].values())
for name,v in report['images'].items():
 assert v['bit_depth']==16
 assert [v['width'],v['height']]==([2048,4438] if name=='hero.png' else [2400,2400])
 report['images'][name]['sha256']=hashlib.sha256((P/name).read_bytes()).hexdigest()
(P/'validation.json').write_text(json.dumps(report,indent=2))
print('VALIDATION_PASSED',report['case_bounds_mm'],len(report['traced_graphics']),report['blend_sha256'])
