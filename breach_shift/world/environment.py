"""Textured scene dressing fitted to existing level collision dimensions."""

from math import cos, pi, sin
import json

from panda3d.core import BitMask32, Fog, TextureStage

from breach_shift.art.primitives import box, cylinder, flatten_local, part, rod, sphere
from breach_shift.art import library


STONE = (.39, .43, .46, 1)
SNOW = (.77, .82, .87, 1)
PALETTES = {
    1: ((.46, .51, .56, 1), (.035, .055, .09)),
    2: ((.26, .30, .28, 1), (.025, .04, .035)),
    3: ((.33, .29, .24, 1), (.045, .04, .035)),
    4: ((.24, .29, .23, 1), (.025, .045, .035)),
    5: ((.32, .34, .36, 1), (.045, .055, .075)),
    6: ((.33, .35, .28, 1), (.045, .05, .04)),
    7: ((.29, .28, .30, 1), (.035, .035, .05)),
    8: ((.48, .52, .44, 1), (.035, .045, .04)),
    9: ((.43, .50, .48, 1), (.025, .045, .05)),
    10: ((.25, .24, .29, 1), (.035, .02, .045)),
}


def production_environment(level):
    if level.number != 1:
        return None
    relative = "environments/quarantine_yard.glb"
    path = library.MODEL_ROOT / relative
    if not path.is_file():
        return None
    contract = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    bounds = level.bounds
    expected_bounds = [bounds.min_x, bounds.max_x, bounds.min_y, bounds.max_y]
    blocks = [[b.x, b.y, b.width, b.depth, b.height] for b in level.blocks if b.reality is None]
    if contract["bounds"] != expected_bounds or contract["blocks"] != blocks:
        return None
    return relative


def dress_block(node, block, number, *, production=False):
    if production and block.reality is None:
        return
    if production:
        metadata = library.MODEL_ROOT / "environments/quarantine_yard.json"
        contract = json.loads(metadata.read_text(encoding="utf-8"))
        geometry = [block.x, block.y, block.width, block.depth, block.height]
        for entry in contract["phase_blocks"]:
            if entry["geometry"] == geometry and entry["reality"] == block.reality.value:
                model = library.instantiate("environments/" + entry["file"])
                model.reparentTo(node)
                model.setColorScale((.82, 1, .95, 1) if block.reality.value == "Normal" else (1, .62, .9, 1))
                return
    w, d, h = block.width, block.depth, block.height
    if block.reality is not None:
        color = (.22, .48, .52, 1) if block.reality.value == "Normal" else (.48, .15, .65, 1)
        part(node, "phase-barrier", box(), (0, 0, h / 2), (w, d, h), color, "metal")
        for index in range(max(1, int(w / 2))):
            x = -w / 2 + 1 + index * 2
            rod(node, "barrier-conduit", (x, -d / 2 - .015, .05), (x, -d / 2 - .015, h - .05),
                .035, (.55, .75, .78, 1) if block.reality.value == "Normal" else (.7, .25, 1, 1), "metal")
    else:
        stone = number == 1
        color = STONE if stone else PALETTES[number][0]
        wall = part(node, "stone-cover" if stone else "industrial-cover", box(), (0, 0, h / 2),
                    (w, d, h), color, "stone" if stone else "metal")
        wall.setTexScale(TextureStage.getDefault(), max(1, w / 2), max(1, h))
        if stone:
            part(node, "snow-cap", box(), (0, 0, h + .025), (w + .06, d + .06, .05), SNOW, "stone")
        elif max(w, d) < 15:
            for z in (.12, max(.2, h - .12)):
                part(node, "reinforced-rim", box(), (0, 0, z), (w + .02, d + .02, .08), (.13, .15, .15, 1), "metal")
    flatten_local(node)
    node.setCollideMask(BitMask32.allOff())


def _tower(parent, x, y, radius=3.4, height=12, clock=False):
    tower = parent.attachNewNode("fortress-tower")
    tower.setPos(x, y, 0)
    wall = part(tower, "masonry-tower", cylinder(1, 24), (0, 0, 0), (radius, radius, height), STONE, "stone")
    wall.setTexScale(TextureStage.getDefault(), 8, height / 2)
    part(tower, "tower-roof", cylinder(0, 24), (0, 0, height), (radius + .5, radius + .5, 4), (.25, .29, .33, 1), "stone")
    for index in range(10):
        angle = index * 2 * pi / 10
        part(tower, "battlement", box(), (cos(angle) * radius, sin(angle) * radius, height - .1),
             (.65, .65, .65), SNOW, "stone")
    for side in (-1, 1):
        window = part(tower, "window-glow", box(), (side * radius * .45, -radius * .9, height * .45),
                      (.45, .05, 1.1), (.74, .45, .18, 1), "metal")
        window.setLightOff(2)
    if clock:
        z, front = height * .73, -radius - .05
        rod(tower, "clock-face", (0, front, z), (0, front - .09, z), 1.15, (.67, .67, .54, 1), "stone", top=1, segments=32)
        for index in range(12):
            angle = index * pi / 6
            part(tower, "clock-marker", sphere(8, 4), (sin(angle), front - .11, z + cos(angle)), (.045, .025, .06), (.09, .09, .08, 1), "metal")
        rod(tower, "clock-hour", (0, front - .13, z), (-.43, front - .13, z + .31), .045, (.08, .08, .07, 1), "metal")
        rod(tower, "clock-minute", (0, front - .14, z), (.17, front - .14, z + .84), .032, (.08, .08, .07, 1), "metal")
    flatten_local(tower)
    tower.setCollideMask(BitMask32.allOff())


def build_environment(parent, level):
    root = parent.attachNewNode("environment-art")
    asset = production_environment(level)
    if asset:
        library.instantiate(asset).reparentTo(root)
        root.setTag("production-environment", "polyhaven+polypizza")
        return root, PALETTES[level.number][1]
    bounds = level.bounds
    ground_color, background = PALETTES[level.number]
    floor = part(root, "textured-ground", box(), ((bounds.min_x + bounds.max_x) / 2,
                 (bounds.min_y + bounds.max_y) / 2, -.018), (bounds.width, bounds.depth, .04),
                 ground_color, "stone")
    floor.setTexScale(TextureStage.getDefault(), bounds.width / 3, bounds.depth / 3)
    if level.number == 1:
        for x in (bounds.min_x - 3, bounds.max_x + 3):
            for y in (bounds.min_y + 2, bounds.max_y - 2):
                _tower(root, x, y)
        _tower(root, 7, bounds.max_y + 4.5, 4.2, 16, True)
        for side in (-1, 1):
            x = bounds.min_x + .5 if side < 0 else bounds.max_x - .5
            for index in range(int(bounds.depth / 3)):
                part(root, "snowy-crenellation", box(), (x, bounds.min_y + 1 + index * 3, 4.6),
                     (1, 1.4, .65), SNOW, "stone")
        moon = part(root, "moon", sphere(20, 12), (-35, bounds.max_y + 50, 35), (4, 4, 4), (.72, .79, .9, 1), "stone")
        moon.setLightOff(2)
    else:
        for side in (-1, 1):
            x = bounds.min_x - .4 if side < 0 else bounds.max_x + .4
            for index in range(5):
                y = bounds.min_y + 8 + index * bounds.depth / 5
                rod(root, "service-pipe", (x, y, 0), (x, y, 7), .18, (.22, .25, .23, 1), "metal", top=1)
                lamp = part(root, "utility-light", box(), (x - side * .5, y, 4), (.5, .35, .12),
                            (.65, .75, .61, 1), "metal")
                lamp.setLightOff(2)
    return root, background


def apply_atmosphere(render, breach, number):
    background = PALETTES[number][1]
    fog = Fog("breach-atmosphere" if breach else "environment-atmosphere")
    color = (.13, .09, .18) if breach else ((.24,.29,.32) if number==1 else background)
    from breach_shift.art.color import atmosphere_input
    fog.setColor(*atmosphere_input(color))
    fog.setExpDensity(.0035 if number == 1 else .008)
    render.setFog(fog)
