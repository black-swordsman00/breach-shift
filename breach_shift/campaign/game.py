from dataclasses import dataclass
from math import hypot
from random import Random

from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import (BitMask32, CollisionHandlerQueue, CollisionNode, CollisionPlane,
                         CollisionSegment, CollisionTraverser, GraphicsWindow,
                         NodePath, Plane, Point3, TextNode, Vec3)

from breach_shift.campaign.state import CampaignProgress
from breach_shift.campaign.director import WaveDirector
from breach_shift.art.primitives import part, sphere
from breach_shift.art.weapons import WeaponView
from breach_shift.combat.arsenal import Arsenal
from breach_shift.combat.catalog import WEAPON_ORDER, WeaponKind
from breach_shift.combat.loot import roll_ammo
from breach_shift.world.pickups import AmmoPickup
from breach_shift.world.environment import apply_atmosphere
from breach_shift.world.scene import CampaignWorld
from breach_shift.world.levels import load_levels
from breach_shift.core.game import BreachShift
from breach_shift.player.health import PlayerHealth
from breach_shift.world.reality import Reality, RealityShift
from breach_shift.combat.target import Target
from breach_shift.enemies.zombie import Zombie
from breach_shift.enemies.catalog import ZOMBIE_ORDER, ZombieKind


@dataclass
class SpitProjectile:
    node: NodePath
    velocity: Vec3
    damage: int
    age: float = 0.0


class CampaignGame(BreachShift):
    """Run the zombie campaign on top of the shared first-person game systems."""

    def __init__(self, *, headless: bool = False):
        self.campaign_ready = False
        super().__init__(headless=headless)
        lens = self.camLens
        if lens is None:
            raise RuntimeError("The campaign requires a camera lens.")
        lens.setFov(75)
        self.setup_campaign()

    def setup_campaign(self):
        self.levels = load_levels()
        self.move_speed = 6.5
        self.progress = CampaignProgress(len(self.levels))
        self.player_health = PlayerHealth()
        self.reality = RealityShift()
        self.zombies: dict[str, Zombie] = {}
        self.world: CampaignWorld | None = None
        self.projectiles: list[SpitProjectile] = []
        self.pickups: list[AmmoPickup] = []
        self.random = Random()
        self.arsenal = Arsenal()
        self.weapon = self.arsenal.active
        self.weapon_view = WeaponView(self.camera, self.arsenal.selected)
        self.director = WaveDirector()
        self.trigger_held = False
        self.last_encounter_time = self.clock.getFrameTime()
        self.previous_view_position = Point3(self.player.getPos())
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
            text="1 Pistol | 2 SMG | 3 Rifle | 4 Shotgun\nShift - Change Reality | E - Interact | T - Retry",
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
        self.accept("mouse1-up", self.release_trigger)
        self.accept("shift-mouse1-up", self.release_trigger)
        for index, kind in enumerate(WEAPON_ORDER, start=1):
            self.accept(str(index), self.select_weapon, [kind])
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
                and (getattr(self, "headless", False)
                     or (window is not None and isinstance(window, GraphicsWindow)
                         and window.getProperties().getForeground())))

    def load_level(self):
        audio = getattr(self, "audio", None)
        if audio is not None:
            audio.stop_all()
        self.clear_projectiles()
        self.clear_pickups()
        self.arsenal.reset()
        self.weapon = self.arsenal.active
        self.weapon_view.equip(self.arsenal.selected)
        self.director = WaveDirector()
        self.trigger_held = False
        self.last_encounter_time = self.clock.getFrameTime()
        for target in self.targets.values():
            self.taskMgr.remove(f"reset-color-{target.name}")
            target.model.removeNode()
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
        self.player.setPos(*level.player_spawn, 0)
        self.previous_view_position = Point3(self.player.getPos())
        bounds = level.bounds
        self.floor.setPos(bounds.min_x, bounds.min_y, -0.2)
        self.floor.setScale(bounds.width, bounds.depth, 0.2)
        boundaries = self.arena_boundaries.node()
        boundaries.clearSolids()
        for normal, point in (
                (Vec3(1, 0, 0), Point3(bounds.min_x, 0, 0)),
                (Vec3(-1, 0, 0), Point3(bounds.max_x, 0, 0)),
                (Vec3(0, 1, 0), Point3(0, bounds.min_y, 0)),
                (Vec3(0, -1, 0), Point3(0, bounds.max_y, 0))):
            boundaries.addSolid(CollisionPlane(Plane(normal, point)))
        self.world = CampaignWorld(self.render, self.load_single_model("models/box"), level)
        pipeline = getattr(self, "render_pipeline", None)
        if pipeline is not None:
            from breach_shift.art.lighting import environment_map
            pipeline.env_map = environment_map(
                "courtyard" if self.world.environment.hasTag("production-environment") else "night")
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
        zombie.next_voice_at = self.clock.getFrameTime() + self.random.uniform(1, 5)
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
        background = (.075, .035, .11) if breach else world.background
        from breach_shift.art.color import atmosphere_input
        self.setBackgroundColor(atmosphere_input(background))
        world.environment.setColorScale((.72, .62, .92, 1) if breach else (1, 1, 1, 1))
        apply_atmosphere(self.render, breach, world.level.number)
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
                self.director.seal()
                self.player_health.heal(20)
                self.apply_reality()
                self.update_weapon_hud()
                self.show_notice("Core recovered. Reinforcements sealed. Clear the remaining zombies and reach the exit.", 5)
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
        now = self.clock.getFrameTime()
        elapsed = max(0.0, now - self.last_encounter_time)
        self.last_encounter_time = now
        if world is None or not self.can_act():
            self.trigger_held = False
            return Task.cont
        dt = min(self.clock.getDt(), 0.05)
        if self.trigger_held and self.weapon.automatic:
            super().shoot()
        self.spawn_reinforcements(self.director.advance(elapsed, self.enemies_remaining))
        player = self.player.getPos()
        grid = world.grids[self.reality.state]
        for zombie in list(self.zombies.values()):
            if zombie.health <= 0:
                if zombie.died_at is not None and now - zombie.died_at >= 10:
                    zombie.model.removeNode()
                    zombie.root.removeNode()
                    self.zombies.pop(zombie.name, None)
                    self.targets.pop(zombie.name, None)
                continue
            origin = zombie.root.getPos() + Vec3(0, 0, 0.9)
            clear = self.query_collision(origin, player + Vec3(0, 0, 0.9)) is None
            had_windup = zombie.windup_until is not None
            for action in zombie.update_ai(dt, now, player, self.reality.state, grid, clear):
                if action.kind == "hit":
                    self.damage_player(action.damage)
                    self.play_sound("zombie_attack", node=zombie.root, volume=.7)
                elif action.kind == "spit":
                    self.spawn_projectile(origin, player + Vec3(0, 0, 0.9), action.damage)
                    self.play_sound("zombie_attack", node=zombie.root, volume=.5, pitch=1.25)
                elif action.kind == "summon" and self.enemies_remaining < self.director.max_alive:
                    self.play_sound("zombie_howl", node=zombie.root, volume=.85)
                    x, y = grid.nearest_free((zombie.root.getX() + 1, zombie.root.getY()))
                    self.spawn_zombie(ZombieKind.WALKER, x, y)
            if zombie.windup_until is not None and not had_windup:
                self.play_sound("zombie_roar" if zombie.kind is ZombieKind.WARDEN else "zombie_attack",
                                node=zombie.root, volume=.8)
            if now >= zombie.next_voice_at:
                if (zombie.root.getPos() - player).length() < 40:
                    self.play_sound("zombie_idle", node=zombie.root, volume=.5,
                                    pitch=self.random.uniform(.82, 1.12))
                zombie.next_voice_at = now + self.random.uniform(3.5, 7)
            zombie.update_animation(dt, player)
        self.update_projectiles(dt)
        self.update_pickups(elapsed)
        moving = (player - self.previous_view_position).lengthSquared() > .0001
        self.previous_view_position = Point3(player)
        self.weapon_view.update(dt, moving)
        return Task.cont

    def spawn_reinforcements(self, count: int) -> None:
        if count <= 0 or self.world is None:
            return
        grid = self.world.grids[self.reality.state]
        player = self.player.getPos()
        candidates = grid.connected_positions((player.x, player.y))
        self.random.shuffle(candidates)
        kinds = [kind for kind in ZOMBIE_ORDER[:self.progress.level_index + 1]
                 if kind is not ZombieKind.WARDEN]
        spawned = 0
        for x, y in candidates:
            if spawned >= count or self.enemies_remaining >= self.director.max_alive:
                break
            if hypot(x - player.x, y - player.y) < 12:
                continue
            if not all(other.is_free(x, y) for other in self.world.grids.values()):
                continue
            if any(zombie.health > 0 and hypot(x - zombie.root.getX(), y - zombie.root.getY()) < 1.5
                   for zombie in self.zombies.values()):
                continue
            self.spawn_zombie(self.random.choice(kinds), x, y)
            spawned += 1
        if spawned:
            self.show_notice(f"Wave {self.director.wave}: {spawned} reinforcements!", 3)

    def update_pickups(self, dt: float) -> None:
        player = self.player.getPos()
        for pickup in list(self.pickups):
            position = pickup.root.getPos(self.render)
            expired = not pickup.update(dt)
            nearby = (self.player_health.is_alive and hypot(position.x - player.x, position.y - player.y) <= 1.5
                      and abs(position.z - player.z) < 1.8)
            collected = not expired and nearby and self.query_collision(position + Vec3(0, 0, .2), player + Vec3(0, 0, .5)) is None
            if collected:
                self.arsenal.add_ammo(pickup.reward.kind, pickup.reward.rounds)
                self.play_sound("ammo_pickup", volume=.4)
                name = self.arsenal.weapons[pickup.reward.kind].name
                self.show_notice(f"{name}: +{pickup.reward.rounds} reserve rounds", 2)
                self.update_weapon_hud()
            if expired or collected:
                pickup.destroy()
                self.pickups.remove(pickup)

    def clear_pickups(self) -> None:
        for pickup in self.pickups:
            pickup.destroy()
        self.pickups.clear()

    def spawn_projectile(self, origin: Point3, destination: Point3, damage: int):
        direction = destination - origin
        if direction.lengthSquared() == 0:
            return
        direction.normalize()
        node = self.render.attachNewNode("spit-projectile")
        node.setPos(origin)
        model = part(node, "acid-projectile", sphere(10, 6), (0, 0, 0), (.10, .10, .10), (.15, .9, .2, 1), "metal")
        model.setLightOff(2)
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
        if not self.campaign_ready:
            super().shoot()
        elif self.can_act():
            self.trigger_held = True
            super().shoot()

    def release_trigger(self):
        self.trigger_held = False

    def toggle_audio(self):
        super().toggle_audio()
        self.show_notice("Sound on" if self.audio.enabled else "Sound muted", 2)

    def select_weapon(self, kind: WeaponKind):
        if not self.can_act() or kind is self.arsenal.selected:
            return
        self.taskMgr.remove("reload-weapon")
        self.weapon = self.arsenal.select(kind)
        self.trigger_held = False
        self.weapon_view.equip(kind)
        self.update_weapon_hud()

    def on_weapon_fired(self):
        super().on_weapon_fired()
        if self.campaign_ready:
            self.weapon_view.fire(self.weapon.damage)

    def on_targets_cleared(self):
        # Campaign statistics remain live while the uncollected core can spawn waves.
        pass

    def reload_weapon(self):
        if not self.campaign_ready or self.can_act():
            super().reload_weapon()

    def damage_target(self, target: Target, damage: int | None = None):
        if isinstance(target, Zombie):
            target.set_context(self.clock.getFrameTime(), self.reality.state)
        accepted = super().damage_target(target, damage)
        if accepted and isinstance(target, Zombie):
            self.play_sound("zombie_death" if target.health == 0 else "zombie_hurt", node=target.root,
                            volume=.75 if target.health == 0 else .55)
        if accepted and isinstance(target, Zombie) and target.health == 0 and not target.loot_dropped:
            target.loot_dropped = True
            target.died_at = self.clock.getFrameTime()
            if len(self.pickups) >= 64:
                self.pickups.pop(0).destroy()
            self.pickups.append(AmmoPickup(self.render, target.root.getPos(self.render), roll_ammo(self.random)))
        return accepted

    def update_target_hud(self):
        if not self.campaign_ready:
            super().update_target_hud()

    def restart_training(self):
        if not self.campaign_ready:
            return super().restart_training()
        self.progress.retry()
        self.load_level()

    def navigation_hint(self, destination: tuple[float, float]) -> str:
        offset = self.player.getRelativePoint(self.render, Point3(*destination, self.player.getZ()))
        distance = Vec3(offset.x, offset.y, 0).length()
        if distance <= 2:
            return "Nearby"
        if abs(offset.x) > abs(offset.y):
            direction = "right" if offset.x > 0 else "left"
        else:
            direction = "ahead" if offset.y > 0 else "behind"
        return f"{distance:.0f}m {direction}"

    def update_campaign_hud(self, task=None):
        level = self.levels[self.progress.level_index]
        remaining = self.enemies_remaining
        ready = self.progress.can_exit(remaining)
        if self.world is not None:
            self.world.set_exit_ready(ready)
        core = "Recovered" if self.progress.core_collected else f"Breach | {self.navigation_hint(level.core)}"
        exit_hint = f"{'E - Enter' if ready else 'Locked'} | {self.navigation_hint(level.exit)}"
        text = (f"Map {level.number}/{len(self.levels)}: {level.name}\n"
                f"New zombie: {level.introduced.value.title()}\nZombies remaining: {remaining}\n"
                f"Core: {core}\nExit: {exit_hint}\n"
                + ("Reinforcements: sealed" if self.director.sealed
                   else f"Wave {self.director.wave + 1} in {self.director.remaining:.0f}s"))
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


