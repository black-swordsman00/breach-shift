"""Platforming, combat and campaign rules without window or graphics state."""
from dataclasses import dataclass, replace
from math import atan2, cos, hypot, sin
from random import Random

from breach_shift.campaign.director import WaveDirector
from breach_shift.campaign.state import CampaignProgress
from breach_shift.combat.arsenal import Arsenal
from breach_shift.combat.catalog import WEAPON_ORDER, WeaponKind
from breach_shift.combat.loot import roll_ammo
from breach_shift.enemies.catalog import ZOMBIE_ORDER, ZOMBIE_SPECS, ZombieKind
from breach_shift.platformer.levels import Spawn, load_side_levels
from breach_shift.platformer.physics import Body, Rect, advance_body, can_stand, move_body, segment_hit
from breach_shift.player.health import PlayerHealth
from breach_shift.training.session import TrainingSession
from breach_shift.world.reality import Reality, RealityShift


@dataclass
class Controls:
    move: float = 0
    aim: tuple[float, float] = (12, 1.2)
    fire: bool = False
    fire_pressed: bool = False
    jump: bool = False
    crouch: bool = False
    shift: bool = False
    interact: bool = False
    reload: bool = False
    slot: int | None = None


@dataclass
class Enemy:
    identifier: int
    kind: ZombieKind
    body: Body
    health: float
    maximum: int
    facing: int = -1
    next_attack: float = 0
    attack_at: float = -100
    damaged_at: float = -100
    dead_at: float | None = None
    windup_until: float | None = None
    leap_until: float = 0
    phase: float = 0
    next_voice: float = 0


@dataclass
class Projectile:
    x: float
    z: float
    vx: float
    vz: float
    damage: int
    age: float = 0


@dataclass
class Pickup:
    identifier: int
    x: float
    z: float
    kind: WeaponKind
    rounds: int


@dataclass
class Trace:
    start: tuple[float, float]
    end: tuple[float, float]
    until: float
    kind: str = "shot"


class SideSession:
    speed = 7.2
    standing_height = 1.8
    crouching_height = 1.05

    def __init__(self, *, level=1, training=False, seed=None):
        self.levels = load_side_levels()
        if not 1 <= level <= len(self.levels):
            raise ValueError("Campaign map must be between 1 and 10.")
        self.training = training
        self.random = Random(seed)
        self.progress = CampaignProgress(len(self.levels))
        self.progress.level_index = level - 1
        self.health = PlayerHealth()
        self.arsenal = Arsenal()
        self.reality = RealityShift()
        self.statistics = TrainingSession()
        self.now = 0.0
        self.revision = 0
        self.events = []
        self.load_level()

    @property
    def weapon(self):
        return self.arsenal.active

    @property
    def alive(self):
        return sum(enemy.health > 0 for enemy in self.enemies.values())

    @property
    def solids(self):
        return self.level.solids(self.reality.state)

    @property
    def reload_progress(self):
        if self.reload_started is None:
            return 0.0
        return min(1, (self.now - self.reload_started) / self.weapon.reload_time)

    def notify(self, message, duration=2.4):
        self.notice, self.notice_until = message, self.now + duration

    def sound(self, cue, x=None, z=None):
        self.events.append((cue, self.player.x if x is None else x,
                            self.player.z if z is None else z))

    def load_level(self):
        self.level = self.levels[self.progress.level_index]
        if self.training:
            self.level = replace(self.level, name="Firing Range", theme="yard", width=44,
                                 platforms=(Rect(0, -3, 44, 3),), normal_gate=Rect(43, 0, .5, 14),
                                 breach_gate=Rect(43, 0, .5, 14), player_spawn=(3, 0),
                                 spawns=tuple(Spawn(ZombieKind.WALKER, x, 0) for x in (13, 23, 34)),
                                 decor=(("barrel", 8, 0, .9), ("lamp", 5, 0, 1)))
        self.revision += 1
        self.health.reset()
        self.arsenal.reset()
        self.reality.reset()
        self.statistics.reset()
        self.director = WaveDirector()
        self.player = Body(*self.level.player_spawn)
        move_body(self.player, 0, -.01, self.solids)
        self.facing = 1
        self.crouching = False
        self.jumps_used = 0
        self.coyote_until = 0
        self.reload_started = None
        self.invulnerable_until = 0
        self.player_phase = 0.0
        self.shot_at = -100.0
        self.damage_at = -100.0
        self.enemies = {}
        self.next_identifier = 0
        self.projectiles = []
        self.pickups = []
        self.traces = []
        self.events.clear()
        self.notice, self.notice_until = self.level.briefing, self.now + 7
        for spawn in self.level.spawns:
            self.spawn_enemy(spawn.kind, spawn.x, spawn.z)

    def spawn_enemy(self, kind, x, z):
        spec = ZOMBIE_SPECS[kind]
        identifier = self.next_identifier
        self.next_identifier += 1
        body = Body(x, z, spec.radius * 2, spec.height)
        move_body(body, 0, -.01, self.solids)
        enemy = Enemy(identifier, kind, body, 100 if self.training else spec.health,
                      100 if self.training else spec.health)
        enemy.next_voice = self.now + self.random.uniform(1,6)
        self.enemies[identifier] = enemy
        return enemy

    def restart(self):
        self.progress.retry()
        self.load_level()

    def hurt(self, damage):
        if not self.health.is_alive or self.now < self.invulnerable_until:
            return
        self.health.take_damage(damage)
        self.invulnerable_until = self.now + .5
        self.damage_at = self.now
        self.sound("zombie_hurt")
        if not self.health.is_alive:
            self.notify("YOU FELL  /  Press T to retry this sector", 1000)

    def damage_enemy(self, enemy, amount):
        if enemy.health <= 0:
            return False
        if enemy.kind is ZombieKind.WARDEN and self.reality.state is Reality.NORMAL:
            self.notify("WARDEN SHIELDED  /  Shift into Breach")
            return False
        if enemy.kind is ZombieKind.ARMORED:
            amount = max(1, round(amount * .65))
        enemy.health = max(0, enemy.health - amount)
        enemy.damaged_at = self.now
        self.sound("zombie_hurt" if enemy.health else "zombie_death", enemy.body.x, enemy.body.z)
        if enemy.health == 0:
            enemy.dead_at = self.now
            if enemy.body.z > -3 and not self.training:
                reward = roll_ammo(self.random)
                self.pickups.append(Pickup(enemy.identifier, enemy.body.x, enemy.body.z,
                                           reward.kind, reward.rounds))
            if self.training and self.alive == 0:
                self.statistics.finish(self.now)
                self.notify("RANGE CLEAR  /  Press T for another run", 1000)
        return True

    def shift(self):
        destination = self.level.solids(self.reality.destination)
        safe = not any(not solid.one_way and self.player.rect.overlaps(solid) for solid in destination)
        if self.reality.try_shift(self.now, safe):
            self.notify(self.reality.state.value.upper() + " REALITY")
        elif not safe:
            self.notify("SHIFT BLOCKED  /  Move away from the gate")
        else:
            self.notify(f"SHIFT RECHARGING  /  {self.reality.remaining(self.now):.1f}s")

    def interact(self):
        if self.training:
            return
        if (not self.progress.core_collected and self.reality.state is Reality.BREACH
                and hypot(self.player.x - self.level.core[0], self.player.z + .9 - self.level.core[1]) < 2):
            self.progress.collect_core()
            self.director.seal()
            self.health.heal(25)
            self.sound("ammo_pickup")
            self.notify("CORE SECURED  /  Clear the infected and extract in Normal")
        elif hypot(self.player.x - self.level.exit[0], self.player.z - self.level.exit[1]) < 2.3:
            if self.reality.state is Reality.NORMAL and self.progress.advance(self.alive):
                if self.progress.complete:
                    self.notify("BREACH CONTAINED  /  All ten sectors cleared  /  T: new campaign", 1000)
                else:
                    self.load_level()
            else:
                self.notify("EXTRACTION LOCKED  /  Core + no infected + Normal required")

    def fire(self, aim):
        if not self.weapon.try_fire(self.now):
            if not self.weapon.ammo:
                self.sound("empty")
            return
        self.shot_at = self.now
        self.statistics.record_shot(self.now)
        self.sound("fire_" + self.arsenal.selected.value)
        start = (self.player.x + self.facing * .32, self.player.z + self.player.height * .72)
        angle = atan2(aim[1] - start[1], aim[0] - start[0])
        hit_any = False
        for pellet in range(self.weapon.pellets):
            spread = (pellet - (self.weapon.pellets - 1) / 2) * self.weapon.spread
            end = (start[0] + cos(angle + spread) * self.weapon.range,
                   start[1] + sin(angle + spread) * self.weapon.range)
            nearest = 1.0
            victim = None
            for solid in self.solids:
                fraction = segment_hit(start, end, solid)
                if fraction is not None and fraction < nearest:
                    nearest = fraction
            for enemy in self.enemies.values():
                if enemy.health <= 0:
                    continue
                fraction = segment_hit(start, end, enemy.body.rect)
                if fraction is not None and fraction < nearest:
                    nearest, victim = fraction, enemy
            point = (start[0] + (end[0] - start[0]) * nearest,
                     start[1] + (end[1] - start[1]) * nearest)
            self.traces.append(Trace(start, point, self.now + .065))
            if victim is not None:
                damage = self.weapon.damage / self.weapon.pellets
                if point[1] > victim.body.z + victim.body.height * .8:
                    damage *= 1.5
                hit_any |= self.damage_enemy(victim, damage)
                self.traces.append(Trace(point, point, self.now + .22, "blood"))
        if hit_any:
            self.statistics.record_hit()

    def _move_player(self, controls, dt):
        solids = self.solids
        self.crouching = controls.crouch or (self.crouching and not can_stand(
            self.player, self.standing_height, solids))
        self.player.height = self.crouching_height if self.crouching else self.standing_height
        target_speed = max(-1, min(1, controls.move)) * self.speed * (.52 if self.crouching else 1)
        acceleration = 54 * dt
        self.player.vx += max(-acceleration, min(acceleration, target_speed - self.player.vx))
        if controls.aim[0] != self.player.x:
            self.facing = 1 if controls.aim[0] > self.player.x else -1
        if self.player.grounded:
            self.coyote_until = self.now + .09
            self.jumps_used = 0
        if controls.jump and self.jumps_used < 2:
            if not self.player.grounded and self.now > self.coyote_until:
                self.jumps_used = max(1, self.jumps_used)
            self.player.vz = 9.3
            self.player.grounded = False
            self.jumps_used += 1
        before = self.player.x
        advance_body(self.player, dt, solids)
        self.player_phase += abs(self.player.x - before) / 1.35
        if self.player.z < -8:
            self.health.take_damage(self.health.maximum)
            self.notify("YOU FELL  /  Press T to retry", 1000)

    def _clear_line(self, start, end):
        return not any(segment_hit(start, end, solid) is not None for solid in self.solids)

    def _update_enemies(self, dt):
        for enemy in tuple(self.enemies.values()):
            body, kind = enemy.body, enemy.kind
            if enemy.health <= 0:
                if self.now - enemy.dead_at > 1.3:
                    del self.enemies[enemy.identifier]
                continue
            if self.training:
                continue
            spec = ZOMBIE_SPECS[kind]
            dx = self.player.x - body.x
            enemy.facing = 1 if dx > 0 else -1
            start, target = (body.x, body.z + body.height * .65), (self.player.x, self.player.z + self.player.height * .6)
            visible = abs(dx) < 32 and self._clear_line(start, target)
            if visible and abs(dx)<16 and self.now>=enemy.next_voice:
                self.sound("zombie_idle",body.x,body.z)
                enemy.next_voice = self.now + self.random.uniform(4,9)
            melee_reach = 1.05 if kind is ZombieKind.SPITTER else spec.reach
            in_reach = visible and abs(dx) < melee_reach and abs(self.player.z - body.z) < 1.3
            if enemy.windup_until is not None:
                if self.now >= enemy.windup_until:
                    enemy.windup_until = None
                    enemy.attack_at = self.now
                    if visible and abs(dx) < 4.5 and self.player.z - body.z < .65:
                        self.hurt(spec.damage)
                    self.sound("zombie_roar", body.x, body.z)
                body.vx = 0
            elif in_reach and self.now >= enemy.next_attack:
                enemy.next_attack = self.now + spec.interval
                enemy.attack_at = self.now
                if kind is ZombieKind.WARDEN:
                    enemy.windup_until = self.now + .65
                    self.notify("WARDEN STOMP  /  JUMP!", .8)
                else:
                    self.hurt(spec.damage)
                    self.sound("zombie_attack", body.x, body.z)
            if kind is ZombieKind.SPITTER and visible and 2 < abs(dx) < 16 and self.now >= enemy.next_attack:
                enemy.next_attack = self.now + spec.interval
                enemy.attack_at = self.now
                distance = max(.01, hypot(target[0] - start[0], target[1] - start[1]))
                self.projectiles.append(Projectile(*start, (target[0] - start[0]) / distance * 9,
                                                   (target[1] - start[1]) / distance * 9, spec.damage))
                self.sound("zombie_attack", body.x, body.z)
            if kind is ZombieKind.HOWLER and visible and abs(dx) < 13 and self.now >= enemy.next_attack:
                enemy.next_attack = self.now + 6
                enemy.attack_at = self.now
                self.sound("zombie_howl", body.x, body.z)
            if kind is ZombieKind.REGENERATOR and self.now - enemy.damaged_at > 4:
                enemy.health = min(enemy.maximum, enemy.health + dt * 5)
            if enemy.windup_until is None:
                speed = spec.speed * 1.5 * (1.2 if self.reality.state is Reality.BREACH else 1)
                if any(other.health > 0 and other.kind is ZombieKind.HOWLER
                       and self.now - other.attack_at < 4 and abs(other.body.x - body.x) < 9
                       for other in self.enemies.values()):
                    speed *= 1.25
                body.vx = 0 if in_reach or abs(dx) > 38 else enemy.facing * speed
                if kind is ZombieKind.SPITTER and visible and 2 < abs(dx) < 10:
                    body.vx = 0
                if enemy.leap_until > self.now:
                    body.vx = enemy.facing * 7.5
                ahead = body.x + enemy.facing * 1.1
                supported = any(solid.x <= ahead <= solid.right and body.z - 3 <= solid.top <= body.z + .1
                                for solid in self.solids)
                if body.grounded and not supported:
                    if kind is ZombieKind.LEAPER:
                        body.vz, body.grounded, enemy.leap_until = 10, False, self.now + .9
                    else:
                        body.vx = 0
                elif kind is ZombieKind.LEAPER and body.grounded and visible and 2 < abs(dx) < 8 and self.now >= enemy.next_attack:
                    body.vz, body.grounded, enemy.leap_until = 9.3, False, self.now + .8
                    enemy.next_attack = self.now + spec.interval
            previous_x = body.x
            blocked, _ = advance_body(body, dt, self.solids)
            enemy.phase += abs(body.x - previous_x) / max(.8, body.height * .65)
            if blocked and body.grounded and any(
                    not solid.one_way and 0 < solid.top - body.z < 2.4
                    and abs((solid.x if enemy.facing > 0 else solid.right) - body.x) < body.width / 2 + .12
                    for solid in self.solids):
                body.vz, body.grounded = 9.3, False
            if body.z < -8:
                enemy.health, enemy.dead_at = 0, self.now

    def _update_projectiles(self, dt):
        for projectile in tuple(self.projectiles):
            start = (projectile.x, projectile.z)
            end = (projectile.x + projectile.vx * dt, projectile.z + projectile.vz * dt)
            walls = [hit for solid in self.solids if (hit := segment_hit(start, end, solid)) is not None]
            player_hit = segment_hit(start, end, self.player.rect)
            if player_hit is not None and player_hit < min(walls, default=2):
                self.hurt(projectile.damage)
                self.projectiles.remove(projectile)
            elif walls or projectile.age > 5:
                self.projectiles.remove(projectile)
            else:
                projectile.x, projectile.z = end
                projectile.age += dt

    def _reinforce(self, dt):
        if self.training:
            return
        count = self.director.advance(dt, self.alive)
        for _ in range(count):
            kind = self.random.choice(ZOMBIE_ORDER[:self.level.number])
            if kind is ZombieKind.WARDEN:
                kind = ZombieKind.WALKER
            # Reuse authored safe spawn points, away from the player's body.
            candidates = [spawn for spawn in self.level.spawns if abs(spawn.x - self.player.x) > 8
                          and not any(not solid.one_way and Body(spawn.x, spawn.z,
                                     ZOMBIE_SPECS[kind].radius * 2, ZOMBIE_SPECS[kind].height).rect.overlaps(solid)
                                     for solid in self.solids)]
            if candidates:
                spawn = self.random.choice(candidates)
                self.spawn_enemy(kind, spawn.x, spawn.z)
        if count:
            self.notify(f"RIFT WAVE {self.director.wave}  /  Recover the core to stop reinforcements")

    def step(self, controls: Controls, dt: float):
        if dt <= 0 or not self.health.is_alive or self.progress.complete:
            return
        dt = min(dt, .05)
        self.now += dt
        self.traces = [trace for trace in self.traces if trace.until > self.now]
        if controls.slot is not None:
            self.arsenal.select(WEAPON_ORDER[controls.slot])
            self.reload_started = None
        self._move_player(controls, dt)
        if not self.health.is_alive:
            return
        if controls.shift:
            self.shift()
        if controls.reload and self.weapon.start_reload():
            self.reload_started = self.now
            self.sound("reload_start")
        if self.weapon.is_reloading and self.reload_progress >= 1:
            self.weapon.finish_reload()
            self.reload_started = None
            self.sound("reload_finish")
        if controls.fire and (self.weapon.automatic or controls.fire_pressed):
            self.fire(controls.aim)
        self._update_enemies(dt)
        self._update_projectiles(dt)
        for pickup in tuple(self.pickups):
            if hypot(pickup.x - self.player.x, pickup.z - self.player.z) < 1.35:
                self.arsenal.add_ammo(pickup.kind, pickup.rounds)
                self.pickups.remove(pickup)
                self.sound("ammo_pickup")
        self._reinforce(dt)
        if controls.interact and self.health.is_alive:
            self.interact()
