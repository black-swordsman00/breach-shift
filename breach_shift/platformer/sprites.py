"""Load only packaged PNG art; every actor is a flat animated card."""
from importlib.resources import files
import json

from panda3d.core import CardMaker, Filename, Texture, TextureStage, TransparencyAttrib


class SpriteLibrary:
    def __init__(self, loader):
        self.loader = loader
        self.root = files("breach_shift").joinpath("data", "sprites")
        self.manifest = json.loads(self.root.joinpath("manifest.json").read_text(encoding="utf-8"))
        self.textures = {}

    def texture(self, filename):
        if filename not in self.textures:
            texture = self.loader.loadTexture(Filename.fromOsSpecific(str(self.root.joinpath(filename))))
            if texture is None:
                raise RuntimeError("Missing 2D image: " + filename)
            texture.setMinfilter(Texture.FTLinear)
            texture.setMagfilter(Texture.FTLinear)
            texture.setWrapU(Texture.WMClamp)
            texture.setWrapV(Texture.WMClamp)
            self.textures[filename] = texture
        return self.textures[filename]

    def sprite(self, parent, name, *, order=30):
        return Sprite(parent, self.manifest["sprites"][name], self, order)


class Sprite:
    def __init__(self, parent, entry, library, order):
        self.entry = entry
        self.node = parent.attachNewNode(entry["file"])
        maker = CardMaker(entry["file"])
        maker.setFrame(*entry["frame"])
        self.card = self.node.attachNewNode(maker.generate())
        self.card.setTexture(library.texture(entry["file"]), 1)
        self.card.setTransparency(TransparencyAttrib.MAlpha)
        self.card.setTwoSided(True)
        self.card.setDepthTest(False)
        self.card.setDepthWrite(False)
        self.card.setLightOff(2)
        self.card.setShaderOff(2)
        self.card.setBin("fixed", order)
        self.card.setTexScale(TextureStage.getDefault(), 1 / entry["columns"], 1 / entry["rows"])
        self.state = None
        self.set_frame("idle", 0)

    def set_frame(self, state, frame):
        row = self.entry["states"].get(state, 0)
        frame = int(frame) % self.entry["columns"]
        key = row, frame
        if key != self.state:
            self.card.setTexOffset(TextureStage.getDefault(), frame / self.entry["columns"],
                                   1 - (row + 1) / self.entry["rows"])
            self.state = key
