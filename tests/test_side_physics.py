import unittest

from breach_shift.platformer.physics import Body, Rect, advance_body, can_stand, move_body, segment_hit


class SidePhysicsTests(unittest.TestCase):
    def test_swept_side_cannot_skip_a_thin_wall(self):
        body = Body(0, 0)
        move_body(body, 20, 0, (Rect(3, 0, .05, 3),))
        self.assertAlmostEqual(body.rect.right, 3)

    def test_fast_fall_lands_on_roof_and_remains_supported(self):
        body = Body(4, 8, vz=-60)
        floor = (Rect(2, 0, 5, 2),)
        advance_body(body, .2, floor)
        self.assertAlmostEqual(body.z, 2)
        self.assertTrue(body.grounded)
        for _ in range(20):
            advance_body(body, 1/120, floor)
        self.assertAlmostEqual(body.z, 2)

    def test_feet_cannot_enter_a_box_when_torso_is_above_roof(self):
        body = Body(1.6, 1.7)
        move_body(body, .8, 0, (Rect(2, 0, 2, 2),))
        self.assertAlmostEqual(body.rect.right, 2)

    def test_roof_edge_support_uses_the_whole_footprint(self):
        body = Body(1.8, 2)
        advance_body(body, .05, (Rect(2, 0, 2, 2),))
        self.assertEqual(body.z, 2)
        self.assertTrue(body.grounded)

    def test_solid_ceiling_stops_ascent(self):
        body = Body(0, 0, vz=9)
        _, ceiling = advance_body(body, .05, (Rect(-2, 2, 4, .2),))
        self.assertTrue(ceiling)
        self.assertAlmostEqual(body.z, .2)
        self.assertEqual(body.vz, 0)

    def test_one_way_platform_allows_ascent_then_catches_descent(self):
        body = Body(0, 0)
        platforms = (Rect(-2, 1, 4, .2, True),)
        move_body(body, 0, 2, platforms)
        self.assertEqual(body.z, 2)
        move_body(body, 0, -2, platforms)
        self.assertAlmostEqual(body.z, 1.2)
        self.assertTrue(body.grounded)

    def test_crouch_can_pass_but_standing_cannot_fit_under_tunnel(self):
        body = Body(0, 0, height=1.05)
        solids = (Rect(-1, 1.2, 6, .4),)
        self.assertFalse(can_stand(body, 1.8, solids))
        move_body(body, 3, 0, solids)
        self.assertEqual(body.x, 3)
        body.x = 6
        self.assertTrue(can_stand(body, 1.8, solids))

    def test_bullet_segment_reports_first_contact_and_parallel_misses(self):
        wall = Rect(4, 0, 2, 3)
        self.assertAlmostEqual(segment_hit((0, 1), (10, 1), wall), .4)
        self.assertIsNone(segment_hit((0, 4), (10, 4), wall))
        self.assertIsNone(segment_hit((3, 0), (3, 3), wall))


if __name__ == "__main__":
    unittest.main()
