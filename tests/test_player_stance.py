import unittest

from breach_shift.player.stance import PlayerStance


class StanceTests(unittest.TestCase):
    def test_eye_transition_takes_the_same_time_at_different_frame_rates(self):
        heights=[]
        for fps in (30,60,120):
            stance=PlayerStance()
            for _ in range(fps//2):
                stance.update(1/fps,True)
            heights.append(stance.eye_height)
        for height in heights:
            self.assertAlmostEqual(height,heights[0],places=8)
            self.assertLess(height,1.01)

    def test_zero_elapsed_time_does_not_teleport_the_camera(self):
        stance=PlayerStance()
        self.assertEqual(stance.update(0,True),1.7)
        self.assertTrue(stance.is_crouching)
