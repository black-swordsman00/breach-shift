"""Read CC0 hm08 geometry and morph data; no MakeHuman application code is used."""
from collections import defaultdict
from pathlib import Path


SOURCE_COMMIT = "a8bc2d54ff0ac92e78ff71431b1023eda42bf482"


def read_obj(path: Path):
    vertices, uv, groups = [], [], defaultdict(list)
    group = "default"
    for line in path.read_text(encoding="utf-8").splitlines():
        words = line.split()
        if not words or words[0].startswith("#"):
            continue
        if words[0] == "v":
            vertices.append(tuple(map(float, words[1:4])))
        elif words[0] == "vt":
            uv.append(tuple(map(float, words[1:3])))
        elif words[0] == "g":
            group = words[1]
        elif words[0] == "f":
            indices, texcoords = [], []
            for token in words[1:]:
                components = token.split("/")
                indices.append(int(components[0]) - 1)
                texcoords.append(int(components[1]) - 1 if len(components) > 1 and components[1] else -1)
            groups[group].append((tuple(indices), tuple(texcoords)))
    return vertices, uv, dict(groups)


def apply_targets(vertices, targets):
    result = [list(vertex) for vertex in vertices]
    for path, weight in targets:
        for line in path.read_text(encoding="utf-8").splitlines():
            words = line.split()
            if not words or words[0].startswith("#"):
                continue
            index = int(words[0])
            if not 0 <= index < len(result):
                raise ValueError(f"Morph index {index} is outside the hm08 mesh")
            for axis in range(3):
                result[index][axis] += float(words[axis + 1]) * weight
    return result


def group_center(vertices, faces):
    indices = {index for face, _uv in faces for index in face}
    if not indices:
        raise ValueError("Cannot locate an empty joint helper")
    return tuple(sum(vertices[index][axis] for index in indices) / len(indices) for axis in range(3))
