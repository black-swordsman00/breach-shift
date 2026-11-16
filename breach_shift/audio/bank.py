"""Bounded sound pools; the 2D view supplies distance-based volume."""

from importlib.resources import files
from random import Random

from panda3d.core import Filename


SOUNDS = {
    "fire_pistol": ("pistol.wav",), "fire_smg": ("smg.wav",),
    "fire_rifle": ("rifle.wav",), "fire_shotgun": ("shotgun.wav",),
    "reload_start": ("reload_start.wav",), "reload_finish": ("reload_finish.wav",),
    "empty": ("empty.wav",), "ammo_pickup": ("ammo_pickup.wav",),
    "zombie_idle": ("growl_1.wav", "growl_2.wav", "growl_3.wav"),
    "zombie_hurt": ("hurt_1.wav", "hurt_2.wav"),
    "zombie_death": ("death_1.wav", "death_2.wav"),
    "zombie_attack": ("attack.wav",), "zombie_howl": ("howl.wav",),
    "zombie_roar": ("roar.wav",),
}


class SoundBank:
    def __init__(self, loader, *, enabled=True, rng=None):
        self.enabled = enabled
        self.loader = loader
        self.random = rng or Random()
        self.voices = {}
        self.cursor = {}
        self._last_empty = -100.0

    def play(self, cue, *, volume=.75, pitch=1.0, now=None):
        if not self.enabled:
            return None
        if cue == "empty" and now is not None:
            if now - self._last_empty < .3:
                return None
            self._last_empty = now
        filename = self.random.choice(SOUNDS[cue])
        key = filename
        if key not in self.voices:
            path = Filename.fromOsSpecific(str(files("breach_shift").joinpath("data", "audio", filename))).getFullpath()
            self.voices[key] = [self.loader.loadSfx(path) for _ in range(4)]
            self.cursor[key] = 0
        pool = self.voices[key]
        sound = pool[self.cursor[key]]
        self.cursor[key] = (self.cursor[key] + 1) % len(pool)
        sound.stop()
        sound.setVolume(max(0.0, min(1.0, volume)))
        sound.setPlayRate(max(.5, min(1.8, pitch)))
        sound.play()
        return sound

    def stop_all(self):
        for pool in self.voices.values():
            for sound in pool:
                sound.stop()

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_all()
        return self.enabled
