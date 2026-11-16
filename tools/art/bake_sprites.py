"""Bake shipped 3D art from Git history into offline side-view PNG atlases.

Only this optional developer tool needs panda3d-gltf and simplepbr. The game
loads flat PNG cards and has no model loader, PBR pipeline or network client.
The immutable source revision keeps retired 3D files out of the working tree.
"""
import argparse
import hashlib
import json
from math import pi, sin
from pathlib import Path
import struct
import subprocess

from panda3d.core import (AmbientLight, DirectionalLight, Filename, NodePath,
                         OrthographicLens, PNMImage, StringStream, loadPrcFileData)

SOURCE_REVISION = "d74159abc1ffb763524c9697d492d021a1d4f785"
ROOT = Path(__file__).resolve().parents[2]
CELL = 256


def source_file(relative, scratch):
    destination = scratch / relative
    if not destination.is_file():
        raw = subprocess.check_output(["git", "show", SOURCE_REVISION + ":" + relative], cwd=ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    return destination


def read_glb(path):
    raw = path.read_bytes()
    length = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20+length])
    binary = raw[28+length:]
    return document, binary


def pose(actor, state, frame, *, player=False):
    phase = frame / 8 * 2 * pi
    actor.setPos(0, 0, 0)
    actor.setHpr(-90, 0, 0)
    joints = actor._sprite_joints
    for name, (node, rest) in joints.items():
        node.setHpr(rest)

    def joint(name, pitch=0, roll=0, heading=0):
        if name in joints:
            node, rest = joints[name]
            node.setHpr(rest.x + heading, rest.y + pitch, rest.z + roll)

    moving = state in ("walk", "crouch")
    wave = sin(phase) if moving else 0
    breath = sin(phase) * .7
    joint("spine", 2 + breath)
    joint("head", -2 - breath)
    if moving:
        actor.setZ(abs(sin(phase)) * .018)
    for index, side in enumerate(("left", "right")):
        stride = wave * (-1 if index else 1)
        joint("leg-" + side, stride * 25)
        joint("shin-" + side, -max(0, -stride) * 38)
        joint("foot-" + side, max(0, -stride) * 17 - stride * 12)
        joint("arm-" + side, -76 if player else -12 - stride * 18)
        joint("forearm-" + side, -12 if player else -14 - max(0, stride) * 15)
    if state == "attack":
        swing = sin(frame / 7 * pi)
        joint("spine", 8 * swing)
        for side in ("left", "right"):
            joint("arm-" + side, -25 - 95 * swing)
            joint("forearm-" + side, -16 - 20 * swing)
    if state == "reload":
        reach = sin(frame / 7 * pi)
        joint("arm-left", -76 + 55 * reach)
        joint("forearm-left", -12 - 60 * reach)
        joint("spine", 8 * reach)
    if state == "crouch":
        actor.setZ(-.5)
        joint("hips", 12)
        joint("spine", -18)
        for index, side in enumerate(("left", "right")):
            joint("leg-" + side, 55 + wave * (12 if index else -12))
            joint("shin-" + side, -105)
            joint("foot-" + side, 50)
    if state == "jump":
        for side in ("left", "right"):
            joint("leg-" + side, -25)
            joint("shin-" + side, 45)
    if state == "death":
        t = frame / 7
        actor.setP(86 * t)
        actor.setZ(actor._death_lift * t)
        for side in ("left", "right"):
            joint("arm-" + side, -25 * t)
            joint("leg-" + side, 15 * t)


class Baker:
    def __init__(self, output):
        loadPrcFileData("sprite-baker", "window-type offscreen\nwin-size 256 256\nframebuffer-alpha true\naudio-library-name null\nsync-video false\ntextures-power-2 none")
        from direct.showbase.ShowBase import ShowBase
        import simplepbr
        self.game = ShowBase(windowType="offscreen")
        self.game.disableMouse()
        self.game.setBackgroundColor(0, 0, 0, 0)
        simplepbr.init(enable_shadows=False, use_normal_maps=True, msaa_samples=4,
                       exposure=.5, use_hardware_skinning=False)
        ambient = AmbientLight("sprite-fill")
        ambient.setColor((.9, .95, 1, 1))
        self.game.render.setLight(self.game.render.attachNewNode(ambient))
        for name, color, angles in (("key", (2.6, 2.35, 2.1, 1), (-30, -35, 0)),
                                     ("rim", (1.1, 1.4, 1.8, 1), (150, -25, 0))):
            light = DirectionalLight(name)
            light.setColor(color)
            node = self.game.render.attachNewNode(light)
            node.setHpr(*angles)
            self.game.render.setLight(node)
        self.lens = OrthographicLens()
        self.lens.setNearFar(.1, 100)
        self.game.cam.node().setLens(self.lens)
        self.output = output
        self.output.mkdir(parents=True, exist_ok=True)
        self.scratch = ROOT / ".cache" / "sprite-bake"
        self.entries = {}

    def camera(self, frame):
        left, right, bottom, top = frame
        x, z = (left + right) / 2, (bottom + top) / 2
        self.lens.setFilmSize(right - left, top - bottom)
        self.game.camera.setPos(x, -12, z)
        self.game.camera.lookAt(x, 0, z)

    def capture(self):
        self.game.taskMgr.step()
        self.game.graphicsEngine.renderFrame()
        image = PNMImage()
        if not self.game.win.getScreenshot(image):
            raise RuntimeError("Sprite render failed.")
        if not image.hasAlpha():
            raise RuntimeError("Sprite render lost alpha transparency.")
        return image

    def record(self, name, image, frame, *, states=None):
        destination = self.output / (name + ".png")
        if not image.write(Filename.fromOsSpecific(str(destination))):
            raise RuntimeError("Cannot save sprite: " + name)
        self.entries[name] = dict(file=destination.name, width=image.getXSize(), height=image.getYSize(),
                                  frame=frame, columns=8 if states else 1,
                                  rows=len(states) if states else 1,
                                  states=states or {}, sha256=hashlib.sha256(destination.read_bytes()).hexdigest())

    def character(self, name):
        import gltf
        from direct.actor.Actor import Actor
        player = name == "player"
        source = source_file("breach_shift/data/models/characters/" + ("armored" if player else name) + ".glb", self.scratch)
        model = NodePath(gltf.load_model(source.as_posix()))
        actor = Actor(model, copy=False)
        bundle = actor.getPartBundle("modelRoot")
        names = ["hips", "spine", "head"] + [limb + "-" + side
                for side in ("left", "right") for limb in ("arm", "forearm", "hand", "leg", "shin", "foot")]
        actor._sprite_joints = {}
        for joint_name in names:
            if bundle.findChild(joint_name) is not None:
                node = actor.controlJoint(None, "modelRoot", joint_name)
                actor._sprite_joints[joint_name] = node, node.getHpr()
        actor.reparentTo(self.game.render)
        low, high = actor.getTightBounds()
        actor._death_lift = max(abs(low.y), abs(high.y)) * .97
        if player:
            actor.setColorScale(.72, .92, 1.14, 1)
        frame = [-2.9, 2.9, -.3, 3.5]
        self.camera(frame)
        states = ["walk", "idle", "reload" if player else "attack", "death"]
        if player:
            states += ["crouch", "jump"]
        atlas = PNMImage(CELL * 8, CELL * len(states), 4)
        atlas.fill(0)
        atlas.alphaFill(0)
        for row, state in enumerate(states):
            for index in range(8):
                pose(actor, state, index, player=player)
                actor.update(force=True)
                image = self.capture()
                atlas.copySubImage(image, index * CELL, row * CELL, 0, 0)
        self.record(name, atlas, frame, states={state: row for row, state in enumerate(states)})
        actor.cleanup()
        actor.removeNode()
        print("Baked character:", name, flush=True)

    def prop(self, name):
        import gltf
        prop_names = {"car": "wrecked-car", "lamp": "street-lamp"}
        source = source_file("assets/models/props/" + prop_names.get(name, name) + ".glb", self.scratch)
        model = NodePath(gltf.load_model(source.as_posix()))
        model.reparentTo(self.game.render)
        low, high = model.getTightBounds()
        if high.y - low.y > high.x - low.x:
            model.setH(-90)
        low, high = model.getTightBounds()
        model.setPos(-(low.x + high.x) / 2, 0, -low.z)
        low, high = model.getTightBounds()
        margin = .08 * max(high.x - low.x, high.z - low.z)
        frame = [low.x - margin, high.x + margin, -margin, high.z + margin]
        self.camera(frame)
        self.record(name, self.capture(), frame)
        model.removeNode()
        print("Baked prop:", name, flush=True)

    def weapon(self, name):
        import gltf
        relative = "breach_shift/data/models/weapons/" + name
        suffix = ".glb" if name == "rifle" else ".bam.pz"
        source = source_file(relative + suffix, self.scratch)
        model = NodePath(gltf.load_model(source.as_posix())) if suffix == ".glb" else self.game.loader.loadModel(Filename.fromOsSpecific(str(source)))
        model.reparentTo(self.game.render)
        model.setH(-90)
        frame = [-.45, 1.35, -.75, 1.05]
        self.camera(frame)
        self.record(name, self.capture(), frame)
        model.removeNode()
        print("Baked weapon:", name, flush=True)

    def tiles(self):
        folder = self.output / "tiles"
        folder.mkdir(exist_ok=True)
        for name, module in (("asphalt", "road_tile"), ("concrete", "sidewalk"),
                             ("brick", "wall"), ("metal", "wall_trim")):
            source = source_file("assets/models/environments/modules/" + module + ".glb", self.scratch)
            document, binary = read_glb(source)
            material = document["materials"][0]
            texture_index = material["pbrMetallicRoughness"]["baseColorTexture"]["index"]
            image_index = document["textures"][texture_index]["source"]
            view = document["bufferViews"][document["images"][image_index]["bufferView"]]
            offset = view.get("byteOffset", 0)
            image = PNMImage()
            if not image.read(StringStream(binary[offset:offset + view["byteLength"]])):
                raise RuntimeError("Unable to extract embedded base colour.")
            tile = PNMImage(256, 256, 3)
            tile.quickFilterFrom(image)
            tile.write(Filename.fromOsSpecific(str(folder / (name + ".png"))))
        print("Extracted four existing Poly Haven base-colour tiles.", flush=True)

    def save_manifest(self):
        path = self.output / "manifest.json"
        existing = json.loads(path.read_text()) if path.is_file() else {}
        entries = existing.get("sprites", {})
        entries.update(self.entries)
        path.write_text(json.dumps(dict(version=1, source_revision=SOURCE_REVISION,
                                       cell_size=CELL, sprites=entries), indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", help="bake selected characters, weapons or props")
    args = parser.parse_args()
    baker = Baker(ROOT / "breach_shift/data/sprites")
    try:
        characters = ["player", "walker", "runner", "brute", "spitter", "leaper", "armored", "howler", "stalker", "regenerator", "warden"]
        weapons = ["pistol", "smg", "rifle", "shotgun"]
        props = ["barricade", "car", "crate", "barrel", "lamp", "debris"]
        for names, method in ((characters, baker.character), (weapons, baker.weapon), (props, baker.prop)):
            for name in names:
                if args.only is None or name in args.only:
                    method(name)
        if args.only is None:
            baker.tiles()
        baker.save_manifest()
    finally:
        baker.game.destroy()


if __name__ == "__main__":
    main()
