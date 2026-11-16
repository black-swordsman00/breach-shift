from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from breach_shift.art.export import export_blender_library


class ArtExportTests(unittest.TestCase):
    def test_incomplete_source_library_cannot_overwrite_live_models(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            source, output = directory / "source", directory / "game"
            (source / "characters").mkdir(parents=True)
            (source / "characters/walker.glb").write_bytes(b"unfinished")
            (output / "characters").mkdir(parents=True)
            live = output / "characters/walker.bam.pz"
            live.write_bytes(b"working-production-model")
            with patch("breach_shift.art.blender_import.import_workshop") as importer:
                with self.assertRaisesRegex(FileNotFoundError, "complete Blender library"):
                    export_blender_library(source, output)
                importer.assert_not_called()
            self.assertEqual(live.read_bytes(), b"working-production-model")
