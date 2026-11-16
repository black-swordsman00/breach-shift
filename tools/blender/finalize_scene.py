"""Open a scene-only library as an ordinary editable file in factory Blender.

Run in a separate background process so no user workspace/history is copied.
"""
from pathlib import Path

import bpy


destination = Path(bpy.data.filepath)
scene = max(bpy.data.scenes, key=lambda item: len(item.objects))
if not any(obj.type == 'MESH' for obj in scene.objects):
    raise ValueError('The authoring scene has no meshes')
bpy.context.window.scene = scene
for other in list(bpy.data.scenes):
    if other != scene:
        bpy.data.scenes.remove(other)
workspace = bpy.context.window.workspace
screen = bpy.context.window.screen
bpy.data.batch_remove(ids=[other for other in bpy.data.workspaces if other != workspace])
bpy.data.batch_remove(ids=[other for other in bpy.data.screens if other != screen])
for area in screen.areas:
    for space in area.spaces:
        if space.type == 'FILE_BROWSER':
            raise ValueError('Factory authoring layout unexpectedly contains a file browser')
scene.render.filepath = '//renders/'
bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True,
                            relative_remap=False, check_existing=False)
print(f'Finalized editable scene: {len(scene.objects)} objects, clean factory layout')
