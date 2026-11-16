import unittest

from panda3d.core import CardMaker, PNMImage, loadPrcFileData

from breach_shift.art.weapons import WeaponView
from breach_shift.combat.catalog import WeaponKind


class WeaponRenderTests(unittest.TestCase):
    def test_weapon_occludes_its_back_faces_while_overlaying_a_closer_world_wall(self):
        from direct.showbase.ShowBase import ShowBase

        loadPrcFileData('weapon-depth-test','audio-library-name null\nwin-size 64 64\nsync-video false')
        base=ShowBase(windowType='offscreen')
        try:
            base.disableMouse()
            base.camLens.setNearFar(.1,10)
            view=WeaponView(base.camera,WeaponKind.RIFLE)
            for child in list(view.root.getChildren()):
                child.removeNode()
            view.root.setPos(0,0,0);view.root.setHpr(0,0,0);view.root.setScale(1)
            view.root.setShaderOff(10);view.root.setLightOff(10);view.root.setTextureOff(10)

            def card(parent,name,y,color,sort=None):
                maker=CardMaker(name);maker.setFrame(-2,2,-2,2)
                node=parent.attachNewNode(maker.generate())
                node.setY(y);node.setColor(*color,1)
                node.setShaderOff(10);node.setLightOff(10)
                if sort is not None:node.setBin('fixed',sort)
                return node

            card(base.render,'closer-world-wall',.3,(0,0,1))
            card(view.root,'front-weapon-surface',.6,(1,0,0),40)
            card(view.root,'back-weapon-surface-drawn-last',.9,(0,1,0),41)
            for _ in range(3):base.graphicsEngine.renderFrame()
            pixels=PNMImage()
            self.assertTrue(base.win.getScreenshot(pixels))
            color=pixels.getXel(pixels.getXSize()//2,pixels.getYSize()//2)
            self.assertGreater(color.x,.9)
            self.assertLess(color.y,.1)
            self.assertLess(color.z,.1)
        finally:
            base.destroy()
