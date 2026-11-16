"""Build editable infected characters. Run with Blender --background --python ... -- --kind walker."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_tools import box, empty, material, mesh, save_asset, sphere, studio, tube
from human_source import SOURCE_COMMIT, apply_targets, group_center, read_obj
from skin_paint import paint_skin

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets/source/makehuman"


class Infected:
    def __init__(self, spec):
        self.spec, self.kind, self.height = spec, spec["kind"], spec["height"]
        self.name = self.kind.title()
        self.rng = random.Random(spec["seed"])
        raw, self.uv, self.groups = read_obj(SOURCE / "base.obj")
        sex, age = spec["sex"], spec["age"]
        targets = [(SOURCE / f"caucasian-{sex}-{age}.target", 1),
                   (SOURCE / f"universal-{sex}-{age}-{spec['physique']}.target", 1),
                   (SOURCE / "mouth-open.target", spec["mouth"])]
        raw = apply_targets(raw, targets)
        body_indices = {i for face, _uv in self.groups["body"] for i in face}
        self.body_indices = body_indices
        low, high = min(raw[i][1] for i in body_indices), max(raw[i][1] for i in body_indices)
        self.scale = self.height / (high - low)
        def convert(vertex):
            x, y, z = vertex
            return Vector((-x * self.scale, z * self.scale, (y - low) * self.scale))
        self.points = [convert(vertex) for vertex in raw]
        self.joints = {key: convert(group_center(raw, faces)) for key, faces in self.groups.items() if key.startswith("joint-")}
        self.root = empty("HERO_" + self.name)
        self.root["enemy_kind"], self.root["design_name"] = self.kind, spec["name"]
        self.root["source_license"] = "CC0 anatomy + original Breach Shift clothing and mutations"
        self.root["source_commit"] = SOURCE_COMMIT
        self.pivots = {"body": empty(self.name + "_body", self.root)}
        for limb, helper in (("arm", "shoulder"), ("leg", "upper-leg")):
            for side, short in (("left", "l"), ("right", "r")):
                self.pivots[limb + "_" + side] = empty(self.name + "_" + limb + "_" + side, self.root,
                                                       self.joints["joint-" + short + "-" + helper])
        self.mats = {
            "skin": material(self.name + "_necrotic_skin", spec["skin"], "skin", .78),
            "jacket": material(self.name + "_weathered_cloth", spec["jacket"]),
            "pants": material(self.name + "_torn_trousers", spec["trousers"]),
            "leather": material(self.name + "_cracked_boots", (.040, .033, .025), "leather", .62),
            "metal": material(self.name + "_oxidized_metal", (.12, .14, .15), "metal", .45, .7),
            "blood": material(self.name + "_dried_blood", (.095, .014, .012), "skin", .68),
            "accent": material(self.name + "_accent", spec["accent"], "fabric", .7),
            "eye": material(self.name + "_clouded_cornea", (.55, .60, .48), "skin", .22),
            "pupil": material(self.name + "_dark_iris", (.065, .08, .048), "skin", .32),
            "teeth": material(self.name + "_aged_teeth", (.47, .40, .25), "skin", .55),
            "hair": material(self.name + "_matted_hair", (.028, .021, .017), "fabric", .9),
        }
        paint_skin(self)
        self.make_surface()
        self.make_eyes()
        self.details()
        self.pose()

    def region(self, center):
        x, _y, z = center
        shoulder = abs(self.joints["joint-l-shoulder"].x)
        hip = self.joints["joint-l-upper-leg"].z
        threshold = shoulder * (.98 if z > self.height * .70 else 1.35)
        if abs(x) > threshold and z > self.height * .43:
            return "arm_left" if x < 0 else "arm_right"
        if z < hip + self.height * .01:
            return "leg_left" if x < 0 else "leg_right"
        return "body"

    def surface(self, name, selected, mat, offset=0, rough=False):
        chunks = {}
        for face, source_uv in selected:
            center = sum((self.points[index] for index in face), Vector()) / len(face)
            region = self.region(center)
            vertices, faces, uv = chunks.setdefault(region, ([], [], []))
            start = len(vertices)
            normal = (self.points[face[1]] - self.points[face[0]]).cross(self.points[face[2]] - self.points[face[0]]).normalized()
            pivot = self.pivots[region].location if region != "body" else Vector()
            for index, uv_index in zip(face, source_uv):
                point = self.points[index].copy()
                # Surface offsets use a shared vertex normal, avoiding cracks between quads.
                n = self.normals[index]
                fold = (.0025 * math.sin(point.z * 145 + point.x * 23) if rough else 0)
                point += n * (offset + fold)
                vertices.append(point - pivot)
                uv.append(self.uv[uv_index] if uv_index >= 0 else (point.x, point.z))
            faces.append(tuple(range(start, len(vertices))))
        for region, (vertices, faces, uv) in chunks.items():
            obj = mesh(self.name + "_" + name + "_" + region, vertices, faces, mat, self.pivots[region], uv)
            # Source topology is welded before export so normals remain continuous.
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            weld = obj.modifiers.new("Weld garment panels", "WELD")
            weld.merge_threshold = .00005
            bpy.ops.object.modifier_apply(modifier=weld.name)
            obj.select_set(False)

    def make_surface(self):
        self.normals = [Vector() for _ in self.points]
        for face, _uv in self.groups["body"]:
            n = (self.points[face[1]] - self.points[face[0]]).cross(self.points[face[2]] - self.points[face[0]])
            for index in face:
                self.normals[index] += n
        self.normals = [n.normalized() for n in self.normals]
        skin, coat, trousers, boots, scalp = [], [], [], [], []
        for face_uv in self.groups["body"]:
            face = face_uv[0]
            c = sum((self.points[i] for i in face), Vector()) / len(face)
            z = c.z / self.height
            arm = self.region(c).startswith("arm")
            # All delivered characters are clothed. Hands, neck and head remain exposed.
            if z < .07:
                boots.append(face_uv)
            elif z < .49:
                trousers.append(face_uv)
            elif z < .83 and not (arm and abs(c.x) > abs(self.joints["joint-l-elbow"].x) * 1.04):
                coat.append(face_uv)
            else:
                skin.append(face_uv)
            hairline = .946 + .005 * math.sin(c.x * 230)
            if (z > hairline or (z > .92 and c.y < self.joints["joint-head"].y - .012)) and (
                    self.spec["style"] != "worker" or c.y < self.joints["joint-head"].y + .015):
                scalp.append(face_uv)
        self.surface("anatomy", skin, self.mats["skin"])
        self.surface("jacket", coat, self.mats["jacket"], .014, True)
        self.surface("trousers", trousers, self.mats["pants"], .012, True)
        self.surface("boots", boots, self.mats["leather"], .014)
        if self.spec["style"] not in ("riot", "boss", "brute"):
            self.surface("hair", scalp, self.mats["hair"], .003)

    def local(self, point, region="body"):
        return Vector(point) - (self.pivots[region].location if region != "body" else Vector())

    def bulb(self, name, position, scale, mat="blood", region="body"):
        return sphere(self.name + "_" + name, self.local(position, region), scale, self.mats[mat], self.pivots[region])

    def seam(self, name, points, width=.002, mat="accent", region="body"):
        return tube(self.name + "_" + name, [self.local(p, region) for p in points], width,
                    self.mats[mat], self.pivots[region], sides=8)

    def panel(self, name, center, dimensions, mat="jacket", region="body", bevel=.004):
        if region == "body" and center[1] > 0:
            center = self.front(center, dimensions[1] / 2 + .019)
        return box(self.name + "_" + name, self.local(center, region), dimensions,
                   self.mats[mat], self.pivots[region], bevel)

    def front(self, point, clearance=.021):
        x, y, z = point
        nearby = [self.points[i].y for i in self.body_indices if abs(self.points[i].z - z) < self.height * .018 and abs(self.points[i].x - x) < self.height * .018]
        return (x, max(nearby) + clearance if nearby else y, z)

    def make_eyes(self):
        for side in ("l", "r"):
            center = self.joints["joint-" + side + "-eye"].copy()
            radius = self.height * .0077
            self.bulb("clouded_eye_" + side, center, (radius, radius, radius), "eye")
            self.bulb("iris_" + side, center + Vector((0, radius * .96, 0)), (radius * .36, radius * .10, radius * .36), "pupil")
            # A narrow irregular blood trail sits on the cheek, not a floating eyeball ring.
            cheek = center + Vector((0, .009, -.025))
            self.seam("tear_" + side, [cheek, cheek + Vector((.003, -.008, -.025)), cheek + Vector((.006, -.015, -.045))], .0016, "blood")
        mouth = self.joints["joint-mouth"].copy()
        mouth.y += .045 * self.height
        for index in range(6):
            self.bulb("broken_tooth_" + str(index), mouth + Vector(((index - 2.5) * .008, -.014, -.010)), (.003, .004, .006), "teeth")

    def details(self):
        h = self.height
        body = self.pivots["body"]
        # Construct a proper standing collar and opened jacket front with asymmetrical lapels.
        neck = self.joints["joint-neck"]
        for sign in (-1, 1):
            collar = [(sign * .061, neck.y - .038, neck.z + .009),
                      (sign * .056, neck.y + .052, neck.z - .020),
                      (sign * .09, neck.y + .085, neck.z - .089),
                      (sign * .090, neck.y - .031, neck.z - .036)]
            mesh(self.name + "_folded_collar", collar, [(0, 1, 2, 3), (3, 2, 1, 0)], self.mats["jacket"], body)
            self.seam("lapel", [self.front(p) for p in [(sign * .085, .12, h * .77), (sign * .035, .145, h * .64), (sign * .027, .13, h * .50)]], .002)
            self.panel("chest_pocket", (sign * .10, .14, h * .70), (.075, .018, .09))
            self.seam("pocket_flap", [self.front(p, .038) for p in [(sign * .14, .153, h * .718), (sign * .10, .16, h * .704), (sign * .062, .153, h * .718)]], .002)
        for index in range(5):
            self.bulb("rusted_fastener", self.front((.019, .148, h * (.52 + index * .045)), .023), (.0035, .002, .0035), "metal")
        waist = [self.points[i] for i in self.body_indices if abs(self.points[i].z - h * .49) < h * .012]
        rx = max(abs(p.x) for p in waist) + .017
        low_y, high_y = min(p.y for p in waist), max(p.y for p in waist)
        cy, ry = (low_y + high_y) / 2, (high_y - low_y) / 2 + .017
        belt_vertices = [(rx * math.cos(a * math.tau / 48), cy + ry * math.sin(a * math.tau / 48), h * .49 + dz)
                         for dz in (-.014, .014) for a in range(48)]
        belt_faces = [(i, (i + 1) % 48, (i + 1) % 48 + 48, i + 48) for i in range(48)]
        mesh(self.name + "_waist_belt", belt_vertices, belt_faces, self.mats["leather"], body)
        self.panel("belt_buckle", (.015, .135, h * .485), (.031, .012, .030), "metal")
        for side, short, sign in (("left", "l", -1), ("right", "r", 1)):
            region = "leg_" + side
            ankle = self.joints["joint-" + short + "-ankle"]
            # Sculpted boots follow the anatomical foot and have sole layers, heel and laces.
            foot = [self.points[i] for i in self.body_indices if self.points[i].z < h * .045 and (self.points[i].x < 0 if sign < 0 else self.points[i].x > 0)]
            front, back = max(p.y for p in foot), min(p.y for p in foot)
            mid, length = (front + back) / 2, front - back
            self.bulb("boot_toe", (ankle.x, mid + length * .12, .060), (.068, length * .57, .060), "leather", region)
            self.panel("boot_sole", (ankle.x, mid, .024), (.14, length + .04, .034), "leather", region, .017)
            for index in range(5):
                y = mid + length * (.06 + index * .035)
                self.seam("boot_lacing", [(ankle.x - .025, y, .112), (ankle.x + .025, y + .009, .114)], .0018, "leather", region)
            knee = self.joints["joint-" + short + "-knee"]
            self.panel("frayed_knee_patch", (knee.x, knee.y + .067, knee.z), (.071, .011, .075), "accent", region)
            # Small cloth rips use dark backing and exposed, irregular red edges.
            self.seam("torn_sleeve", [(sign * .27, .02, h * .69), (sign * .28, .025, h * .65), (sign * .30, .023, h * .64)], .006, "blood", "arm_" + side)
        eye = self.joints["joint-l-eye"]
        self.seam("facial_laceration", [(eye.x + .016, eye.y + .013, eye.z + .013),
                     (eye.x + .025, eye.y + .018, eye.z - .025),
                     (eye.x + .045, eye.y - .010, eye.z - .061)], .0023, "blood")
        self.style_details()

    def style_details(self):
        style, h = self.spec["style"], self.height
        if style == "worker":
            self.panel("name_patch", (-.10, .157, h * .74), (.067, .008, .022), "accent")
            self.panel("hanging_radio", (.15, .14, h * .51), (.039, .033, .065), "metal")
            self.seam("radio_aerial", [(.15, .14, h * .53), (.15, .14, h * .60)], .003, "metal")
        elif style == "runner":
            head = self.joints["joint-head"]
            self.seam("pony_tail", [(0, head.y - .07, h * .95), (.02, head.y - .13, h * .91), (.03, head.y - .10, h * .82)], .026, "hair")
            for sign in (-1, 1):
                self.seam("reflective_track_stripe", [(sign * .12, .135, h * .73), (sign * .12, .15, h * .62), (sign * .11, .12, h * .51)], .007)
        elif style in ("riot", "boss"):
            width = h * (.092 if style == "riot" else .105)
            center = self.front((0, .14, h * .70), .035)
            # A clipped, curved ballistic plate rather than a solid rectangular box.
            outline = [(-.65, 1), (.65, 1), (1, .68), (1, -.70), (.65, -1), (-.65, -1), (-1, -.70), (-1, .68)]
            verts = [(x * width, center[1] + depth - .035 * abs(x), center[2] + z * h * .105)
                     for depth in (0, .025) for x, z in outline]
            faces = [tuple(reversed(range(8))), tuple(range(8, 16))] + [(i, (i + 1) % 8, (i + 1) % 8 + 8, i + 8) for i in range(8)]
            mesh(self.name + "_curved_ballistic_plate", verts, faces, self.mats["metal"], self.pivots["body"])
            for sign, side in ((-1, "left"), (1, "right")):
                shoulder = self.joints["joint-" + ("l" if sign < 0 else "r") + "-shoulder"]
                self.panel("shoulder_guard", shoulder + Vector((sign * .02, .015, .015)), (.14, .17, .09), "metal", "arm_" + side, .025)
            eye = self.joints["joint-l-eye"]
            helmet_v, helmet_f = [], []
            for ring in range(9):
                latitude = ring / 8 * math.pi / 2
                for i in range(40):
                    a = i * math.tau / 40
                    helmet_v.append((h * .059 * math.cos(latitude) * math.sin(a),
                                     eye.y - h * .027 + h * .067 * math.cos(latitude) * math.cos(a),
                                     eye.z + h * .017 + h * .062 * math.sin(latitude)))
                    if ring:
                        j = ring * 40 + i
                        helmet_f.append((j - 40, ring * 40 + (i + 1) % 40 - 40, ring * 40 + (i + 1) % 40, j))
            mesh(self.name + "_open_face_helmet", helmet_v, helmet_f, self.mats["metal"], self.pivots["body"])
            self.panel("helmet_brow", (0, eye.y + .09, eye.z + h * .019), (h * .12, .045, .016), "metal", bevel=.008)
            for index in range(4):
                box(self.name + "_vest_webbing", (0, center[1] + .029, h * (.62 + index * .034)),
                    (width * 1.65, .008, .012), self.mats["leather"], self.pivots["body"], .002)
            for sign in (-1, 1):
                self.panel("waist_ammo_pouch", (sign * width * .65, .15, h * .54), (.07, .05, .09), "leather", bevel=.012)
        elif style == "spitter":
            neck = self.joints["joint-neck"]
            for index in range(7):
                p = neck + Vector((self.rng.uniform(-.045, .045), self.rng.uniform(.025, .075), self.rng.uniform(-.14, .015)))
                self.bulb("infected_throat_sac", p, (.035, .03, .035), "accent")
            self.seam("saliva", [(0, .175, h * .88), (.01, .18, h * .82), (.014, .17, h * .78)], .0025, "accent")
        elif style == "brute":
            for sign in (-1, 1):
                self.seam("overall_strap", [(sign * .16, .06, h * .80), (sign * .11, .19, h * .64), (sign * .10, .15, h * .51)], .022)
            self.panel("overall_bib", (0, .18, h * .59), (.22, .028, .23), "accent", bevel=.015)
        elif style == "howler":
            neck = self.joints["joint-neck"]
            self.bulb("distended_throat", neck + Vector((0, .045, -.035)), (.048, .035, .065), "blood")
            for sign in (-1, 1):
                self.seam("taut_throat_tendon", [(sign * .055, .105, h * .89), (sign * .04, .11, h * .80), (sign * .10, .12, h * .75)], .008, "skin")
        elif style == "stalker":
            head = self.joints["joint-head"]
            # Open cowl: a tailored shell, with a clear face opening toward +Y.
            vertices, faces = [], []
            for ring, (z, radius) in enumerate(((h * .81, .14), (h * .93, .115), (h * .99, .07), (h * 1.012, .002))):
                for i in range(25):
                    a = math.radians(45 + i * 270 / 24)
                    vertices.append((math.sin(a) * radius, head.y + math.cos(a) * radius, z))
                    if ring and i:
                        n = ring * 25 + i
                        faces.append((n - 26, n - 25, n, n - 1))
            mesh("Stalker_open_cowl", vertices, faces, self.mats["jacket"], self.pivots["body"])
        elif style == "regenerator":
            for sign in (-1, 1):
                self.panel("coat_tail", (sign * .105, -.025, h * .40), (.16, .22, .32), "jacket", bevel=.025)
                self.seam("luminescent_vein", [(sign * .06, .165, h * .83), (sign * .085, .17, h * .76), (sign * .14, .17, h * .72)], .0035)
            self.panel("hospital_id", (-.09, .169, h * .72), (.05, .009, .066), "accent")
        elif style == "leaper":
            for side, sign in (("left", -1), ("right", 1)):
                for index in range(3):
                    self.seam("forearm_tendon", [(sign * .33, .12 + index * .008, h * .66), (sign * .39, .17 + index * .008, h * .53)], .004, "skin", "arm_" + side)
        if style == "boss":
            for index in range(8):
                x = self.rng.uniform(-.18, .18)
                z = self.rng.uniform(h * .60, h * .77)
                self.seam("breach_fissure", [(x, .212, z), (x + .028, .215, z - .03), (x + .014, .214, z - .07)], .005)

    def pose(self):
        bpy.context.view_layer.update()
        cached = [(obj, [obj.matrix_world @ v.co for v in obj.data.vertices])
                  for obj in self.root.children_recursive if obj.type == "MESH"]
        shoulder = abs(self.joints["joint-l-shoulder"].x)
        pelvis = Vector((0, 0, self.height * .49))
        lean = Matrix.Rotation(math.radians(-self.spec["hunch"]), 3, "X")
        def deform(point):
            p = point.copy()
            if p.z > self.height * .43:
                side = "l" if p.x < 0 else "r"
                pivot = self.joints["joint-" + side + "-shoulder"]
                weight = max(0, min(1, (abs(p.x) - shoulder * .65) / (self.height * .12)))
                weight = weight * weight * (3 - 2 * weight)
                rotation = Matrix.Rotation(math.radians(-37 if side == "l" else 37), 3, "Y")
                p = p.lerp(pivot + rotation @ (p - pivot), weight)
            weight = max(0, min(1, (point.z - pelvis.z) / (self.height * .13)))
            weight = weight * weight * (3 - 2 * weight)
            return p.lerp(pelvis + lean @ (p - pelvis), weight)
        for key, pivot in self.pivots.items():
            if key != "body":
                pivot.location = deform(pivot.location)
        bpy.context.view_layer.update()
        for obj, vertices in cached:
            inverse = obj.parent.matrix_world.inverted()
            obj.matrix_basis = Matrix.Identity(4)
            for vertex, point in zip(obj.data.vertices, vertices):
                vertex.co = inverse @ deform(point)
            obj.data.update()


def build(kind, render):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.data.orphans_purge(do_recursive=True)
    spec = json.loads((ROOT / "assets/designs/characters" / (kind + ".json")).read_text())
    character = Infected(spec)
    studio(spec["height"])
    target = ROOT / "assets/blender/characters" / kind
    save_asset(character.root, target, ROOT / "assets/previews/characters" / (kind + ".png") if render else None,
               export_path=ROOT / ".cache/blender-export/characters" / (kind + ".glb"))
    triangles = 0
    for child in character.root.children_recursive:
        if child.type == "MESH":
            triangles += sum(len(poly.vertices) - 2 for poly in child.data.polygons)
    print(json.dumps({"kind": kind, "triangles": triangles, "blend": str(target.with_suffix('.blend'))}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", default="walker")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    for kind in ([path.stem for path in sorted((ROOT / "assets/designs/characters").glob("*.json"))] if args.kind == "all" else [args.kind]):
        build(kind, args.render)
