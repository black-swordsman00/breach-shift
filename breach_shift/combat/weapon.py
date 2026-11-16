from breach_shift.combat.catalog import WeaponSpec


class Weapon:
    """Manage weapon damage, ammunition, and firing cooldown."""

    def __init__(
        self,
        damage: int = 25,
        fire_interval: float = 0.25,
        magazine_size: int = 12,
        reserve_ammo: int = 36,
        reload_time: float = 1.5,
        *,
        spec: WeaponSpec | None = None,
    ) -> None:
        if spec is not None:
            damage, fire_interval = spec.damage, spec.fire_interval
            magazine_size, reserve_ammo = spec.magazine_size, spec.reserve_ammo
            reload_time = spec.reload_time
        self.name = spec.name if spec else "Pistol"
        self.range = spec.range if spec else 100.0
        self.automatic = spec.automatic if spec else False
        self.pellets = spec.pellets if spec else 1
        self.spread = spec.spread if spec else 0.0
        self.damage = damage
        self.fire_interval = fire_interval
        self.magazine_size = magazine_size
        self.reload_time = reload_time
        self._starting_reserve_ammo = reserve_ammo
        self.reset()

    def try_fire(self, now: float) -> bool:
        if (self.is_reloading or
            self.ammo <= 0 or
            now < self._next_shot_time
            ):
            return False

        self.ammo -= 1
        self._next_shot_time = now + self.fire_interval
        return True

    def start_reload(self) -> bool:
        if (
            self.is_reloading
            or self.ammo >= self.magazine_size
            or self.reserve_ammo <= 0
        ):
            return False

        self.is_reloading = True
        return True

    def finish_reload(self) -> None:
        if not self.is_reloading:
            return

        needed = self.magazine_size - self.ammo
        loaded = min(needed, self.reserve_ammo)

        self.ammo += loaded
        self.reserve_ammo -= loaded
        self.is_reloading = False

    def cancel_reload(self) -> None:
        self.is_reloading = False



    def reset(self) -> None:
        self.ammo = self.magazine_size
        self.reserve_ammo = self._starting_reserve_ammo
        self.is_reloading = False
        self._next_shot_time = 0.0


