"""Install the Blender library, or explicitly export procedural study models."""

import argparse
from pathlib import Path

from panda3d.core import Filename

from breach_shift.art.characters import zombie_template
from breach_shift.art.library import MODEL_ROOT
from breach_shift.art.weapons import weapon_template
from breach_shift.combat.catalog import WEAPON_ORDER
from breach_shift.enemies.catalog import ZOMBIE_ORDER


def export_procedural(output: Path) -> None:
    for folder, kinds, source in (("characters", ZOMBIE_ORDER, zombie_template),
                                   ("weapons", WEAPON_ORDER, weapon_template)):
        directory = output / folder
        directory.mkdir(parents=True, exist_ok=True)
        for kind in kinds:
            path = directory / f"{kind.value}.bam"
            if not source(kind).writeBamFile(Filename.fromOsSpecific(str(path))):
                raise RuntimeError(f"Unable to export {path}")
            print(path)


def export_blender_library(source: Path, output: Path) -> None:
    from breach_shift.art.blender_import import import_workshop

    required = [source / folder / f"{kind.value}.glb" for folder, kinds in
                (("characters", ZOMBIE_ORDER), ("weapons", WEAPON_ORDER)) for kind in kinds]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Build the complete Blender library first; missing " + ", ".join(path.name for path in missing))
    for path in required:
        for result in import_workshop(path, output, compress=True):
            print(result["file"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    project = Path(__file__).resolve().parents[2]
    parser.add_argument("--source", type=Path, default=project / ".cache/blender-export")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--procedural", action="store_true", help="export the earlier study meshes to the cache")
    args = parser.parse_args()
    if args.procedural:
        export_procedural(args.output or project / ".cache/procedural-models")
    else:
        export_blender_library(args.source, args.output or MODEL_ROOT)


if __name__ == "__main__":
    main()
