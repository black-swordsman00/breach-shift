"""Convert named Blender workshop roots to self-contained runtime BAM models."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from panda3d.core import BitMask32, Filename, NodePath, compressFile, loadPrcFileData

from breach_shift.art.library import MODEL_ROOT
from breach_shift.art.primitives import flatten_local
from breach_shift.combat.catalog import WEAPON_ORDER
from breach_shift.enemies.catalog import ZOMBIE_ORDER


def import_workshop(source: Path, output: Path, *, compress: bool = False) -> list[dict]:
    import gltf

    source = source.resolve()
    scene = NodePath(gltf.load_model(source.as_posix()))
    loadPrcFileData("blender-export", "bam-texture-mode rawdata")
    exported = []
    staged = []
    categories = (("characters", ZOMBIE_ORDER, "HERO_"), ("weapons", WEAPON_ORDER, "WEAPON_"))
    for folder, kinds, prefix in categories:
        for kind in kinds:
            name = prefix + kind.value.title()
            original = scene.find("**/" + name)
            if original.isEmpty():
                continue
            model = NodePath(kind.value + "-model")
            instance = original.copyTo(model)
            instance.setMat(original.getMat(scene))
            instance.setPos(0, 0, 0)
            model.setTag("source", "blender")
            model.setTag("source-file", source.name)
            if folder == "characters":
                model.setTag("zombie-kind", kind.value)
                model.setTag("design", "female" if kind.value == "runner" else "infected")
                for body_part in ("arm", "leg"):
                    for side in ("left", "right"):
                        joint = model.find(f"**/{kind.value.title()}_{body_part}_{side}")
                        if joint.isEmpty():
                            raise ValueError(f"Missing animation pivot: {name}/{body_part}/{side}")
                        joint.setName(f"{body_part}-{side}")
                        flatten_local(joint)
                body = model.find(f"**/{kind.value.title()}_body")
                if not body.isEmpty():
                    flatten_local(body)
            else:
                model.setTag("weapon-kind", kind.value)
                flatten_local(instance)
            model.setCollideMask(BitMask32.allOff())
            bounds = model.getTightBounds()
            if bounds is None:
                raise ValueError(f"No visible mesh in {name}")
            low, high = bounds
            if folder == "characters" and not 1.4 <= high.z - low.z <= 3.2:
                raise ValueError(f"Invalid character scale in {name}: {high.z - low.z:.3f}m")
            relative = Path(folder) / f"{kind.value}.bam"
            if compress:
                relative = relative.with_suffix(".bam.pz")
            staged.append((relative, model))
            exported.append({"kind": kind.value, "file": relative.as_posix(),
                             "bounds": [list(low), list(high)], "source": source.name})
    if not exported:
        raise ValueError("The GLB contains no supported HERO_ or WEAPON_ roots.")
    # Validate every root and serialize every model before replacing any installed asset.
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="blender-import-", dir=output.parent) as directory:
        staging = Path(directory)
        for relative, model in staged:
            temporary = staging / relative
            temporary.parent.mkdir(parents=True, exist_ok=True)
            raw = temporary.with_suffix("") if compress else temporary
            if not model.writeBamFile(Filename.fromOsSpecific(str(raw))):
                raise RuntimeError(f"Unable to export {relative}")
            if compress:
                if not compressFile(Filename.fromOsSpecific(str(raw)), Filename.fromOsSpecific(str(temporary)), 9):
                    raise RuntimeError(f"Unable to compress {relative}")
                raw.unlink()
        for relative, _model in staged:
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            (staging / relative).replace(destination)
    return exported


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="a GLB/glTF file or a directory containing GLBs")
    parser.add_argument("--output", type=Path, default=MODEL_ROOT)
    parser.add_argument("--compress", action="store_true", help="write smaller, self-contained BAM.PZ assets")
    arguments = parser.parse_args()
    sources = sorted(arguments.source.rglob("*.glb")) if arguments.source.is_dir() else [arguments.source]
    if not sources:
        parser.error("No GLB files found in the source directory.")
    exported = [model for source in sources for model in import_workshop(source, arguments.output.resolve(), compress=arguments.compress)]
    print(json.dumps(exported, indent=2))


if __name__ == "__main__":
    main()
