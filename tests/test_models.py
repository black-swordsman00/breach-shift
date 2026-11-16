import unittest

from panda3d.core import NodePath

from breach_shift.art.characters import make_zombie_model
from breach_shift.art.weapons import make_weapon_model
from breach_shift.combat.catalog import WEAPON_ORDER
from breach_shift.enemies.catalog import ZOMBIE_ORDER, ZOMBIE_SPECS, ZombieKind


class ModelTests(unittest.TestCase):
    def test_shipped_characters_use_blender_art_at_game_scale(self):
        for kind in ZOMBIE_ORDER:
            with self.subTest(kind=kind):
                model = make_zombie_model(kind)
                self.assertEqual(model.getTag("source"), "blender")
                self.assertEqual(model.getTag("source-file"), kind.value + ".glb")
                low, high = model.getTightBounds()
                self.assertAlmostEqual(high.z - low.z, ZOMBIE_SPECS[kind].height, delta=.1)
                self.assertGreater(model.findAllTextures().getNumTextures(), 1)
                model.removeNode()

    def test_every_zombie_has_visible_geometry_and_separate_animation_joints(self):
        for kind in ZOMBIE_ORDER:
            with self.subTest(kind=kind):
                model = make_zombie_model(kind)
                self.assertGreater(model.findAllMatches("**/+GeomNode").getNumPaths(), 0)
                self.assertFalse(model.find("**/arm-left").isEmpty())
                self.assertFalse(model.find("**/leg-right").isEmpty())
                self.assertEqual(model.getTag("zombie-kind"), kind.value)
                model.removeNode()

    def test_runner_is_female_and_animating_one_instance_does_not_change_another(self):
        first = make_zombie_model(ZombieKind.RUNNER)
        second = make_zombie_model(ZombieKind.RUNNER)
        self.assertEqual(first.getTag("design"), "female")
        original_pitch = second.find("**/arm-left").getP()
        first.find("**/arm-left").setP(45)
        self.assertEqual(second.find("**/arm-left").getP(), original_pitch)
        first.removeNode()
        second.removeNode()

    def test_weapon_models_are_distinct_visible_meshes_without_collision_masks(self):
        lengths = []
        parent = NodePath("model-tests")
        for kind in WEAPON_ORDER:
            model = make_weapon_model(kind)
            model.reparentTo(parent)
            self.assertEqual(model.getTag("source"), "blender")
            self.assertGreater(model.findAllTextures().getNumTextures(), 1)
            self.assertGreater(model.findAllMatches("**/+GeomNode").getNumPaths(), 0)
            low, high = model.getTightBounds()
            lengths.append(round(high.y - low.y, 2))
            self.assertTrue(model.getCollideMask().isZero())
        self.assertEqual(len(set(lengths)), 4)
        parent.removeNode()
