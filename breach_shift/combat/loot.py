"""Roll a weapon-specific ammunition reward once for each defeated enemy."""

from dataclasses import dataclass
from random import Random

from breach_shift.combat.catalog import WEAPON_ORDER, WEAPON_SPECS, WeaponKind


@dataclass(frozen=True)
class AmmoReward:
    kind: WeaponKind
    rounds: int


def roll_ammo(rng: Random) -> AmmoReward:
    kind = rng.choice(WEAPON_ORDER)
    return AmmoReward(kind, rng.randint(*WEAPON_SPECS[kind].ammo_bundle))
