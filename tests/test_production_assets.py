from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest

from breach_shift.art.glb import inspect_glb
from breach_shift.art.library import MODEL_ROOT, instantiate
from breach_shift.world.environment import production_environment
from breach_shift.world.levels import MapBounds, load_levels


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/models/environments/quarantine_yard.glb"
RUNTIME = MODEL_ROOT / "environments/quarantine_yard.glb"
MODULE = ROOT / "assets/models/props/barrel.glb"


class ProductionAssetTests(unittest.TestCase):
    def test_packaged_courtyard_matches_the_reviewed_source_and_game_budget(self):
        self.assertEqual(sha256(SOURCE.read_bytes()).digest(), sha256(RUNTIME.read_bytes()).digest())
        report = inspect_glb(RUNTIME)
        self.assertLess(report["triangles"], 80000)
        self.assertGreaterEqual(report["textures"], 12)
        self.assertLess(report["bytes"], 30 * 1024 * 1024)

    def test_courtyard_loads_offline_outside_the_checkout_with_embedded_textures(self):
        previous = Path.cwd()
        with TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                model = instantiate("environments/quarantine_yard.glb")
            finally:
                os.chdir(previous)
        self.assertTrue(model.getCollideMask().isZero())
        low, high = model.getTightBounds()
        self.assertAlmostEqual(high.x-low.x, 61.3, delta=.1)
        self.assertGreater(high.y-low.y, 90)
        self.assertLess(high.z-low.z, 5.3)
        for texture in model.findAllTextures():
            self.assertTrue(texture.hasRamImage())
        model.removeNode()

    def test_visual_map_contract_matches_all_live_solid_cover_and_prop_colliders(self):
        level = load_levels()[0]
        self.assertEqual(production_environment(level), "environments/quarantine_yard.glb")
        contract = json.loads(RUNTIME.with_suffix(".json").read_text())
        self.assertEqual(len(contract["blocks"]), sum(b.reality is None for b in level.blocks))
        # A custom map must never accidentally receive the shipped map's visuals.
        custom = replace(level, bounds=MapBounds(-10, 10, -5, 20))
        self.assertIsNone(production_environment(custom))

    def test_every_reusable_module_and_cc0_prop_is_self_contained(self):
        paths = sorted((ROOT / "assets/models/props").glob("*.glb"))
        paths += sorted((ROOT / "assets/models/environments/modules").glob("*.glb"))
        self.assertEqual(len(paths), 11)
        for path in paths:
            with self.subTest(asset=path.name):
                self.assertGreater(inspect_glb(path)["triangles"], 0)

    def test_triangle_budget_is_exclusive(self):
        count = inspect_glb(MODULE)["triangles"]
        with self.assertRaisesRegex(ValueError, "must be below"):
            inspect_glb(MODULE, triangle_limit=count)
        self.assertEqual(inspect_glb(MODULE, triangle_limit=count+1)["triangles"], count)

    def test_phase_barriers_load_at_the_dimensions_used_by_their_colliders(self):
        contract = json.loads(RUNTIME.with_suffix(".json").read_text())
        self.assertEqual(len(contract["phase_blocks"]), 4)
        for entry in contract["phase_blocks"]:
            with self.subTest(asset=entry["file"]):
                relative = "environments/"+entry["file"]
                self.assertGreater(inspect_glb(MODEL_ROOT / relative)["textures"], 0)
                model = instantiate(relative)
                low, high = model.getTightBounds()
                for actual, expected in zip(high-low, entry["geometry"][2:]):
                    self.assertAlmostEqual(actual, expected, delta=.1)
                self.assertTrue(model.getCollideMask().isZero())
                model.removeNode()

    def corrupt_metadata(self, mutate):
        data = MODULE.read_bytes()
        size = struct.unpack_from("<I", data, 12)[0]
        document = json.loads(data[20:20+size])
        mutate(document)
        encoded = json.dumps(document).encode()
        encoded += b" " * (-len(encoded) % 4)
        binary_chunk = data[20+size:]
        return (struct.pack("<4sII", b"glTF", 2, 20+len(encoded)+len(binary_chunk))
                + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded + binary_chunk)

    def test_external_resources_and_private_metadata_are_rejected_before_import(self):
        changes = (
            (lambda doc: doc["buffers"][0].update(uri="https://example.invalid/tracking.bin"), "embed every"),
            (lambda doc: doc["nodes"][0].update(name="C:/Users/private-account/model"), "private filesystem"),
            (lambda doc: doc["asset"].update(extras={"credential": "do-not-distribute"}), "custom metadata"),
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "untrusted.glb"
            for mutate, message in changes:
                path.write_bytes(self.corrupt_metadata(mutate))
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    inspect_glb(path)

    def test_truncated_glb_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "broken.glb"
            path.write_bytes(MODULE.read_bytes()[:-8])
            with self.assertRaisesRegex(ValueError, "header or length"):
                inspect_glb(path)
