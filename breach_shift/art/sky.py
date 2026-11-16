"""The courtyard's licensed HDRI, displayed behind the playable architecture."""
from pathlib import Path

from panda3d.core import BitMask32, Filename, TexturePool

from breach_shift.art.primitives import sphere


class CourtyardSky:
    def __init__(self, render):
        path=Path(__file__).resolve().parents[1]/'data/lighting/courtyard-sky.png'
        texture=TexturePool.loadTexture(Filename.fromOsSpecific(str(path)))
        if texture is None:
            raise FileNotFoundError('The packaged courtyard sky is missing')
        self.node=sphere(64,32).copyTo(render)
        self.node.setName('poly-haven-courtyard-sky')
        self.node.setScale(350)
        self.node.setTwoSided(True)
        self.node.setLightOff(3)
        self.node.setShaderOff(3)
        self.node.setFogOff(3)
        self.node.setTexture(texture,3)
        self.node.setBin('background',0)
        self.node.setDepthWrite(False)
        self.node.hide(BitMask32.bit(6))

    def update(self, position, breach=False):
        self.node.setPos(position)
        self.node.setColorScale((.22,.18,.32,1) if breach else (.28,.34,.40,1))

    def destroy(self):
        self.node.removeNode()
