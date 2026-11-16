import unittest

from panda3d.core import BitMask32, CollisionHandlerQueue, CollisionNode, CollisionSegment, CollisionTraverser, NodePath, Point3

from breach_shift.world.scene import CampaignWorld
from breach_shift.world.levels import load_levels
from breach_shift.world.reality import Reality


class CampaignWorldTests(unittest.TestCase):
    def setUp(self):
        self.render = NodePath("world-test-render")
        self.world = CampaignWorld(self.render, NodePath("cube"), load_levels()[0])

    def tearDown(self):
        self.render.removeNode()

    def crosses_first_gate(self):
        gate = self.world.level.blocks[0]
        ray = CollisionNode("test-ray")
        ray.addSolid(CollisionSegment(Point3(gate.x, gate.y - 1, 1), Point3(gate.x, gate.y + 1, 1)))
        ray.setFromCollideMask(BitMask32.bit(2))
        ray.setIntoCollideMask(BitMask32.allOff())
        node = self.render.attachNewNode(ray)
        queue = CollisionHandlerQueue()
        traverser = CollisionTraverser()
        traverser.addCollider(node, queue)
        traverser.traverse(self.render)
        count = queue.getNumEntries()
        node.removeNode()
        return count

    def test_real_collision_geometry_switches_with_the_visible_world(self):
        self.assertGreater(self.crosses_first_gate(), 0)
        self.world.apply(Reality.BREACH, False)
        self.assertEqual(self.crosses_first_gate(), 0)
        self.world.apply(Reality.NORMAL, False)
        self.assertGreater(self.crosses_first_gate(), 0)

    def test_shift_rejects_embedded_positions_but_allows_standing_on_cover(self):
        gate = self.world.level.blocks[0]
        cover = next(block for block in self.world.level.blocks if block.reality is None)
        self.assertFalse(self.world.destination_safe(Point3(gate.x, gate.y, 0), Reality.NORMAL))
        self.assertTrue(self.world.destination_safe(Point3(gate.x, gate.y, 0), Reality.BREACH))
        self.assertTrue(self.world.destination_safe(Point3(cover.x, cover.y, cover.height), Reality.NORMAL))

    def test_core_requires_breach_and_stays_collected_after_switching(self):
        self.assertTrue(self.world.core.isStashed())
        self.world.apply(Reality.BREACH, False)
        self.assertFalse(self.world.core.isStashed())
        self.world.apply(Reality.BREACH, True)
        self.assertTrue(self.world.core.isStashed())
        self.world.apply(Reality.NORMAL, True)
        self.world.apply(Reality.BREACH, True)
        self.assertTrue(self.world.core.isStashed())

    def test_shift_destinations_must_stay_inside_the_map(self):
        bounds = self.world.level.bounds
        self.assertFalse(self.world.destination_safe(Point3(bounds.max_x + 1, 0, 5), Reality.BREACH))
        self.assertFalse(self.world.destination_safe(Point3(0, bounds.max_y + 1, 5), Reality.NORMAL))

    def test_scene_dressing_preserves_every_logical_collision_anchor(self):
        for block, node in self.world.blocks:
            with self.subTest(x=block.x, y=block.y):
                self.assertEqual(node.getPos(), Point3(block.x, block.y, 0))
