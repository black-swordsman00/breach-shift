from dataclasses import dataclass
import json
from math import isfinite
from pathlib import Path

from reality import Reality
from zombie_catalog import ZOMBIE_ORDER, ZombieKind


@dataclass(frozen=True)
class MapBounds:
    min_x: float = -10
    max_x: float = 10
    min_y: float = -5
    max_y: float = 20

    def __post_init__(self) -> None:
        if (not all(isfinite(value) for value in (self.min_x, self.max_x, self.min_y, self.max_y))
                or self.min_x >= self.max_x or self.min_y >= self.max_y):
            raise ValueError("Map bounds must be finite and have positive dimensions.")

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def depth(self) -> float:
        return self.max_y - self.min_y

    def contains(self, x: float, y: float, margin: float = 0.0) -> bool:
        return (self.min_x + margin <= x <= self.max_x - margin
                and self.min_y + margin <= y <= self.max_y - margin)


@dataclass(frozen=True)
class Block:
    x: float
    y: float
    width: float
    depth: float
    height: float
    reality: Reality | None = None

    def active(self, reality: Reality) -> bool:
        return self.reality is None or self.reality is reality

    def overlaps_xy(self, x: float, y: float, radius: float = 0.0) -> bool:
        return (abs(x - self.x) < self.width / 2 + radius
                and abs(y - self.y) < self.depth / 2 + radius)

    def blocks_player(self, x: float, y: float, z: float) -> bool:
        return self.overlaps_xy(x, y, 0.4) and z < self.height - 0.001 and z + 1.8 > 0


@dataclass(frozen=True)
class Spawn:
    kind: ZombieKind
    x: float
    y: float


@dataclass(frozen=True)
class LevelDefinition:
    number: int
    name: str
    introduced: ZombieKind
    briefing: str
    blocks: tuple[Block, ...]
    spawns: tuple[Spawn, ...]
    core: tuple[float, float]
    exit: tuple[float, float]
    bounds: MapBounds = MapBounds()
    player_spawn: tuple[float, float] = (0, -2)


def load_levels(directory: Path | None = None) -> tuple[LevelDefinition, ...]:
    directory = directory or Path(__file__).with_name("levels")
    levels = []
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        number = data["number"]
        if number != len(levels) + 1 or not 1 <= number <= len(ZOMBIE_ORDER):
            raise ValueError("Campaign levels must be consecutive from 1 to 10.")
        introduced = ZombieKind(data["introduced"])
        if introduced is not ZOMBIE_ORDER[number - 1]:
            raise ValueError(f"Level {number} introduces the wrong zombie.")
        bounds = MapBounds(*data.get("bounds", (-10, 10, -5, 20)))
        player_spawn = tuple(data.get("player_spawn", (0, -2)))
        if len(player_spawn) != 2 or not bounds.contains(*player_spawn, margin=0.7):
            raise ValueError(f"Level {number} has an invalid player spawn.")
        center_x = (bounds.min_x + bounds.max_x) / 2
        blocks = [
            Block(center_x, data["normal_gate_y"], bounds.width, 0.6, 3.5, Reality.NORMAL),
            Block(center_x, data["breach_gate_y"], bounds.width, 0.6, 3.5, Reality.BREACH),
        ]
        for key, reality in (("shared_blocks", None), ("normal_blocks", Reality.NORMAL),
                             ("breach_blocks", Reality.BREACH)):
            for values in data.get(key, []):
                block = Block(*values, reality=reality)
                if min(block.width, block.depth, block.height) <= 0:
                    raise ValueError(f"Invalid block in level {number}.")
                blocks.append(block)
        spawns = tuple(Spawn(ZombieKind(kind), x, y) for kind, x, y in data["spawns"])
        if not any(spawn.kind is introduced for spawn in spawns):
            raise ValueError(f"Level {number} must spawn its new zombie.")
        if any(spawn.kind not in ZOMBIE_ORDER[:number] for spawn in spawns):
            raise ValueError(f"Level {number} spawns a zombie before its introduction.")
        if (not all(bounds.contains(spawn.x, spawn.y, margin=0.7) for spawn in spawns)
                or not bounds.contains(*data["core"], margin=0.7)
                or not bounds.contains(*data["exit"], margin=0.7)):
            raise ValueError(f"Level {number} places an actor or objective outside its bounds.")
        levels.append(LevelDefinition(number, data["name"], introduced, data["briefing"],
                                      tuple(blocks), spawns, tuple(data["core"]), tuple(data["exit"]),
                                      bounds, player_spawn))
    if not levels:
        raise ValueError("Campaign level data is missing.")
    return tuple(levels)
