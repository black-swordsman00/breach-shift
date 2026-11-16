"""Layered original 2D city/interior scenes with shared licensed texture tiles."""
from math import cos, pi, sin, sqrt
from random import Random

from panda3d.core import (CardMaker, LineSegs, PNMImage, TextNode, Texture,
                         TextureStage, TransparencyAttrib)


PALETTES = {
    "yard": ((.055,.09,.12), (.11,.19,.22), (.32,.81,.76)),
    "tunnel": ((.04,.065,.07), (.12,.17,.16), (.83,.65,.30)),
    "depot": ((.08,.075,.065), (.21,.18,.14), (.96,.59,.26)),
    "drain": ((.035,.075,.08), (.09,.19,.19), (.30,.83,.64)),
    "rooftop": ((.075,.07,.12), (.17,.18,.27), (.57,.70,.99)),
    "security": ((.045,.075,.09), (.13,.20,.22), (.42,.83,.89)),
    "broadcast": ((.075,.065,.10), (.19,.16,.22), (.93,.51,.44)),
    "ward": ((.045,.075,.07), (.15,.23,.20), (.70,.84,.64)),
    "lab": ((.045,.07,.08), (.12,.20,.24), (.32,.88,.91)),
    "core": ((.08,.045,.10), (.19,.11,.22), (.88,.38,.83)),
}


def quad(parent, x, z, width, height, color, *, order=10, texture=None, repeat=None):
    maker = CardMaker("panel")
    maker.setFrame(x, x + width, z, z + height)
    node = parent.attachNewNode(maker.generate())
    node.setColor(*color)
    node.setLightOff(2)
    node.setShaderOff(2)
    node.setDepthTest(False)
    node.setDepthWrite(False)
    node.setBin("fixed", order)
    if len(color) > 3 and color[3] < 1:
        node.setTransparency(TransparencyAttrib.MAlpha)
    if texture is not None:
        node.setTexture(texture, 1)
        if repeat is not None:
            texture.setWrapU(Texture.WMRepeat)
            texture.setWrapV(Texture.WMRepeat)
            node.setTexScale(TextureStage.getDefault(), *repeat)
    return node


def line(parent, points, color, *, width=1.4, order=15):
    path = LineSegs("detail")
    path.setColor(*color)
    path.setThickness(width)
    path.moveTo(points[0][0], 0, points[0][1])
    for x, z in points[1:]:
        path.drawTo(x, 0, z)
    node = parent.attachNewNode(path.create())
    node.setLightOff(2)
    node.setDepthTest(False)
    node.setDepthWrite(False)
    node.setBin("fixed", order)
    return node


def label(parent, text, x, z, scale=.18, color=(.6,.75,.78,1), order=18):
    content = TextNode("sign")
    content.setText(text)
    content.setTextColor(*color)
    node = parent.attachNewNode(content)
    node.setPos(x, 0, z)
    node.setScale(scale)
    node.setLightOff(2)
    node.setDepthTest(False)
    node.setDepthWrite(False)
    node.setBin("fixed", order)
    return node


def glow_texture():
    image = PNMImage(64, 64, 4)
    for y in range(64):
        for x in range(64):
            distance = sqrt(((x-31.5)/31.5)**2 + ((y-31.5)/31.5)**2)
            image.setXelA(x, y, 1, 1, 1, max(0, 1-distance)**2)
    texture = Texture("soft-light")
    texture.load(image)
    return texture


class SideScenery:
    def __init__(self, parent, level, library):
        self.root = parent.attachNewNode("side-view-map")
        self.sky = self.root.attachNewNode("sky")
        self.far = self.root.attachNewNode("far-silhouette")
        self.mid = self.root.attachNewNode("midground")
        self.architecture = self.root.attachNewNode("platforms")
        self.props = self.root.attachNewNode("background-props")
        self.glow = glow_texture()
        dark, wall, accent = PALETTES[level.theme]
        self.accent = accent
        self.level = level
        self.library = library
        self._background(dark, wall, accent)
        self._platforms(wall, accent)
        for name, x, z, scale in level.decor:
            sprite = library.sprite(self.props, name, order=17)
            sprite.node.setPos(x, 0, z)
            sprite.node.setScale(scale)
            sprite.node.setColorScale(.58,.69,.72,1)
            if name == "lamp":
                quad(self.props, x-2, 1.2, 4, 4.2, (*accent,.17), order=19, texture=self.glow)
                quad(self.props, x-2.4, -.15, 4.8, .35, (*accent,.2), order=21, texture=self.glow)
        self.gates = {}
        for name, gate, color in (("Normal", level.normal_gate, (.22,.85,.83)),
                                   ("Breach", level.breach_gate, (.86,.34,.95))):
            node = self.root.attachNewNode(name + "-gate")
            quad(node, gate.x, gate.z, gate.width, gate.height, (*color,.27), order=23)
            for edge in (gate.x, gate.right-.055):
                quad(node, edge, gate.z, .055, gate.height, (*color,.95), order=24)
            for z in range(0, int(gate.height), 1):
                line(node, [(gate.x,z), (gate.right,z+.6)], (*color,.65), width=1, order=25)
            label(node, name.upper() + " GATE", gate.x-1.1, 3.5, .16, (*color,1), 25)
            self.gates[name] = node
        self.core = self.root.attachNewNode("rift-core")
        self.core.setPos(level.core[0], 0, level.core[1])
        quad(self.core, -1.2, -1.2, 2.4, 2.4, (.72,.22,1,.6), order=26, texture=self.glow)
        line(self.core, [(0,-.48),(.26,0),(0,.48),(-.26,0),(0,-.48)], (.85,.63,1,1), width=3, order=27)
        line(self.core, [(-.26,0),(.26,0),(0,.48),(0,-.48)], (.86,.45,1,1), order=27)
        self.exit = self.root.attachNewNode("extraction-door")
        x, z = level.exit
        quad(self.exit, x-1, z, 2, 3.2, (.035,.075,.075,1), order=22)
        line(self.exit, [(x-1,z),(x-1,z+3.2),(x+1,z+3.2),(x+1,z)], (.4,.7,.62,1), width=3, order=24)
        label(self.exit, "EXTRACTION", x-.85, z+3.45, .19, (.55,.9,.78,1), 24)
        for root in (self.far, self.mid, self.architecture):
            root.flattenStrong()

    def _background(self, dark, wall, accent):
        level = self.level
        gradient = PNMImage(2, 128, 3)
        for y in range(128):
            t = y/127
            color = tuple(value * (.42 + t*.95) for value in dark)
            for x in range(2):
                gradient.setXel(x, y, *color)
        sky_texture = Texture("night-gradient")
        sky_texture.load(gradient)
        quad(self.sky, -150, -12, level.width+300, 50, (1,1,1,1), order=0, texture=sky_texture)
        rng = Random(level.number)
        for x in range(-30, int(level.width)+90, 6):
            height = rng.uniform(4, 13)
            color = tuple(value*.75 for value in wall)
            quad(self.far, x, 1, 5.5, height, (*color,1), order=2)
            quad(self.far, x+1, 1+height, 2, .5, (*color,1), order=2)
            if rng.random() < .35:
                line(self.far, [(x+2,1+height),(x+2,4+height)], (*color,1), order=3)
            for wx in range(1, 5):
                for wz in range(3, int(height), 2):
                    if rng.random() < .32:
                        quad(self.far, x+wx, wz, .23, .45, (.34,.35,.25,.6), order=3)
        interior = level.theme in ("tunnel", "security", "ward", "lab", "core")
        facade_texture = self.library.texture("tiles/concrete.png" if interior else "tiles/brick.png")
        for x in range(-12, int(level.width)+25, 12):
            height = 13 if interior else rng.uniform(5, 9)
            quad(self.mid, x, 0, 11.8, height, (*wall,1), order=4,
                 texture=facade_texture, repeat=(3,height/3))
            quad(self.mid, x, height, 11.8, .2, (*wall,1), order=5)
            for wx in (1, 4.5, 8):
                for wz in ((2.5, 6.0) if height > 8 else (2.5,)):
                    quad(self.mid, x+wx, wz, 2.2, 1.6, (.08,.14,.16,1), order=5)
                    quad(self.mid, x+wx+.08, wz+.08, 2.04, 1.44, (*accent,.14), order=6)
                    for division in (0,.75,1.5):
                        quad(self.mid, x+wx+division, wz, .035, 1.6, (*wall,1), order=7)
                    quad(self.mid, x+wx, wz+.85, 2.2, .04, (*wall,1), order=7)
            line(self.mid, [(x+.3,0),(x+.3,height-.2),(x+3,height-.2)], (.23,.29,.28,1), width=3, order=8)
            for z in (.8,1.6,2.4,3.2,4):
                line(self.mid, [(x+.15,z),(x+.5,z)], (.3,.35,.33,1), width=2, order=8)
            if interior:
                quad(self.mid, x+5, 7.9, 2.5, .075, (*accent,.85), order=9)
                quad(self.mid, x+3.5, 5.8, 6, 4, (*accent,.10), order=9, texture=self.glow)
        if not interior:
            for x in range(-5, int(level.width)+12, 2):
                line(self.mid, [(x,0),(x,2.5),(x+.25,2.8)], (.22,.29,.29,.8), order=12)
                line(self.mid, [(x-1,2.6),(x+1,2.6)], (.22,.29,.29,.8), order=12)
            for x in range(-5, int(level.width)+12):
                line(self.mid, [(x,0),(x+2,2.5)], (.16,.23,.23,.6), width=.7, order=11)
                line(self.mid, [(x,2.5),(x+2,0)], (.16,.23,.23,.6), width=.7, order=11)
            line(self.mid, [(-10,7),(12,6.2),(38,7.2),(70,6.4),(110,7.4),(level.width+10,6)], (.04,.075,.08,1), width=2, order=13)
        quad(self.mid, 4, 4.4, 6.3, 1.25, (.025,.055,.065,1), order=14)
        label(self.mid, f"SECTOR {level.number:02}", 4.3, 5.05, .36, (*accent,1), 15)
        label(self.mid, level.name.upper(), 4.3, 4.65, .17, (.52,.65,.66,1), 15)
        quad(self.mid, 4.25, 4.5, 5.8, .035, (*accent,.7), order=15)

    def _platforms(self, wall, accent):
        concrete = self.library.texture("tiles/concrete.png")
        metal = self.library.texture("tiles/metal.png")
        asphalt = self.library.texture("tiles/asphalt.png")
        for solid in self.level.platforms:
            tile = metal if solid.one_way else concrete
            quad(self.architecture, solid.x, solid.z, solid.width, solid.height,
                 (.50,.58,.59,1), order=20, texture=tile,
                 repeat=(max(1,solid.width/2), max(.2,solid.height/2)))
            quad(self.architecture, solid.x, solid.top-.09, solid.width, .09,
                 (.55,.68,.67,1), order=21)
            if solid.top == 0:
                quad(self.architecture, solid.x, -.22, solid.width, .13,
                     (.55,.62,.63,1), order=21, texture=asphalt, repeat=(solid.width/3,.15))
            quad(self.architecture, solid.x, solid.z, solid.width, .08,
                 (.035,.055,.06,1), order=21)
            if solid.z >= 0:
                for x in range(int(solid.x), int(solid.right)):
                    line(self.architecture, [(x,solid.top-.25),(x+.2,solid.top-.09)],
                         (.78,.61,.27,1), width=3, order=22)
                if solid.one_way:
                    for x in (solid.x+.4,solid.right-.4):
                        line(self.architecture, [(x,solid.z),(x,solid.z-.7),(x+.7,solid.z)],
                             (.27,.35,.35,1), width=3, order=21)
        # A decorative continuation beyond the boundary frames the first screen.
        quad(self.architecture, -10, -3, 10, 3, (.35,.42,.43,1), order=20,
             texture=concrete, repeat=(5,1.5))

    def update(self, session, camera_x):
        self.far.setX(camera_x*.18)
        self.mid.setX(camera_x*.035)
        breached = session.reality.state.value == "Breach"
        self.root.setColorScale(.84 if breached else 1, .65 if breached else 1, 1, 1)
        for name, node in self.gates.items():
            node.setColorScale(1,1,1, 1 if name == session.reality.state.value else .09)
            node.setTransparency(TransparencyAttrib.MAlpha)
        self.core.hide() if session.progress.core_collected or not breached or session.training else self.core.show()
        self.core.setZ(self.level.core[1]+sin(session.now*2)*.09)
        ready = session.progress.core_collected and session.alive == 0 and not breached
        self.exit.setColorScale(.5,1,.8,1) if ready else self.exit.setColorScale(.65,.7,.75,1)
        if session.training:
            self.exit.hide()

    def destroy(self):
        self.root.removeNode()
