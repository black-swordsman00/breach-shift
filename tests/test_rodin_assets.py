from hashlib import sha256
import json
from pathlib import Path
import unittest

from panda3d.core import GeomVertexReader, Thread

from breach_shift.art.characters import make_zombie_model
from breach_shift.art.glb import inspect_glb
from breach_shift.art.library import MODEL_ROOT
from breach_shift.art.weapons import make_weapon_model, muzzle_position
from breach_shift.combat.catalog import WeaponKind
from breach_shift.enemies.catalog import ZombieKind


ROOT=Path(__file__).resolve().parents[1]


def skinned_vertices(actor):
    actor.update(force=True)
    result=[]
    for node in actor.findAllMatches('**/+GeomNode'):
        for index in range(node.node().getNumGeoms()):
            data=node.node().getGeom(index).getVertexData().animateVertices(True,Thread.getCurrentThread())
            reader=GeomVertexReader(data,'vertex')
            while not reader.isAtEnd():
                result.append(tuple(reader.getData3f()))
    return result


class RodinAssetTests(unittest.TestCase):
    def test_removing_a_skinned_model_releases_its_animation_parts(self):
        model=make_zombie_model(ZombieKind.WALKER)
        self.assertTrue(model.getPartNames())
        model.removeNode()
        self.assertTrue(model.isEmpty())
        self.assertEqual(model.getPartNames(),[])

    def test_live_generated_assets_match_sources_and_enforce_strict_budgets(self):
        for folder,name,limit in (('weapons','rifle',5000),('characters','walker',12000)):
            with self.subTest(model=name):
                source=ROOT/'assets/models'/folder/(name+'.glb')
                runtime=MODEL_ROOT/folder/(name+'.glb')
                self.assertEqual(sha256(source.read_bytes()).digest(),sha256(runtime.read_bytes()).digest())
                report=inspect_glb(runtime,triangle_limit=limit)
                self.assertGreaterEqual(report['textures'],3)
                self.assertFalse(runtime.with_suffix('.bam.pz').exists())
                metadata=json.loads(runtime.with_suffix('.json').read_text())
                self.assertEqual(metadata['provider'],'Hyper3D Rodin')
                self.assertEqual(metadata['triangles'],report['triangles'])
                self.assertTrue(metadata['uv_layers_preserved'])

    def test_rifle_uses_its_measured_muzzle_and_correct_metre_length(self):
        model=make_weapon_model(WeaponKind.RIFLE)
        try:
            self.assertEqual(model.getTag('provider'),'Hyper3D Rodin')
            low,high=model.getTightBounds()
            self.assertAlmostEqual(high.y-low.y,.92,delta=.005)
            muzzle=muzzle_position(WeaponKind.RIFLE)
            self.assertAlmostEqual(muzzle[1],high.y,delta=.002)
            self.assertGreaterEqual(muzzle[2],low.z)
            self.assertLessEqual(muzzle[2],high.z)
        finally:
            model.removeNode()

    def test_walker_joint_controls_deform_skin_without_changing_another_instance(self):
        first=make_zombie_model(ZombieKind.WALKER)
        second=make_zombie_model(ZombieKind.WALKER)
        try:
            self.assertEqual(first.getTag('animation'),'skinned-humanoid')
            self.assertNotEqual(first.getPartBundle('modelRoot'),second.getPartBundle('modelRoot'))
            before=skinned_vertices(first)
            other_before=skinned_vertices(second)
            joint=first.find('**/arm-left')
            joint.setP(joint.getP()+30)
            after=skinned_vertices(first)
            self.assertGreater(sum(old!=new for old,new in zip(before,after)),100)
            self.assertEqual(other_before,skinned_vertices(second))
        finally:
            first.cleanup();second.cleanup()
