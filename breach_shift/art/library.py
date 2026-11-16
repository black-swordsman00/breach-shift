"""Load packaged assets; missing production art is an explicit error."""

from functools import lru_cache
import json
from pathlib import Path

from panda3d.core import Filename, Loader, NodePath


MODEL_ROOT = Path(__file__).resolve().parents[1] / "data" / "models"


@lru_cache(maxsize=32)
def _metadata(path: str) -> dict:
    source = Path(path)
    return json.loads(source.read_text(encoding="utf-8")) if source.is_file() else {}


def metadata(relative_path: str) -> dict:
    return _metadata(str(MODEL_ROOT / relative_path))


@lru_cache(maxsize=24)
def _load(path: str) -> NodePath:
    if Path(path).suffix == ".glb":
        import gltf
        from breach_shift.art.glb import inspect_glb

        folder = Path(path).parent.name
        limit = 5000 if folder == "weapons" else 12000 if folder == "characters" else None
        inspect_glb(Path(path), triangle_limit=limit)
        model = NodePath(gltf.load_model(Path(path).as_posix()))
        model.setTag("source", "blender")
        model.setTag("source-file", Path(path).name)
        model.setCollideMask(0)
        if folder != "characters":
            model.flattenStrong()
        return model
    node = Loader.getGlobalPtr().loadSync(Filename.fromOsSpecific(path))
    if node is None:
        raise RuntimeError(f"Unable to load game model: {path}")
    return NodePath(node)


def instantiate(relative_path: str) -> NodePath:
    path = MODEL_ROOT / relative_path
    compressed = path.with_name(path.name + ".pz")
    glb = path.with_suffix(".glb")
    if glb.is_file():
        path = glb
    elif compressed.is_file():
        path = compressed
    if not path.is_file():
        raise FileNotFoundError(f"Missing packaged model: {relative_path}")
    template = _load(str(path))
    return template.copyTo(NodePath("model-staging"))
