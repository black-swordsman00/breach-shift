"""Blender-only export helpers for self-contained, privacy-safe production GLBs."""
from contextlib import contextmanager
from pathlib import Path
import subprocess

import bpy


def prepare_game_textures(materials, maximum_size=1024):
    """Use 8-bit game textures; scan sources often contain costly 16-bit PNGs."""
    converted = {}
    for material in materials:
        if not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if node.type != "TEX_IMAGE" or node.image is None:
                continue
            source = node.image
            if source.name.endswith("_game_1k"):
                continue
            if source.name not in converted:
                width, height = source.size
                factor = min(1.0, maximum_size / max(width, height))
                width, height = max(1, round(width*factor)), max(1, round(height*factor))
                source.scale(width, height)
                image = bpy.data.images.new(source.name + "_game_1k", width=width, height=height,
                                            alpha=True, float_buffer=False,
                                            is_data=source.colorspace_settings.is_data)
                image.colorspace_settings.name = source.colorspace_settings.name
                image.pixels[:] = source.pixels[:]
                image.pack()
                converted[source.name] = image
                source.use_fake_user = False
            node.image = converted[source.name]


def apply_transforms(objects):
    """Bake world transforms into mesh data, retaining UV layers."""
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [obj for obj in objects if obj.type == "MESH"]
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        obj.select_set(True)
    if meshes:
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return meshes


def triangle_count(objects):
    total = 0
    for obj in objects:
        if obj.type == "MESH":
            obj.data.calc_loop_triangles()
            total += len(obj.data.loop_triangles)
    return total


def export_glb(objects, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.context.view_layer.update()
    bpy.ops.file.pack_all()
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_yup=True, export_apply=True, export_extras=False,
        export_materials="EXPORT", export_texcoords=True,
        export_normals=True, export_tangents=True,
        export_cameras=False, export_lights=False,
    )
    return {"file": path.name, "triangles": triangle_count(objects),
            "bytes": path.stat().st_size}


@contextmanager
def private_scene_settings_removed():
    """Never serialize MCP credentials, account settings or embedded scripts."""
    saved = []
    for scene in bpy.data.scenes:
        names = {prop.identifier for prop in scene.bl_rna.properties
                 if prop.identifier.lower().startswith("blendermcp_")}
        names.update(name for name in dir(scene) if name.lower().startswith("blendermcp_"))
        for name in names:
            if not scene.is_property_set(name):
                continue
            saved.append((scene, name, getattr(scene, name)))
            scene.property_unset(name)
    try:
        yield
    finally:
        for scene, name, value in saved:
            setattr(scene, name, value)


def save_clean_blend(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    for image in bpy.data.images:
        if image.packed_file:
            image.filepath = "//textures/" + image.name.replace("/", "_").replace("\\", "_")
    for text in list(bpy.data.texts):
        bpy.data.texts.remove(text)
    bpy.context.scene.render.filepath = "//renders/"
    bpy.ops.file.pack_all()
    with private_scene_settings_removed():
        # Write scene dependencies only. A normal full-session save includes
        # file-browser history and workspace paths outside the asset itself.
        bpy.data.libraries.write(str(path), {bpy.context.scene}, path_remap="NONE",
                                 fake_user=True, compress=True)
    subprocess.run([bpy.app.binary_path, "--background", "--factory-startup",
                    "--disable-autoexec", "--python-exit-code", "1", str(path),
                    "--python", str(Path(__file__).with_name("finalize_scene.py"))],
                   check=True, timeout=90, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
