"""Ten recognizable articulated humanoids, including an adult female Runner."""

from functools import lru_cache

from panda3d.core import NodePath

from breach_shift.art.primitives import box, flatten_local, part, rod, sphere
from breach_shift.art.library import instantiate
from breach_shift.enemies.catalog import ZOMBIE_SPECS, ZombieKind


SKIN = (.48, .49, .39, 1)
BOOTS = (.075, .067, .06, 1)
METAL = (.16, .19, .22, 1)


@lru_cache(maxsize=10)
def zombie_template(kind: ZombieKind) -> NodePath:
    root = NodePath(f"{kind.value}-model")
    root.setTag("zombie-kind", kind.value)
    root.setTag("design", "female" if kind is ZombieKind.RUNNER else "infected")
    figure = root.attachNewNode("figure")
    figure.setScale(ZOMBIE_SPECS[kind].height / 1.8)
    body = figure.attachNewNode("body")
    female = kind is ZombieKind.RUNNER
    heavy = kind in (ZombieKind.BRUTE, ZombieKind.WARDEN)
    skin = (.59, .52, .43, 1) if female else SKIN
    if kind is ZombieKind.BRUTE:
        skin = (.49, .38, .30, 1)
    elif kind in (ZombieKind.STALKER, ZombieKind.WARDEN):
        skin = (.29, .28, .32, 1)
    elif kind is ZombieKind.REGENERATOR:
        skin = (.57, .65, .57, 1)
    coat = {
        ZombieKind.WALKER: (.24, .29, .18, 1), ZombieKind.RUNNER: (.19, .19, .18, 1),
        ZombieKind.BRUTE: (.46, .24, .13, 1), ZombieKind.SPITTER: (.18, .29, .19, 1),
        ZombieKind.LEAPER: (.55, .28, .12, 1), ZombieKind.ARMORED: (.13, .20, .26, 1),
        ZombieKind.HOWLER: (.32, .12, .17, 1), ZombieKind.STALKER: (.08, .10, .13, 1),
        ZombieKind.REGENERATOR: (.60, .63, .53, 1), ZombieKind.WARDEN: (.15, .13, .19, 1),
    }[kind]
    width = .33 if heavy else (.205 if female else .235)
    trousers = tuple(channel * .65 for channel in coat[:3]) + (1,)
    part(body, "hips", sphere(), (0, 0, .86), (width * .85, .14, .17), trousers)
    part(body, "waist", sphere(), (0, -.015, 1.05), (width * .78, .14, .22), coat)
    part(body, "jacket", sphere(), (0, -.025, 1.25), (width, .16, .25), coat)
    rod(body, "neck", (0, .015, 1.39), (0, .035, 1.51), .075 if female else .09, skin, "skin")
    head_scale = (.137, .128, .19) if female else ((.18, .15, .20) if heavy else (.15, .135, .21))
    part(body, "head", sphere(), (0, .035, 1.61), head_scale, skin, "skin")
    part(body, "jaw", sphere(), (0, .055, 1.50), (.11, .11, .07), skin, "skin")
    for side in (-1, 1):
        part(body, "ear", sphere(10, 6), (side * head_scale[0], .015, 1.61), (.033, .025, .055), skin, "skin")
        part(body, "eye-socket", sphere(12, 6), (side * .055, .157, 1.65), (.038, .022, .029), (.10, .09, .08, 1), "skin")
        eye = part(body, "infected-eye", sphere(10, 6), (side * .055, .175, 1.65), (.013, .009, .013),
                   (.88, .68, .29, 1) if kind is not ZombieKind.WARDEN else (.75, .25, 1, 1), "metal")
        eye.setLightOff(1)
        rod(body, "brow", (side * .018, .16, 1.70), (side * .10, .14, 1.71), .021, skin, "skin")
    part(body, "nose", sphere(12, 6), (0, .173, 1.60), (.027, .042, .047), skin, "skin")
    part(body, "mouth", sphere(12, 6), (0, .156, 1.535), (.065, .017, .033), (.09, .045, .04, 1), "skin")
    for tooth in range(5):
        part(body, "tooth", box(), ((tooth - 2) * .018, .174, 1.548), (.012, .008, .018), (.67, .63, .44, 1), "skin")

    for side, label in ((-1, "left"), (1, "right")):
        leg = figure.attachNewNode(f"leg-{label}")
        leg.setPos(side * .12, 0, .85)
        rod(leg, "trouser-thigh", (0, 0, 0), (side * .025, .01, -.37), .105 if heavy else .075, trousers)
        part(leg, "knee", sphere(), (side * .025, .01, -.38), (.08, .075, .08), trousers)
        rod(leg, "lower-leg", (side * .025, .01, -.39), (side * .025, .025, -.70), .075 if heavy else .055, trousers)
        part(leg, "boot", sphere(), (side * .025, .075, -.77), (.10, .18, .085), BOOTS, "leather")
        if female:
            rod(leg, "mustard-stripe", (side * .07, .02, -.04), (side * .085, .04, -.66), .012, (.68, .55, .20, 1))
        flatten_local(leg)

        shoulder = side * (width + .025)
        arm = figure.attachNewNode(f"arm-{label}")
        arm.setPos(shoulder, -.015, 1.37)
        thick = .105 if heavy else .065
        elbow = (side * .07, .035, -.27)
        wrist = (side * .065, .16 if not female else (.26 if side < 0 else -.08), -.48)
        part(arm, "shoulder", sphere(), (0, 0, -.015), (thick * 1.25, thick * 1.2, thick * 1.35), coat)
        rod(arm, "sleeve", (0, 0, -.03), elbow, thick, coat)
        rod(arm, "forearm", elbow, wrist, thick * .75, skin, "skin")
        part(arm, "hand", sphere(), wrist, (thick * .85, .04, .085), skin, "skin")
        for finger in range(4):
            x = wrist[0] + (finger - 1.5) * .022
            rod(arm, "finger", (x, wrist[1] + .01, wrist[2] - .045),
                (x, wrist[1] + .065, wrist[2] - .13 + abs(finger - 1.5) * .015), .012, skin, "skin")
        if kind is ZombieKind.ARMORED:
            part(arm, "shoulder-plate", sphere(10, 6), (0, -.015, -.015), (.13, .13, .13), METAL, "metal")
        flatten_local(arm)

    if female:
        hair = (.065, .048, .038, 1)
        part(body, "hair", sphere(), (0, -.01, 1.755), (.145, .13, .065), hair, "leather")
        rod(body, "ponytail", (0, -.115, 1.75), (.035, -.24, 1.55), .055, hair, "leather")
        for side in (-1, 1):
            rod(body, "sports-jacket-stripe", (side * .16, .12, 1.40), (side * .12, .13, 1.15), .021, (.65, .52, .18, 1))
        rod(body, "zipper", (0, .15, .99), (0, .14, 1.43), .008, (.55, .54, .48, 1), "metal")
    elif kind is ZombieKind.WALKER:
        part(body, "cap", sphere(), (0, .015, 1.78), (.17, .15, .07), coat)
        part(body, "cap-peak", box(), (0, .16, 1.755), (.25, .18, .025), coat)
        for x in (-.105, .105):
            part(body, "work-pocket", box(), (x, .13, 1.26), (.09, .045, .10), (.30, .32, .21, 1))
        part(body, "id-badge", box(), (.11, .16, 1.29), (.04, .012, .055), (.68, .65, .50, 1))
    elif kind is ZombieKind.BRUTE:
        for side in (-1, 1):
            rod(body, "overall-strap", (side * .18, .13, 1.43), (side * .14, .17, 1.03), .026, trousers)
        part(body, "overall-bib", box(), (0, .145, 1.17), (.34, .065, .28), trousers)
    elif kind is ZombieKind.ARMORED:
        part(body, "riot-helmet", sphere(), (0, 0, 1.76), (.19, .17, .10), METAL, "metal")
        part(body, "visor", box(), (0, .183, 1.66), (.29, .025, .14), (.09, .13, .15, 1), "metal")
        for z in (1.10, 1.24, 1.38):
            part(body, "ballistic-plate", box(), (0, .14, z), (.38, .065, .115), METAL, "metal")
    elif kind is ZombieKind.SPITTER:
        part(body, "distended-abdomen", sphere(), (0, .05, 1.07), (.27, .23, .28), coat)
        for x, z in ((-.07, 1.43), (.07, 1.45), (0, 1.36)):
            part(body, "acid-sac", sphere(), (x, .12, z), (.07, .07, .09), (.28, .50, .12, 1), "skin")
    elif kind is ZombieKind.HOWLER:
        part(body, "open-throat", sphere(), (0, .17, 1.52), (.075, .025, .085), (.09, .025, .04, 1), "skin")
        for side in (-1, 1):
            rod(body, "neck-tendon", (side * .075, .09, 1.34), (side * .09, .10, 1.53), .027, skin, "skin")
    elif kind is ZombieKind.STALKER:
        part(body, "hood", sphere(), (0, -.04, 1.66), (.20, .17, .23), coat)
        part(body, "hood-opening", sphere(), (0, .13, 1.63), (.12, .038, .15), skin, "skin")
        for side in (-1, 1):
            part(body, "ragged-cloak", box(), (side * .16, -.14, 1.05), (.19, .065, .55), coat).setR(side * 12)
    elif kind is ZombieKind.REGENERATOR:
        for side in (-1, 1):
            part(body, "lab-coat-tail", box(), (side * .12, 0, .82), (.21, .27, .36), coat)
            rod(body, "regrowth-vein", (side * .18, .145, 1.38), (side * .13, .17, 1.11), .014, (.12, .68, .49, 1), "skin")
    elif kind is ZombieKind.WARDEN:
        for side in (-1, 1):
            for index in range(3):
                x, z = side * (.16 + .08 * index), 1.40 - .11 * index
                plate = part(body, "fused-armor", box(), (x, .14, z), (.22, .12, .19), coat, "metal")
                plate.setR(side * (18 + index * 8))
                rod(body, "armor-spike", (x, 0, z + .06), (x + side * .07, -.03, z + .32), .075, coat, "metal", top=0, segments=5)
            crack = rod(body, "breach-fracture", (side * .04, .21, 1.02), (side * .20, .22, 1.42), .015, (.65, .18, .95, 1), "metal")
            crack.setLightOff(1)
    body.flattenStrong()
    return root


def make_zombie_model(kind: ZombieKind) -> NodePath:
    return instantiate(f"characters/{kind.value}.bam", lambda: zombie_template(kind))
