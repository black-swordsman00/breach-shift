


class Weapon:
    """Manage weapon damage, ammunition, and firing cooldown."""

    def __init__(
        self,
        damage: int = 25,
        fire_interval: float = 0.25,
        magazine_size: int = 12,
        reserve_ammo: int = 36,
        reload_time: float = 1.5
    ) -> None:
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



    def reset(self) -> None:
        self.ammo = self.magazine_size
        self.reserve_ammo = self._starting_reserve_ammo
        self.is_reloading = False
        self._next_shot_time = 0.0


