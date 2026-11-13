"""Transfer designer film materials verbatim; adapt only UVs and overall size.

No new shaders are constructed. Material IDs are the source Blender datablock IDs.
The original atlas bytes remain embedded, and are also extracted alongside this job.
"""
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
FILM = Path('/Users/naufalirsyad/Downloads/perhaps-unboxing-for-designer/source/unboxing-film-v3.blend')
BOX = PROJECT / 'Box 3D Blender/Box 5/Box 5 - Leather gold seal.blend'
DEST = OUT / 'Box 5 - Film v3 matched.blend'
IDS = ('leather-base', 'lid-suede', 'cavity-lining')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mesh_digest(o):
    return hashlib.sha256(repr((
        [tuple(v.co) for v in o.data.vertices],
        [tuple(p.vertices) for p in o.data.polygons],
        [p.material_index for p in o.data.polygons],
    )).encode()).hexdigest()


def bounds(objects):
    pts = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    lo = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return lo, hi


assert not DEST.exists(), 'Use a new version instead of replacing an output'
protected = {str(p): sha(p) for p in (FILM, BOX)}
bpy.ops.wm.open_mainfile(filepath=str(FILM), load_ui=False, use_scripts=False)
bpy.context.scene.frame_set(1)
source = bpy.data.objects['U6f5790de6100']
# The exterior bottom is a complete, grain-bearing square in the base atlas.
# Its padding permits the 0.6 mm bevel extension to the full 140 mm face.
face = next(p for p in source.data.polygons if p.area > .009 and p.normal.z < -.99)
loops = list(face.loop_indices)
xy = [source.data.vertices[source.data.loops[i].vertex_index].co for i in loops]
uv = [source.data.uv_layers.active.data[i].uv.copy() for i in loops]
coords = Matrix([(p.x, p.y, 1) for p in xy]).inverted()
u_coeff = coords @ Vector([p.x for p in uv])
v_coeff = coords @ Vector([p.y for p in uv])
reference_ids = {'base': source.name, 'lid': 'Uc73a9f4fe739'}
source_colors = {name: list(bpy.data.materials[name].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)
                 for name in IDS}

bpy.ops.wm.open_mainfile(filepath=str(BOX), load_ui=False, use_scripts=False)
scene = bpy.context.scene
scene.frame_set(1)
meshes = [o for o in scene.objects if o.type == 'MESH']
structure_before = {o.name: mesh_digest(o) for o in meshes}
old_materials = {name: bpy.data.materials.get(name) for name in IDS}
with bpy.data.libraries.load(str(FILM), link=False) as (have, want):
    assert set(IDS) <= set(have.materials)
    want.materials = list(IDS)
imported = dict(zip(IDS, want.materials))
for name, old in old_materials.items():
    if old:
        old.user_remap(imported[name])
        if old.users == 0:
            bpy.data.materials.remove(old)
for name, m in imported.items():
    m.name = name
    m['source_material_id'] = name
    m['source_blend_sha256'] = protected[str(FILM)]

assignments = []
for o in meshes:
    if o.name in ('Body | back', 'Interior | raised display stage'):
        for slot in o.material_slots:
            if slot.material == imported['lid-suede']:
                slot.material = imported['cavity-lining']
                assignments.append([o.name, 'lid-suede', 'cavity-lining'])

shells = [o for o in meshes if not o.name.startswith('Seal |')]
lo, hi = bounds(shells)
size_before = hi - lo
target = Vector((.14, .14, .14))
factor = Vector([target[i] / size_before[i] for i in range(3)])
root = bpy.data.objects.new('CTRL | Film v3 dimensions', None)
scene.collection.objects.link(root)
root.empty_display_type = 'PLAIN_AXES'
# Root parenting preserves both existing door actions and seal-to-door parenting.
for o in meshes:
    if o.parent is None:
        world = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = world
root.scale = factor
root.location = (0, 0, -lo.z * factor.z)
bpy.context.view_layer.update()

for o in shells:
    layer = o.data.uv_layers.new(name='Film v3 leather UV')
    for p in o.data.polygons:
        axis = max(range(3), key=lambda i: abs((o.matrix_world.to_3x3() @ p.normal)[i]))
        for idx in p.loop_indices:
            point = o.matrix_world @ o.data.vertices[o.data.loops[idx].vertex_index].co
            if axis == 0:
                q = Vector((point.y, point.z - .07, 1))
            elif axis == 1:
                q = Vector((point.x, point.z - .07, 1))
            else:
                q = Vector((point.x, point.y, 1))
            layer.data[idx].uv = (u_coeff.dot(q), v_coeff.dot(q))
    o.data.uv_layers.active = layer
    layer.active_render = True

assert structure_before == {o.name: mesh_digest(o) for o in meshes}
new_lo, new_hi = bounds(shells)
assert all(abs((new_hi-new_lo)[i] - .14) < 1e-7 for i in range(3))
assert all(tuple(imported[n].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value) == tuple(source_colors[n]) for n in IDS)
for image in bpy.data.images:
    if image.packed_file:
        image.filepath = '//textures/' + image.name + '.jpg'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True)
assert all(sha(Path(p)) == h for p, h in protected.items())
manifest = {
    'source_blends_sha256': protected,
    'output': str(DEST), 'output_sha256': sha(DEST),
    'reference_shells': reference_ids,
    'material_ids': list(IDS), 'interior_assignments': assignments,
    'source_interior_colors_linear': {n: source_colors[n] for n in ('lid-suede','cavity-lining')},
    'shell_dimensions_before_mm': [v*1000 for v in size_before],
    'shell_dimensions_after_mm': [v*1000 for v in new_hi-new_lo],
    'root_scale': list(factor),
    'atlas_uv_from_local_face_xy_m': [list(u_coeff),list(v_coeff)],
    'atlas_note': 'Original base exterior bottom atlas island reused at its physical scale on each box panel. Original packed images and shader graphs retained.',
    'mesh_structure_sha256': structure_before,
    'visual_approval': 'pending designer review',
}
(OUT/'update-manifest.json').write_text(json.dumps(manifest, indent=2))
print('UPDATE_OK', json.dumps({'output':str(DEST),'shell_dimensions_mm':manifest['shell_dimensions_after_mm'],'materials':list(IDS)}))
