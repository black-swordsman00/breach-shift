"""Original, editable hard-surface weapon models; +Y is the firing direction."""
import argparse
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_tools import aim, box, empty, material, mesh, save_asset, sphere, studio, tube

ROOT = Path(__file__).resolve().parents[2]


class Weapon:
    def __init__(self, kind):
        self.kind = kind
        self.root = empty("WEAPON_" + kind.title())
        self.root["weapon_kind"] = kind
        self.root["designer"] = "Breach Shift Blender workshop"
        self.steel = material(kind + "_worn_gunmetal", (.105, .12, .135), "metal", .36, .85)
        self.black = material(kind + "_anodized_black", (.023, .03, .034), "metal", .51, .65)
        self.rubber = material(kind + "_textured_grip", (.035, .030, .024), "leather", .86)
        self.olive = material(kind + "_olive_polymer", (.105, .125, .076), "fabric", .68)
        self.silver = material(kind + "_machined_steel", (.31, .34, .35), "metal", .28, .95)
        self.bore = material(kind + "_barrel_interior", (.003, .004, .005), "metal", .9)
        self.wood = material(kind + "_walnut", (.18, .073, .026), "fabric", .62)
        self.brass = material(kind + "_brass", (.46, .28, .07), "metal", .35, .75)
        self.red = material(kind + "_shell_red", (.26, .018, .012), "fabric", .5)
        if kind == "pistol":
            self.pistol()
        else:
            self.long_gun()
        self.trigger()
        self.root["units"] = "metres"

    def block(self, name, center, dimensions, mat=None, bevel=.005):
        return box(self.kind + "_" + name, center, dimensions, mat or self.black, self.root, bevel)

    def pipe(self, name, start, end, radius, mat=None, **kwargs):
        return tube(self.kind + "_" + name, (start, end), radius, mat or self.steel, self.root, sides=24, **kwargs)

    def barrel(self, start, end, radius=.019):
        # Concentric rings include the visible muzzle wall and a recessed bore.
        vertices, faces = [], []
        for y, width in ((start, radius), (end, radius), (end, radius * .58), (end - .055, radius * .58)):
            for index in range(40):
                a = math.tau * index / 40
                vertices.append((math.cos(a) * width, y, .055 + math.sin(a) * width))
        for ring in range(3):
            for index in range(40):
                nxt = (index + 1) % 40
                faces.append((ring * 40 + index, ring * 40 + nxt, (ring + 1) * 40 + nxt, (ring + 1) * 40 + index))
        mesh(self.kind + "_hollow_barrel", vertices, faces, self.steel, self.root)
        self.pipe("bore_shadow", (0, end - .056, .055), (0, end - .055, .055), radius * .56, self.bore)

    def grip(self, y=.005):
        grip = self.block("pistol_grip", (0, y, -.115), (.076, .11, .205), self.rubber, .013)
        grip.rotation_euler.x = math.radians(-13)
        for side in (-1, 1):
            for row in range(9):
                strip = self.block("grip_stipple", (0, 0, 0), (.002, .072, .004), self.black, .001)
                strip.parent, strip.location = grip, (side * .039, 0, .075 - row * .016)
        base = self.block("grip_base", (0, 0, 0), (.086, .105, .022), self.rubber, .006)
        base.parent, base.location = grip, (0, 0, -.109)

    def pistol(self):
        self.block("polymer_frame", (0, .11, -.006), (.082, .29, .065), self.rubber, .009)
        self.block("machined_slide", (0, .12, .062), (.090, .335, .075), self.steel, .008)
        self.block("recoil_rail", (0, .208, -.022), (.073, .125, .035), self.black)
        self.grip()
        self.barrel(.245, .38, .024)
        for side in (-1, 1):
            for index in range(8):
                self.block("slide_serration", (side * .046, -.014 + index * .009, .063), (.0025, .003, .044), self.black, .001)
            self.pipe("takedown_pin", (side * .043, .054, -.008), (side * .048, .054, -.008), .006, self.silver)
        self.block("ejection_port", (.046, .15, .07), (.003, .085, .039), self.bore, .003)
        self.block("chamber_hood", (.048, .136, .072), (.004, .052, .028), self.silver, .002)
        for x in (-.027, .027):
            self.block("rear_sight", (x, -.027, .111), (.018, .024, .021), self.black, .002)
        self.block("front_sight", (0, .268, .111), (.012, .024, .020), self.black, .002)
        self.block("sight_dot", (0, .254, .115), (.005, .002, .008), self.brass, .001)

    def long_gun(self):
        shotgun, smg = self.kind == "shotgun", self.kind == "smg"
        polymer = self.wood if shotgun else self.olive if not smg else self.rubber
        self.block("upper_receiver", (0, .11, .035), (.105, .40 if smg else .45, .115), self.steel, .009)
        self.block("lower_receiver", (0, .115, -.035), (.098, .30, .064), self.black, .006)
        self.grip(-.010)
        self.block("stock_buffer", (0, -.185, .015), (.067, .20, .059), self.steel)
        self.block("stock_comb", (0, -.29, -.005), (.083, .22, .10), polymer, .012)
        self.block("shoulder_pad", (0, -.405, -.034), (.102, .035, .164), self.rubber, .01)
        for index in range(6):
            self.block("buttpad_groove", (0, -.424, -.096 + index * .025), (.085, .003, .004), self.black, .001)
        for side in (-1, 1):
            for y in (-.02, .20):
                self.pipe("receiver_pin", (side * .054, y, .018), (side * .057, y, .018), .006, self.silver)
        self.block("ejection_port", (.054, .15, .042), (.003, .115, .04), self.bore)
        self.block("bolt_face", (.056, .145, .043), (.004, .065, .027), self.silver, .002)
        self.pipe("charging_handle", (.048, .17, .052), (.086, .17, .052), .007, self.black)
        if shotgun:
            self.barrel(.29, 1.05, .027)
            self.pipe("magazine_tube", (0, .29, -.010), (0, .89, -.010), .024)
            self.pipe("walnut_pump", (0, .40, -.010), (0, .68, -.010), .057, self.wood)
            for index in range(11):
                self.pipe("pump_checkering", (0, .415 + index * .022, -.010), (0, .420 + index * .022, -.010), .0585, self.rubber)
            for index in range(4):
                y = -.025 + index * .052
                self.pipe("spare_shell", (-.065, y, -.010), (-.065, y, .062), .017, self.red)
                self.pipe("shell_rim", (-.065, y, .052), (-.065, y, .066), .018, self.brass)
            self.block("bead_sight", (0, 1.01, .086), (.009, .015, .010), self.brass, .002)
        else:
            muzzle, end = (.60, .49) if smg else (.96, .76)
            self.barrel(.29, muzzle, .020)
            self.block("vented_handguard", (0, (.31 + end) / 2, .018), (.10, end - .31, .097), polymer, .008)
            for side in (-1, 1):
                for index in range(6 if smg else 10):
                    self.block("handguard_vent", (side * .051, .325 + index * (.024 if smg else .038), .026), (.003, .017, .032), self.bore, .002)
            for index in range(9 if smg else 17):
                y = -.035 + index * .037
                self.block("picatinny_tooth", (0, y, .103), (.070, .018, .016), self.steel, .002)
            magazine = self.block("detachable_magazine", (0, .17, -.156), (.074, .11, .25 if smg else .23), self.black, .008)
            magazine.rotation_euler.x = math.radians(-7 if smg else -15)
            for side in (-1, 1):
                for index in range(4):
                    self.block("magazine_reinforcement", (side * .039, .17, -.08 - index * .043), (.003, .083, .005), self.steel, .001)
            # An open optical hood preserves sight through the middle in first person.
            self.block("optic_mount", (0, .08, .133), (.067, .11, .032), self.black)
            for x in (-.037, .037):
                self.block("optic_side", (x, .08, .178), (.012, .062, .079), self.black, .004)
            self.block("optic_top", (0, .08, .219), (.086, .064, .013), self.black, .004)
            self.block("optic_bottom", (0, .08, .142), (.080, .064, .012), self.black)
            self.pipe("muzzle_collar", (0, muzzle - .078, .055), (0, muzzle - .045, .055), .028, self.black)

    def trigger(self):
        points = [(-.031, .010, -.045), (-.040, .034, -.094), (-.037, .110, -.101),
                  (.037, .110, -.101), (.040, .034, -.094), (.031, .010, -.045)]
        tube(self.kind + "_trigger_guard", points, .006, self.black, self.root, sides=12)
        tube(self.kind + "_curved_trigger", [(0, .054, -.036), (0, .044, -.063), (0, .054, -.081)], .005, self.silver, self.root, sides=12)


def build(kind, render):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.data.orphans_purge(do_recursive=True)
    weapon = Weapon(kind)
    camera = studio(1.2, wide=True)
    camera.location = (1.45, 1.7, 1.05)
    aim(camera, (0, .2, -.02))
    camera.data.ortho_scale = 1.55 if kind != "pistol" else .77
    # A floating inspection scene avoids intersecting the grip with the floor.
    bpy.data.objects["STUDIO_floor"].location.z = -.35
    destination = ROOT / "assets/blender/weapons" / kind
    save_asset(weapon.root, destination, ROOT / "assets/previews/weapons" / (kind + ".png") if render else None,
               export_path=ROOT / ".cache/blender-export/weapons" / (kind + ".glb"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("all", "pistol", "smg", "rifle", "shotgun"), default="all")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    for kind in (("pistol", "smg", "rifle", "shotgun") if args.kind == "all" else (args.kind,)):
        build(kind, args.render)
