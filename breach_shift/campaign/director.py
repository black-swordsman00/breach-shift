"""Escalate reinforcements using active gameplay time; cores seal the rift."""


class WaveDirector:
    max_alive = 32

    def __init__(self) -> None:
        self.elapsed = 0.0
        self.wave = 0
        self.next_wave = 30.0
        self.sealed = False

    @property
    def remaining(self) -> float:
        return max(0.0, self.next_wave - self.elapsed)

    def advance(self, dt: float, alive: int) -> int:
        if self.sealed:
            return 0
        self.elapsed += max(0.0, dt)
        if self.elapsed < self.next_wave or alive >= self.max_alive:
            return 0
        self.wave += 1
        count = min(2 + int(self.elapsed // 30), 10, self.max_alive - alive)
        self.next_wave = self.elapsed + max(8.0, 26.0 - self.wave * 2.0)
        return count

    def seal(self) -> None:
        self.sealed = True
