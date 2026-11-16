"""Blender-only construction tools for the editable game art workshop."""
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


def empty(name, parent=None, location=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent, obj.location = parent, location
    return obj


def mesh(name, vertices, faces, material, parent=None, uv=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    if material:
        data.materials.append(material)
    layer = data.uv_layers.new(name="UVMap")
    for poly in data.polygons:
        poly.use_smooth = True
        normal = poly.normal
        drop = max(range(3), key=lambda axis: abs(normal[axis]))
        axes = [axis for axis in range(3) if axis != drop]
        for loop_index in poly.loop_indices:
            vertex = data.vertices[data.loops[loop_index].vertex_index]
            layer.data[loop_index].uv = uv[loop_index] if uv else (vertex.co[axes[0]] * 4, vertex.co[axes[1]] * 4)
    return obj


def texture(name, category="fabric", size=512):
    existing = bpy.data.images.get(name)
    if existing:
        return existing
    rng = np.random.default_rng(725)
    y, x = np.mgrid[0:size, 0:size] / size
    value = np.zeros((size, size))
    for frequency, amplitude in ((3, .13), (11, .08), (37, .05), (121, .025)):
        phase = rng.random(3) * math.tau
        value += amplitude * np.sin(x * frequency * math.tau + phase[0]) * np.cos(y * frequency * math.tau + phase[1])
    value += rng.normal(0, .025, (size, size))
    if category == "fabric":
        value += .035 * (np.sin(x * math.tau * 240) + np.cos(y * math.tau * 240))
    if category == "metal":
        value += .04 * np.sin(y * math.tau * 210)
    level = np.clip(.78 + value, .25, .98)
    pixels = np.ones((size, size, 4), dtype=np.float32)
    for channel in range(3):
        pixels[:, :, channel] = level
    image = bpy.data.images.new(name, width=size, height=size)
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    return image


def material(name, color, category="fabric", roughness=.83, metallic=0):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = texture("BS_" + category + "_grain", category)
    tint = nodes.new("ShaderNodeMixRGB")
    tint.blend_type = "MULTIPLY"
    tint.inputs[0].default_value = 1
    tint.inputs[2].default_value = (*color, 1)
    links.new(tex.outputs["Color"], tint.inputs[1])
    links.new(tint.outputs[0], shader.inputs["Base Color"])
    if category in ("skin", "fabric", "leather"):
        normal_image = bpy.data.images.get("BS_" + category + "_tangent_normal")
        if normal_image is None:
            normal_image = bpy.data.images.new("BS_" + category + "_tangent_normal", width=512, height=512)
            normal_image.colorspace_settings.name = "Non-Color"
            height = np.asarray(tex.image.pixels[:], dtype=np.float32).reshape((512, 512, 4))[:, :, 0]
            dy, dx = np.gradient(height)
            vectors = np.stack((-dx * .7, -dy * .7, np.ones_like(dx)), axis=2)
            vectors /= np.linalg.norm(vectors, axis=2)[:, :, None]
            rgba = np.ones((512, 512, 4), dtype=np.float32)
            rgba[:, :, :3] = vectors * .5 + .5
            normal_image.pixels.foreach_set(rgba.ravel())
            normal_image.pack()
        normal_tex = nodes.new("ShaderNodeTexImage")
        normal_tex.image = normal_image
        normal = nodes.new("ShaderNodeNormalMap")
        normal.inputs["Strength"].default_value = .5
        links.new(normal_tex.outputs["Color"], normal.inputs["Color"])
        links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    # glTF exports a direct image multiplied by the material base-color factor.
    # Use image pixels tinted on disk so the exact color also survives export.
    tinted = tex.image.copy()
    tinted.name = name + "_albedo"
    pixels = np.asarray(tex.image.pixels[:], dtype=np.float32).reshape((-1, 4))
    # Blender image pixels are linear; the exporter stores the tagged sRGB PNG.
    pixels[:, :3] *= np.asarray(color)
    tinted.pixels.foreach_set(pixels.ravel())
    tinted.pack()
    tex.image = tinted
    links.new(tex.outputs["Color"], shader.inputs["Base Color"])
    nodes.remove(tint)
    return mat


def box(name, center, dimensions, mat, parent=None, bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name, obj.location, obj.dimensions, obj.parent = name, center, dimensions, parent
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Manufactured rounded edges", "BEVEL")
        modifier.width, modifier.segments = bevel, 3
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.modifiers.new("Weighted edge normals", "WEIGHTED_NORMAL")
    return obj


def sphere(name, center, scale, mat, parent=None, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=16, location=center)
    obj = bpy.context.object
    obj.name, obj.scale, obj.parent = name, scale, parent
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def tube(name, points, radius, mat, parent=None, sides=10, radii=None, caps=True):
    points = [Vector(point) for point in points]
    vertices, faces = [], []
    for index, point in enumerate(points):
        tangent = points[min(index + 1, len(points) - 1)] - points[max(0, index - 1)]
        tangent.normalize()
        normal = tangent.cross(Vector((0, 0, 1)))
        if normal.length < .01:
            normal = tangent.cross(Vector((0, 1, 0)))
        normal.normalize()
        binormal = tangent.cross(normal).normalized()
        width = radius * (radii[index] if radii else 1)
        for side in range(sides):
            angle = side * math.tau / sides
            vertices.append(point + width * (math.cos(angle) * normal + math.sin(angle) * binormal))
        if index:
            for side in range(sides):
                a, b = index * sides + side, index * sides + (side + 1) % sides
                faces.append((a - sides, b - sides, b, a))
    if caps:
        faces += [tuple(reversed(range(sides))), tuple((len(points) - 1) * sides + side for side in range(sides))]
    return mesh(name, vertices, faces, mat, parent)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def studio(height, wide=False):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x = 1440 if wide else 960
    scene.render.resolution_y = 960 if wide else 1200
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    floor = material("Studio_charcoal", (.027, .033, .04), "metal", .9)
    box("STUDIO_floor", (0, 0, -.045), (200, 200, .08), floor, bevel=0)
    camera_data = bpy.data.cameras.new("Review_camera")
    camera = bpy.data.objects.new("STUDIO_camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (height * 1.55, height * 2.6, height * .82)
    aim(camera, (0, 0, height * .50))
    camera_data.type, camera_data.ortho_scale = "ORTHO", height * 1.22
    scene.camera = camera
    for name, position, power, color, size in (
        ("key", (-2, 4, 4), 550, (1, .84, .68), 3),
        ("fill", (3, 2, 2), 220, (.65, .78, 1), 2),
        ("rim", (-2, -2, 3), 600, (.48, .70, 1), 2),
    ):
        data = bpy.data.lights.new("STUDIO_" + name, "AREA")
        data.energy, data.color, data.shape, data.size = power, color, "DISK", size
        light = bpy.data.objects.new(data.name, data)
        bpy.context.collection.objects.link(light)
        light.location = position
        aim(light, (0, 0, height * .65))
    scene.world.color = (.10, .10, .10)
    return camera


def save_asset(root, destination: Path, render_path: Path | None = None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for child in root.children_recursive:
        child.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(destination.with_suffix(".blend")), compress=True)
    bpy.ops.export_scene.gltf(filepath=str(destination.with_suffix(".glb")), export_format="GLB",
                              use_selection=True, export_yup=True, export_extras=True,
                              export_materials="EXPORT", export_apply=True)
    if render_path:
        render_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.context.scene.render.filepath = str(render_path)
        bpy.ops.render.render(write_still=True)
