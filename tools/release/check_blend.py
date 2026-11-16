"""Check a production scene in factory Blender with automatic scripts disabled."""
import re

import bpy


private = re.compile(r"(?i)(?:blendermcp|api_key|secret|token|password)")
if not any(obj.type == 'MESH' for obj in bpy.context.scene.objects):
    raise ValueError('No editable production scene is active')
for group in (bpy.data.scenes,bpy.data.objects,bpy.data.materials,bpy.data.worlds):
    for item in group:
        if any(private.search(key) for key in item.keys()):
            raise ValueError("Private add-on properties were serialized into the scene")
if bpy.data.texts:
    raise ValueError("The scene contains embedded scripts")
if bpy.data.libraries:
    raise ValueError("The scene depends on external Blender libraries")
textures = [image for image in bpy.data.images if image.type not in {'RENDER_RESULT','COMPOSITING'}]
for image in textures:
    if not image.packed_file or not image.filepath.replace('\\','/').startswith('//textures/'):
        raise ValueError("A texture is unpacked or contains an external filesystem path")
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        if obj.location.length > 1e-5 or any(abs(value-1)>1e-5 for value in obj.scale) or any(abs(value)>1e-5 for value in obj.rotation_euler):
            raise ValueError("Mesh transforms were not applied")
print(f"Scene verified: {len(textures)} packed images, no private add-on properties or embedded scripts")
