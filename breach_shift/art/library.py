"""Prefer exported local BAM assets; source builders also support installed packages."""

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


def instantiate(relative_path: str, source) -> NodePath:
    path = MODEL_ROOT / relative_path
    compressed = path.with_name(path.name + ".pz")
    if compressed.is_file():
        path = compressed
    template = _load(str(path)) if path.is_file() else source()
    return template.copyTo(NodePath("model-staging"))
