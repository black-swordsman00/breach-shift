import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from level_data import MapBounds, load_levels


class LevelDataTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "levels" / "01_quarantine_yard.json"
        self.data = json.loads(path.read_text(encoding="utf-8"))

    def load_data(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "01_test.json"
            path.write_text(json.dumps(self.data), encoding="utf-8")
            return load_levels(Path(directory))[0]

    def test_custom_bounds_and_start_control_the_full_width_gates(self):
        self.data["bounds"] = [-30, 30, -15, 75]
        self.data["player_spawn"] = [20, -10]
        level = self.load_data()
        self.assertEqual((level.bounds.width, level.bounds.depth), (60, 90))
        self.assertEqual(level.player_spawn, (20, -10))
        self.assertEqual(level.blocks[0].width, 60)
        self.assertEqual(level.blocks[1].width, 60)

    def test_legacy_levels_keep_the_training_sized_defaults(self):
        self.data.pop("bounds", None)
        self.data.pop("player_spawn", None)
        self.data.update(normal_gate_y=8, breach_gate_y=14, core=[0, 11], exit=[0, 18],
                         spawns=[["walker", -7, 4], ["walker", 3, 11]])
        self.assertEqual(self.load_data().bounds, MapBounds())
        self.assertEqual(self.load_data().player_spawn, (0, -2))

    def test_invalid_bounds_are_rejected(self):
        for values in ((0, 0, -5, 20), (5, -5, -5, 20), (-10, 10, 5, 5),
                       (float("nan"), 10, -5, 20), (-10, float("inf"), -5, 20)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                MapBounds(*values)

    def test_spawns_and_objectives_cannot_be_outside_the_floor(self):
        for key in ("player_spawn", "core", "exit"):
            with self.subTest(key=key):
                old_value = self.data.get(key)
                self.data[key] = [1000, 1000]
                with self.assertRaises(ValueError):
                    self.load_data()
                if old_value is None:
                    self.data.pop(key)
                else:
                    self.data[key] = old_value
