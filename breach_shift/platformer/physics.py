"""Small swept rectangle controller in metres, independent of the renderer."""
from dataclasses import dataclass

EPSILON = 1e-6
GRAVITY = 25.0


@dataclass(frozen=True)
class Rect:
    x: float
    z: float
    width: float
    height: float
    one_way: bool = False

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.z + self.height

    def overlaps(self, other):
        return (self.x < other.right - EPSILON and self.right > other.x + EPSILON
                and self.z < other.top - EPSILON and self.top > other.z + EPSILON)


@dataclass
class Body:
    x: float
    z: float
    width: float = .62
    height: float = 1.8
    vx: float = 0.0
    vz: float = 0.0
    grounded: bool = False

    @property
    def rect(self):
        return Rect(self.x - self.width / 2, self.z, self.width, self.height)


def move_body(body: Body, dx: float, dz: float, solids: tuple[Rect, ...]):
    """Sweep both axes; roofs catch feet and solid undersides stop the head.

    One-way platforms can be crossed sideways or from below. They support a
    descending body only when its previous feet position was above their top.
    """
    old = body.rect
    target_x = body.x + dx
    for solid in solids:
        if solid.one_way or old.z >= solid.top - EPSILON or old.top <= solid.z + EPSILON:
            continue
        near, far = solid.x - body.width / 2, solid.right + body.width / 2
        if dx > 0 and body.x <= near + EPSILON and target_x > near:
            target_x = min(target_x, near)
        elif dx < 0 and body.x >= far - EPSILON and target_x < far:
            target_x = max(target_x, far)
    blocked_x = abs(target_x - body.x - dx) > EPSILON
    body.x = target_x
    if blocked_x:
        body.vx = 0

    target_z = body.z + dz
    body.grounded = False
    ceiling = False
    for solid in solids:
        if (body.rect.right <= solid.x + EPSILON
                or body.rect.x >= solid.right - EPSILON):
            continue
        if dz <= 0 and old.z >= solid.top - EPSILON and target_z <= solid.top:
            target_z = max(target_z, solid.top)
            body.grounded = True
        elif (not solid.one_way and dz > 0 and old.top <= solid.z + EPSILON
              and target_z + body.height >= solid.z):
            target_z = min(target_z, solid.z - body.height)
            ceiling = True
    body.z = target_z
    if body.grounded or ceiling:
        body.vz = 0
    return blocked_x, ceiling


def advance_body(body: Body, dt: float, solids: tuple[Rect, ...]):
    dz = body.vz * dt - .5 * GRAVITY * dt * dt
    body.vz -= GRAVITY * dt
    return move_body(body, body.vx * dt, dz, solids)


def can_stand(body: Body, height: float, solids: tuple[Rect, ...]):
    standing = Rect(body.rect.x, body.z, body.width, height)
    return not any(not solid.one_way and standing.overlaps(solid) for solid in solids)


def segment_hit(start, end, rectangle: Rect):
    """Return the first segment fraction in [0, 1], or None when it misses."""
    near, far = 0.0, 1.0
    for origin, delta, low, high in (
        (start[0], end[0] - start[0], rectangle.x, rectangle.right),
        (start[1], end[1] - start[1], rectangle.z, rectangle.top),
    ):
        if abs(delta) < EPSILON:
            if origin < low or origin > high:
                return None
            continue
        entry, leave = sorted(((low - origin) / delta, (high - origin) / delta))
        near, far = max(near, entry), min(far, leave)
        if near > far:
            return None
    return near
