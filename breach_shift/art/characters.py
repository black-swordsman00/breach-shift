"""Load the shipped articulated zombie assets."""

from panda3d.core import NodePath

from breach_shift.art.library import instantiate
from breach_shift.enemies.catalog import ZombieKind


def make_zombie_model(kind: ZombieKind) -> NodePath:
    return instantiate(f"characters/{kind.value}.bam")
