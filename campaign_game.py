from dataclasses import dataclass

from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import (BitMask32, CollisionHandlerQueue, CollisionNode,
                         CollisionSegment, CollisionTraverser, GraphicsWindow,
                         NodePath, Point3, TextNode, Vec3)

from campaign_state import CampaignProgress
from campaign_world import CampaignWorld
from level_data import load_levels
from main import BreachShift
from player_health import PlayerHealth
from reality import Reality, RealityShift
from target import Target
from zombie import Zombie
from zombie_catalog import ZombieKind


@dataclass
class SpitProjectile:
    node: NodePath
    velocity: Vec3
    damage: int
    age: float = 0.0


class CampaignGame(BreachShift):
    """Run the zombie campaign while keeping the original training entry point."""

    def __init__(self):
        self.campaign_ready = False
        super().__init__()
        lens = self.camLens
        if lens is None:
            raise RuntimeError("The campaign requires a camera lens.")
        lens.setFov(75)
        self.setup_campaign()

    def setup_campaign(self):
        self.levels = load_levels()
        self.progress = CampaignProgress(len(self.levels))
        self.player_health = PlayerHealth()
        self.reality = RealityShift()
        self.zombies: dict[str, Zombie] = {}
        self.world: CampaignWorld | None = None
        self.projectiles: list[SpitProjectile] = []
        self.shift_held = False
        self.next_zombie_id = 0
        self.notice = ""
        self.notice_until = 0.0
        self.target_hud.hide()
        self.training_hud.hide()
        self.taskMgr.remove("update-training-hud")

        self.campaign_hud = OnscreenText(text="", parent=self.a2dTopLeft,
                                        pos=(0.05, -0.1), scale=0.045,
                                        fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1),
                                        align=TextNode.ALeft, mayChange=True)
        self.status_hud = OnscreenText(text="", parent=self.a2dTopRight,
                                      pos=(-0.05, -0.1), scale=0.045,
                                      fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1),
                                      align=TextNode.ARight, mayChange=True)
        self.notice_hud = OnscreenText(text="", parent=self.aspect2d,
                                      pos=(0, -0.58), scale=0.035,
                                      fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1), mayChange=True)
        notice_node = self.notice_hud.textNode
        if notice_node is not None:
            notice_node.setWordwrap(65)
        self.campaign_controls = OnscreenText(
            text="Shift - Change Reality | E - Interact | T - Retry",
            parent=self.a2dBottomLeft, pos=(0.05, 0.2), scale=0.035,
            fg=(1, 1, 1, 1), shadow=(0, 0, 0, 1), align=TextNode.ALeft)

        self.query_segment = CollisionSegment()
        node = CollisionNode("campaign-query")
        node.addSolid(self.query_segment)
        node.setIntoCollideMask(BitMask32.allOff())
        self.query_node = self.render.attachNewNode(node)
        self.query_queue = CollisionHandlerQueue()
        self.query_traverser = CollisionTraverser("campaign-query")
        self.query_traverser.addCollider(self.query_node, self.query_queue)
        self.player_collider.node().setIntoCollideMask(BitMask32.bit(4))
        self.player_collider.setTag("player", "true")
        self.accept("shift", self.shift_reality)
        self.accept("shift-up", self.release_shift)
        self.accept("e", self.interact)
        for event, callback in (("shift-mouse1", self.shoot), ("shift-r", self.reload_weapon),
                                ("shift-space", self.jump_player), ("shift-space-up", self.release_jump),
                                ("shift-e", self.interact), ("shift-t", self.restart_training)):
            self.accept(event, callback)
        self.campaign_ready = True
        self.load_level()
        self.taskMgr.add(self.update_campaign_hud, "update-campaign-hud", sort=15)

    @property
    def enemies_remaining(self) -> int:
        return sum(zombie.health > 0 for zombie in self.zombies.values())

    def can_act(self) -> bool:
        window = self.win
        return (self.player_health.is_alive and not self.progress.complete
                and window is not None and isinstance(window, GraphicsWindow)
                and window.getProperties().getForeground())

    def load_level(self):
        self.clear_projectiles()
        for target in self.targets.values():
            self.taskMgr.remove(f"reset-color-{target.name}")
            target.root.removeNode()
        self.targets.clear()
        self.zombies.clear()
        if self.world is not None:
            self.world.destroy()
            self.world = None
        BreachShift.restart_training(self)
        camera = self.camera
        if camera is not None:
            camera.setHpr(0, 0, 0)
        self.player_health.reset()
        self.reality.reset()
        self.shift_held = False
        self.next_zombie_id = 0
        level = self.levels[self.progress.level_index]
        self.world = CampaignWorld(self.render, self.load_single_model("models/box"), level)
        for spawn in level.spawns:
            self.spawn_zombie(spawn.kind, spawn.x, spawn.y)
        self.apply_reality()
        self.show_notice(level.briefing, 8)
        self.update_campaign_hud()

    def spawn_zombie(self, kind: ZombieKind, x: float, y: float):
        self.next_zombie_id += 1
        name = f"zombie-{self.next_zombie_id}"
        zombie = Zombie(self.render, self.load_single_model("models/box"), Point3(x, y, 0),
                        kind, name, self.clock.getFrameTime())
        zombie.set_context(self.clock.getFrameTime(), self.reality.state)
        self.zombies[name] = zombie
        self.targets[name] = zombie
        return zombie

    def apply_reality(self):
        world = self.world
        if world is None:
            return
        world.apply(self.reality.state, self.progress.core_collected)
        breach = self.reality.state is Reality.BREACH
        self.floor.setColor((0.18, 0.1, 0.24, 1) if breach else (0.22, 0.3, 0.28, 1))
        self.setBackgroundColor((0.1, 0.025, 0.14) if breach else (0.035, 0.065, 0.07))
        grid = world.grids[self.reality.state]
        for zombie in self.zombies.values():
            zombie.set_context(self.clock.getFrameTime(), self.reality.state)
            if zombie.health > 0 and not grid.is_free(zombie.root.getX(), zombie.root.getY()):
                x, y = grid.nearest_free((zombie.root.getX(), zombie.root.getY()))
                zombie.root.setPos(x, y, 0)
                zombie.lunge_until = None

    def shift_reality(self):
        if not self.can_act() or self.shift_held:
            return
        self.shift_held = True
        world = self.world
        if world is None:
            return
        safe = world.destination_safe(self.player.getPos(), self.reality.destination)
        if self.reality.try_shift(self.clock.getFrameTime(), safe):
            self.apply_reality()
            self.show_notice(f"Reality shifted: {self.reality.state.value}")
        else:
            self.show_notice("Shift recharging." if safe else "Cannot shift inside a barrier.")
        self.update_campaign_hud()

    def release_shift(self):
        self.shift_held = False

    def show_notice(self, text: str, duration: float = 2.0):
        self.notice = text
        self.notice_until = self.clock.getFrameTime() + duration

    def interact(self):
        if not self.can_act():
            return
        level = self.levels[self.progress.level_index]
        position = self.player.getPos()
        if not self.progress.core_collected and (position - Point3(*level.core, 0)).length() <= 1.7:
            if self.reality.state is not Reality.BREACH:
                self.show_notice("Recover the power core in Breach reality.")
            elif self.progress.collect_core():
                self.weapon.reserve_ammo += 24
                self.player_health.heal(20)
                self.apply_reality()
                self.update_weapon_hud()
                self.show_notice("Core recovered. Ammunition supplied. Clear the map and reach the exit.", 4)
        elif (position - Point3(*level.exit, 0)).length() <= 2:
            if self.progress.advance(self.enemies_remaining):
                if self.progress.complete:
                    self.clear_projectiles()
                    self.show_notice("Campaign complete! T - Play again", 30)
                else:
                    self.load_level()
            else:
                self.show_notice("Exit locked: recover the core and defeat every zombie.")
        self.update_campaign_hud()

    def query_collision(self, start: Point3, end: Point3, include_player: bool = False) -> NodePath | None:
        self.query_segment.setPointA(start)
        self.query_segment.setPointB(end)
        self.query_node.node().setFromCollideMask(
            BitMask32.bit(2) | (BitMask32.bit(4) if include_player else BitMask32.allOff()))
        self.query_queue.clearEntries()
        self.query_traverser.traverse(self.render)
        self.query_queue.sortEntries()
        for index in range(self.query_queue.getNumEntries()):
            node = self.query_queue.getEntry(index).getIntoNodePath()
            if not node.getNetTag("target"):
                return node
        return None

    def update_targets(self, task):
        if not self.campaign_ready:
            return super().update_targets(task)
        world = self.world
        if world is None or not self.can_act():
            return Task.cont
        dt = min(self.clock.getDt(), 0.05)
        now = self.clock.getFrameTime()
        player = self.player.getPos()
        grid = world.grids[self.reality.state]
        for zombie in list(self.zombies.values()):
            if zombie.health <= 0:
                continue
            origin = zombie.root.getPos() + Vec3(0, 0, 0.9)
            clear = self.query_collision(origin, player + Vec3(0, 0, 0.9)) is None
            for action in zombie.update_ai(dt, now, player, self.reality.state, grid, clear):
                if action.kind == "hit":
                    self.damage_player(action.damage)
                elif action.kind == "spit":
                    self.spawn_projectile(origin, player + Vec3(0, 0, 0.9), action.damage)
                elif action.kind == "summon" and self.enemies_remaining < 12:
                    x, y = grid.nearest_free((zombie.root.getX() + 1, zombie.root.getY()))
                    self.spawn_zombie(ZombieKind.WALKER, x, y)
        self.update_projectiles(dt)
        return Task.cont

    def spawn_projectile(self, origin: Point3, destination: Point3, damage: int):
        direction = destination - origin
        if direction.lengthSquared() == 0:
            return
        direction.normalize()
        node = self.render.attachNewNode("spit-projectile")
        node.setPos(origin)
        model = self.load_single_model("models/box")
        model.reparentTo(node)
        model.setPos(-0.1, -0.1, -0.1)
        model.setScale(0.2)
        model.setTextureOff(1)
        model.setColor(0.1, 1, 0.2, 1)
        model.setCollideMask(BitMask32.allOff())
        self.projectiles.append(SpitProjectile(node, direction * 8, damage))

    def update_projectiles(self, dt: float):
        for projectile in list(self.projectiles):
            start = projectile.node.getPos()
            end = start + projectile.velocity * dt
            hit = self.query_collision(start, end, True)
            projectile.age += dt
            if hit is not None or projectile.age >= 4:
                if hit is not None and hit.getNetTag("player"):
                    self.damage_player(projectile.damage)
                projectile.node.removeNode()
                self.projectiles.remove(projectile)
            else:
                projectile.node.setPos(end)

    def clear_projectiles(self):
        for projectile in self.projectiles:
            projectile.node.removeNode()
        self.projectiles.clear()

    def damage_player(self, damage: int):
        if self.player_health.take_damage(damage):
            self.show_notice(f"Hit! -{damage} HP" if self.player_health.is_alive else "You died. T - Retry this map", 3)

    def update_movement(self, task):
        if self.campaign_ready:
            if not self.can_act():
                self.shift_held = False
            if not self.player_health.is_alive or self.progress.complete:
                return Task.cont
        return super().update_movement(task)

    def jump_player(self):
        if not self.campaign_ready or self.can_act():
            super().jump_player()

    def shoot(self):
        if not self.campaign_ready or self.can_act():
            super().shoot()

    def reload_weapon(self):
        if not self.campaign_ready or self.can_act():
            super().reload_weapon()

    def damage_target(self, target: Target):
        if isinstance(target, Zombie):
            target.set_context(self.clock.getFrameTime(), self.reality.state)
        super().damage_target(target)

    def update_target_hud(self):
        if not self.campaign_ready:
            super().update_target_hud()

    def restart_training(self):
        if not self.campaign_ready:
            return super().restart_training()
        self.progress.retry()
        self.load_level()

    def update_campaign_hud(self, task=None):
        level = self.levels[self.progress.level_index]
        remaining = self.enemies_remaining
        ready = self.progress.can_exit(remaining)
        if self.world is not None:
            self.world.set_exit_ready(ready)
        text = (f"Map {level.number}/{len(self.levels)}: {level.name}\n"
                f"New zombie: {level.introduced.value.title()}\nZombies remaining: {remaining}\n"
                f"Core: {'Recovered' if self.progress.core_collected else 'Find in Breach'}\n"
                f"Exit: {'E - Enter' if ready else 'Locked'}")
        if self.progress.complete:
            text = f"Campaign complete!\nAll {len(self.levels)} maps survived.\nT - Play again"
        elif not self.player_health.is_alive:
            text = f"You died.\nMap {level.number}: {level.name}\nT - Retry this map"
        self.campaign_hud.setText(text)
        cooldown = self.reality.remaining(self.clock.getFrameTime())
        shift = f"{cooldown:.1f}s" if cooldown else "Ready"
        self.status_hud.setText(
            f"HP: {self.player_health.current}/{self.player_health.maximum}\n"
            f"Reality: {self.reality.state.value}\nShift: {shift}\n"
            f"Shots: {self.training_session.shots} | Hits: {self.training_session.hits}\n"
            f"Accuracy: {self.training_session.accuracy:.1f}%")
        self.status_hud.setFg((1, 0.3, 0.3, 1) if self.player_health.current <= 25 else (1, 1, 1, 1))
        self.notice_hud.setText(self.notice if self.clock.getFrameTime() < self.notice_until else "")
        return Task.cont


if __name__ == "__main__":
    game = CampaignGame()
    game.run()
