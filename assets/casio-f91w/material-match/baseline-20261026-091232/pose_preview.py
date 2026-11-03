import bpy
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'previous-flatlay/casio_f91w.blend'))
exec(compile((OUT/'pose_studio.py').read_text(),str(OUT/'pose_studio.py'),'exec'))
