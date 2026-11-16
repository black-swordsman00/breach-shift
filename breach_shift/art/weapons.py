"""Load weapon assets and animate the first-person view."""

from math import exp, sin

from panda3d.core import AmbientLight, DirectionalLight, NodePath

from breach_shift.art.primitives import part, rod, sphere
from breach_shift.art.library import instantiate
from breach_shift.combat.catalog import WeaponKind


MUZZLES = {WeaponKind.PISTOL: .38, WeaponKind.SMG: .60, WeaponKind.RIFLE: .96, WeaponKind.SHOTGUN: 1.05}


def make_weapon_model(kind: WeaponKind) -> NodePath:
    return instantiate(f"weapons/{kind.value}.bam")


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
