

class Target:
    """Manage a training target's health."""

    def __init__(self, max_health: int = 100) -> None:
        self.max_health = max_health
        self.reset()

    def take_damage(self, damage: int) -> bool:
        if self.health <= 0:
            return False

        self.health = max(0, self.health - damage)
        return True

    def reset(self) -> None:
        self.health = self.max_health