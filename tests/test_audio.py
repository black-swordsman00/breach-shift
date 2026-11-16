from importlib.resources import files
from random import Random
import unittest
from unittest.mock import MagicMock
import wave

from breach_shift.audio.bank import SOUNDS, SoundBank


class AudioTests(unittest.TestCase):
    def test_all_bundled_effects_are_nonempty_mono_pcm_waves(self):
        root = files("breach_shift").joinpath("data", "audio")
        for filename in {filename for variants in SOUNDS.values() for filename in variants}:
            with self.subTest(filename=filename), root.joinpath(filename).open("rb") as source:
                with wave.open(source, "rb") as sound:
                    self.assertEqual(sound.getnchannels(), 1)
                    self.assertEqual(sound.getsampwidth(), 2)
                    self.assertEqual(sound.getframerate(), 44100)
                    self.assertGreater(sound.getnframes(), 4000)
                    self.assertNotEqual(set(sound.readframes(1000)), {0})

    def test_weapon_effect_reuses_a_bounded_pool_of_independent_voices(self):
        loader = MagicMock()
        loader.loadSfx.side_effect = lambda path: MagicMock()
        bank = SoundBank(loader, rng=Random(1))
        for _ in range(20):
            bank.play("fire_smg")
        self.assertEqual(loader.loadSfx.call_count, 4)
        self.assertEqual(len(bank.voices), 1)

    def test_enemy_audio_accepts_distance_volume_and_clamps_playback_pitch(self):
        bank = SoundBank(MagicMock(), rng=Random(1))
        sound = bank.play("zombie_attack", volume=.3, pitch=99)
        sound.setVolume.assert_called_once_with(.3)
        sound.setPlayRate.assert_called_once_with(1.8)

    def test_mute_stops_playing_voices_and_prevents_new_sound(self):
        loader = MagicMock()
        loader.loadSfx.side_effect = lambda path: MagicMock()
        bank = SoundBank(loader)
        sound = bank.play("fire_pistol")
        self.assertFalse(bank.toggle())
        self.assertIsNone(bank.play("fire_pistol"))
        self.assertEqual(sound.play.call_count, 1)
        self.assertTrue(bank.toggle())

    def test_holding_empty_trigger_does_not_spam_dry_fire(self):
        loader = MagicMock()
        loader.loadSfx.side_effect = lambda path: MagicMock()
        bank = SoundBank(loader)
        self.assertIsNotNone(bank.play("empty", now=1))
        self.assertIsNone(bank.play("empty", now=1.1))
        self.assertIsNotNone(bank.play("empty", now=1.5))

    def test_checkpoint_cleanup_stops_all_pooled_voices(self):
        loader = MagicMock()
        loader.loadSfx.side_effect = lambda path: MagicMock()
        bank = SoundBank(loader)
        bank.play("zombie_attack")
        pool = bank.voices["attack.wav"]
        previous = [sound.stop.call_count for sound in pool]
        bank.stop_all()
        self.assertEqual([sound.stop.call_count for sound in pool],[count+1 for count in previous])
