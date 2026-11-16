from dataclasses import dataclass
from math import hypot, pi, sin

from panda3d.core import BitMask32, CardMaker, CollisionBox, NodePath, Point3, TextNode, Vec3

from breach_shift.art.characters import make_zombie_model
from breach_shift.world.navigation import NavigationGrid, Position
from breach_shift.world.reality import Reality
from breach_shift.combat.target import Target
from breach_shift.enemies.catalog import ZOMBIE_SPECS, ZombieKind


@dataclass(frozen=True)
class ZombieAction:
    kind: str
    damage: int = 0


class Zombie(Target):
    """An articulated infected actor with one of ten combat behaviors."""

    def __init__(self, parent: NodePath, cube: NodePath, position: Point3,
                 kind: ZombieKind, name: str, now: float = 0.0) -> None:
        self.kind = kind
        self.spec = ZOMBIE_SPECS[kind]
        super().__init__(parent, make_zombie_model(kind), position,
                         max_health=self.spec.health, name=name)
        self.model.setScale(1)
        height = self.spec.height
        radius = self.spec.radius
        cube.removeNode()
        self.default_color = self.spec.color
        self.restore_color()
        node = self.collider.node()
        node.clearSolids()
        node.addSolid(CollisionBox(Point3(-radius, -radius, 0), Point3(radius, radius, height)))
        node.setIntoCollideMask(BitMask32.bit(1) | BitMask32.bit(2))
        self.current_reality = Reality.NORMAL
        self.current_time = now
        self.last_hit_at = now
        self.next_attack = now + 0.6
        self.next_voice_at = now + 1.5
        self.next_summon = now + 5.0
        self.summons_used = 0
        self.healing_fraction = 0.0
        self.path: list[Position] = []
        self.next_route = 0.0
        self.windup_until: float | None = None
        self.lunge_until: float | None = None
        self.lunge_started = 0.0
        self.lunge_direction = Vec3(0, 1, 0)
        self.impact_available = False
        self.loot_dropped = False
        self.died_at: float | None = None
        self.animation_time = 0.0
        self.previous_visual_position = Point3(position)
        self.arms = [self.model.find(f"**/arm-{side}") for side in ("left", "right")]
        self.legs = [self.model.find(f"**/leg-{side}") for side in ("left", "right")]
        self.health_display = self.root.attachNewNode("enemy-health")
        self.health_display.setZ(height + .14)
        self.health_display.setBillboardPointEye()
        self.health_display.setLightOff(2)
        background = CardMaker("health-background")
        background.setFrame(-.33, .33, -.01, .065)
        self.health_display.attachNewNode(background.generate()).setColor(.05, .05, .05, 1)
        fill = CardMaker("health-fill")
        fill.setFrame(0, .64, 0, .045)
        self.health_fill = self.health_display.attachNewNode(fill.generate())
        self.health_fill.setPos(-.32, -.005, 0)
        self.health_fill.setColor(.7, .14, .10, 1)
        self.health_label = TextNode("enemy-health-label")
        self.health_label.setAlign(TextNode.ACenter)
        label = self.health_display.attachNewNode(self.health_label)
        label.setPos(0, 0, .09)
        label.setScale(.08)
        self.update_health_display()

    def restore_color(self) -> None:
        self.model.clearColor()
        self.model.setColorScale(1, 1, 1, 1)

    def flash_hit(self) -> None:
        self.model.setColorScale(1.8, .9, .35, 1)

    def update_health_display(self) -> None:
        self.health_fill.setSx(self.health / self.max_health)
        self.health_label.setText(f"{self.kind.value.title()} {self.health}/{self.max_health}")

    def update_animation(self, dt: float, player: Point3) -> None:
        if self.health <= 0:
            return
        self.animation_time += dt
        position = self.root.getPos()
        moving = (position - self.previous_visual_position).lengthSquared() > .00001
        self.previous_visual_position = Point3(position)
        if hypot(player.x - position.x, player.y - position.y) > .01:
            self.root.lookAt(player.x, player.y, position.z)
        swing = sin(self.animation_time * (10 if self.kind is ZombieKind.RUNNER else 6)) * (22 if moving else 2)
        for index, (arm, leg) in enumerate(zip(self.arms, self.legs)):
            phase = -1 if index else 1
            arm.setP(-swing * phase - (35 if self.windup_until else 8))
            leg.setP(swing * phase)
        distance = hypot(player.x - position.x, player.y - position.y)
        hidden = self.kind is ZombieKind.STALKER and self.current_reality is Reality.NORMAL and distance > 4
        self.health_display.hide() if hidden or distance > 18 else self.health_display.show()

    def set_context(self, now: float, reality: Reality) -> None:
        if reality is not self.current_reality:
            self.path.clear()
            self.next_route = 0.0
        self.current_time = now
        self.current_reality = reality

    def take_damage(self, damage: int) -> bool:
        if damage <= 0 or (self.kind is ZombieKind.WARDEN and self.current_reality is Reality.NORMAL):
            return False
        if self.kind is ZombieKind.ARMORED and self.current_reality is Reality.NORMAL:
            damage = max(1, damage // 2)
        accepted = super().take_damage(damage)
        if accepted:
            self.last_hit_at = self.current_time
            self.healing_fraction = 0.0
            self.update_health_display()
        return accepted

    def _move(self, dt: float, now: float, goal: Point3, grid: NavigationGrid) -> None:
        position = self.root.getPos()
        start, destination = (position.x, position.y), (goal.x, goal.y)
        if grid.segment_is_free(start, destination):
            self.path = [destination]
        elif now >= self.next_route or not self.path:
            self.path = grid.pursuit_path(start, destination)
            self.next_route = now + 0.45
        speed = self.spec.speed * (1.35 if self.current_reality is Reality.BREACH else 1.0)
        remaining = speed * max(0.0, dt)
        while self.path and remaining > 0:
            dx, dy = self.path[0][0] - position.x, self.path[0][1] - position.y
            distance = hypot(dx, dy)
            if distance < .01:
                self.path.pop(0)
                continue
            step = min(remaining, distance)
            x, y = position.x + dx / distance * step, position.y + dy / distance * step
            if not grid.segment_is_free((position.x, position.y), (x, y)):
                self.path.clear()
                self.next_route = 0.0
                break
            self.root.setX(x)
            self.root.setY(y)
            position = self.root.getPos()
            remaining -= step
            if step >= distance - .0001:
                self.path.pop(0)

    def update_ai(self, dt: float, now: float, player: Point3,
                  reality: Reality, grid: NavigationGrid, line_clear: bool) -> list[ZombieAction]:
        self.set_context(now, reality)
        if self.health <= 0:
            return []
        actions = []
        position = self.root.getPos()
        distance = hypot(player.x - position.x, player.y - position.y)
        vertical_gap = abs(player.z - position.z)
        if self.kind is ZombieKind.STALKER:
            self.model.hide() if reality is Reality.NORMAL and distance > 4 else self.model.show()
        if self.kind is ZombieKind.REGENERATOR and reality is Reality.NORMAL and now - self.last_hit_at >= 2:
            self.healing_fraction += 8 * dt
            recovered = int(self.healing_fraction)
            self.healing_fraction -= recovered
            self.health = min(self.max_health, self.health + recovered)
            self.update_health_display()
        if self.kind is ZombieKind.HOWLER and line_clear and distance < 9 and now >= self.next_summon and self.summons_used < 2:
            actions.append(ZombieAction("summon"))
            self.summons_used += 1
            self.next_summon = now + 6

        if self.kind is ZombieKind.WARDEN:
            if self.windup_until is not None:
                self.model.setColorScale(2, .25, .35, 1)
                if now >= self.windup_until:
                    if line_clear and distance <= 3.2 and player.z < 0.5:
                        actions.append(ZombieAction("hit", self.spec.damage))
                    self.windup_until = None
                    self.next_attack = now + self.spec.interval
                    self.restore_color()
            elif line_clear and distance <= self.spec.reach and now >= self.next_attack:
                self.windup_until = now + 0.65
            elif distance > self.spec.reach or not line_clear:
                self._move(dt, now, player, grid)
            return actions

        if self.windup_until is not None:
            self.model.setColorScale(2, .3, .2, 1)
            if now < self.windup_until:
                return actions
            self.windup_until = None
            self.lunge_started = now
            self.lunge_until = now + 0.45
            self.impact_available = True
        if self.lunge_until is not None:
            leap = self.kind is ZombieKind.LEAPER
            candidate = position + self.lunge_direction * (8 if leap else 5) * dt
            if grid.is_free(candidate.x, candidate.y):
                self.root.setX(candidate.x)
                self.root.setY(candidate.y)
            progress = min(1.0, (now - self.lunge_started) / 0.45)
            self.root.setZ(sin(pi * progress) * 1.1 if leap else 0)
            distance = hypot(player.x - self.root.getX(), player.y - self.root.getY())
            if self.impact_available and line_clear and distance < 1.5 and abs(player.z - self.root.getZ()) < 1.4:
                actions.append(ZombieAction("hit", self.spec.damage))
                self.impact_available = False
            if now >= self.lunge_until:
                self.root.setZ(0)
                self.lunge_until = None
                self.next_attack = now + self.spec.interval
                self.restore_color()
            return actions
        if self.kind in (ZombieKind.BRUTE, ZombieKind.LEAPER) and line_clear and 2 < distance < 5 and now >= self.next_attack:
            self.lunge_direction = Vec3(player.x - position.x, player.y - position.y, 0)
            self.lunge_direction.normalize()
            self.windup_until = now + (0.25 if self.kind is ZombieKind.LEAPER else 0.6)
            return actions

        if line_clear and distance <= self.spec.reach and now >= self.next_attack:
            if self.kind is ZombieKind.SPITTER:
                actions.append(ZombieAction("spit", self.spec.damage))
                self.next_attack = now + self.spec.interval
            elif vertical_gap < 1.4:
                actions.append(ZombieAction("hit", self.spec.damage))
                self.next_attack = now + self.spec.interval
        if not line_clear or distance > (3.5 if self.kind is ZombieKind.SPITTER else self.spec.reach * 0.8):
            self._move(dt, now, player, grid)
        return actions
