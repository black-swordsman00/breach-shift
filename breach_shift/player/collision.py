"""Full-height player movement against the game's box-shaped architecture."""
from dataclasses import dataclass
from itertools import product

from panda3d.core import BitMask32, CollisionBox, NodePath, Point3


EPSILON = .001
PLAYER_RADIUS = .4


@dataclass(frozen=True)
class ObstacleBox:
    minimum: Point3
    maximum: Point3

    def supports(self, position: Point3, radius: float = PLAYER_RADIUS) -> bool:
        return all(position[axis] + radius > self.minimum[axis] + EPSILON
                   and position[axis] - radius < self.maximum[axis] - EPSILON
                   for axis in (0, 1))


def collect_obstacles(root: NodePath) -> list[ObstacleBox]:
    """Read active colliders, including parent transforms and reality stashing.

    Moving enemies keep their existing Panda3D pusher response. Architecture
    and training targets have a landing mask; untagged overhangs also qualify.
    Rotated boxes use conservative world-aligned bounds. Imported stairways
    or slopes still need an appropriate authored collision representation.
    """
    boxes = []
    for path in root.findAllMatches("**/+CollisionNode"):
        node = path.node()
        mask = node.getIntoCollideMask()
        if not mask & BitMask32.bit(1):
            continue
        if path.hasNetTag("target") and not mask & BitMask32.bit(3):
            continue
        matrix = path.getMat(root)
        for solid in node.getSolids():
            if not isinstance(solid, CollisionBox):
                continue
            low, high = solid.getMin(), solid.getMax()
            corners = [matrix.xformPoint(Point3(*corner)) for corner in
                       product(*[(low[axis], high[axis]) for axis in range(3)])]
            boxes.append(ObstacleBox(
                Point3(*(min(point[axis] for point in corners) for axis in range(3))),
                Point3(*(max(point[axis] for point in corners) for axis in range(3)))))
    return boxes


def resolve_motion(start: Point3, destination: Point3, height: float,
                   boxes: list[ObstacleBox]) -> tuple[Point3, bool]:
    """Sweep feet/head vertically, then slide horizontally along box faces.

    Return the safe position and whether the head struck a ceiling. A ceiling
    hit must stop ascent without replenishing the player's airborne jumps.
    """
    position = Point3(start)
    position.z = destination.z
    ceiling_hit = False
    for box in boxes:
        if not box.supports(start):
            continue
        if (destination.z <= start.z and start.z >= box.maximum.z - EPSILON
                and position.z < box.maximum.z):
            position.z = box.maximum.z
        elif (destination.z > start.z
              and start.z + height <= box.minimum.z + EPSILON
              and position.z + height > box.minimum.z):
            position.z = box.minimum.z - height
            ceiling_hit = True

    for axis in (0, 1):
        other = 1 - axis
        target = destination[axis]
        for box in boxes:
            if (position.z >= box.maximum.z - EPSILON
                    or position.z + height <= box.minimum.z + EPSILON
                    or position[other] + PLAYER_RADIUS <= box.minimum[other] + EPSILON
                    or position[other] - PLAYER_RADIUS >= box.maximum[other] - EPSILON):
                continue
            near = box.minimum[axis] - PLAYER_RADIUS
            far = box.maximum[axis] + PLAYER_RADIUS
            if position[axis] <= near + EPSILON and target > near:
                target = min(target, near)
            elif position[axis] >= far - EPSILON and target < far:
                target = max(target, far)
        position[axis] = target

    # Recover horizontally from a moving obstacle or an already embedded save
    # position. Never lift the player through a roof to hide an intersection.
    for _ in range(4):
        moved = False
        for box in boxes:
            if (not box.supports(position)
                    or position.z >= box.maximum.z - EPSILON
                    or position.z + height <= box.minimum.z + EPSILON):
                continue
            exits = [(abs(position[axis] - face), axis, face)
                     for axis in (0, 1)
                     for face in (box.minimum[axis] - PLAYER_RADIUS,
                                  box.maximum[axis] + PLAYER_RADIUS)]
            _, axis, face = min(exits)
            position[axis] = face
            moved = True
        if not moved:
            break
    return position, ceiling_hit


def has_support(position: Point3, boxes: list[ObstacleBox]) -> bool:
    return any(box.supports(position) and abs(position.z - box.maximum.z) <= EPSILON
               for box in boxes)
