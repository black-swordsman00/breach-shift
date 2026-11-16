"""Install the complete, validated Blender model library."""

import argparse
from pathlib import Path

from breach_shift.art.library import MODEL_ROOT
from breach_shift.combat.catalog import WEAPON_ORDER
from breach_shift.enemies.catalog import ZOMBIE_ORDER


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
    args = parser.parse_args()
    export_blender_library(args.source, args.output or MODEL_ROOT)


if __name__ == "__main__":
    main()
