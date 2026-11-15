"""Keep each weapon's ammunition and firing state when switching slots."""

from breach_shift.combat.catalog import WEAPON_ORDER, WEAPON_SPECS, WeaponKind
from breach_shift.combat.weapon import Weapon


class Arsenal:
    def __init__(self) -> None:
        self.weapons = {kind: Weapon(spec=WEAPON_SPECS[kind]) for kind in WEAPON_ORDER}
        self.selected = WeaponKind.PISTOL

    @property
    def active(self) -> Weapon:
        return self.weapons[self.selected]

    def select(self, kind: WeaponKind) -> Weapon:
        self.active.cancel_reload()
        self.selected = kind
        return self.active

    def add_ammo(self, kind: WeaponKind, amount: int) -> None:
        if amount <= 0:
            raise ValueError("An ammunition pickup must contain a positive number of rounds.")
        self.weapons[kind].reserve_ammo += amount

    def reset(self) -> None:
        for weapon in self.weapons.values():
            weapon.reset()
