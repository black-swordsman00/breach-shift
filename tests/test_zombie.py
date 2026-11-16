import unittest

from panda3d.core import NodePath, Point3

from breach_shift.world.navigation import NavigationGrid
from breach_shift.world.levels import Block
from breach_shift.world.reality import Reality
from breach_shift.enemies.zombie import Zombie
from breach_shift.enemies.catalog import ZombieKind


class ZombieTests(unittest.TestCase):
    def test_slow_enemy_keeps_approaching_across_many_route_refreshes(self):
        zombie = self.make(ZombieKind.WALKER)
        player = Point3(0, 9, 0)
        for frame in range(180):
            zombie.update_ai(.05, frame * .05, player, Reality.NORMAL, self.grid, True)
        self.assertGreater(zombie.root.getY(), 7)
        self.assertLessEqual(zombie.root.getY(), 9)

    def test_enemy_goes_around_cover_and_reaches_the_player(self):
        grid = NavigationGrid((Block(0, 3, 3, 2, 2),), Reality.NORMAL)
        zombie = self.make(ZombieKind.RUNNER)
        player = Point3(0, 8, 0)
        for frame in range(240):
            zombie.update_ai(.05, frame * .05, player, Reality.NORMAL, grid, False)
            self.assertTrue(grid.is_free(zombie.root.getX(), zombie.root.getY()))
        self.assertLess((zombie.root.getPos() - player).length(), 1.2)

    def test_enemy_approaches_a_closed_gate_without_crossing_it(self):
        grid = NavigationGrid((Block(0, 8, 20, .6, 3.5),), Reality.NORMAL)
        zombie = self.make(ZombieKind.WALKER)
        for frame in range(200):
            zombie.update_ai(.05, frame * .05, Point3(0, 12, 0), Reality.NORMAL, grid, False)
        self.assertGreater(zombie.root.getY(), 6)
        self.assertLess(zombie.root.getY(), 8)

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

    def test_pursuit_is_twenty_percent_faster_and_gait_stops_when_stationary(self):
        zombie=self.make(ZombieKind.WALKER)
        player=Point3(0,9,0)
        for frame in range(20):
            zombie.update_ai(.05,frame*.05,player,Reality.NORMAL,self.grid,True)
            zombie.update_animation(.05,player)
        self.assertAlmostEqual(zombie.root.getY(),1.44,places=5)
        phase=zombie.motion.phase
        for _ in range(10):
            zombie.update_animation(.05,player)
        self.assertEqual(zombie.motion.phase,phase)

    def test_turns_blend_and_death_leaves_a_falling_body_without_collision(self):
        zombie=self.make(ZombieKind.WALKER)
        zombie.update_animation(.05,Point3(0,-5,0))
        self.assertGreater(abs(zombie.root.getH()),1)
        self.assertLess(abs(zombie.root.getH()),179)
        zombie.take_damage(1000)
        self.assertFalse(zombie.root.isStashed())
        self.assertTrue(zombie.collider.isStashed())
        for _ in range(15):
            zombie.update_animation(.05,Point3(0,-5,0))
        self.assertGreater(zombie.model.getP(),60)
        self.assertFalse(zombie.take_damage(1))

    def test_wide_warden_routes_with_clearance_for_its_actual_body(self):
        wall=Block(0,3,4,2,3)
        grid=NavigationGrid((wall,),Reality.NORMAL)
        boss=self.make(ZombieKind.WARDEN)
        for frame in range(240):
            boss.update_ai(.05,frame*.05,Point3(0,9,0),Reality.NORMAL,grid,False)
            p=boss.root.getPos()
            self.assertFalse(wall.overlaps_xy(p.x,p.y,boss.spec.radius+.1))
        self.assertGreater(boss.root.getY(),6)

    def test_walking_around_cover_turns_toward_travel_instead_of_sliding_sideways(self):
        zombie=self.make(ZombieKind.WALKER)
        zombie.root.setX(.1)
        zombie.update_animation(.05,Point3(0,10,0))
        self.assertLess(zombie.root.getH(),-20)
        self.assertGreater(zombie.root.getH(),-90)

    def test_armored_and_warden_damage_depend_on_reality(self):
        armor = self.make(ZombieKind.ARMORED)
        armor.take_damage(25)
        self.assertEqual(armor.health, armor.max_health - 12)
        armor.set_context(1, Reality.BREACH)
        armor.take_damage(25)
        self.assertEqual(armor.health, armor.max_health - 37)
        warden = self.make(ZombieKind.WARDEN)
        self.assertFalse(warden.take_damage(25))
        warden.set_context(1, Reality.BREACH)
        self.assertTrue(warden.take_damage(25))
        self.assertEqual(warden.health, warden.max_health - 25)

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
        self.assertEqual(zombie.health, zombie.max_health - 25)
        zombie.update_ai(0.5, 3, Point3(0, 7, 0), Reality.NORMAL, self.grid, True)
        self.assertEqual(zombie.health, zombie.max_health - 21)
        zombie.update_ai(0.5, 4, Point3(0, 7, 0), Reality.BREACH, self.grid, True)
        self.assertEqual(zombie.health, zombie.max_health - 21)
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

    def test_ranged_enemies_keep_routing_when_cover_blocks_a_nearby_player(self):
        grid = NavigationGrid((Block(0, 1, 1, 0.4, 2),), Reality.NORMAL)
        for kind in (ZombieKind.SPITTER, ZombieKind.WARDEN):
            with self.subTest(kind=kind):
                zombie = self.make(kind)
                actions = zombie.update_ai(0.1, 1, Point3(0, 2.5, 0), Reality.NORMAL, grid, False)
                self.assertFalse(actions)
                self.assertGreater(zombie.root.getPos().lengthSquared(), 0)
