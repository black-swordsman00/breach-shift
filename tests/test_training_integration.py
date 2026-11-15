import unittest
from unittest.mock import MagicMock, patch

from direct.task import Task
from panda3d.core import Camera, ClockObject, GraphicsWindow, NodePath, Point3

from main import BreachShift
from training_session import TrainingSession
from weapon import Weapon


class TrainingIntegrationTests(unittest.TestCase):
    """Exercise game callbacks with real weapon, target, and ray collisions."""

    def setUp(self):
        self.game = BreachShift.__new__(BreachShift)
        game = self.game
        self.window = MagicMock(spec=GraphicsWindow)
        self.window.getProperties().getForeground.return_value = True
        game.win = self.window
        self.task_manager = MagicMock()
        game.taskMgr = self.task_manager
        game.accept = MagicMock()
        game.clock = ClockObject()
        game.clock.setMode(ClockObject.M_non_real_time)
        game.clock.setFrameTime(10.0)
        game.clock.setDt(0.05)

        game.render = NodePath("test-render")
        game.player = game.render.attachNewNode("player")
        game.player.setPos(0, -2, 0)
        self.camera = game.player.attachNewNode(Camera("camera"))
        self.camera.setPos(0, 0, 1.7)
        game.camera = self.camera
        game.camNode = self.camera.node()
        game.camera_pitch = 0.0
        game.mouse_ready = False
        game.floor = game.render.attachNewNode("floor")
        game.load_single_model = lambda path: NodePath("test-model")
        game.create_targets()
        game.setup_collisions()
        game.setup_shooting()

        game.aspect2d = NodePath("test-aspect2d")
        game.create_crosshair()
        game.create_hitmarker()
        game.weapon = Weapon()
        game.training_session = TrainingSession()
        self.weapon_hud = MagicMock()
        game.weapon_hud = self.weapon_hud
        game.target_hud = MagicMock()
        self.training_hud = MagicMock()
        game.training_hud = self.training_hud

    def tearDown(self):
        self.game.render.removeNode()
        self.game.aspect2d.removeNode()

    def hud_text(self):
        return self.training_hud.setText.call_args.args[0]

    def test_accepted_shot_hits_only_the_nearest_target(self):
        game = self.game
        game.shoot()

        self.assertEqual(game.weapon.ammo, 11)
        self.assertEqual(game.training_session.shots, 1)
        self.assertEqual(game.training_session.hits, 1)
        self.assertEqual(game.targets["target-1"].health, 75)
        self.assertEqual(game.targets["target-2"].health, 100)
        self.assertEqual(game.targets["target-3"].health, 100)
        self.assertFalse(game.hitmarker.isHidden())
        self.assertIn("Shots: 1 | Hits: 1", self.hud_text())
        self.assertIn("Accuracy: 100.0%", self.hud_text())
        self.assertEqual(game.hide_hitmarker(None), Task.done)
        self.assertTrue(game.hitmarker.isHidden())

    def test_miss_counts_and_starts_timer_without_hitmarker(self):
        game = self.game
        game.player.setH(180)
        game.shoot()
        game.clock.setFrameTime(12.5)
        self.assertEqual(game.update_training_hud(None), Task.cont)

        self.assertEqual(game.training_session.shots, 1)
        self.assertEqual(game.training_session.hits, 0)
        self.assertIn("Accuracy: 0.0%", self.hud_text())
        self.assertIn("Time: 2.50s", self.hud_text())
        self.assertTrue(game.hitmarker.isHidden())
        self.assertTrue(all(target.health == 100 for target in game.targets.values()))

    def test_shot_with_no_collision_still_counts(self):
        game = self.game
        game.shot_traverser = MagicMock()
        game.shoot()

        self.assertEqual(game.training_session.shots, 1)
        self.assertEqual(game.training_session.hits, 0)
        self.assertIn("Shots: 1 | Hits: 0", self.hud_text())

    def test_cooldown_rejection_does_not_count(self):
        game = self.game
        game.shoot()
        game.clock.setFrameTime(10.1)
        game.shoot()

        self.assertEqual(game.weapon.ammo, 11)
        self.assertEqual(game.training_session.shots, 1)
        self.assertEqual(game.training_session.hits, 1)
        self.assertEqual(game.targets["target-1"].health, 75)
        self.assertAlmostEqual(game.training_session.elapsed_time(10.1), 0.1)

    def test_empty_or_reloading_weapon_does_not_start_timer(self):
        game = self.game
        for ammo, reloading in ((0, False), (11, True)):
            with self.subTest(ammo=ammo, reloading=reloading):
                game.weapon.ammo = ammo
                game.weapon.is_reloading = reloading
                game.shoot()

                self.assertEqual(game.weapon.ammo, ammo)
                self.assertEqual(game.training_session.shots, 0)
                self.assertEqual(game.training_session.hits, 0)
                self.assertEqual(game.training_session.elapsed_time(20.0), 0.0)
                self.assertTrue(game.hitmarker.isHidden())

    def test_unfocused_or_unavailable_window_does_not_count(self):
        game = self.game
        self.window.getProperties().getForeground.return_value = False
        game.shoot()
        game.win = None
        game.shoot()
        self.assertEqual(game.training_session.shots, 0)
        self.assertEqual(game.weapon.ammo, 12)

    def test_destroyed_target_cannot_add_a_hit(self):
        game = self.game
        game.shoot()
        target = game.targets["target-1"]
        target.take_damage(100)
        game.hitmarker.hide()
        game.damage_target(target)

        self.assertEqual(game.training_session.hits, 1)
        self.assertTrue(game.hitmarker.isHidden())
        self.assertFalse(game.training_session.is_complete)

    def test_reload_preserves_counts_and_running_timer(self):
        game = self.game
        game.shoot()
        game.reload_weapon()
        self.assertTrue(game.weapon.is_reloading)
        self.task_manager.doMethodLater.assert_any_call(
            game.weapon.reload_time, game.finish_weapon_reload, "reload-weapon"
        )
        game.clock.setFrameTime(11.0)
        game.shoot()
        self.assertEqual(game.training_session.shots, 1)
        self.assertEqual(game.training_session.hits, 1)
        self.assertEqual(game.training_session.elapsed_time(11.0), 1.0)

        game.clock.setFrameTime(11.5)
        self.assertEqual(game.finish_weapon_reload(None), Task.done)
        self.assertFalse(game.weapon.is_reloading)
        self.assertEqual(game.weapon.ammo, 12)
        self.assertEqual(game.weapon.reserve_ammo, 35)
        game.shoot()
        self.assertEqual(game.training_session.shots, 2)
        self.assertEqual(game.training_session.hits, 2)
        self.assertEqual(game.training_session.elapsed_time(11.5), 1.5)

    def complete_training(self):
        game = self.game
        shots = 0
        for target in game.targets.values():
            self.camera.lookAt(target.root, Point3(1, 1, 1))
            for _ in range(4):
                game.clock.setFrameTime(10.0 + shots * 0.5)
                game.shoot()
                shots += 1
                self.assertEqual(game.training_session.is_complete, shots == 12)
            self.assertEqual(target.health, 0)
            self.assertTrue(target.root.isStashed())

    def test_last_target_finishes_timer_and_later_shots_keep_results(self):
        game = self.game
        self.complete_training()
        self.assertEqual(game.training_session.shots, 12)
        self.assertEqual(game.training_session.hits, 12)
        self.assertIn("Complete: 5.50s", self.hud_text())

        game.reload_weapon()
        game.clock.setFrameTime(30.0)
        game.finish_weapon_reload(None)
        game.shoot()
        game.update_training_hud()

        self.assertEqual(game.weapon.ammo, 11)
        self.assertEqual(game.training_session.shots, 12)
        self.assertEqual(game.training_session.hits, 12)
        self.assertEqual(game.training_session.accuracy, 100.0)
        self.assertEqual(game.training_session.elapsed_time(100.0), 5.5)
        self.assertIn("Complete: 5.50s", self.hud_text())

    def test_restart_resets_session_and_existing_game_state(self):
        game = self.game
        game.shoot()
        game.reload_weapon()
        game.update_targets(None)
        self.assertNotEqual(game.targets["target-2"].root.getX(), -5)
        game.player.setPos(2, 3, 0)
        game.player.setH(45)
        game.camera_pitch = 30.0
        self.camera.setP(30)
        game.mouse_ready = True
        game.restart_training()

        self.assertEqual(game.training_session.shots, 0)
        self.assertEqual(game.training_session.hits, 0)
        self.assertEqual(game.training_session.elapsed_time(100.0), 0.0)
        self.assertFalse(game.training_session.is_complete)
        self.assertIn("Shots: 0 | Hits: 0", self.hud_text())
        self.assertIn("Time: 0.00s", self.hud_text())
        self.assertEqual(game.weapon.ammo, 12)
        self.assertEqual(game.weapon.reserve_ammo, 36)
        self.assertFalse(game.weapon.is_reloading)
        self.assertEqual(game.player.getPos(), Point3(0, -2, 0))
        self.assertEqual(game.player.getH(), 0)
        self.assertEqual(game.camera_pitch, 0)
        self.assertEqual(self.camera.getP(), 0)
        self.assertFalse(game.mouse_ready)
        self.assertTrue(game.hitmarker.isHidden())
        for target in game.targets.values():
            self.assertEqual(target.health, 100)
            self.assertFalse(target.root.isStashed())
            self.assertEqual(target.root.getPos(), target.start_position)
            self.assertEqual(target.move_direction, 1)
            self.task_manager.remove.assert_any_call(f"reset-color-{target.name}")
        self.task_manager.remove.assert_any_call("hide-hitmarker")
        self.task_manager.remove.assert_any_call("reload-weapon")

    def test_restart_allows_another_completed_run(self):
        self.complete_training()
        self.game.restart_training()
        self.complete_training()
        self.assertEqual(self.game.training_session.shots, 12)
        self.assertEqual(self.game.training_session.hits, 12)
        self.assertEqual(self.game.training_session.elapsed_time(100.0), 5.5)

    def test_training_hud_uses_top_right_anchor(self):
        game = self.game
        game.a2dTopRight = game.aspect2d.attachNewNode("top-right")
        with patch("main.OnscreenText") as onscreen_text:
            game.setup_training_hud()
        self.assertIs(onscreen_text.call_args.kwargs["parent"], game.a2dTopRight)
        self.assertEqual(onscreen_text.call_args.kwargs["pos"], (-0.05, -0.10))
        self.task_manager.add.assert_any_call(
            game.update_training_hud, "update-training-hud", sort=15
        )

    def test_reload_hud_keeps_existing_ammunition_thresholds(self):
        game = self.game
        for ammo in range(12):
            with self.subTest(ammo=ammo):
                game.weapon.ammo = ammo
                game.update_weapon_hud()
                text = self.weapon_hud.setText.call_args.args[0]
                prompt = "R - Emergency Reload" if ammo < 5 else "R - Reload"
                self.assertIn(prompt, text)
        game.weapon.reserve_ammo = 0
        game.update_weapon_hud()
        self.assertNotIn("R -", self.weapon_hud.setText.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
