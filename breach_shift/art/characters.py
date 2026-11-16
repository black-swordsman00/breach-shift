"""Load the shipped articulated zombie assets."""

from panda3d.core import NodePath
from direct.actor.Actor import Actor

from breach_shift.art.library import instantiate, metadata
from breach_shift.enemies.catalog import ZombieKind


class _SkinnedZombieModel(Actor):
    """Keep the existing NodePath removal contract while releasing rig resources."""

    def removeNode(self):
        if self.getPartNames():
            self.cleanup()
        else:
            super().removeNode()


def make_zombie_model(kind: ZombieKind) -> NodePath:
    model = instantiate(f"characters/{kind.value}.bam")
    if not model.find("**/+Character").isEmpty():
        actor = _SkinnedZombieModel(model, copy=False)
        bundle = actor.getPartBundle("modelRoot")
        required = ("arm-left", "arm-right", "leg-left", "leg-right")
        optional = ("hips", "spine", "head", "forearm-left", "forearm-right",
                    "hand-left", "hand-right", "shin-left", "shin-right", "foot-left", "foot-right")
        for name in required + optional:
            if bundle.findChild(name) is None:
                if name in optional:
                    continue
                actor.cleanup()
                raise ValueError(f"Missing zombie animation joint: {kind.value}/{name}")
            actor.controlJoint(None, "modelRoot", name)
        actor.setTag("source", "blender")
        actor.setTag("source-file", kind.value + ".glb")
        actor.setTag("animation", "skinned-humanoid")
        actor.setCollideMask(0)
        model = actor
    model.setTag("zombie-kind", kind.value)
    model.setTag("design", "female" if kind is ZombieKind.RUNNER else "infected")
    profile = metadata(f"characters/{kind.value}.json")
    if profile.get("provider"):
        model.setTag("provider", profile["provider"])
    model.setName(f"{kind.value}-model")
    return model
