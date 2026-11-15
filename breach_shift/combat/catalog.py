"""Weapon balance and appearance identifiers, independent of rendering."""

from dataclasses import dataclass
from enum import Enum


class WeaponKind(Enum):
    PISTOL = "pistol"
    SMG = "smg"
    RIFLE = "rifle"
    SHOTGUN = "shotgun"


@dataclass(frozen=True)
class WeaponSpec:
    name: str
    damage: int
    fire_interval: float
    magazine_size: int
    reserve_ammo: int
    reload_time: float
    range: float
    ammo_bundle: tuple[int, int]
    color: tuple[float, float, float, float]
    automatic: bool = False
    pellets: int = 1
    spread: float = 0.0


WEAPON_ORDER = tuple(WeaponKind)
WEAPON_SPECS = {
    WeaponKind.PISTOL: WeaponSpec("Pistol", 25, 0.25, 12, 36, 1.5, 100, (6, 18), (0.9, 0.72, 0.3, 1)),
    WeaponKind.SMG: WeaponSpec("SMG", 14, 0.09, 30, 90, 1.8, 65, (15, 40), (0.25, 0.7, 0.95, 1), True),
    WeaponKind.RIFLE: WeaponSpec("Rifle", 38, 0.18, 24, 72, 2.1, 160, (10, 25), (0.45, 0.85, 0.4, 1), True),
    WeaponKind.SHOTGUN: WeaponSpec("Shotgun", 96, 0.9, 6, 18, 2.8, 24, (2, 6), (0.95, 0.35, 0.2, 1),
                                   pellets=6, spread=0.055),
}
