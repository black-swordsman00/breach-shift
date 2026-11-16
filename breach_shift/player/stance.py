"""A held crouch with smooth eye height and safe standing clearance."""
from math import exp


class PlayerStance:
    standing_eye = 1.7
    crouching_eye = 1.0
    standing_height = 1.8
    crouching_height = 1.15
    crouch_speed = .52

    def __init__(self):
        self.reset()

    def reset(self):
        self.is_crouching = False
        self.eye_height = self.standing_eye

    def update(self, dt, requested, can_stand=True):
        self.is_crouching = requested or (self.is_crouching and not can_stand)
        target = self.crouching_eye if self.is_crouching else self.standing_eye
        self.eye_height += (target-self.eye_height) * (1-exp(-14*max(0, dt)))
        return self.eye_height

    @property
    def speed_factor(self):
        return self.crouch_speed if self.is_crouching else 1.0

    @property
    def height(self):
        return self.crouching_height if self.is_crouching else self.standing_height
