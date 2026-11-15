from enum import Enum


class Reality(Enum):
    NORMAL = "Normal"
    BREACH = "Breach"


class RealityShift:
    """Switch realities using the game clock and a validated destination."""

    def __init__(self, cooldown: float = 2.0) -> None:
        if cooldown < 0:
            raise ValueError("Shift cooldown cannot be negative.")
        self.cooldown = cooldown
        self.reset()

    @property
    def destination(self) -> Reality:
        return Reality.BREACH if self.state is Reality.NORMAL else Reality.NORMAL

    def remaining(self, now: float) -> float:
        return max(0.0, self._ready_at - now)

    def try_shift(self, now: float, destination_safe: bool) -> bool:
        if not destination_safe or self.remaining(now) > 0:
            return False
        self.state = self.destination
        self._ready_at = now + self.cooldown
        return True

    def reset(self) -> None:
        self.state = Reality.NORMAL
        self._ready_at = 0.0
