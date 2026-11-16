from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import unittest

from breach_shift.combat.catalog import WEAPON_ORDER, WeaponKind
from breach_shift.enemies.catalog import ZOMBIE_ORDER, ZombieKind
from breach_shift.platformer.levels import load_side_levels
from breach_shift.platformer.physics import Body, Rect
from breach_shift.platformer.session import Controls, Projectile, SideSession
from breach_shift.world.reality import Reality


class SideSessionTests(unittest.TestCase):
    def setUp(self):
        self.session = SideSession(training=True, seed=7)

    def tick(self, duration, controls=None):
        for _ in range(round(duration * 120)):
            self.session.step(controls or Controls(), 1/120)

    def test_double_jump_reverses_fall_and_rejects_a_third_jump(self):
        game = self.session
        game.step(Controls(jump=True), .05)
        self.tick(.5)
        game.step(Controls(jump=True), .01)
        self.assertGreater(game.player.vz, 0)
        self.assertEqual(game.jumps_used, 2)
        speed = game.player.vz
        game.step(Controls(jump=True), .01)
        self.assertLess(game.player.vz, speed)
        self.tick(2)
        self.assertTrue(game.player.grounded)
        game.step(Controls(jump=True), .01)
        self.assertEqual(game.jumps_used, 1)

    def test_releasing_crouch_waits_until_tunnel_is_clear(self):
        game = self.session
        game.level = replace(game.level, platforms=game.level.platforms + (Rect(1, 1.2, 7, .4),))
        game.step(Controls(crouch=True), .01)
        game.step(Controls(), .01)
        self.assertTrue(game.crouching)
        game.player.x = 10
        game.step(Controls(), .01)
        self.assertFalse(game.crouching)

    def test_ceiling_does_not_replenish_airborne_jumps(self):
        game = self.session
        game.level = replace(game.level, platforms=game.level.platforms + (Rect(1, 2, 7, .3),))
        game.step(Controls(jump=True), .05)
        self.assertAlmostEqual(game.player.z, .2)
        self.assertEqual(game.player.vz, 0)
        self.assertEqual(game.jumps_used, 1)

    def test_bullets_hit_nearest_enemy_and_walls_block_damage(self):
        game = self.session
        enemies = list(game.enemies.values())
        enemies[0].body.x, enemies[1].body.x = 8, 12
        game.fire((20, 1.2))
        self.assertLess(enemies[0].health, 100)
        self.assertEqual(enemies[1].health, 100)
        game.now += 1
        game.level = replace(game.level, platforms=game.level.platforms + (Rect(5, 0, .2, 3),))
        health = enemies[0].health
        game.fire((20, 1.2))
        self.assertEqual(enemies[0].health, health)

    def test_reload_is_timed_and_switching_cancels_without_free_ammo(self):
        game = self.session
        game.fire((0, 9))
        ammo = game.weapon.ammo
        game.step(Controls(reload=True), .01)
        self.tick(.5)
        self.assertEqual(game.weapon.ammo, ammo)
        self.assertTrue(game.weapon.is_reloading)
        game.step(Controls(slot=2), .01)
        self.assertFalse(game.arsenal.weapons[WeaponKind.PISTOL].is_reloading)
        self.assertIsNone(game.reload_started)
        game.step(Controls(slot=0, reload=True), .01)
        self.tick(1.6)
        self.assertEqual(game.weapon.ammo, 12)
        self.assertEqual(game.weapon.reserve_ammo, 35)

    def test_shift_refuses_materializing_a_gate_inside_player(self):
        game = SideSession(seed=2)
        game.player.x = game.level.breach_gate.x + .2
        before = game.player.x
        game.shift()
        self.assertIs(game.reality.state, Reality.NORMAL)
        self.assertEqual(game.player.x, before)
        game.player.x -= 3
        game.shift()
        self.assertIs(game.reality.state, Reality.BREACH)
        game.shift()
        self.assertIs(game.reality.state, Reality.BREACH)

    def test_crouch_avoids_high_spit_but_low_spit_still_hits(self):
        game = self.session
        game.step(Controls(crouch=True), .01)
        game.projectiles.append(Projectile(game.player.x + .8, 1.3, -9, 0, 10))
        self.tick(.15, Controls(crouch=True))
        self.assertEqual(game.health.current, 100)
        game.projectiles.append(Projectile(game.player.x + .8, .6, -9, 0, 10))
        self.tick(.15, Controls(crouch=True))
        self.assertEqual(game.health.current, 90)

    def test_warden_is_unique_and_vulnerable_only_in_breach(self):
        game = SideSession(level=10, seed=2)
        bosses = [enemy for enemy in game.enemies.values() if enemy.kind is ZombieKind.WARDEN]
        self.assertEqual(len(bosses), 1)
        boss = bosses[0]
        self.assertFalse(game.damage_enemy(boss, 50))
        self.assertEqual(boss.health, boss.maximum)
        game.reality.state = Reality.BREACH
        self.assertTrue(game.damage_enemy(boss, 50))
        self.assertEqual(boss.health, boss.maximum - 50)

    def test_all_ten_sectors_require_core_clear_and_normal_to_extract(self):
        game = SideSession(seed=2)
        for number in range(1, 11):
            self.assertEqual(game.level.number, number)
            game.player.x, game.player.z = game.level.exit
            game.interact()
            self.assertFalse(game.progress.complete)
            game.reality.state = Reality.BREACH
            game.player.x, game.player.z = game.level.core[0], game.level.core[1] - .9
            game.interact()
            self.assertTrue(game.progress.core_collected)
            self.assertTrue(game.director.sealed)
            for enemy in tuple(game.enemies.values()):
                game.damage_enemy(enemy, 10000)
            game.player.x, game.player.z = game.level.exit
            game.interact()
            self.assertEqual(game.level.number, number)
            game.reality.state = Reality.NORMAL
            game.interact()
        self.assertTrue(game.progress.complete)
        game.restart()
        self.assertEqual(game.level.number, 1)
        self.assertTrue(game.health.is_alive)

    def test_dead_enemy_drops_once_and_retry_clears_transient_state(self):
        game = SideSession(seed=2)
        enemy = next(iter(game.enemies.values()))
        game.damage_enemy(enemy, 10000)
        game.damage_enemy(enemy, 10000)
        self.assertEqual(len(game.pickups), 1)
        game.health.take_damage(60)
        game.restart()
        self.assertEqual(game.health.current, 100)
        self.assertEqual(game.pickups, [])
        self.assertEqual(game.traces, [])
        self.assertEqual(game.projectiles, [])
        self.assertEqual(game.player.z, 0)

    def test_sealed_core_stops_future_reinforcements(self):
        game = SideSession(seed=1)
        game.director.seal()
        count = game.alive
        game._reinforce(120)
        self.assertEqual(game.alive, count)

    def test_training_records_a_pellet_burst_as_one_shot_and_one_hit(self):
        game = self.session
        game.arsenal.select(WeaponKind.SHOTGUN)
        first = next(iter(game.enemies.values()))
        first.body.x = 8
        game.fire((8, 1.2))
        self.assertEqual(game.statistics.shots, 1)
        self.assertEqual(game.statistics.hits, 1)


class SideLevelTests(unittest.TestCase):
    def test_all_maps_have_original_platform_layouts_and_ordered_rosters(self):
        levels = load_side_levels()
        self.assertEqual(len(levels), 10)
        self.assertEqual(len({level.platforms for level in levels}), 10)
        for level in levels:
            self.assertIs(level.introduced, ZOMBIE_ORDER[level.number - 1])
            self.assertTrue(any(spawn.kind is level.introduced for spawn in level.spawns))
            self.assertLess(level.normal_gate.x, level.core[0])
            self.assertLess(level.core[0], level.breach_gate.x)
            self.assertLess(level.breach_gate.x, level.exit[0])
            self.assertGreaterEqual(level.normal_gate.height, 12)

    def test_levels_load_without_the_checkout_as_current_directory(self):
        previous = Path.cwd()
        with TemporaryDirectory() as temporary:
            try:
                os.chdir(temporary)
                self.assertEqual(len(load_side_levels()), 10)
            finally:
                os.chdir(previous)

    def test_invalid_coordinates_and_solid_spawns_are_rejected(self):
        source = Path(__file__).resolve().parents[1] / "breach_shift/data/platforms/01_yard.json"
        for field, value in (("size", [float("inf"), 18]), ("player_spawn", [2000, 0]),
                             ("player_spawn", [19.5, 0])):
            data = json.loads(source.read_text())
            data[field] = value
            with self.subTest(field=field, value=value), TemporaryDirectory() as temporary:
                (Path(temporary) / "01.json").write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    load_side_levels(Path(temporary))
