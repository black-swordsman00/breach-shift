class PlayerJump:
    """Track vertical motion using frame time supplied by the game clock."""

    def __init__(self, jump_speed: float = 7.0, gravity: float = 18.0) -> None:
        if jump_speed <= 0 or gravity <= 0:
            raise ValueError("Jump speed and gravity must be positive.")
        self.jump_speed = jump_speed
        self.gravity = gravity
        self.reset()

    def try_jump(self) -> bool:
        if not self.is_grounded:
            return False

        self.vertical_speed = self.jump_speed
        self.is_grounded = False
        return True

    def update(self, dt: float) -> float:
        """Return the vertical displacement for one frame."""
        if self.is_grounded or dt <= 0:
            return 0.0

        displacement = self.vertical_speed * dt - 0.5 * self.gravity * dt * dt
        self.vertical_speed -= self.gravity * dt
        return displacement

    def leave_ground(self) -> None:
        if self.is_grounded:
            self.is_grounded = False
            self.vertical_speed = 0.0

    def land(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.vertical_speed = 0.0
        self.is_grounded = True
