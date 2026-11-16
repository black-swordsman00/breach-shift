"""Distance driven gait and blended combat poses for articulated enemies."""
from math import atan2, degrees, exp, hypot, pi, sin

from panda3d.core import Point3, Vec3


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value*value*(3-2*value)


class ZombieMotion:
    def __init__(self, root, model, height, *, runner=False, heavy=False):
        self.root, self.model, self.height = root, model, height
        self.runner, self.heavy = runner, heavy
        names = ['hips', 'spine', 'head']
        names += [f'{limb}-{side}' for side in ('left', 'right')
                  for limb in ('arm', 'forearm', 'hand', 'leg', 'shin', 'foot')]
        self.joints = {name:model.find('**/'+name) for name in names}
        self.rest = {name:Vec3(node.getHpr()) for name,node in self.joints.items() if not node.isEmpty()}
        self.position = Point3(root.getPos())
        self.phase = 0.0
        self.time = 0.0
        self.moving = 0.0
        self.speed = 0.0
        self.death_time = 0.0
        low,high=model.getTightBounds()
        self.death_lift=max(abs(low.y),abs(high.y))*.97

    def pose(self, name, *, heading=0, pitch=0, roll=0):
        if name in self.rest:
            self.joints[name].setHpr(self.rest[name]+Vec3(heading, pitch, roll))

    def update(self, dt, player, now, *, windup=None, attack=-100, dead=False):
        dt = max(0, dt)
        self.time += dt
        position = self.root.getPos()
        travel_x,travel_y=position.x-self.position.x,position.y-self.position.y
        distance = hypot(travel_x,travel_y)
        self.position = Point3(position)
        if dead:
            self.death_time += dt
            fall = smoothstep(self.death_time/.85)
            self.model.setP(86*fall)
            self.model.setZ(self.death_lift*fall)
            for side in ('left', 'right'):
                self.pose('arm-'+side, pitch=-24*fall)
                self.pose('leg-'+side, pitch=12*fall)
                self.pose('shin-'+side, pitch=-22*fall)
            return
        blend = 1-exp(-10*dt)
        measured = min(5, distance/max(dt, .001))
        self.speed += (measured-self.speed)*blend
        self.moving += ((1 if distance > .0001 else 0)-self.moving)*blend
        stride = self.height*(.63 if self.runner else .48)
        # A stationary enemy never cycles its walk, including against a wall.
        self.phase += distance/stride * 2*pi
        dx, dy = player.x-position.x, player.y-position.y
        if distance>.0001 and windup is None and now-attack>.45:
            dx,dy=travel_x,travel_y
        if hypot(dx, dy) > .01:
            wanted = degrees(atan2(-dx, dy))
            delta = (wanted-self.root.getH()+180)%360-180
            self.root.setH(self.root.getH()+delta*(1-exp(-(7 if self.heavy else 11)*dt)))
        gait = sin(self.phase)*self.moving
        sway = sin(self.phase)*(.7 if self.heavy else 1.5)*self.moving
        breath = sin(self.time*2.2)*.6
        wind = .0 if windup is None else smoothstep(1-max(0, windup-now)/.65)
        strike = max(0, 1-max(0, now-attack)/(.65 if self.heavy else .45))
        strike = sin(strike*pi)
        self.model.setZ(abs(sin(self.phase))*.012*self.moving + sin(self.time*2.2)*.002)
        self.model.setR(sway*.35)
        self.pose('hips', heading=gait*2, roll=sway)
        self.pose('spine', heading=-gait*3, pitch=3+self.speed*.7+strike*10-wind*7, roll=-sway*.65)
        self.pose('head', heading=gait*1.2, pitch=breath-2, roll=-sway*.5)
        for index,side in enumerate(('left', 'right')):
            wave = gait * (-1 if index else 1)
            swing = wave*(29 if self.runner else 21)
            knee = max(0, -wave)*(45 if self.runner else 30)
            if position.z > .05:
                swing,knee=-28,55
            self.pose('leg-'+side, pitch=swing+wind*8)
            self.pose('shin-'+side, pitch=-knee-wind*16)
            self.pose('foot-'+side, pitch=knee*.55-swing*.3)
            self.pose('arm-'+side, pitch=-8-swing*.65-wind*65-strike*48,
                      roll=(-1 if index else 1)*(3+wind*6))
            self.pose('forearm-'+side, pitch=-10-max(0,wave)*18-wind*20-strike*18)
            self.pose('hand-'+side, pitch=-breath*2)
