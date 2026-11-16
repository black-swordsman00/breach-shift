import unittest

from panda3d.core import ClockObject, OrthographicLens, PNMImage

from breach_shift.combat.catalog import WeaponKind
from breach_shift.platformer.game import SideViewGame
from breach_shift.platformer.session import Controls, SideSession


class SideRenderTests(unittest.TestCase):
    """Exercise the real PNG renderer and controls, including mirrored sprites."""
    @classmethod
    def setUpClass(cls):
        cls.game = SideViewGame(training=True,headless=True)
        cls.game.clock.setMode(ClockObject.M_non_real_time)
        cls.game.clock.setDt(.05)

    @classmethod
    def tearDownClass(cls):
        cls.game.destroy()

    def setUp(self):
        self.game.session = SideSession(training=True,seed=1)
        self.game._rebuild()
        self.game.set_paused(False)
        self.game.render_scene(0)

    def capture(self):
        self.game.graphicsEngine.renderFrame()
        self.game.graphicsEngine.renderFrame()
        image = PNMImage()
        self.assertTrue(self.game.win.getScreenshot(image))
        return image

    def test_actors_are_flat_cards_and_the_camera_is_orthographic(self):
        self.assertIsInstance(self.game.lens,OrthographicLens)
        self.assertTrue(self.game.render.find("**/+Character").isEmpty())
        vertices = self.game.player_sprite.card.node().getGeom(0).getVertexData().getNumRows()
        self.assertEqual(vertices,4)
        self.assertEqual(self.game.player_sprite.entry["file"],"player.png")

    def test_enemy_facing_left_really_draws_in_the_framebuffer(self):
        game = self.game
        enemy = next(iter(game.session.enemies.values()))
        enemy.facing = -1
        game.render_scene(0)
        visible = self.capture()
        game.enemies[enemy.identifier].node.hide()
        hidden = self.capture()
        x = round((enemy.body.x-game.camera_x)/game.view_width*visible.getXSize()+visible.getXSize()/2)
        z = round(visible.getYSize()/2-(enemy.body.z+.9-game.camera_z)/14.4*visible.getYSize())
        difference = sum(abs(visible.getXel(px,py)[channel]-hidden.getXel(px,py)[channel])
                         for py in range(z-48,z+48) for px in range(x-30,x+30) for channel in range(3))
        self.assertGreater(difference,20)

    def test_pause_freezes_simulation_and_clears_fire_input(self):
        game = self.game
        game.session.fire((20,8))
        game.session.step(Controls(reload=True),.01)
        before = game.session.now
        game._fire(True)
        game.set_paused(True)
        for _ in range(20):
            game.update_frame(None)
        self.assertEqual(game.session.now,before)
        self.assertEqual(game.session.reload_progress,0)
        self.assertFalse(game.fire_held)
        game.set_paused(False)
        game.update_frame(None)
        self.assertGreater(game.session.now,before)

    def test_held_pistol_fires_once_and_automatic_weapon_repeats(self):
        game = self.game
        game._fire(True)
        for _ in range(15):
            game.update_frame(None)
        self.assertEqual(game.session.weapon.ammo,11)
        game._fire(False)
        game._select(1)
        game._fire(True)
        for _ in range(12):
            game.update_frame(None)
        self.assertIs(game.session.arsenal.selected,WeaponKind.SMG)
        self.assertLess(game.session.weapon.ammo,28)

    def test_retry_restores_player_and_removes_previous_enemy_cards(self):
        game = self.game
        old_nodes = [sprite.node for sprite in game.enemies.values()]
        game.session.health.take_damage(80)
        game.session.player.x = 25
        game.set_paused(True)
        game.restart_sector()
        self.assertEqual(game.session.health.current,100)
        self.assertEqual(game.session.player.x,3)
        self.assertFalse(game.paused)
        self.assertTrue(all(node.isEmpty() for node in old_nodes))
        game.render_scene(0)
        self.assertEqual(len(game.enemies),3)

    def test_all_ten_scenes_load_in_both_realities_without_models(self):
        game = self.game
        from breach_shift.world.reality import Reality
        for number in range(1,11):
            game.session = SideSession(level=number,seed=1)
            game._rebuild()
            for reality in Reality:
                game.session.reality.state = reality
                game.render_scene(.01)
                self.capture()
                self.assertTrue(game.render.find("**/+Character").isEmpty())
                self.assertEqual(len(game.enemies),game.session.alive)


if __name__=="__main__":
    unittest.main()
