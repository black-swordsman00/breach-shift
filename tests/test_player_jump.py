import unittest

from player_jump import PlayerJump


class PlayerJumpTests(unittest.TestCase):
    def setUp(self):
        self.jump = PlayerJump()

    def test_starts_grounded_without_vertical_motion(self):
        self.assertTrue(self.jump.is_grounded)
        self.assertEqual(self.jump.vertical_speed, 0.0)
        self.assertEqual(self.jump.update(0.05), 0.0)

    def test_jump_lifts_player_and_gravity_eventually_reverses_motion(self):
        self.assertTrue(self.jump.try_jump())
        self.assertFalse(self.jump.is_grounded)
        self.assertGreater(self.jump.update(0.05), 0.0)
        for _ in range(8):
            self.jump.update(0.05)
        self.assertLess(self.jump.vertical_speed, 0.0)
        self.assertLess(self.jump.update(0.05), 0.0)

    def test_single_jump_rejects_an_airborne_attempt_without_changing_speed(self):
        self.jump.try_jump()
        self.jump.update(0.2)
        speed = self.jump.vertical_speed
        self.assertFalse(self.jump.try_jump())
        self.assertEqual(self.jump.vertical_speed, speed)

    def test_constant_gravity_is_independent_of_frame_partitioning(self):
        other = PlayerJump()
        self.jump.try_jump()
        other.try_jump()
        single_frame = self.jump.update(0.2)
        multiple_frames = sum(other.update(0.05) for _ in range(4))
        self.assertAlmostEqual(single_frame, multiple_frames)
        self.assertAlmostEqual(self.jump.vertical_speed, other.vertical_speed)

    def test_zero_or_negative_frame_time_does_not_change_airborne_state(self):
        self.jump.try_jump()
        for dt in (0.0, -0.1):
            with self.subTest(dt=dt):
                self.assertEqual(self.jump.update(dt), 0.0)
                self.assertEqual(self.jump.vertical_speed, self.jump.jump_speed)
                self.assertFalse(self.jump.is_grounded)

    def test_walking_off_support_starts_a_fall(self):
        self.jump.leave_ground()
        self.assertFalse(self.jump.is_grounded)
        self.assertEqual(self.jump.vertical_speed, 0.0)
        self.assertLess(self.jump.update(0.05), 0.0)
        self.assertFalse(self.jump.try_jump())

    def test_landing_stops_a_fall_and_allows_another_jump(self):
        self.jump.try_jump()
        self.jump.update(0.5)
        self.jump.land()
        self.assertTrue(self.jump.is_grounded)
        self.assertEqual(self.jump.vertical_speed, 0.0)
        self.assertEqual(self.jump.update(0.05), 0.0)
        self.assertTrue(self.jump.try_jump())

    def test_reset_clears_an_airborne_jump(self):
        self.jump.try_jump()
        self.jump.update(0.1)
        self.jump.reset()
        self.assertTrue(self.jump.is_grounded)
        self.assertEqual(self.jump.vertical_speed, 0.0)
        self.assertTrue(self.jump.try_jump())

    def test_invalid_jump_speed_or_gravity_is_rejected(self):
        for speed, gravity in ((0, 18), (-1, 18), (7, 0), (7, -1)):
            with self.subTest(speed=speed, gravity=gravity):
                with self.assertRaises(ValueError):
                    PlayerJump(jump_speed=speed, gravity=gravity)

    def test_double_jump_restores_upward_speed_and_rejects_a_third_jump(self):
        jump = PlayerJump(max_jumps=2)
        self.assertTrue(jump.try_jump())
        jump.update(0.2)
        self.assertTrue(jump.try_jump())
        self.assertEqual(jump.vertical_speed, jump.jump_speed)
        self.assertEqual(jump.jumps_used, 2)
        jump.update(0.1)
        speed = jump.vertical_speed
        self.assertFalse(jump.try_jump())
        self.assertEqual(jump.vertical_speed, speed)

    def test_double_jump_can_reverse_a_fall(self):
        jump = PlayerJump(max_jumps=2)
        jump.try_jump()
        jump.update(0.5)
        self.assertLess(jump.vertical_speed, 0.0)
        self.assertTrue(jump.try_jump())
        self.assertGreater(jump.update(0.05), 0.0)

    def test_landing_replenishes_both_jumps(self):
        jump = PlayerJump(max_jumps=2)
        for _ in range(2):
            self.assertTrue(jump.try_jump())
            self.assertTrue(jump.try_jump())
            self.assertFalse(jump.try_jump())
            jump.land()
            self.assertEqual(jump.jumps_used, 0)
            self.assertTrue(jump.is_grounded)

    def test_reset_restores_both_jumps_during_a_double_jump(self):
        jump = PlayerJump(max_jumps=2)
        jump.try_jump()
        jump.try_jump()
        jump.update(0.1)
        jump.reset()
        self.assertEqual(jump.jumps_used, 0)
        self.assertTrue(jump.try_jump())
        self.assertTrue(jump.try_jump())

    def test_walking_off_a_ledge_leaves_one_airborne_jump(self):
        jump = PlayerJump(max_jumps=2)
        jump.leave_ground()
        self.assertEqual(jump.jumps_used, 1)
        self.assertTrue(jump.try_jump())
        self.assertFalse(jump.try_jump())

    def test_airborne_ground_check_does_not_restore_used_jumps(self):
        jump = PlayerJump(max_jumps=2)
        jump.try_jump()
        jump.try_jump()
        jump.update(0.1)
        speed = jump.vertical_speed
        jump.leave_ground()
        self.assertEqual(jump.jumps_used, 2)
        self.assertEqual(jump.vertical_speed, speed)
        self.assertFalse(jump.try_jump())

    def test_nonpositive_jump_limit_is_rejected(self):
        for limit in (0, -1):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    PlayerJump(max_jumps=limit)


if __name__ == "__main__":
    unittest.main()
