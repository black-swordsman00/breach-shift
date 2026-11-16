"""Load weapon assets and animate the first-person view."""

from math import exp, isfinite, pi, sin

from panda3d.core import AmbientLight, BitMask32, DepthOffsetAttrib, DirectionalLight, NodePath

from breach_shift.art.primitives import part, rod, sphere
from breach_shift.art.library import instantiate, metadata
from breach_shift.combat.catalog import WeaponKind
from breach_shift.art.motion import smoothstep


MUZZLES = {WeaponKind.PISTOL: .38, WeaponKind.SMG: .60, WeaponKind.RIFLE: .96, WeaponKind.SHOTGUN: 1.05}


def make_weapon_model(kind: WeaponKind) -> NodePath:
    model = instantiate(f"weapons/{kind.value}.bam")
    model.setName(f"{kind.value}-model")
    model.setTag("weapon-kind", kind.value)
    profile = metadata(f"weapons/{kind.value}.json")
    if profile.get("provider"):
        model.setTag("provider", profile["provider"])
    return model


def muzzle_position(kind: WeaponKind) -> tuple[float, float, float]:
    position = metadata(f"weapons/{kind.value}.json").get("muzzle", (0, MUZZLES[kind], .055))
    if len(position) != 3 or not all(isfinite(value) for value in position):
        raise ValueError(f"Invalid muzzle position for {kind.value}")
    return tuple(position)


def _arms(parent, kind):
    sleeve, glove = (.20, .23, .18, 1), (.075, .07, .06, 1)
    support = .08 if kind is WeaponKind.PISTOL else (.47 if kind is WeaponKind.SHOTGUN else .29)
    pivots = {}
    for label, hand, elbow in (
        ("right", (.040, -.015, -.12), (.18, -.31, -.42)),
        ("left", (-.025, support, -.105), (-.20, -.22, -.43)),
    ):
        pivot = parent.attachNewNode(label+"-forearm")
        pivots[label] = pivot
        rod(pivot, f"{label}-sleeve", elbow, (hand[0], hand[1] - .05, hand[2] - .02), .048, sleeve, top=.76)
        part(pivot, f"{label}-glove", sphere(), hand, (.033, .052, .027), glove, "leather")
        part(pivot, f"{label}-knuckle-padding", sphere(12,8),
             (hand[0],hand[1]-.005,hand[2]+.024), (.03,.035,.008), (.11,.115,.10,1), "leather")
        for index in range(4):
            x = hand[0] + (index - 1.5) * .014
            rod(pivot, "gloved-finger", (x, hand[1] + .02, hand[2]), (x, hand[1] + .045, hand[2] + .018), .008, glove, "leather")
            rod(pivot, "curled-fingertip", (x, hand[1]+.045,hand[2]+.018),
                (x,hand[1]+.034,hand[2]+.032),.007,glove,"leather")
        rod(pivot,"gloved-thumb",(hand[0]-.024,hand[1]-.015,hand[2]),
            (hand[0]-.032,hand[1]+.02,hand[2]+.02),.012,glove,"leather")
        pivot.flattenStrong()
    return pivots


def reload_pose(progress, shotgun=False):
    """Smooth key poses: lower, reach for ammo, insert, work action, recover."""
    keys = ((0,(0,0,0,0,0)), (.16,(10,-27,.02,-.10,-.08)),
            (.38,(16,-34,.07,-.24,-.24)), (.62,(14,-31,.03,-.02,-.09)),
            (.80,(7,-20,.05,.08,.04)), (1,(0,0,0,0,0)))
    for (start,a),(end,b) in zip(keys,keys[1:]):
        if progress <= end:
            t=smoothstep((progress-start)/(end-start))
            pose=tuple(x+(y-x)*t for x,y in zip(a,b))
            if shotgun and .20 < progress < .80:
                pitch,roll,x,y,z=pose
                cycle=sin((progress-.2)/.6*pi*6)
                return pitch,roll,x,y-.035*cycle,z+.035*cycle
            return pose
    return keys[-1][1]


class WeaponView:
    def __init__(self, camera: NodePath, kind: WeaponKind) -> None:
        self.root = camera.attachNewNode("first-person-weapon")
        self.root.hide(BitMask32.bit(6))
        self.root.setScale(.78)
        self.root.setBin("fixed", 40)
        self.root.setDepthTest(True)
        self.root.setDepthWrite(True)
        # Compress viewmodel depth into the near slice: world walls cannot cut
        # through it, while front/back triangles still occlude one another.
        self.root.setAttrib(DepthOffsetAttrib.make(0, 0.0, .1))
        ambient = AmbientLight("weapon-fill")
        ambient.setColor((.72, .75, .77, 1))
        key = DirectionalLight("weapon-key")
        key.setColor((.8, .75, .65, 1))
        self.root.setLightOff(1)
        self.root.setLight(camera.attachNewNode(ambient), 2)
        key_node = camera.attachNewNode(key)
        key_node.setHpr(-35, -40, 0)
        self.root.setLight(key_node, 2)
        self.kick = 0.0
        self.time = 0.0
        self.flash_time = 0.0
        self.reload_started = None
        self.reload_duration = 1.0
        self.reload_progress = 0.0
        self.move_blend = 0.0
        self.sway = (0.0, 0.0)
        self.equip(kind)

    def equip(self, kind: WeaponKind) -> None:
        for child in self.root.getChildren():
            child.removeNode()
        self.kind = kind
        make_weapon_model(kind).reparentTo(self.root)
        arms = self.root.attachNewNode("player-arms")
        self.hands = _arms(arms, kind)
        muzzle_x, muzzle_y, muzzle_z = muzzle_position(kind)
        self.flash = part(self.root, "muzzle-flash", sphere(8, 4), (muzzle_x, muzzle_y + .025, muzzle_z),
                          (.045, .13, .045), (1, .65, .13, 1), "metal")
        self.flash.setLightOff(3)
        self.flash.hide()
        self.kick = self.flash_time = 0.0
        self.reload_started = None
        self.reload_progress = 0.0
        self.draw_time = 0.0
        self.update(0, False)

    def fire(self, damage: int) -> None:
        self.kick = min(.10, .035 + damage * .0005)
        self.flash_time = .045
        self.flash.show()

    def start_reload(self, duration, now=None):
        self.reload_duration = max(.01,duration)
        self.reload_started = self.time if now is None else now
        self.reload_progress = 0.0
        self.kick = self.flash_time = 0.0
        self.flash.hide()

    def finish_reload(self):
        self.reload_started = None
        self.reload_progress = 0.0
        self.hands['left'].setPos(0,0,0)
        self.hands['left'].setHpr(0,0,0)

    def update(self, dt: float, moving: bool, *, now=None, crouching=False,
               turn=(0.0,0.0), vertical_speed=0.0) -> None:
        dt = max(0,dt)
        self.time += max(0, dt)
        self.draw_time += dt
        self.kick *= exp(-16 * max(0, dt))
        self.flash_time -= max(0, dt)
        if self.flash_time <= 0:
            self.flash.hide()
        self.move_blend += ((1 if moving else 0)-self.move_blend)*(1-exp(-12*dt))
        self.sway=tuple(a+(max(-8,min(8,b))-a)*(1-exp(-14*dt)) for a,b in zip(self.sway,turn))
        bob = sin(self.time*(7 if crouching else 10))*(.003 if crouching else .006)*self.move_blend
        bob += sin(self.time*1.8)*.0015
        draw = 1-smoothstep(self.draw_time/.28)
        pitch=roll=hand_x=hand_y=hand_z=0.0
        if self.reload_started is not None:
            time=self.time if now is None else now
            self.reload_progress=max(0,min(1,(time-self.reload_started)/self.reload_duration))
            pitch,roll,hand_x,hand_y,hand_z=reload_pose(self.reload_progress,self.kind is WeaponKind.SHOTGUN)
        self.hands['left'].setPos(hand_x,hand_y,hand_z)
        self.hands['left'].setHpr(roll*.15, -hand_z*55,roll*.25)
        landing=max(-2,min(2,vertical_speed))*.55
        self.root.setPos(.21-self.sway[0]*.001-abs(roll)*.002, .57-self.kick,
                         -.265+bob-draw*.20+abs(roll)*.003)
        self.root.setHpr(-2-self.sway[0]*.12, self.kick*50+pitch+landing-self.sway[1]*.1,
                         roll+draw*12+sin(self.time*5)*self.move_blend*.35)
