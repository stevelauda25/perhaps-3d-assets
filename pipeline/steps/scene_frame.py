"""scene_frame: set the scene to one frame (e.g. the last frame of a lid animation) for the renders that follow.

Params: frame (int).
"""


def run(params):
    import bpy
    scene = bpy.context.scene
    scene.frame_set(params["frame"])
    return {"frame": scene.frame_current}
