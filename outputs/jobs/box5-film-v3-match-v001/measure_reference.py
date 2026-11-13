import hashlib
import json
import statistics
from pathlib import Path

import bpy

OUT = Path(__file__).resolve().parent
FILM = '/Users/naufalirsyad/Downloads/perhaps-unboxing-for-designer/source/unboxing-film-v3.blend'
bpy.ops.wm.open_mainfile(filepath=FILM, load_ui=False, use_scripts=False)
bpy.context.scene.frame_set(1)
base = bpy.data.objects['U6f5790de6100']
lid = bpy.data.objects['Uc73a9f4fe739']
inv = base.matrix_world.inverted()
points = [inv @ (o.matrix_world @ v.co) for o in (base, lid) for v in o.data.vertices]
sizes = [(max(v[i] for v in points) - min(v[i] for v in points)) * 1000 for i in range(3)]
measurements = {'closed_shell_dimensions_mm': sizes, 'uv_mm_per_unit': {}}
for o in (base, lid):
    uv = o.data.uv_layers.active.data
    samples = []
    for p in o.data.polygons:
        if p.area < 0.0001:
            continue
        loops = list(p.loop_indices)
        for a, b in zip(loops, loops[1:] + loops[:1]):
            va, vb = (o.data.vertices[o.data.loops[i].vertex_index].co for i in (a, b))
            d = (va-vb).length
            duv = (uv[a].uv-uv[b].uv).length
            if d > 0.02 and duv > 1e-6:
                samples.append(d * 1000 / duv)
    measurements['uv_mm_per_unit'][o.active_material.name] = {
        'min': min(samples), 'max': max(samples), 'median': statistics.median(samples), 'samples': len(samples),
    }
textures = OUT / 'textures'
textures.mkdir(exist_ok=True)
measurements['images'] = {}
for name in ('base_basecolor','base_normal','base_orm','lid_basecolor','lid_normal','lid_orm'):
    i = bpy.data.images[name]
    data = i.packed_file.data
    ext = '.png' if data[:8] == b'\x89PNG\r\n\x1a\n' else '.jpg'
    path = textures / (name + ext)
    path.write_bytes(data)
    measurements['images'][name] = {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
(OUT / 'reference-measurements.json').write_text(json.dumps(measurements, indent=2))
print('MEASUREMENTS', json.dumps(measurements))
