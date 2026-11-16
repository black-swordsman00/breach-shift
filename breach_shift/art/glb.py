"""Validate local, embedded glTF assets before the engine imports them."""
import json
from pathlib import Path
import re
import struct


_PRIVATE_PATH = re.compile(r"(?i)(?:[a-z]:[\\/]|/(?:users|home)/|\\\\[^\\]+\\)")


def inspect_glb(path: Path, *, triangle_limit: int | None = None) -> dict:
    """Reject broken/external assets and return export statistics.

    A triangle limit is exclusive: weapons must contain fewer than 5,000
    triangles and zombies fewer than 12,000.
    """
    path = Path(path)
    if path.stat().st_size > 96 * 1024 * 1024:
        raise ValueError("GLB exceeds the 96 MiB per-asset budget")
    data = path.read_bytes()
    if len(data) < 28:
        raise ValueError("Incomplete GLB")
    magic, version, length = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2 or length != len(data):
        raise ValueError("Invalid GLB header or length")
    size, kind = struct.unpack_from("<II", data, 12)
    if kind != 0x4E4F534A or size % 4 or 20 + size + 8 > len(data):
        raise ValueError("Invalid GLB JSON chunk")
    document = json.loads(data[20:20+size])
    binary_size, binary_kind = struct.unpack_from("<II", data, 20+size)
    if binary_kind != 0x004E4942 or 28+size+binary_size != len(data):
        raise ValueError("Invalid GLB binary chunk")
    if document.get("asset", {}).get("version") != "2.0":
        raise ValueError("Expected glTF 2.0")

    def check_metadata(value):
        if isinstance(value, dict):
            if "uri" in value:
                raise ValueError("Production GLBs must embed every buffer and texture")
            if "extras" in value:
                raise ValueError("Production GLBs must omit custom metadata")
            for item in value.values():
                check_metadata(item)
        elif isinstance(value, list):
            for item in value:
                check_metadata(item)
        elif isinstance(value, str) and _PRIVATE_PATH.search(value):
            raise ValueError("Production GLB contains a private filesystem path")

    check_metadata(document)
    buffers = document.get("buffers", [])
    if len(buffers) != 1 or not 0 < buffers[0].get("byteLength", 0) <= binary_size:
        raise ValueError("Expected a single embedded GLB buffer")
    for view in document.get("bufferViews", []):
        start, count = view.get("byteOffset", 0), view.get("byteLength", 0)
        if view.get("buffer", 0) != 0 or start < 0 or count <= 0 or start+count > buffers[0]["byteLength"]:
            raise ValueError("Buffer view lies outside the embedded buffer")
    for image in document.get("images", []):
        if not isinstance(image.get("bufferView"), int) or image.get("mimeType") not in {"image/png", "image/jpeg"}:
            raise ValueError("Expected embedded PNG/JPEG texture data")
    if document.get("extensionsRequired"):
        raise ValueError("GLB requires an unsupported extension")
    accessors = document.get("accessors", [])
    mesh_triangles = []
    for mesh in document.get("meshes", []):
        triangles = 0
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4:
                raise ValueError("Production meshes must use triangle lists")
            attributes = primitive.get("attributes", {})
            if "POSITION" not in attributes or "NORMAL" not in attributes:
                raise ValueError("Mesh is missing positions or normals")
            index = primitive.get("indices", attributes["POSITION"])
            count = accessors[index]["count"]
            if count <= 0 or count % 3:
                raise ValueError("Invalid triangle index count")
            triangles += count // 3
        mesh_triangles.append(triangles)
    triangles = sum(mesh_triangles[node["mesh"]] for node in document.get("nodes", []) if "mesh" in node)
    if not triangles:
        raise ValueError("GLB contains no visible triangles")
    if triangle_limit is not None and triangles >= triangle_limit:
        raise ValueError(f"GLB has {triangles} triangles; must be below {triangle_limit}")
    return {"file": path.name, "triangles": triangles,
            "textures": len(document.get("images", [])), "bytes": len(data)}
