import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
SOURCES = {
    'film': Path('/Users/naufalirsyad/Downloads/perhaps-unboxing-for-designer/source/unboxing-film-v3.blend'),
    'box5': ROOT.parents[2] / 'Box 3D Blender/Box 5/Box 5 - Leather gold seal.blend',
}


def value(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    try:
        return list(v)
    except TypeError:
        return str(v)


def material(m):
    return {
        'name': m.name,
        'diffuse_color': list(m.diffuse_color),
        'nodes': [{
            'name': n.name, 'type': n.bl_idname,
            'inputs': {s.identifier: value(s.default_value) for s in n.inputs if hasattr(s, 'default_value')},
            'image': n.image.name if n.type == 'TEX_IMAGE' and n.image else None,
            'uv_map': n.uv_map if n.type == 'UVMAP' else None,
        } for n in m.node_tree.nodes] if m.use_nodes else [],
        'links': [(l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier)
                  for l in m.node_tree.links] if m.use_nodes else [],
    }


for label, path in SOURCES.items():
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    saved_frame = scene.frame_current
    scene.frame_set(scene.frame_start)
    objects = []
    for o in scene.objects:
        entry = {
            'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None,
            'location': list(o.location), 'scale': list(o.scale),
            'dimensions_mm': [v * scene.unit_settings.scale_length * 1000 for v in o.dimensions],
            'world_matrix': [list(row) for row in o.matrix_world],
            'materials': [s.material.name if s.material else None for s in o.material_slots],
            'hide_render': o.hide_render,
            'collections': [c.name for c in o.users_collection],
            'modifiers': [(m.name, m.type) for m in o.modifiers],
            'constraints': [(c.name, c.type) for c in o.constraints],
            'animated': bool(o.animation_data),
        }
        if o.type == 'MESH':
            pts = [o.matrix_world @ Vector(p) for p in o.bound_box]
            entry['bounds_mm'] = [[f(p[i] for p in pts) * scene.unit_settings.scale_length * 1000
                                   for i in range(3)] for f in (min, max)]
            entry['vertices'] = len(o.data.vertices)
            entry['uvs'] = [u.name for u in o.data.uv_layers]
        objects.append(entry)
    report = {
        'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'frame_start': scene.frame_start, 'frame_end': scene.frame_end, 'saved_frame': saved_frame,
        'unit_scale': scene.unit_settings.scale_length,
        'objects': objects,
        'materials': [material(m) for m in bpy.data.materials if m.users],
        'images': [{
            'name': i.name, 'filepath': i.filepath, 'size': list(i.size),
            'packed': bool(i.packed_file), 'colorspace': i.colorspace_settings.name,
            'exists': Path(bpy.path.abspath(i.filepath)).is_file(),
        } for i in bpy.data.images],
    }
    (ROOT / f'{label}-inspection.json').write_text(json.dumps(report, indent=2))
    print('INSPECTION', label, json.dumps({
        'frame': saved_frame, 'units': report['unit_scale'],
        'objects': [{k: o[k] for k in ('name', 'type', 'parent', 'dimensions_mm', 'materials', 'animated')}
                    for o in objects if o['type'] in ('MESH', 'EMPTY')],
        'images': report['images'],
    }))
