"""Install the complete, validated Blender model library."""

import argparse
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from breach_shift.art.library import MODEL_ROOT
from breach_shift.combat.catalog import WEAPON_ORDER
from breach_shift.enemies.catalog import ZOMBIE_ORDER


def export_blender_library(source: Path, output: Path, *, production: Path | None = None) -> None:
    from breach_shift.art.blender_import import import_workshop
    from breach_shift.art.glb import inspect_glb

    entries = []
    for folder, kinds in (("characters", ZOMBIE_ORDER), ("weapons", WEAPON_ORDER)):
        for kind in kinds:
            relative = Path(folder) / (kind.value + ".glb")
            override = production / relative if production is not None else None
            entries.append((relative, override if override and override.is_file() else source / relative,
                            bool(override and override.is_file())))
    required = [path for _relative, path, _production in entries]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Build the complete Blender library first; missing " + ", ".join(path.name for path in missing))
    # Serialize the complete mixed library before replacing live files.
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="model-export-", dir=output.parent) as directory:
        staging = Path(directory)
        for relative, path, is_production in entries:
            if is_production:
                limit = 5000 if relative.parts[0] == "weapons" else 12000
                inspect_glb(path, triangle_limit=limit)
                destination = staging / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                copyfile(path, destination)
                copyfile(path.with_suffix(".json"), destination.with_suffix(".json"))
            else:
                import_workshop(path, staging, compress=True)
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                relative = path.relative_to(staging)
                destination = output / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.replace(destination)
                print(relative.as_posix())
        for relative, _path, is_production in entries:
            if is_production:
                for suffix in (".bam", ".bam.pz"):
                    obsolete = output / relative.with_suffix(suffix)
                    if obsolete.is_file():
                        obsolete.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    project = Path(__file__).resolve().parents[2]
    parser.add_argument("--source", type=Path, default=project / ".cache/blender-export")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--production", type=Path, default=project / "assets/models",
                        help="prefer reviewed production GLBs over earlier study sources")
    args = parser.parse_args()
    export_blender_library(args.source, args.output or MODEL_ROOT, production=args.production)


if __name__ == "__main__":
    main()
