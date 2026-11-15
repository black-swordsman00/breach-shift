"""Four distinct model sources: pistol, compact SMG, rifle and pump shotgun."""

from functools import lru_cache
from math import exp, sin

from panda3d.core import AmbientLight, DirectionalLight, NodePath

from breach_shift.art.primitives import box, part, rod, sphere
from breach_shift.art.library import instantiate
from breach_shift.combat.catalog import WeaponKind


DARK = (.09, .105, .12, 1)
STEEL = (.32, .35, .37, 1)
GRIP = (.12, .10, .075, 1)
MUZZLES = {WeaponKind.PISTOL: .38, WeaponKind.SMG: .60, WeaponKind.RIFLE: .96, WeaponKind.SHOTGUN: 1.05}


@lru_cache(maxsize=4)
def weapon_template(kind: WeaponKind) -> NodePath:
    root = NodePath(f"{kind.value}-model")
    root.setTag("weapon-kind", kind.value)
    if kind is WeaponKind.PISTOL:
        part(root, "polymer-frame", box(), (0, .10, 0), (.10, .32, .075), DARK, "metal")
        part(root, "steel-slide", box(), (0, .12, .065), (.105, .34, .075), STEEL, "metal")
        grip = part(root, "pistol-grip", box(), (0, -.005, -.12), (.085, .11, .23), GRIP, "leather")
        grip.setP(-12)
        rod(root, "barrel", (0, .24, .055), (0, .38, .055), .026, DARK, "metal", top=1)
        part(root, "rear-sight", box(), (0, -.015, .113), (.08, .035, .025), DARK, "metal")
        part(root, "front-sight", box(), (0, .265, .11), (.018, .025, .025), DARK, "metal")
    else:
        length = .40 if kind is WeaponKind.SMG else .51
        receiver_color = (.27, .30, .22, 1) if kind is WeaponKind.RIFLE else DARK
        part(root, "receiver", box(), (0, .13, .025), (.12, length, .13), receiver_color, "metal")
        part(root, "grip", box(), (0, -.005, -.13), (.085, .10, .21), GRIP, "leather").setP(-12)
        part(root, "stock", box(), (0, -.23, -.025), (.10, .29, .13), GRIP, "leather")
        part(root, "butt-pad", box(), (0, -.385, -.025), (.13, .04, .18), DARK, "leather")
        if kind is WeaponKind.SHOTGUN:
            rod(root, "shotgun-barrel", (0, .27, .055), (0, 1.05, .055), .028, STEEL, "metal", top=1)
            rod(root, "magazine-tube", (0, .28, -.025), (0, .88, -.025), .027, DARK, "metal", top=1)
            rod(root, "wooden-pump", (0, .40, -.025), (0, .69, -.025), .065, (.35, .18, .08, 1), "leather", top=1)
            for index in range(7):
                rod(root, "pump-rib", (0, .42 + index * .035, -.025), (0, .43 + index * .035, -.025), .068, GRIP, "leather", top=1)
            for index in range(4):
                rod(root, "shell-holder", (.077, .05 + index * .055, .025), (.077, .05 + index * .055, -.075), .019, (.65, .12, .07, 1), "metal", top=1)
        else:
            muzzle = MUZZLES[kind]
            rod(root, "barrel", (0, .31, .055), (0, muzzle, .055), .023, STEEL, "metal", top=1)
            handguard_length = .20 if kind is WeaponKind.SMG else .38
            part(root, "handguard", box(), (0, .33 + handguard_length / 2, .02), (.115, handguard_length, .105), DARK, "metal")
            for index in range(5):
                part(root, "vent-slot", box(), (.061, .35 + index * handguard_length / 6, .035), (.009, .022, .035), (.025, .028, .03, 1), "metal")
            magazine = part(root, "magazine", box(), (0, .17, -.15), (.085, .13, .26 if kind is WeaponKind.SMG else .22), DARK, "metal")
            magazine.setP(-8 if kind is WeaponKind.SMG else -18)
            part(root, "sight-base", box(), (0, .07, .135), (.08, .16, .045), DARK, "metal")
            part(root, "sight-left", box(), (-.043, .09, .18), (.018, .07, .09), DARK, "metal")
            part(root, "sight-right", box(), (.043, .09, .18), (.018, .07, .09), DARK, "metal")
            part(root, "sight-top", box(), (0, .09, .225), (.10, .07, .018), DARK, "metal")
    for side in (-1, 1):
        rod(root, "trigger-guard", (side * .042, .035, -.04), (side * .042, .12, -.10), .009, DARK, "metal", top=1)
    root.flattenStrong()
    return root


def make_weapon_model(kind: WeaponKind) -> NodePath:
    return instantiate(f"weapons/{kind.value}.bam", lambda: weapon_template(kind))


def _arms(parent, kind):
    sleeve, glove = (.20, .23, .18, 1), (.075, .07, .06, 1)
    support = .13 if kind is WeaponKind.PISTOL else (.54 if kind is WeaponKind.SHOTGUN else .37)
    for label, hand, elbow in (
        ("right", (.025, -.015, -.14), (.18, -.31, -.42)),
        ("left", (-.035, support, -.09), (-.24, -.22, -.43)),
    ):
        rod(parent, f"{label}-sleeve", elbow, (hand[0], hand[1] - .08, hand[2] - .025), .065, sleeve, top=.82)
        part(parent, f"{label}-glove", sphere(), hand, (.055, .075, .06), glove, "leather")
        for index in range(4):
            x = hand[0] + (index - 1.5) * .018
            rod(parent, "gloved-finger", (x, hand[1] + .02, hand[2]), (x, hand[1] + .06, hand[2] + .025), .012, glove, "leather")


class WeaponView:
    def __init__(self, camera: NodePath, kind: WeaponKind) -> None:
        self.root = camera.attachNewNode("first-person-weapon")
        self.root.setScale(.78)
        self.root.setBin("fixed", 40)
        self.root.setDepthTest(False)
        self.root.setDepthWrite(False)
        ambient = AmbientLight("weapon-fill")
        ambient.setColor((.72, .75, .77, 1))
        key = DirectionalLight("weapon-key")
        key.setColor((.8, .75, .65, 1))
        self.root.setLightOff(1)
        self.root.setLight(camera.attachNewNode(ambient), 2)
        key_node = camera.attachNewNode(key)
        key_node.setHpr(-35, -40, 0)
        self.root.setLight(key_node, 2)
        self.kick = 0.0
        self.time = 0.0
        self.flash_time = 0.0
        self.equip(kind)

    def equip(self, kind: WeaponKind) -> None:
        for child in self.root.getChildren():
            child.removeNode()
        self.kind = kind
        make_weapon_model(kind).reparentTo(self.root)
        arms = self.root.attachNewNode("player-arms")
        _arms(arms, kind)
        arms.flattenStrong()
        self.flash = part(self.root, "muzzle-flash", sphere(8, 4), (0, MUZZLES[kind] + .025, .055),
                          (.045, .13, .045), (1, .65, .13, 1), "metal")
        self.flash.setLightOff(3)
        self.flash.hide()
        self.kick = self.flash_time = 0.0
        self.update(0, False)

    def fire(self, damage: int) -> None:
        self.kick = min(.10, .035 + damage * .0005)
        self.flash_time = .045
        self.flash.show()

    def update(self, dt: float, moving: bool) -> None:
        self.time += max(0, dt)
        self.kick *= exp(-16 * max(0, dt))
        self.flash_time -= max(0, dt)
        if self.flash_time <= 0:
            self.flash.hide()
        bob = sin(self.time * 10) * .008 if moving else sin(self.time * 1.8) * .002
        self.root.setPos(.23, .57 - self.kick, -.27 + bob)
        self.root.setHpr(-2, self.kick * 50, 0)
