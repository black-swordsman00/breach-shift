"""Reusable lit meshes with normals, UVs and deterministic material grain."""

from functools import lru_cache
from math import acos, cos, degrees, pi, sin
from random import Random

from panda3d.core import (BitMask32, Geom, GeomNode, GeomTriangles, GeomVertexData,
                         GeomVertexFormat, GeomVertexWriter, Material, NodePath,
                         PNMImage, Point3, Quat, Texture, Vec3)


def _mesh(name, vertices, normals, uvs, triangles):
    data = GeomVertexData(name, GeomVertexFormat.getV3n3t2(), Geom.UHStatic)
    data.setNumRows(len(vertices))
    position = GeomVertexWriter(data, "vertex")
    normal = GeomVertexWriter(data, "normal")
    texcoord = GeomVertexWriter(data, "texcoord")
    for vertex, vector, uv in zip(vertices, normals, uvs):
        position.addData3f(*vertex)
        normal.addData3f(*vector)
        texcoord.addData2f(*uv)
    primitive = GeomTriangles(Geom.UHStatic)
    for triangle in triangles:
        primitive.addVertices(*triangle)
    primitive.closePrimitive()
    geom = Geom(data)
    geom.addPrimitive(primitive)
    node = GeomNode(name)
    node.addGeom(geom)
    result = NodePath(node)
    result.setCollideMask(BitMask32.allOff())
    return result


@lru_cache(maxsize=32)
def sphere(segments=16, rings=10):
    vertices, normals, uvs, triangles = [], [], [], []
    for row in range(rings + 1):
        latitude = -pi / 2 + pi * row / rings
        for column in range(segments + 1):
            longitude = 2 * pi * column / segments
            vertex = (cos(latitude) * cos(longitude), cos(latitude) * sin(longitude), sin(latitude))
            vertices.append(vertex)
            normals.append(vertex)
            uvs.append((column / segments, row / rings))
    for row in range(rings):
        for column in range(segments):
            a = row * (segments + 1) + column
            b = a + segments + 1
            triangles.extend(((a, a + 1, b), (a + 1, b + 1, b)))
    return _mesh("rounded-mesh", vertices, normals, uvs, triangles)


@lru_cache(maxsize=32)
def cylinder(top=1.0, segments=16):
    vertices, normals, uvs, triangles = [], [], [], []
    for z, radius in ((0, 1), (1, top)):
        for column in range(segments + 1):
            angle = column * 2 * pi / segments
            vector = Vec3(cos(angle), sin(angle), 1 - top)
            vector.normalize()
            vertices.append((radius * cos(angle), radius * sin(angle), z))
            normals.append(tuple(vector))
            uvs.append((column / segments, z))
    for column in range(segments):
        a, b = column, column + segments + 1
        triangles.extend(((a, a + 1, b), (a + 1, b + 1, b)))
    for z, radius, direction in ((0, 1, -1), (1, top, 1)):
        center = len(vertices)
        vertices.append((0, 0, z))
        normals.append((0, 0, direction))
        uvs.append((0.5, 0.5))
        for column in range(segments + 1):
            angle = column * 2 * pi / segments
            vertices.append((radius * cos(angle), radius * sin(angle), z))
            normals.append((0, 0, direction))
            uvs.append(((cos(angle) + 1) / 2, (sin(angle) + 1) / 2))
        for column in range(segments):
            a, b = center + column + 1, center + column + 2
            triangles.append((center, a, b) if direction > 0 else (center, b, a))
    return _mesh("cylinder-mesh", vertices, normals, uvs, triangles)


@lru_cache(maxsize=1)
def box():
    vertices, normals, uvs, triangles = [], [], [], []
    for normal, corners in (
        ((1, 0, 0), ((.5, -.5, -.5), (.5, .5, -.5), (.5, .5, .5), (.5, -.5, .5))),
        ((-1, 0, 0), ((-.5, .5, -.5), (-.5, -.5, -.5), (-.5, -.5, .5), (-.5, .5, .5))),
        ((0, 1, 0), ((.5, .5, -.5), (-.5, .5, -.5), (-.5, .5, .5), (.5, .5, .5))),
        ((0, -1, 0), ((-.5, -.5, -.5), (.5, -.5, -.5), (.5, -.5, .5), (-.5, -.5, .5))),
        ((0, 0, 1), ((-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5))),
        ((0, 0, -1), ((-.5, .5, -.5), (.5, .5, -.5), (.5, -.5, -.5), (-.5, -.5, -.5))),
    ):
        start = len(vertices)
        vertices.extend(corners)
        normals.extend([normal] * 4)
        uvs.extend(((0, 0), (1, 0), (1, 1), (0, 1)))
        triangles.extend(((start, start + 1, start + 2), (start, start + 2, start + 3)))
    return _mesh("panel-mesh", vertices, normals, uvs, triangles)


@lru_cache(maxsize=12)
def grain(surface):
    rng = Random(surface)
    image = PNMImage(64, 64, 3)
    for y in range(64):
        for x in range(64):
            value = rng.uniform(.77, 1.0)
            if surface == "cloth" and (x % 3 == 0 or y % 3 == 0):
                value *= .86
            if surface == "stone" and (y % 16 == 0 or (x + (y // 16 % 2) * 16) % 32 == 0):
                value *= .46
            image.setXel(x, y, value, value, value)
    texture = Texture(surface)
    texture.load(image)
    texture.setWrapU(Texture.WMRepeat)
    texture.setWrapV(Texture.WMRepeat)
    texture.setMinfilter(Texture.FTLinearMipmapLinear)
    texture.setMagfilter(Texture.FTLinear)
    return texture


def part(parent, name, shape, position, scale, color, surface="cloth"):
    model = shape.copyTo(parent)
    model.setName(name)
    model.setPos(*position)
    model.setScale(*scale)
    model.setColor(*color)
    model.setTexture(grain(surface), 1)
    material = Material(surface)
    material.setDiffuse(color)
    material.setAmbient(color)
    material.setSpecular((.28, .28, .28, 1) if surface == "metal" else (.04, .04, .04, 1))
    material.setShininess(35 if surface == "metal" else 4)
    model.setMaterial(material)
    return model


def flatten_local(node):
    """Batch static geometry without baking away an actor or collision anchor."""
    transform = node.getTransform()
    node.clearTransform()
    node.flattenStrong()
    node.setTransform(transform)


def rod(parent, name, start, end, radius, color, surface="cloth", top=.85, segments=12):
    direction = Point3(*end) - Point3(*start)
    length = direction.length()
    if length <= 0:
        raise ValueError("A model segment must have a positive length.")
    direction /= length
    node = part(parent, name, cylinder(top, segments), start, (radius, radius, length), color, surface)
    axis = Vec3(0, 0, 1).cross(direction)
    rotation = Quat()
    if axis.lengthSquared() > .000001:
        axis.normalize()
        rotation.setFromAxisAngle(degrees(acos(max(-1, min(1, direction.z)))), axis)
    elif direction.z < 0:
        rotation.setFromAxisAngle(180, Vec3(1, 0, 0))
    node.setQuat(rotation)
    return node
