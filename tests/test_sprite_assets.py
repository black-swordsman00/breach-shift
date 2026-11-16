from importlib.resources import files
import hashlib
import json
import unittest

from panda3d.core import Filename, PNMImage

from breach_shift.combat.catalog import WEAPON_ORDER
from breach_shift.enemies.catalog import ZOMBIE_ORDER


class SpriteAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = files("breach_shift").joinpath("data","sprites")
        cls.manifest = json.loads(cls.root.joinpath("manifest.json").read_text())

    def image(self, entry):
        image = PNMImage()
        self.assertTrue(image.read(Filename.fromOsSpecific(str(self.root.joinpath(entry["file"])))))
        return image

    def test_only_required_art_is_present_and_every_asset_has_a_consumer(self):
        expected = {kind.value for kind in ZOMBIE_ORDER} | {kind.value for kind in WEAPON_ORDER}
        expected |= {"player","barricade","car","crate","barrel","lamp","debris"}
        self.assertEqual(set(self.manifest["sprites"]),expected)
        self.assertEqual({path.name for path in self.root.iterdir() if path.name.endswith(".png")},
                         {name+".png" for name in expected})

    def test_every_atlas_is_nonempty_transparent_and_matches_its_digest(self):
        for name,entry in self.manifest["sprites"].items():
            with self.subTest(sprite=name):
                raw = self.root.joinpath(entry["file"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),entry["sha256"])
                image = self.image(entry)
                self.assertTrue(image.hasAlpha())
                self.assertEqual((image.getXSize(),image.getYSize()),(entry["width"],entry["height"]))
                self.assertEqual(image.getAlpha(0,0),0)
                alpha = [image.getAlpha(x,y) for y in range(0,image.getYSize(),12)
                         for x in range(0,image.getXSize(),12)]
                self.assertGreater(max(alpha),.9)
                self.assertGreater(sum(alpha),1)
                self.assertLess(sum(alpha),len(alpha)*.8)

    def test_characters_have_distinct_walk_attack_and_death_frames(self):
        for kind in ZOMBIE_ORDER:
            entry = self.manifest["sprites"][kind.value]
            image = self.image(entry)
            self.assertEqual(set(entry["states"]),{"idle","walk","attack","death"})
            self.assertEqual((entry["columns"],entry["rows"]),(8,4))
            def sample(frame,row):
                return tuple(tuple(image.getXelA(x+frame*256,y+row*256))
                             for y in range(32,256,4) for x in range(48,208,4))
            self.assertNotEqual(sample(0,0),sample(2,0))
            self.assertNotEqual(sample(0,3),sample(7,3))

    def test_player_has_real_reload_crouch_and_jump_poses(self):
        entry = self.manifest["sprites"]["player"]
        self.assertEqual(set(entry["states"]),{"idle","walk","reload","death","crouch","jump"})
        self.assertEqual(entry["rows"],6)

    def test_four_small_tiles_and_provenance_ship_with_the_game(self):
        for name in ("asphalt","concrete","brick","metal"):
            image = PNMImage()
            self.assertTrue(image.read(Filename.fromOsSpecific(str(self.root.joinpath("tiles",name+".png")))))
            self.assertEqual((image.getXSize(),image.getYSize()),(256,256))
        credits = files("breach_shift").joinpath("data","credits","sprites.md").read_text()
        self.assertIn("Warden",credits)
        self.assertIn("No CC0 claim",credits)


if __name__=="__main__":
    unittest.main()
