from dataclasses import dataclass
from enum import Enum


class ZombieKind(Enum):
    WALKER = "walker"
    RUNNER = "runner"
    BRUTE = "brute"
    SPITTER = "spitter"
    LEAPER = "leaper"
    ARMORED = "armored"
    HOWLER = "howler"
    STALKER = "stalker"
    REGENERATOR = "regenerator"
    WARDEN = "warden"


ZOMBIE_ORDER = tuple(ZombieKind)


@dataclass(frozen=True)
class ZombieSpec:
    health: int
    speed: float
    damage: int
    reach: float
    interval: float
    color: tuple[float, float, float, float]
    radius: float = 0.32


ZOMBIE_SPECS = {
    ZombieKind.WALKER: ZombieSpec(75, 1.2, 12, 1.05, 1.1, (0.35, 0.65, 0.25, 1)),
    ZombieKind.RUNNER: ZombieSpec(50, 2.8, 8, 1.05, 0.7, (0.8, 0.75, 0.15, 1)),
    ZombieKind.BRUTE: ZombieSpec(175, 0.8, 28, 1.3, 1.8, (0.6, 0.3, 0.15, 1), 0.5),
    ZombieKind.SPITTER: ZombieSpec(75, 1.1, 10, 6.0, 2.2, (0.2, 0.9, 0.35, 1)),
    ZombieKind.LEAPER: ZombieSpec(75, 1.5, 18, 1.1, 2.4, (0.85, 0.35, 0.15, 1)),
    ZombieKind.ARMORED: ZombieSpec(125, 1.0, 16, 1.15, 1.4, (0.35, 0.45, 0.6, 1)),
    ZombieKind.HOWLER: ZombieSpec(100, 0.9, 10, 1.05, 1.3, (0.75, 0.2, 0.65, 1)),
    ZombieKind.STALKER: ZombieSpec(75, 1.8, 14, 1.05, 1.0, (0.25, 0.35, 0.5, 1)),
    ZombieKind.REGENERATOR: ZombieSpec(100, 1.0, 12, 1.05, 1.2, (0.2, 0.75, 0.7, 1)),
    ZombieKind.WARDEN: ZombieSpec(300, 0.9, 25, 3.0, 3.0, (0.65, 0.15, 0.85, 1), 0.5),
}
