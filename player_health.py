class PlayerHealth:
    """Manage player damage, healing, and death without rendering dependencies."""

    def __init__(self, maximum: int = 100) -> None:
        if maximum <= 0:
            raise ValueError("Maximum health must be positive.")
        self.maximum = maximum
        self.reset()

    @property
    def is_alive(self) -> bool:
        return self.current > 0

    def take_damage(self, amount: int) -> bool:
        if amount <= 0 or not self.is_alive:
            return False
        self.current = max(0, self.current - amount)
        return True

    def heal(self, amount: int) -> bool:
        if amount <= 0 or not self.is_alive or self.current == self.maximum:
            return False
        self.current = min(self.maximum, self.current + amount)
        return True

    def reset(self) -> None:
        self.current = self.maximum
