from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from panda3d.core import Filename, Loader, NodePath, TexturePool

from breach_shift.art.blender_import import import_workshop


class BlenderImportTests(unittest.TestCase):
    def test_compressed_embedded_asset_loads_through_the_runtime_library(self):
        from breach_shift.art import library

        fixture = Path(__file__).resolve().parent / "fixtures/workshop.gltf"
        with TemporaryDirectory() as directory:
            output = Path(directory) / "models"
            result = import_workshop(fixture, output, compress=True)
            self.assertEqual(result[0]["file"], "characters/walker.bam.pz")
            self.assertFalse((output / "characters/walker.bam").exists())
            with patch.object(library, "MODEL_ROOT", output):
                model = library.instantiate("characters/walker.bam")
            self.assertEqual(model.getTag("source"), "blender")
            self.assertGreater(model.findAllTextures().getNumTextures(), 0)
            model.removeNode()

    def test_missing_asset_is_reported_instead_of_replaced_with_primitives(self):
        from breach_shift.art import library

        with TemporaryDirectory() as directory, patch.object(library, "MODEL_ROOT", Path(directory)):
            with self.assertRaisesRegex(FileNotFoundError, "Missing packaged model: characters/walker.bam"):
                library.instantiate("characters/walker.bam")

    def test_import_preserves_pivots_and_embeds_textures_without_needing_the_glb(self):
        original = Path(__file__).resolve().parent / "fixtures/workshop.gltf"
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "portable.gltf"
            copyfile(original, source)
            output = directory / "models"
            result = import_workshop(source, output)
            self.assertEqual([model["kind"] for model in result], ["walker"])
            source.unlink()
            TexturePool.releaseAllTextures()
            node = Loader.getGlobalPtr().loadSync(Filename.fromOsSpecific(str(output / "characters/walker.bam")))
            self.assertIsNotNone(node)
            model = NodePath(node)
            self.assertEqual(model.getTag("source"), "blender")
            for part in ("arm-left", "arm-right", "leg-left", "leg-right"):
                self.assertFalse(model.find("**/" + part).isEmpty())
            textures = model.findAllTextures()
            self.assertGreater(textures.getNumTextures(), 0)
            for texture in textures:
                self.assertTrue(texture.hasRamImage())
            low, high = model.getTightBounds()
            self.assertGreater(high.z - low.z, 1.7)
            self.assertLess(high.z - low.z, 2)

    def test_missing_pivots_cannot_replace_an_existing_character_asset(self):
        scene = NodePath("Scene")
        scene.attachNewNode("HERO_Walker")
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            output = directory / "models"
            (output / "characters").mkdir(parents=True)
            target = output / "characters/walker.bam"
            target.write_bytes(b"existing-asset")
            with patch("gltf.load_model", return_value=scene.node()), self.assertRaises(ValueError):
                import_workshop(directory / "source.glb", output)
            self.assertEqual(target.read_bytes(), b"existing-asset")

    def test_a_later_invalid_character_does_not_replace_an_earlier_valid_character(self):
        import gltf

        fixture = Path(__file__).resolve().parent / "fixtures/workshop.gltf"
        scene = NodePath(gltf.load_model(fixture.as_posix()))
        scene.attachNewNode("HERO_Runner")
        with TemporaryDirectory() as directory:
            output = Path(directory) / "models"
            (output / "characters").mkdir(parents=True)
            target = output / "characters/walker.bam"
            target.write_bytes(b"keep-working-walker")
            with patch("gltf.load_model", return_value=scene.node()), self.assertRaises(ValueError):
                import_workshop(fixture, output)
            self.assertEqual(target.read_bytes(), b"keep-working-walker")
