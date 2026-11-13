"""Technical verification only; never render or assess appearance."""
import hashlib
import json
import struct
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

OUT = Path(__file__).resolve().parent
M = json.loads((OUT/'update-manifest.json').read_text())
SOURCES = list(M['source_blends_sha256'])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def val(v):
    if isinstance(v, (str, int, float, bool)):
        return v
    try:
        return list(v)
    except TypeError:
        return str(v)


def tree_sig(t):
    if t is None:
        return None
    nodes = []
    for n in t.nodes:
        info = {'name':n.name,'type':n.bl_idname}
        for key in ('operation','blend_type','data_type','interpolation','extension','uv_map','space','invert','samples','clamp_factor','clamp_result'):
            if hasattr(n,key):
                info[key] = val(getattr(n,key))
        for direction in ('inputs','outputs'):
            info[direction] = [(s.identifier,val(s.default_value)) for s in getattr(n,direction) if hasattr(s,'default_value')]
        if n.type == 'TEX_IMAGE':
            assert n.image and n.image.packed_file, n.name
            info['image_sha256'] = sha(n.image.packed_file.data)
            info['colorspace'] = n.image.colorspace_settings.name
        if n.type == 'GROUP':
            info['group'] = tree_sig(n.node_tree)
        if hasattr(n,'color_ramp'):
            info['ramp'] = [(e.position,list(e.color)) for e in n.color_ramp.elements]
        nodes.append(info)
    return {'nodes':nodes,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links]}


def mesh_digest(o):
    return sha(repr(([tuple(v.co) for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons],
                     [p.material_index for p in o.data.polygons])).encode())


def open_scene(p):
    bpy.ops.wm.open_mainfile(filepath=p, load_ui=False, use_scripts=False)
    bpy.context.scene.frame_set(1)


def mats():
    return {n:tree_sig(bpy.data.materials[n].node_tree) for n in M['material_ids']}


open_scene(SOURCES[0])
expected_materials = mats()
open_scene(SOURCES[1])
expected_objects = set(o.name for o in bpy.context.scene.objects)
expected_camera_lights = {o.name:[list(r) for r in o.matrix_world] for o in bpy.context.scene.objects if o.type in ('CAMERA','LIGHT')}
gold = tree_sig(bpy.data.materials['Gold wax seal'].node_tree)
frames = (1,30,60,90,120)
before_poses = {}
for f in frames:
    bpy.context.scene.frame_set(f)
    before_poses[f] = {o.name:o.matrix_world.copy() for o in bpy.context.scene.objects if o.type=='MESH'}
open_scene(M['output'])
assert mats() == expected_materials, 'Material graph or color differs from source'
assert tree_sig(bpy.data.materials['Gold wax seal'].node_tree) == gold
assert set(o.name for o in bpy.context.scene.objects) == expected_objects | {'CTRL | Film v3 dimensions'}
assert {o.name:[list(r) for r in o.matrix_world] for o in bpy.context.scene.objects if o.type in ('CAMERA','LIGHT')} == expected_camera_lights
assert {o.name:mesh_digest(o) for o in bpy.context.scene.objects if o.type=='MESH'} == M['mesh_structure_sha256']
root = bpy.data.objects['CTRL | Film v3 dimensions']
root_mat = root.matrix_world.copy()
for f in frames:
    bpy.context.scene.frame_set(f)
    for n,mat in before_poses[f].items():
        expected = root_mat @ mat
        actual = bpy.data.objects[n].matrix_world
        assert max(abs(expected[i][j]-actual[i][j]) for i in range(4) for j in range(4)) < 1e-6, (f,n)
bpy.context.scene.frame_set(1)
shells = [o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('Seal |')]
pts = [o.matrix_world @ v.co for o in shells for v in o.data.vertices]
sizes = [(max(p[i] for p in pts)-min(p[i] for p in pts))*1000 for i in range(3)]
assert all(abs(s-140) < .001 for s in sizes)
expected_images = json.loads((OUT/'reference-measurements.json').read_text())['images']
used_images = [n.image for m in bpy.data.materials if m.users and m.node_tree for n in m.node_tree.nodes if n.type=='TEX_IMAGE']
assert used_images
for i in used_images:
    assert i.packed_file and list(i.size)==[2048,2048]
    assert sha(i.packed_file.data) in {d['sha256'] for d in expected_images.values()}
    # Force decoding, so valid packed metadata alone cannot hide a missing map.
    pixel = i.pixels[0]
for name,info in expected_images.items():
    assert sha(Path(info['path']).read_bytes()) == info['sha256']
uv_min, uv_max = [1,1], [0,0]
for o in shells:
    uvs = o.data.uv_layers.active
    assert uvs.name == 'Film v3 leather UV' and uvs.active_render
    for p in o.data.polygons:
        if o.material_slots[p.material_index].material.name != 'leather-base':
            continue
        for idx in p.loop_indices:
            for axis in (0,1):
                uv_min[axis]=min(uv_min[axis],uvs.data[idx].uv[axis])
                uv_max[axis]=max(uv_max[axis],uvs.data[idx].uv[axis])
# Bounds of the full source exterior square, including the original atlas padding.
assert .224 < uv_min[0] < uv_max[0] < .449
assert 0 < uv_min[1] < uv_max[1] < .225
assert all(sha(Path(p).read_bytes())==h for p,h in M['source_blends_sha256'].items())
report = {'status':'passed','dimensions_mm':sizes,'source_material_graphs_identical':True,
          'original_texture_bytes_verified':True,'extracted_maps':len(expected_images),
          'mesh_structure_unchanged':True,'gold_seal_unchanged':True,
          'door_animation_frames_verified':list(frames),'camera_lights_unchanged':True,
          'exterior_uv_bounds':[uv_min,uv_max],'sources_unchanged':True,
          'visual_approval':'pending designer review'}
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
print('VERIFIED',json.dumps(report))
