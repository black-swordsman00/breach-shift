"""Visible, weapon-colored ammunition boxes that do not block movement or shots."""

from math import sin

from panda3d.core import NodePath, TextNode

from breach_shift.art.primitives import box, part, rod, sphere
from breach_shift.combat.catalog import WEAPON_SPECS, WeaponKind
from breach_shift.combat.loot import AmmoReward


class AmmoPickup:
    lifetime = 90.0

    def __init__(self, parent: NodePath, position, reward: AmmoReward) -> None:
        self.reward = reward
        self.age = 0.0
        self.root = parent.attachNewNode("ammo-pickup")
        self.root.setPos(position.x, position.y, .18)
        self.visual = self.root.attachNewNode("ammo-model")
        color = WEAPON_SPECS[reward.kind].color
        part(self.visual, "ammo-box", box(), (0, 0, 0), (.38, .26, .18), color, "metal")
        for x in (-.11, 0, .11):
            brass = (.72, .51, .18, 1)
            rod(self.visual, "cartridge", (x, 0, .09), (x, 0, .22), .025,
                (.65, .12, .08, 1) if reward.kind is WeaponKind.SHOTGUN else brass, "metal", top=1)
            part(self.visual, "bullet-tip", sphere(8, 4), (x, 0, .23), (.025, .025, .04), brass, "metal")
        self.visual.flattenStrong()
        label = TextNode("ammo-label")
        label.setText(f"{WEAPON_SPECS[reward.kind].name} +{reward.rounds}")
        label.setAlign(TextNode.ACenter)
        label.setTextColor(*color)
        node = self.root.attachNewNode(label)
        node.setScale(.14)
        node.setZ(.49)
        node.setBillboardPointEye()
        node.setLightOff(2)

    def update(self, dt: float) -> bool:
        self.age += max(0, dt)
        self.visual.setH(self.age * 36)
        self.visual.setZ(sin(self.age * 3) * .035)
        return self.age < self.lifetime

    def destroy(self) -> None:
        self.root.removeNode()
