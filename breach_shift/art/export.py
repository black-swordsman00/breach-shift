"""Rebuild the fourteen checked-in runtime models with python -m breach_shift.art.export."""

from panda3d.core import Filename

from breach_shift.art.characters import zombie_template
from breach_shift.art.library import MODEL_ROOT
from breach_shift.art.weapons import weapon_template
from breach_shift.combat.catalog import WEAPON_ORDER
from breach_shift.enemies.catalog import ZOMBIE_ORDER


def main() -> None:
    for folder, kinds, source in (("characters", ZOMBIE_ORDER, zombie_template),
                                   ("weapons", WEAPON_ORDER, weapon_template)):
        directory = MODEL_ROOT / folder
        directory.mkdir(parents=True, exist_ok=True)
        for kind in kinds:
            path = directory / f"{kind.value}.bam"
            if not source(kind).writeBamFile(Filename.fromOsSpecific(str(path))):
                raise RuntimeError(f"Unable to export {path}")
            print(path.relative_to(MODEL_ROOT.parent))


if __name__ == "__main__":
    main()
