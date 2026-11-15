import unittest
from unittest.mock import MagicMock

from panda3d.core import Camera, ClockObject, GraphicsWindow, KeyboardButton, NodePath, Point3

from main import BreachShift
from training_session import TrainingSession
from weapon import Weapon


class JumpIntegrationTests(unittest.TestCase):
    """Exercise jumps against the real arena floor and target colliders."""

    def setUp(self):
        self.game = BreachShift.__new__(BreachShift)
        game = self.game
        self.window = MagicMock(spec=GraphicsWindow)
        self.window.getProperties().getForeground.return_value = True
        game.win = self.window
        self.accept_events = MagicMock()
        game.accept = self.accept_events
        game.taskMgr = MagicMock()
        game.clock = ClockObject()
        game.clock.setMode(ClockObject.M_non_real_time)
        game.clock.setFrameTime(10.0)
        game.clock.setDt(0.05)
        game.render = NodePath("jump-test-render")
        game.player = game.render.attachNewNode("player")
        game.player.setPos(0, -2, 0)
        self.camera = game.player.attachNewNode(Camera("camera"))
        self.camera.setPos(0, 0, 1.7)
        game.camera = self.camera
        game.camNode = self.camera.node()
        game.camera_pitch = 0.0
        game.mouse_ready = False
        self.keyboard = MagicMock()
        self.keyboard.isButtonDown.return_value = False
        game.mouseWatcherNode = self.keyboard
        game.move_speed = 5.0
        game.setup_jumping()

        game.floor = game.render.attachNewNode("floor")
        game.load_single_model = lambda path: NodePath("jump-test-model")
        game.create_targets()
        game.setup_collisions()
        game.setup_shooting()
        game.aspect2d = NodePath("jump-test-aspect2d")
        game.create_crosshair()
        game.create_hitmarker()
        game.weapon = Weapon()
        game.training_session = TrainingSession()
        game.weapon_hud = MagicMock()
        game.target_hud = MagicMock()
        game.training_hud = MagicMock()

    def tearDown(self):
        self.game.render.removeNode()
        self.game.aspect2d.removeNode()

    def step(self, frames=1):
        for _ in range(frames):
            self.game.update_movement(None)
            self.game.update_targets(None)
            self.game.update_collisions(None)

    def land_on_floor(self):
        for _ in range(100):
            self.step()
            if self.game.jump_state.is_grounded:
                break
        self.assertTrue(self.game.jump_state.is_grounded)
        self.assertAlmostEqual(self.game.player.getZ(), 0.0)

    def test_space_events_lift_player_and_camera_then_land(self):
        game = self.game
        self.accept_events.assert_any_call("space", game.jump_player)
        self.accept_events.assert_any_call("space-up", game.release_jump)
        game.jump_player()
        self.step()
        self.assertGreater(game.player.getZ(), 0.0)
        self.assertGreater(self.camera.getZ(game.render), 1.7)
        self.assertAlmostEqual(self.camera.getZ(), 1.7)
        self.land_on_floor()
        self.assertEqual(game.jump_state.vertical_speed, 0.0)

    def test_holding_space_does_not_jump_again_after_landing(self):
        game = self.game
        game.jump_player()
        self.land_on_floor()
        game.jump_player()
        self.assertTrue(game.jump_state.is_grounded)
        game.release_jump()
        game.jump_player()
        self.assertFalse(game.jump_state.is_grounded)

    def test_jump_requires_a_focused_graphics_window(self):
        game = self.game
        self.window.getProperties().getForeground.return_value = False
        game.jump_player()
        self.assertTrue(game.jump_state.is_grounded)
        self.assertFalse(game.jump_held)
        game.win = None
        game.jump_player()
        self.assertTrue(game.jump_state.is_grounded)
        self.assertFalse(game.jump_held)

    def test_gravity_continues_without_a_keyboard_monitor(self):
        game = self.game
        game.jump_player()
        game.mouseWatcherNode = None
        self.step(2)
        self.assertGreater(game.player.getZ(), 0.0)
        self.assertLess(game.jump_state.vertical_speed, game.jump_state.jump_speed)

    def test_focus_loss_releases_the_jump_latch(self):
        game = self.game
        game.jump_player()
        self.window.getProperties().getForeground.return_value = False
        self.step()
        self.assertFalse(game.jump_held)
        self.assertFalse(game.jump_state.is_grounded)

    def test_diagonal_movement_keeps_its_speed_while_airborne(self):
        game = self.game
        self.keyboard.isButtonDown.side_effect = lambda key: key in (
            KeyboardButton.asciiKey("w"), KeyboardButton.asciiKey("d")
        )
        game.jump_player()
        self.step()
        displacement = game.player.getPos() - Point3(0, -2, game.player.getZ())
        self.assertAlmostEqual(displacement.length(), 0.25, places=5)
        self.assertGreater(game.player.getZ(), 0.0)

    def test_floor_catches_a_fall_that_crosses_the_floor_in_one_frame(self):
        game = self.game
        game.player.setZ(0.02)
        game.jump_state.leave_ground()
        game.jump_state.vertical_speed = -12.0
        self.step()
        self.assertAlmostEqual(game.player.getZ(), 0.0)
        self.assertTrue(game.jump_state.is_grounded)

    def test_player_can_land_and_stay_on_a_target_top(self):
        game = self.game
        game.player.setPos(0, 6, 2.05)
        game.jump_state.leave_ground()
        self.step(3)
        self.assertAlmostEqual(game.player.getZ(), 2.0)
        self.assertTrue(game.jump_state.is_grounded)
        self.step(3)
        self.assertAlmostEqual(game.player.getZ(), 2.0)

    def test_walking_off_a_target_starts_falling_to_the_floor(self):
        game = self.game
        game.player.setPos(0, 6, 2.0)
        self.step()
        game.player.setX(4.0)
        self.step()
        self.assertFalse(game.jump_state.is_grounded)
        self.land_on_floor()

    def test_destroying_support_removes_its_landing_surface(self):
        game = self.game
        game.player.setPos(0, 6, 2.0)
        self.step()
        game.targets["target-1"].take_damage(100)
        self.step()
        self.assertFalse(game.jump_state.is_grounded)
        self.land_on_floor()

    def test_arena_boundaries_still_block_airborne_movement(self):
        game = self.game
        game.player.setPos(9.9, 0, 1.0)
        game.jump_state.leave_ground()
        self.step()
        self.assertLessEqual(game.player.getX(), 9.61)
        self.assertGreater(game.player.getZ(), 0.0)

    def test_restart_clears_airborne_motion_and_preserves_training_reset(self):
        game = self.game
        game.jump_player()
        self.step()
        self.camera.lookAt(game.targets["target-1"].root, Point3(1, 1, 1))
        game.shoot()
        self.assertEqual(game.training_session.shots, 1)
        self.assertEqual(game.training_session.hits, 1)
        game.reload_weapon()
        self.assertTrue(game.weapon.is_reloading)
        game.restart_training()
        self.assertEqual(game.player.getPos(), Point3(0, -2, 0))
        self.assertTrue(game.jump_state.is_grounded)
        self.assertEqual(game.jump_state.vertical_speed, 0.0)
        self.assertFalse(game.jump_held)
        self.assertEqual(game.previous_player_z, 0.0)
        self.assertEqual(game.training_session.shots, 0)
        self.assertEqual(game.training_session.hits, 0)
        self.assertEqual(game.weapon.ammo, 12)
        self.assertFalse(game.weapon.is_reloading)
        self.assertTrue(game.hitmarker.isHidden())
        game.jump_player()
        self.assertFalse(game.jump_state.is_grounded)


if __name__ == "__main__":
    unittest.main()
