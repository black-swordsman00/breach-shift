import unittest

from panda3d.core import NodePath, Point3

from navigation import NavigationGrid
from reality import Reality
from zombie import Zombie
from zombie_catalog import ZombieKind


class ZombieTests(unittest.TestCase):
    def setUp(self):
        self.render = NodePath("zombie-test-render")
        self.grid = NavigationGrid((), Reality.NORMAL)

    def tearDown(self):
        self.render.removeNode()

    def make(self, kind):
        return Zombie(self.render, NodePath("cube"), Point3(0, 0, 0), kind, kind.value)

    def test_walker_attacks_have_cooldowns_and_respect_line_of_sight_and_height(self):
        zombie = self.make(ZombieKind.WALKER)
        self.assertFalse(zombie.update_ai(0.05, 1, Point3(0, 0.8, 0), Reality.NORMAL, self.grid, False))
        self.assertFalse(zombie.update_ai(0.05, 1, Point3(0, 0.8, 2), Reality.NORMAL, self.grid, True))
        actions = zombie.update_ai(0.05, 1, Point3(0, 0.8, 0), Reality.NORMAL, self.grid, True)
        self.assertEqual(actions[0].kind, "hit")
        self.assertFalse(zombie.update_ai(0.05, 1.1, Point3(0, 0.8, 0), Reality.NORMAL, self.grid, True))

    def test_runner_and_breach_movement_are_faster(self):
        walker = self.make(ZombieKind.WALKER)
        runner = self.make(ZombieKind.RUNNER)
        shifted = self.make(ZombieKind.WALKER)
        for zombie, reality in ((walker, Reality.NORMAL), (runner, Reality.NORMAL), (shifted, Reality.BREACH)):
            zombie.update_ai(0.1, 1, Point3(0, 6, 0), reality, self.grid, True)
        self.assertGreater(runner.root.getY(), walker.root.getY())
        self.assertGreater(shifted.root.getY(), walker.root.getY())

    def test_armored_and_warden_damage_depend_on_reality(self):
        armor = self.make(ZombieKind.ARMORED)
        armor.take_damage(25)
        self.assertEqual(armor.health, 113)
        armor.set_context(1, Reality.BREACH)
        armor.take_damage(25)
        self.assertEqual(armor.health, 88)
        warden = self.make(ZombieKind.WARDEN)
        self.assertFalse(warden.take_damage(25))
        warden.set_context(1, Reality.BREACH)
        self.assertTrue(warden.take_damage(25))
        self.assertEqual(warden.health, 275)

    def test_spitter_emits_projectiles_instead_of_instant_melee_damage(self):
        zombie = self.make(ZombieKind.SPITTER)
        actions = zombie.update_ai(0.05, 1, Point3(0, 5, 0), Reality.NORMAL, self.grid, True)
        self.assertEqual([action.kind for action in actions], ["spit"])

    def test_howler_has_a_bounded_summon_budget(self):
        zombie = self.make(ZombieKind.HOWLER)
        summons = []
        for now in (5, 12, 19):
            summons.extend(action for action in zombie.update_ai(0.05, now, Point3(0, 7, 0), Reality.NORMAL, self.grid, True) if action.kind == "summon")
        self.assertEqual(len(summons), 2)

    def test_stalker_is_revealed_by_breach_or_proximity(self):
        zombie = self.make(ZombieKind.STALKER)
        zombie.update_ai(0.01, 1, Point3(0, 7, 0), Reality.NORMAL, self.grid, True)
        self.assertTrue(zombie.model.isHidden())
        zombie.update_ai(0.01, 2, Point3(0, 7, 0), Reality.BREACH, self.grid, True)
        self.assertFalse(zombie.model.isHidden())
        zombie.update_ai(0.01, 3, Point3(0, 2, 0), Reality.NORMAL, self.grid, True)
        self.assertFalse(zombie.model.isHidden())

    def test_regeneration_waits_after_hits_and_stops_in_breach_or_after_death(self):
        zombie = self.make(ZombieKind.REGENERATOR)
        zombie.take_damage(25)
        zombie.update_ai(0.5, 1, Point3(0, 7, 0), Reality.NORMAL, self.grid, True)
        self.assertEqual(zombie.health, 75)
        zombie.update_ai(0.5, 3, Point3(0, 7, 0), Reality.NORMAL, self.grid, True)
        self.assertEqual(zombie.health, 79)
        zombie.update_ai(0.5, 4, Point3(0, 7, 0), Reality.BREACH, self.grid, True)
        self.assertEqual(zombie.health, 79)
        zombie.take_damage(500)
        self.assertFalse(zombie.update_ai(1, 10, Point3(0, 7, 0), Reality.NORMAL, self.grid, True))
        self.assertEqual(zombie.health, 0)

    def test_leaper_telegraphs_then_lunges_and_lands(self):
        zombie = self.make(ZombieKind.LEAPER)
        zombie.update_ai(0.05, 1, Point3(0, 4, 0), Reality.NORMAL, self.grid, True)
        self.assertIsNotNone(zombie.windup_until)
        zombie.update_ai(0.05, 1.3, Point3(0, 4, 0), Reality.NORMAL, self.grid, True)
        zombie.update_ai(0.1, 1.45, Point3(0, 4, 0), Reality.NORMAL, self.grid, True)
        self.assertGreater(zombie.root.getZ(), 0)
        self.assertGreater(zombie.root.getY(), 0)
        zombie.update_ai(0.05, 2, Point3(0, 4, 0), Reality.NORMAL, self.grid, True)
        self.assertEqual(zombie.root.getZ(), 0)

    def test_warden_stomp_can_be_dodged_by_jumping(self):
        zombie = self.make(ZombieKind.WARDEN)
        zombie.update_ai(0.05, 1, Point3(0, 2, 1), Reality.BREACH, self.grid, True)
        self.assertFalse(zombie.update_ai(0.05, 1.7, Point3(0, 2, 1), Reality.BREACH, self.grid, True))
        zombie.update_ai(0.05, 5, Point3(0, 2, 0), Reality.BREACH, self.grid, True)
        actions = zombie.update_ai(0.05, 5.7, Point3(0, 2, 0), Reality.BREACH, self.grid, True)
        self.assertEqual([action.kind for action in actions], ["hit"])

    def test_brute_has_a_longer_windup_and_a_grounded_charge(self):
        zombie = self.make(ZombieKind.BRUTE)
        zombie.update_ai(0.05, 1, Point3(0, 4, 0), Reality.NORMAL, self.grid, True)
        windup = zombie.windup_until
        assert windup is not None
        self.assertAlmostEqual(windup, 1.6)
        zombie.update_ai(0.05, 1.3, Point3(0, 4, 0), Reality.NORMAL, self.grid, True)
        self.assertEqual(zombie.root.getY(), 0)
        zombie.update_ai(0.1, 1.7, Point3(0, 4, 0), Reality.NORMAL, self.grid, True)
        self.assertGreater(zombie.root.getY(), 0)
        self.assertEqual(zombie.root.getZ(), 0)
