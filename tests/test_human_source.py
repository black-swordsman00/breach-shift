from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.blender.human_source import apply_targets, group_center, read_obj


SOURCE = Path(__file__).resolve().parents[1] / "assets/source/makehuman"


class HumanSourceTests(unittest.TestCase):
    def test_body_is_separate_from_clothing_and_joint_helpers(self):
        vertices, uv, groups = read_obj(SOURCE / "base.obj")
        self.assertEqual(len(vertices), 19158)
        self.assertGreater(len(groups["body"]), 10000)
        self.assertIn("helper-tights", groups)
        for faces in groups.values():
            for indices, texcoords in faces:
                self.assertEqual(len(indices), len(texcoords))
                self.assertTrue(all(0 <= i < len(vertices) for i in indices))
                self.assertTrue(all(-1 <= i < len(uv) for i in texcoords))
        left = group_center(vertices, groups["joint-l-shoulder"])
        right = group_center(vertices, groups["joint-r-shoulder"])
        self.assertAlmostEqual(left[0], -right[0], places=3)

    def test_targets_change_joint_helpers_and_do_not_mutate_the_base(self):
        vertices, _, groups = read_obj(SOURCE / "base.obj")
        original = group_center(vertices, groups["joint-head"])
        changed = apply_targets(vertices, [(SOURCE / "caucasian-male-old.target", 1)])
        self.assertNotEqual(original, group_center(changed, groups["joint-head"]))
        self.assertEqual(original, group_center(vertices, groups["joint-head"]))

    def test_wrong_topology_target_is_rejected(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "bad.target"
            target.write_text("# wrong mesh\n9 1 2 3\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside the hm08 mesh"):
                apply_targets([(0, 0, 0)], [(target, 1)])
