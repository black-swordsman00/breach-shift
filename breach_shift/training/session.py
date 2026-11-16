class TrainingSession:
    """Track one training run using timestamps supplied by the game clock."""

    def __init__(self) -> None:
        self.reset()

    @property
    def is_complete(self) -> bool:
        return self._finished_at is not None

    @property
    def accuracy(self) -> float:
        return 100.0 * self.hits / self.shots if self.shots else 0.0

    def elapsed_time(self, now: float) -> float:
        if self._started_at is None:
            return 0.0

        end = self._finished_at if self._finished_at is not None else now
        return max(0.0, end - self._started_at)

    def record_shot(self, now: float) -> None:
        """Record a shot accepted by the weapon, including misses."""
        if self.is_complete:
            return

        if self._started_at is None:
            self._started_at = now
        self.shots += 1

    def record_hit(self) -> None:
        """Record a target hit while the session is active."""
        if not self.is_complete and self.hits < self.shots:
            self.hits += 1

    def finish(self, now: float) -> None:
        """Freeze the results when the last target is destroyed."""
        if self._started_at is not None and not self.is_complete:
            self._finished_at = now

    def reset(self) -> None:
        self.shots = 0
        self.hits = 0
        self._started_at: float | None = None
        self._finished_at: float | None = None
