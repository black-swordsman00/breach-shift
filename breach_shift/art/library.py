"""Load packaged assets; missing production art is an explicit error."""

from functools import lru_cache
from pathlib import Path

from panda3d.core import Filename, Loader, NodePath


MODEL_ROOT = Path(__file__).resolve().parents[1] / "data" / "models"


@lru_cache(maxsize=24)
def _load(path: str) -> NodePath:
    node = Loader.getGlobalPtr().loadSync(Filename.fromOsSpecific(path))
    if node is None:
        raise RuntimeError(f"Unable to load game model: {path}")
    return NodePath(node)


def instantiate(relative_path: str) -> NodePath:
    path = MODEL_ROOT / relative_path
    compressed = path.with_name(path.name + ".pz")
    if compressed.is_file():
        path = compressed
    if not path.is_file():
        raise FileNotFoundError(f"Missing packaged model: {relative_path}")
    template = _load(str(path))
    return template.copyTo(NodePath("model-staging"))
