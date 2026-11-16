import unittest

from breach_shift.world.reality import Reality, RealityShift


class RealityShiftTests(unittest.TestCase):
    def test_switch_and_cooldown_use_supplied_game_time(self):
        shift = RealityShift()
        self.assertTrue(shift.try_shift(10.0, True))
        self.assertIs(shift.state, Reality.BREACH)
        self.assertFalse(shift.try_shift(11.9, True))
        self.assertAlmostEqual(shift.remaining(11.0), 1.0)
        self.assertTrue(shift.try_shift(12.0, True))
        self.assertIs(shift.state, Reality.NORMAL)

    def test_blocked_destination_does_not_change_reality_or_consume_cooldown(self):
        shift = RealityShift()
        self.assertFalse(shift.try_shift(5.0, False))
        self.assertIs(shift.state, Reality.NORMAL)
        self.assertEqual(shift.remaining(5.0), 0.0)
        self.assertTrue(shift.try_shift(5.0, True))

    def test_restart_restores_normal_and_clears_cooldown(self):
        shift = RealityShift()
        shift.try_shift(20.0, True)
        shift.reset()
        self.assertIs(shift.state, Reality.NORMAL)
        self.assertTrue(shift.try_shift(20.1, True))

    def test_shift_at_zero_and_invalid_cooldown(self):
        self.assertTrue(RealityShift().try_shift(0.0, True))
        with self.assertRaises(ValueError):
            RealityShift(-1)
