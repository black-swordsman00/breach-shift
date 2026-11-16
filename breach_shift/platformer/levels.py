"""Load authored side-view maps; positions are (horizontal x, vertical z)."""
from dataclasses import dataclass
from importlib.resources import files
import json
from math import isfinite
from pathlib import Path

from breach_shift.enemies.catalog import ZOMBIE_ORDER, ZombieKind
from breach_shift.platformer.physics import Body, Rect
from breach_shift.world.reality import Reality


@dataclass(frozen=True)
class Spawn:
    kind: ZombieKind
    x: float
    z: float


@dataclass(frozen=True)
class SideLevel:
    number: int
    name: str
    introduced: ZombieKind
    theme: str
    width: float
    height: float
    player_spawn: tuple[float, float]
    platforms: tuple[Rect, ...]
    normal_gate: Rect
    breach_gate: Rect
    core: tuple[float, float]
    exit: tuple[float, float]
    spawns: tuple[Spawn, ...]
    decor: tuple[tuple, ...]
    briefing: str

    def solids(self, reality: Reality):
        gate = self.normal_gate if reality is Reality.NORMAL else self.breach_gate
        return self.platforms + (gate, Rect(-2, -12, 2, self.height + 16),
                                 Rect(self.width, -12, 2, self.height + 16))


def load_side_levels(directory: Path | None = None) -> tuple[SideLevel, ...]:
    root = directory if directory is not None else files("breach_shift").joinpath("data", "platforms")
    levels = []
    paths = sorted((entry for entry in root.iterdir() if entry.name.endswith(".json")),
                   key=lambda entry: entry.name)
    if not paths:
        raise ValueError("Side-view campaign data is missing.")
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        number = data["number"]
        introduced = ZombieKind(data["introduced"])
        if (number != len(levels) + 1 or not 1 <= number <= len(ZOMBIE_ORDER)
                or introduced is not ZOMBIE_ORDER[number - 1]):
            raise ValueError("Levels must introduce the ten zombies consecutively.")
        width, height = data["size"]
        if not all(isfinite(value) and value > 0 for value in (width, height)):
            raise ValueError("Invalid map size.")
        rectangles = [Rect(*values) for values in data["platforms"]]
        gates = [Rect(*data[key]) for key in ("normal_gate", "breach_gate")]
        for rectangle in rectangles + gates:
            values = (rectangle.x, rectangle.z, rectangle.width, rectangle.height)
            if (not all(isfinite(value) for value in values)
                    or min(rectangle.width, rectangle.height) <= 0
                    or rectangle.x < 0 or rectangle.right > width or rectangle.top > height):
                raise ValueError("Invalid platform or reality gate.")
        spawn = tuple(data["player_spawn"])
        core, exit_position = tuple(data["core"]), tuple(data["exit"])
        spawns = tuple(Spawn(ZombieKind(kind), x, z) for kind, x, z in data["spawns"])
        if (not spawns or not any(item.kind is introduced for item in spawns)
                or any(item.kind not in ZOMBIE_ORDER[:number] for item in spawns)):
            raise ValueError("Invalid enemy introduction or empty encounter.")
        for point in (spawn, core, exit_position, *((item.x, item.z) for item in spawns)):
            if (len(point) != 2 or not all(isfinite(value) for value in point)
                    or not 0 <= point[0] <= width or not -3 <= point[1] <= height):
                raise ValueError("Actor or objective outside map bounds.")
        if any(Body(*spawn).rect.overlaps(solid) for solid in rectangles + [gates[0]]):
            raise ValueError("Player spawn intersects architecture.")
        if any(Body(item.x, item.z).rect.overlaps(solid) for item in spawns
               for solid in rectangles + [gates[0]] if not solid.one_way):
            raise ValueError("Enemy spawn intersects architecture.")
        levels.append(SideLevel(number, data["name"], introduced, data["theme"],
                                width, height, spawn, tuple(rectangles), *gates,
                                core, exit_position, spawns,
                                tuple(tuple(item) for item in data["decor"]), data["briefing"]))
    return tuple(levels)
