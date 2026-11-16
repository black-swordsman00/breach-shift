from dataclasses import replace
import unittest
from unittest.mock import MagicMock

from panda3d.core import Camera, ClockObject, GraphicsWindow, KeyboardButton, NodePath, Point3

from breach_shift.campaign.game import CampaignGame
from breach_shift.world.levels import MapBounds
from breach_shift.world.reality import Reality
from breach_shift.training.session import TrainingSession
from breach_shift.combat.weapon import Weapon
from breach_shift.enemies.catalog import ZombieKind
from breach_shift.combat.catalog import WEAPON_ORDER, WEAPON_SPECS, WeaponKind


class CampaignIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.game = CampaignGame.__new__(CampaignGame)
        game = self.game
        game.campaign_ready = False
        self.window = MagicMock(spec=GraphicsWindow)
        self.window.getProperties().getForeground.return_value = True
        game.win = self.window
        self.accept_events = MagicMock()
        game.accept = self.accept_events
        game.taskMgr = MagicMock()
        game.setBackgroundColor = MagicMock()
        game.clock = ClockObject()
        game.clock.setMode(ClockObject.M_non_real_time)
        game.clock.setFrameTime(10.0)
        game.clock.setDt(0.05)
        game.render = NodePath("campaign-test-render")
        game.player = game.render.attachNewNode("player")
        game.player.setPos(0, -2, 0)
        game.setup_jumping()
        self.camera = game.player.attachNewNode(Camera("camera"))
        self.camera.setPos(0, 0, 1.7)
        game.camera = self.camera
        game.camNode = self.camera.node()
        game.camera_pitch = 0.0
        game.mouse_ready = False
        game.move_speed = 5.0
        game.mouseWatcherNode = None
        game.floor = game.render.attachNewNode("floor")
        game.load_single_model = lambda path: NodePath("test-cube")
        game.create_targets()
        game.setup_collisions()
        game.setup_shooting()
        game.aspect2d = NodePath("campaign-test-aspect2d")
        game.a2dTopLeft = game.aspect2d.attachNewNode("top-left")
        game.a2dTopRight = game.aspect2d.attachNewNode("top-right")
        game.a2dBottomLeft = game.aspect2d.attachNewNode("bottom-left")
        game.create_crosshair()
        game.create_hitmarker()
        game.weapon = Weapon()
        game.training_session = TrainingSession()
        game.weapon_hud = MagicMock()
        game.target_hud = MagicMock()
        game.training_hud = MagicMock()
        game.setup_campaign()
        self.campaign_hud = MagicMock()
        game.campaign_hud = self.campaign_hud
        self.level = game.levels[0]
        self.initial_enemies = game.enemies_remaining

    def tearDown(self):
        self.game.render.removeNode()
        self.game.aspect2d.removeNode()

    def tick(self, seconds=0.05):
        self.game.clock.setFrameTime(self.game.clock.getFrameTime() + seconds)

    def test_shift_preserves_combat_state_and_respects_cooldown_and_hold(self):
        game = self.game
        zombie = next(iter(game.zombies.values()))
        zombie.take_damage(25)
        game.player_health.take_damage(20)
        game.shift_reality()
        self.assertIs(game.reality.state, Reality.BREACH)
        self.assertEqual(zombie.health, 50)
        self.assertEqual(game.player_health.current, 80)
        self.assertEqual(game.weapon.ammo, 12)
        game.release_shift()
        game.shift_reality()
        self.assertIs(game.reality.state, Reality.BREACH)
        self.tick(2.1)
        game.shift_reality()
        self.assertIs(game.reality.state, Reality.BREACH)
        game.release_shift()
        game.shift_reality()
        self.assertIs(game.reality.state, Reality.NORMAL)

    def test_crouch_avoids_a_high_projectile_and_keeps_low_shots_dangerous(self):
        game=self.game
        x,y=self.level.player_spawn
        game.press_crouch('control')
        game.update_movement(None)
        game.spawn_projectile(Point3(x,y+2,1.16),Point3(x,y,1.16),10)
        game.update_projectiles(.3)
        self.assertEqual(game.player_health.current,100)
        game.clear_projectiles()
        game.spawn_projectile(Point3(x,y+2,.55),Point3(x,y,.55),10)
        game.update_projectiles(.3)
        self.assertEqual(game.player_health.current,90)

    def test_reload_moves_support_hand_and_weapon_without_granting_ammo_early(self):
        game=self.game
        game.select_weapon(WeaponKind.RIFLE)
        game.shoot()
        remaining=game.weapon.ammo
        game.reload_weapon()
        started=game.weapon_view.reload_started
        self.tick(.2)
        game.reload_weapon()
        self.assertEqual(game.weapon_view.reload_started,started)
        self.tick(game.weapon.reload_time*.4)
        game.update_targets(None)
        self.assertGreater(game.weapon_view.reload_progress,.3)
        self.assertGreater(abs(game.weapon_view.root.getR()),10)
        self.assertGreater(game.weapon_view.hands['left'].getPos().length(),.05)
        self.assertEqual(game.weapon.ammo,remaining)
        self.assertFalse(game.weapon.try_fire(game.clock.getFrameTime()))
        game.finish_weapon_reload(None)
        self.assertEqual(game.weapon.ammo,game.weapon.magazine_size)
        self.assertIsNone(game.weapon_view.reload_started)
        self.assertEqual(game.weapon_view.hands['left'].getPos(),Point3(0,0,0))

    def test_slot_switch_and_retry_cancel_reload_pose_and_pending_ammo(self):
        game=self.game
        game.shoot()
        game.reload_weapon()
        pistol=game.weapon
        game.select_weapon(WeaponKind.SHOTGUN)
        self.assertFalse(pistol.is_reloading)
        self.assertEqual(pistol.ammo,11)
        self.assertIsNone(game.weapon_view.reload_started)
        game.shoot()
        game.reload_weapon()
        game.restart_training()
        self.assertIsNone(game.weapon_view.reload_started)
        self.assertEqual(game.weapon_view.hands['left'].getPos(),Point3(0,0,0))

    def test_unsafe_shift_does_not_consume_cooldown(self):
        game = self.game
        game.shift_reality()
        self.tick(3)
        gate = self.level.blocks[0]
        game.player.setPos(gate.x, gate.y, 0)
        game.release_shift()
        game.shift_reality()
        self.assertIs(game.reality.state, Reality.BREACH)
        self.assertEqual(game.reality.remaining(game.clock.getFrameTime()), 0)
        game.player.setY(gate.y + 2)
        game.release_shift()
        game.shift_reality()
        self.assertIs(game.reality.state, Reality.NORMAL)

    def test_accepted_shots_damage_independent_zombies_and_destroy_their_colliders(self):
        game = self.game
        zombie, other = tuple(game.zombies.values())[:2]
        game.player.setPos(zombie.root.getX(), zombie.root.getY() - 3, 0)
        self.camera.lookAt(zombie.root, Point3(0, 0, 1))
        game.shoot()
        self.assertEqual(zombie.health, 50)
        self.assertEqual(other.health, 75)
        self.assertEqual(game.training_session.shots, 1)
        self.assertEqual(game.training_session.hits, 1)
        game.shoot()
        self.assertEqual(game.training_session.shots, 1)
        for _ in range(2):
            self.tick(0.3)
            game.shoot()
        self.assertEqual(zombie.health, 0)
        self.assertFalse(zombie.root.isStashed())
        self.assertTrue(zombie.collider.isStashed())
        self.assertIsNone(game.query_collision(zombie.root.getPos()+Point3(0,-1,1),
                                              zombie.root.getPos()+Point3(0,1,1)))
        self.assertEqual(game.enemies_remaining, self.initial_enemies - 1)
        self.assertTrue(game.hitmarker.isHidden() is False)

    def test_melee_damage_death_input_lock_and_retry(self):
        game = self.game
        zombie = next(iter(game.zombies.values()))
        zombie.root.setPos(game.player.getX(), game.player.getY() + 0.8, 0)
        self.tick(1)
        game.update_targets(None)
        self.assertEqual(game.player_health.current, 88)
        self.tick()
        game.update_targets(None)
        self.assertEqual(game.player_health.current, 88)
        game.damage_player(1000)
        game.shoot()
        game.jump_player()
        game.shift_reality()
        self.assertEqual(game.weapon.ammo, 12)
        self.assertEqual(game.jump_state.jumps_used, 0)
        self.assertIs(game.reality.state, Reality.NORMAL)
        game.restart_training()
        self.assertEqual(game.player_health.current, 100)
        self.assertEqual(game.player.getPos(), Point3(*self.level.player_spawn, 0))
        self.assertEqual(game.weapon.ammo, 12)
        self.assertEqual(game.enemies_remaining, self.initial_enemies)

    def test_core_reward_is_once_and_every_map_can_advance_through_real_interactions(self):
        game = self.game
        for index, level in enumerate(game.levels):
            game.player.setPos(*level.exit, 0)
            game.interact()
            self.assertEqual(game.progress.level_index, index)
            self.assertFalse(game.progress.complete)
            game.player.setPos(*level.core, 0)
            game.interact()
            self.assertFalse(game.progress.core_collected)
            game.shift_reality()
            game.interact()
            self.assertTrue(game.progress.core_collected)
            reserve = game.weapon.reserve_ammo
            game.interact()
            self.assertEqual(game.weapon.reserve_ammo, reserve)
            for zombie in game.zombies.values():
                zombie.set_context(game.clock.getFrameTime(), Reality.BREACH)
                zombie.take_damage(1000)
            game.player.setPos(*level.exit, 0)
            game.interact()
        self.assertTrue(game.progress.complete)
        game.restart_training()
        self.assertEqual(game.progress.level_index, 0)
        self.assertFalse(game.progress.complete)

    def test_projectiles_hit_player_and_are_blocked_by_geometry(self):
        game = self.game
        x, y = self.level.player_spawn
        game.spawn_projectile(Point3(x, y + 2, 0.9), Point3(x, y, 0.9), 10)
        game.update_projectiles(0.3)
        self.assertEqual(game.player_health.current, 90)
        self.assertFalse(game.projectiles)
        gate = self.level.blocks[0]
        game.spawn_projectile(Point3(gate.x, gate.y + 1, 0.9), Point3(gate.x, gate.y - 3, 0.9), 10)
        game.update_projectiles(0.5)
        self.assertEqual(game.player_health.current, 90)
        self.assertFalse(game.projectiles)

    def test_zombies_cannot_attack_through_a_reality_barrier(self):
        game = self.game
        zombie = next(iter(game.zombies.values()))
        gate = self.level.blocks[0]
        zombie.root.setPos(gate.x, gate.y + 0.5, 0)
        game.player.setPos(gate.x, gate.y - 0.5, 0)
        self.tick(1)
        game.update_targets(None)
        self.assertEqual(game.player_health.current, 100)

    def test_howler_summons_are_registered_for_bullets_and_exit_conditions(self):
        game = self.game
        howler = game.spawn_zombie(ZombieKind.HOWLER, game.player.getX(), game.player.getY() + 6)
        howler.next_summon = 0
        game.update_targets(None)
        self.assertEqual(game.enemies_remaining, self.initial_enemies + 2)
        self.assertEqual(len(game.targets), self.initial_enemies + 2)

    def test_shift_relocates_embedded_zombies_without_restoring_their_health(self):
        game = self.game
        game.shift_reality()
        zombie = next(iter(game.zombies.values()))
        gate = self.level.blocks[0]
        zombie.root.setPos(gate.x, gate.y, 0)
        zombie.take_damage(25)
        self.tick(3)
        game.release_shift()
        game.shift_reality()
        world = game.world
        self.assertIsNotNone(world)
        assert world is not None
        self.assertTrue(world.grids[Reality.NORMAL].is_free(zombie.root.getX(), zombie.root.getY()))
        self.assertEqual(zombie.health, 50)

    def test_loading_a_large_map_updates_floor_boundaries_grounding_and_retry(self):
        game = self.game
        level = replace(game.levels[0], bounds=MapBounds(-30, 30, -15, 75), player_spawn=(20, -10))
        game.levels = (level, *game.levels[1:])
        game.load_level()
        self.assertEqual(game.player.getPos(), Point3(20, -10, 0))
        self.assertAlmostEqual(game.floor.getX(), -30)
        self.assertAlmostEqual(game.floor.getY(), -15)
        self.assertAlmostEqual(game.floor.getSx(), 60)
        self.assertAlmostEqual(game.floor.getSy(), 90)
        game.update_collisions(None)
        self.assertEqual(game.player.getPos(), Point3(20, -10, 0))
        game.jump_player()
        for _ in range(40):
            game.update_movement(None)
            game.update_collisions(None)
        self.assertTrue(game.jump_state.is_grounded)
        self.assertAlmostEqual(game.player.getZ(), 0)
        game.player.setPos(29.9, -10, 0)
        game.update_collisions(None)
        self.assertLessEqual(game.player.getX(), 29.61)
        game.restart_training()
        self.assertEqual(game.player.getPos(), Point3(20, -10, 0))

    def test_campaign_pace_is_consistent_across_frame_rates_and_diagonal_input(self):
        game = self.game
        keyboard = MagicMock()
        game.mouseWatcherNode = keyboard
        for frame_rate in (20, 30, 60, 144):
            for diagonal in (False, True):
                with self.subTest(frame_rate=frame_rate, diagonal=diagonal):
                    game.player.setPos(*self.level.player_spawn, 0)
                    game.player.setH(0)
                    game.jump_state.reset()
                    start = game.player.getPos()
                    keyboard.isButtonDown.side_effect = lambda button: (
                        button == KeyboardButton.asciiKey("w")
                        or (diagonal and button == KeyboardButton.asciiKey("d")))
                    game.clock.setDt(1 / frame_rate)
                    for _ in range(frame_rate):
                        game.update_movement(None)
                        game.update_collisions(None)
                    distance = (game.player.getPos() - start).length()
                    self.assertAlmostEqual(distance, 6.5, places=4)

    def test_objective_guidance_tracks_player_direction_and_nearby_interactions(self):
        game = self.game
        game.player.setPos(0, 0, 0)
        game.player.setH(0)
        self.assertEqual(game.navigation_hint((0, 10)), "10m ahead")
        self.assertEqual(game.navigation_hint((10, 0)), "10m right")
        self.assertEqual(game.navigation_hint((-10, 0)), "10m left")
        self.assertEqual(game.navigation_hint((0, -10)), "10m behind")
        game.player.setH(180)
        self.assertEqual(game.navigation_hint((0, 10)), "10m behind")
        self.assertEqual(game.navigation_hint((0, 1)), "Nearby")
        game.update_campaign_hud()
        self.assertIn("Core: Breach |", self.campaign_hud.setText.call_args.args[0])
        game.progress.collect_core()
        game.update_campaign_hud()
        self.assertIn("Core: Recovered", self.campaign_hud.setText.call_args.args[0])

    def test_weapon_switching_updates_the_visible_model_and_cancels_old_reload(self):
        game = self.game
        game.shoot()
        pistol = game.weapon
        game.reload_weapon()
        game.select_weapon(WeaponKind.RIFLE)
        self.assertFalse(pistol.is_reloading)
        self.assertEqual(game.weapon.damage, 38)
        self.assertFalse(game.weapon_view.root.find("**/rifle-model").isEmpty())
        game.finish_weapon_reload(None)
        game.select_weapon(WeaponKind.PISTOL)
        self.assertEqual(game.weapon.ammo, 11)
        self.game.taskMgr.remove.assert_any_call("reload-weapon")

    def test_firing_and_enemy_damage_trigger_the_matching_audio_events(self):
        game = self.game
        game.audio = MagicMock()
        game.select_weapon(WeaponKind.RIFLE)
        game.shoot()
        cues = [call.args[0] for call in game.audio.play.call_args_list]
        self.assertIn("fire_rifle", cues)
        zombie = next(zombie for zombie in game.zombies.values() if zombie.health > 0)
        game.damage_target(zombie, 1)
        self.assertEqual(game.audio.play.call_args.args[0], "zombie_hurt")
        game.damage_target(zombie, 1000)
        self.assertEqual(game.audio.play.call_args.args[0], "zombie_death")

    def test_every_weapon_deals_its_damage_and_shotgun_uses_one_shell(self):
        game = self.game
        zombie = game.spawn_zombie(ZombieKind.WARDEN, game.player.getX(), game.player.getY() + 3)
        game.reality.state = Reality.BREACH
        game.apply_reality()
        self.camera.lookAt(zombie.root, Point3(0, 0, 1))
        for kind in WEAPON_ORDER:
            with self.subTest(kind=kind):
                zombie.health = zombie.max_health
                game.select_weapon(kind)
                self.tick(2)
                game.shoot()
                self.assertEqual(zombie.max_health - zombie.health, WEAPON_SPECS[kind].damage)
                self.assertEqual(game.weapon.ammo, game.weapon.magazine_size - 1)
        self.assertEqual(game.training_session.shots, 4)
        self.assertEqual(game.training_session.hits, 4)

    def test_dead_enemy_drops_once_and_pickup_adds_only_its_ammunition(self):
        game = self.game
        zombie = next(iter(game.zombies.values()))
        zombie.root.setPos(game.player.getX(), game.player.getY() + 1, 0)
        game.damage_target(zombie, 1000)
        self.assertEqual(len(game.pickups), 1)
        pickup = game.pickups[0]
        weapon = game.arsenal.weapons[pickup.reward.kind]
        before = weapon.reserve_ammo
        game.damage_target(zombie, 1000)
        self.assertEqual(len(game.pickups), 1)
        game.update_pickups(.05)
        self.assertFalse(game.pickups)
        self.assertEqual(weapon.reserve_ammo, before + pickup.reward.rounds)

    def test_expired_loot_and_retry_remove_old_pickups(self):
        game = self.game
        zombie = next(iter(game.zombies.values()))
        game.damage_target(zombie, 1000)
        pickup = game.pickups[0]
        game.player.setPos(pickup.root.getX(), pickup.root.getY(), 0)
        before = game.arsenal.weapons[pickup.reward.kind].reserve_ammo
        game.update_pickups(91)
        self.assertEqual(game.arsenal.weapons[pickup.reward.kind].reserve_ammo, before)
        self.assertFalse(game.pickups)
        zombie = next(zombie for zombie in game.zombies.values() if zombie.health > 0)
        game.damage_target(zombie, 1000)
        game.restart_training()
        self.assertFalse(game.pickups)
        self.assertEqual(game.director.elapsed, 0)

    def test_reinforcements_are_reachable_distant_and_use_only_introduced_enemies(self):
        game = self.game
        original = set(game.zombies)
        self.tick(31)
        game.update_targets(None)
        additions = [zombie for name, zombie in game.zombies.items() if name not in original]
        self.assertEqual(len(additions), 3)
        for zombie in additions:
            self.assertIs(zombie.kind, ZombieKind.WALKER)
            self.assertGreaterEqual((zombie.root.getPos() - game.player.getPos()).length(), 11.9)
            for grid in game.world.grids.values():
                self.assertTrue(grid.is_free(zombie.root.getX(), zombie.root.getY()))
            grid = game.world.grids[game.reality.state]
            self.assertTrue(grid.find_path((game.player.getX(), game.player.getY()),
                                           (zombie.root.getX(), zombie.root.getY())))

    def test_unfocused_time_does_not_advance_waves_and_core_seals_them(self):
        game = self.game
        self.window.getProperties().getForeground.return_value = False
        self.tick(100)
        game.update_targets(None)
        self.window.getProperties().getForeground.return_value = True
        self.tick()
        game.update_targets(None)
        self.assertEqual(game.enemies_remaining, self.initial_enemies)
        game.player.setPos(*self.level.core, 0)
        game.shift_reality()
        game.interact()
        self.assertTrue(game.director.sealed)
        self.tick(100)
        game.update_targets(None)
        self.assertEqual(game.enemies_remaining, self.initial_enemies)

    def test_automatic_fire_requires_hold_and_stops_on_release_and_focus_loss(self):
        game = self.game
        game.select_weapon(WeaponKind.SMG)
        game.shoot()
        self.tick(.1)
        game.update_targets(None)
        self.assertEqual(game.weapon.ammo, 28)
        game.release_trigger()
        self.tick(.1)
        game.update_targets(None)
        self.assertEqual(game.weapon.ammo, 28)
        game.shoot()
        self.window.getProperties().getForeground.return_value = False
        self.tick(.1)
        game.update_targets(None)
        self.assertFalse(game.trigger_held)
