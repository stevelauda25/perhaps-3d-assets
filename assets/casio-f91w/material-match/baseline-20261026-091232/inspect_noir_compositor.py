import bpy,json
from pathlib import Path
s=bpy.data.scenes['NOIR | Product Studio']
result={'properties':[],'node_groups':[]}
for p in s.bl_rna.properties:
 if 'node' in p.identifier:
  x=getattr(s,p.identifier,None);result['properties'].append([p.identifier,str(x)])
  if hasattr(x,'nodes'):result['nodes']=[n.bl_idname for n in x.nodes];result['links']=[(l.from_node.bl_idname,l.to_node.bl_idname) for l in x.links]
for g in bpy.data.node_groups:
 result['node_groups'].append({'name':g.name,'type':g.bl_idname,'nodes':[n.bl_idname for n in g.nodes]})
Path(__file__).with_name('noir_compositor_inspection.json').write_text(json.dumps(result,indent=2))
print(result)
