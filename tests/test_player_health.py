import unittest

from player_health import PlayerHealth


class PlayerHealthTests(unittest.TestCase):
    def test_damage_is_clamped_and_dead_players_cannot_be_hit_or_healed(self):
        health = PlayerHealth()
        self.assertTrue(health.take_damage(25))
        self.assertEqual(health.current, 75)
        self.assertTrue(health.take_damage(500))
        self.assertEqual(health.current, 0)
        self.assertFalse(health.is_alive)
        self.assertFalse(health.take_damage(10))
        self.assertFalse(health.heal(100))

    def test_healing_is_limited_and_nonpositive_damage_does_not_heal(self):
        health = PlayerHealth()
        self.assertFalse(health.take_damage(-10))
        self.assertFalse(health.take_damage(0))
        self.assertFalse(health.heal(5))
        health.take_damage(40)
        self.assertTrue(health.heal(15))
        self.assertEqual(health.current, 75)
        self.assertTrue(health.heal(50))
        self.assertEqual(health.current, 100)

    def test_retry_restores_full_health_after_death(self):
        health = PlayerHealth(80)
        health.take_damage(100)
        health.reset()
        self.assertEqual(health.current, 80)
        self.assertTrue(health.is_alive)

    def test_nonpositive_maximum_is_rejected(self):
        for maximum in (0, -1):
            with self.assertRaises(ValueError):
                PlayerHealth(maximum)
