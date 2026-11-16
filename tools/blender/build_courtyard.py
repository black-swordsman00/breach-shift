"""Build the first courtyard from BlenderMCP-imported Poly Haven / Poly Pizza assets.

Run through BlenderMCP after acquiring the sources in docs/production-assets.md.
Only architecture is modeled here; every set-dressing mesh comes from Poly Pizza.
"""
import json
import math
from pathlib import Path
import shutil
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production import apply_transforms, export_glb, prepare_game_textures, save_clean_blend

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "assets/models/environments"
MATERIALS = {"asphalt": ("asphalt_02", 3.0),
             "concrete": ("concrete_wall_008", 2.71),
             "brick": ("brick_wall_07", 1.7),
             "steel": ("rusty_metal_03", 1.35)}
PROPS = {"barricade": "Barrier_Large", "wrecked-car": "Debris_BrokenCar",
         "crate": "Crate", "barrel": "ExplodingBarrel",
         "street-lamp": "StreetLight", "debris": "Debris_Pile"}


def phase_barriers(level):
    results = []
    specs = [('normal_gate', [0,level['normal_gate_y'],level['bounds'][1]-level['bounds'][0],.6,3.5], 'Normal'),
             ('breach_gate', [0,level['breach_gate_y'],level['bounds'][1]-level['bounds'][0],.6,3.5], 'Breach')]
    specs.extend((f'normal_{i}',values,'Normal') for i,values in enumerate(level['normal_blocks']))
    specs.extend((f'breach_{i}',values,'Breach') for i,values in enumerate(level['breach_blocks']))
    runtime = ROOT / 'breach_shift/data/models/environments'
    runtime.mkdir(parents=True,exist_ok=True)
    for label, values, reality in specs:
        x,y,w,d,h = values
        pieces = [block('PHASE_concrete_sill',(0,0,.1),(w,d,.2),'concrete')]
        along_x = w >= d
        length,thickness = (w,d) if along_x else (d,w)
        count = math.ceil(length/2)
        span = length/count
        for index in range(count):
            t = -length/2+(index+.5)*span
            center = (t,0,h/2) if along_x else (0,t,h/2)
            size = (span-.035,thickness-.08,h-.16) if along_x else (thickness-.08,span-.035,h-.16)
            pieces.append(block('PHASE_rusted_panel',center,size,'steel',.018))
            center = (t-span/2+.02,0,h/2) if along_x else (0,t-span/2+.02,h/2)
            size = (.075,thickness,h) if along_x else (thickness,.075,h)
            pieces.append(block('PHASE_structural_rib',center,size,'concrete',.015))
        pieces.append(block('PHASE_top_rail',(0,0,h-.07),(w,d,.14),'steel',.02))
        report = export_glb(pieces,OUTPUT / f'phase_{label}.glb')
        shutil.copyfile(OUTPUT / report['file'], runtime / report['file'])
        results.append({'geometry':values,'reality':reality,**report})
        for piece in pieces:
            bpy.data.objects.remove(piece,do_unlink=True)
    return results


def material_setup():
    for key, (name, tile_m) in MATERIALS.items():
        mat = bpy.data.materials[name]
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        # Bake real-world repeat into mesh UVs. glTF supports these directly.
        for node in list(nodes):
            if node.type in {"MAPPING", "DISPLACEMENT", "TEX_COORD"} or (node.type == "TEX_IMAGE" and node.image and "Displacement" in node.image.name):
                nodes.remove(node)
        uv = nodes.new("ShaderNodeTexCoord")
        for node in nodes:
            if node.type == "TEX_IMAGE":
                links.new(uv.outputs["UV"], node.inputs["Vector"])
        shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
        shader.inputs["Metallic"].default_value = .55 if key == "steel" else 0
        mat["tile_metres"] = tile_m
    # The imported props retain their authored palette and UVs, with matte wear.
    for mat in bpy.data.materials:
        if mat.name in {name for name, _ in MATERIALS.values()} or not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                node.inputs["Roughness"].default_value = .78


def block(name, center, size, surface, bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name, obj.dimensions = name, size
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.data.materials.append(bpy.data.materials[MATERIALS[surface][0]])
    tile = MATERIALS[surface][1]
    uv = obj.data.uv_layers.active or obj.data.uv_layers.new(name="UVMap")
    # Planar projection per face, in metres, keeps brick courses horizontal.
    for face in obj.data.polygons:
        dominant = max(range(3), key=lambda axis: abs(face.normal[axis]))
        axes = (0, 1) if dominant == 2 else ((0, 2) if dominant == 1 else (1, 2))
        for loop_index in face.loop_indices:
            co = obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (co[axes[0]] / tile, co[axes[1]] / tile)
    if bevel:
        modifier = obj.modifiers.new("Small manufactured edge bevel", "BEVEL")
        modifier.width, modifier.segments = min(bevel, min(size) * .2), 2
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        modifier = obj.modifiers.new("Weighted face normals", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def prepare_props():
    result = {}
    for label, name in PROPS.items():
        source = bpy.data.objects.get(name)
        if source is None:
            path = OUTPUT.parent / "props" / (label + ".glb")
            if not path.is_file():
                raise FileNotFoundError(f"Import the Poly Pizza source for {label} first")
            bpy.ops.import_scene.gltf(filepath=str(path))
            source = next(obj for obj in bpy.context.selected_objects if obj.type == "MESH")
        # Blender's importer puts an axis conversion on the parent. Bake WORLD
        # space before removing it, otherwise cars/barrels end up standing on end.
        apply_transforms([source])
        low = Vector(tuple(min(vertex.co[axis] for vertex in source.data.vertices) for axis in range(3)))
        high = Vector(tuple(max(vertex.co[axis] for vertex in source.data.vertices) for axis in range(3)))
        origin = Vector(((low.x + high.x)/2, (low.y + high.y)/2, low.z))
        for vertex in source.data.vertices:
            vertex.co -= origin
        source.name = "SOURCE_" + label
        result[label] = source
        export_glb([source], OUTPUT.parent / "props" / (label + ".glb"))
        source.hide_render = True
        source.hide_set(True)
    for obj in list(bpy.context.scene.objects):
        if obj.type == "EMPTY":
            bpy.data.objects.remove(obj, do_unlink=True)
    return result


def industrial_details(bounds):
    """Add real facade silhouettes and service details within perimeter solids."""
    x0,x1,y0,y1=bounds
    pieces=[]
    paint=bpy.data.materials.get('Yard_Paint')
    if paint is None:
        paint=bpy.data.materials['concrete_wall_008'].copy()
        paint.name='Yard_Paint'
        shader=next(node for node in paint.node_tree.nodes if node.type=='BSDF_PRINCIPLED')
        for link in list(shader.inputs['Base Color'].links):
            paint.node_tree.links.remove(link)
        shader.inputs['Base Color'].default_value=(.72,.56,.21,1)
        shader.inputs['Roughness'].default_value=.85
    MATERIALS['paint']=('Yard_Paint',2.71)
    # The facades sit in the existing solid perimeter, so walking and routes
    # remain consistent with their authored collision. No hidden obstacles.
    for side in (-1,1):
        x=x0-.3 if side<0 else x1+.3
        for index,y in enumerate(range(int(y0)+9,int(y1),18)):
            height=8.7+(index%3)*.8
            pieces.append(block('ARCH_factory_facade',(x,y,height/2),(.6,17.7,height),'concrete',.02))
            pieces.append(block('ARCH_factory_coping',(x,y,height-.08),(.72,17.85,.16),'steel',.02))
            for offset in (-5,0,5):
                pieces.append(block('ARCH_recessed_shutter',(x-side*.315,y+offset,6.4),
                                    (.035,3.3,1.55),'steel',.01))
                pieces.append(block('ARCH_window_sill',(x-side*.36,y+offset,5.59),
                                    (.16,3.55,.12),'concrete',.01))
            for z in (4.45,7.4):
                pieces.append(block('ARCH_facade_band',(x-side*.32,y,z),
                                    (.07,17.7,.10),'concrete',.01))
    # A taller end building gives the yard an actual skyline and a readable
    # destination instead of an unbroken four-metre box wall.
    y=y1+.3
    pieces.append(block('ARCH_containment_facade',(0,y,5.6),(x1-x0,.6,11.2),'brick',.02))
    for z in (4.45,8.6,11.15):
        pieces.append(block('ARCH_containment_trim',(0,y-.32,z),(x1-x0,.10,.17),'concrete',.02))
    for x in range(int(x0)+5,int(x1),7):
        pieces.append(block('ARCH_upper_shutter',(x,y-.32,7),(4,.04,2),'steel',.01))
        pieces.append(block('ARCH_upper_lintel',(x,y-.38,8.09),(4.2,.18,.14),'concrete',.01))
    for x in (-4.6,4.6):
        for y in range(int(y0)+2,int(y1)-2,6):
            pieces.append(block('ARCH_lane_marking',(x,y,.012),(.09,2.5,.008),'paint',0))
    # A locally authored sign uses the existing licensed PBR material maps.
    curve=bpy.data.curves.new('Containment_sign','FONT')
    curve.body='QUARANTINE  /  SECTOR 01'
    curve.align_x='CENTER';curve.size=.48;curve.extrude=.001
    sign=bpy.data.objects.new('ARCH_containment_sign',curve)
    bpy.context.collection.objects.link(sign)
    sign.location=(0,y1-.04,9.45)
    sign.rotation_euler=(math.pi/2,0,0)
    curve.materials.append(paint)
    bpy.ops.object.select_all(action='DESELECT')
    sign.select_set(True);bpy.context.view_layer.objects.active=sign
    bpy.ops.object.convert(target='MESH')
    pieces.append(bpy.context.object)
    return pieces


def place(sources, label, location, heading=0, scale=1):
    source = sources[label]
    obj = source.copy()
    obj.data = source.data.copy()
    bpy.context.collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_set(False)
    obj.name = "PROP_" + label
    obj.location = location
    obj.rotation_euler.z = math.radians(heading)
    obj.scale = (scale,) * 3
    return obj


def build():
    material_setup()
    prepare_game_textures(list(bpy.data.materials))
    sources = prepare_props()
    # Retain the acquired mesh templates, then clear the previous build/defaults.
    for obj in list(bpy.context.scene.objects):
        if obj not in sources.values():
            bpy.data.objects.remove(obj, do_unlink=True)
    level = json.loads((ROOT / "breach_shift/data/levels/01_quarantine_yard.json").read_text())
    architecture, props = [], []
    x0, x1, y0, y1 = level["bounds"]
    # Reusable modules, exported separately for later map sections.
    module_specs = (("road_tile", (0, 0, -.08), (6, 6, .16), "asphalt"),
                    ("sidewalk", (0, 0, -.08), (2, 6, .18), "concrete"),
                    ("curb", (0, 0, -.02), (.24, 6, .20), "concrete"),
                    ("wall", (0, 0, 2.25), (6, .6, 4.5), "brick"),
                    ("wall_trim", (0, 0, .06), (6, .12, .12), "steel"))
    for name, center, size, surface in module_specs:
        module = block("MODULE_" + name, center, size, surface)
        export_glb([module], OUTPUT / "modules" / (name + ".glb"))
        bpy.data.objects.remove(module, do_unlink=True)
    # One continuous surface avoids thousands of redundant draw calls and seams.
    architecture.append(block("ARCH_asphalt", (0, (y0+y1)/2, -.075), (x1-x0, y1-y0, .16), "asphalt", 0))
    for side in (-1, 1):
        x = x0 + 1.05 if side < 0 else x1 - 1.05
        architecture.append(block("ARCH_sidewalk", (x, (y0+y1)/2, -.075), (2.1, y1-y0, .18), "concrete"))
        architecture.append(block("ARCH_beveled_curb", (x-side*1.06, (y0+y1)/2, -.02), (.22, y1-y0, .20), "concrete"))
        # Lamp poles live inside the existing perimeter collision volume.
        for y in range(int(y0)+7, int(y1), 16):
            props.append(place(sources, "street-lamp", (x0-.3 if side<0 else x1+.3, y, 0), 90 if side<0 else -90))
    perimeter = ((x0-.3,(y0+y1)/2,.6,y1-y0+1.2,4.5),
                 (x1+.3,(y0+y1)/2,.6,y1-y0+1.2,4.5),
                 (0,y0-.3,x1-x0,.6,4.5), (0,y1+.3,x1-x0,.6,4.5))
    for x,y,w,d,h in perimeter:
        architecture.append(block("ARCH_perimeter_brick", (x,y,h/2), (w,d,h), "brick"))
        architecture.append(block("ARCH_concrete_footing", (x,y,.18), (w+.06,d+.06,.36), "concrete"))
        architecture.append(block("ARCH_coping_trim", (x,y,h-.07), (w+.10,d+.10,.14), "concrete"))
        long_x = w > d
        for t in range(0, int(max(w,d)), 6):
            px = x-w/2+t if long_x else x
            py = y if long_x else y-d/2+t
            architecture.append(block("ARCH_masonry_pier", (px,py,h/2),
                                      (.7,.7,h), "concrete"))
    architecture.extend(industrial_details(level['bounds']))
    # Existing cover anchors become material-rich loading/containment platforms.
    # Everything large remains within the original collision footprints.
    collision_additions = []
    for index,(x,y,w,d,h) in enumerate(level["shared_blocks"]):
        architecture.append(block("ARCH_loading_platform", (x,y,h/2), (w,d,h), "concrete", .08))
        architecture.append(block("ARCH_platform_cap", (x,y,h-.045), (w,d,.09), "steel"))
        for side in (-1,1):
            architecture.append(block('ARCH_platform_edge_trim',(x,y+side*(d/2+.012),h-.15),
                                      (w,.035,.10),'steel',.008))
            for offset in (-w*.32,w*.32):
                architecture.append(block('ARCH_platform_steel_rib',(x+offset,y+side*(d/2+.014),h/2),
                                          (.085,.04,h-.2),'steel',.008))
        if index in (0,1):
            car_x = x + (1.5 if index == 0 else -1.5)
            props.append(place(sources,"wrecked-car",(car_x,y,h),0 if index==0 else 180))
            collision_additions.append([car_x,y,2.05,4.2,h+1.346])
        for side in (-1,1):
            px = x+side*(w/2-.7)
            props.append(place(sources,"crate",(px,y-.65,h),0))
            props.append(place(sources,"barrel",(px,y+.65,h),12*index))
            collision_additions.extend(([px,y-.65,1.05,1.05,h+1.05], [px,y+.65,.77,.77,h+1.0]))
        # A CC0 barricade at the rear leaves the loading platform silhouette clear.
        props.append(place(sources,"barricade",(x,y+d/2-.3,h),0, .75))
        collision_additions.append([x,y+d/2-.3,1.8,.32,h+1.506])
    # Ground debris is shallow enough to walk across; it does not block routes.
    for index,(x,y) in enumerate(((-19,4),(20,11),(-7,5),(8,28),(-20,54),(21,69),(-10,67),(9,-3))):
        props.append(place(sources,"debris",(x,y,.015),index*47))
    objects = apply_transforms(architecture + props)
    result = export_glb(objects, OUTPUT / "quarantine_yard.glb")
    phases = phase_barriers(level)
    for source in sources.values():
        bpy.data.objects.remove(source, do_unlink=True)
    scene = bpy.context.scene
    engines = scene.render.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1440, 900
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    if scene.world and scene.world.use_nodes:
        for node in scene.world.node_tree.nodes:
            if node.type == "BACKGROUND":
                node.inputs["Strength"].default_value = .38
    light_data = bpy.data.lights.new("Courtyard soft sun", "SUN")
    light_data.energy, light_data.angle = 1.7, math.radians(18)
    light = bpy.data.objects.new("REVIEW_sun", light_data)
    bpy.context.collection.objects.link(light)
    light.rotation_euler = (math.radians(28), math.radians(-22), math.radians(-35))
    camera_data = bpy.data.cameras.new("Courtyard review")
    camera = bpy.data.objects.new("REVIEW_camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (24,-12,17)
    camera.rotation_euler = (Vector((0,22,1))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.lens = 25
    scene.camera = camera
    # The HDRI is packed in Blender and also exported as six float cube faces for
    # the offline Panda3D PBR environment (the glTF standard has no world HDRI).
    image = bpy.data.images['overcast_industrial_courtyard_1k']
    import numpy as np
    rgba = np.empty(image.size[0]*image.size[1]*4,dtype=np.float32)
    image.pixels.foreach_get(rgba)
    rgba = rgba.reshape((image.size[1],image.size[0],4))
    cube_size = 64
    lighting = ROOT / '.cache/courtyard-hdri'
    lighting.mkdir(parents=True, exist_ok=True)
    for face in range(6):
        u,v = np.meshgrid(2*(np.arange(cube_size)+.5)/cube_size-1,2*(np.arange(cube_size)+.5)/cube_size-1)
        ones = np.ones_like(u)
        xyz = ((ones,-u,-v),(-ones,u,-v),(u,ones,-v),(-u,-ones,-v),(u,-v,ones),(u,v,-ones))[face]
        dx,dy,dz = xyz
        magnitude = np.sqrt(dx*dx+dy*dy+dz*dz)
        longitude = np.arctan2(dy,dx)/(2*np.pi)+.5
        latitude = np.arcsin(dz/magnitude)/np.pi+.5
        pixels = rgba[(latitude*(image.size[1]-1)).astype(int),(longitude*(image.size[0]-1)).astype(int)].copy()
        # A cool dusk exposure for readable offline reflections.
        pixels[:,:,:3] *= np.array([.22,.26,.34])
        face_image = bpy.data.images.new('HDRI_face_'+str(face),width=cube_size,height=cube_size,float_buffer=True)
        face_image.pixels.foreach_set(pixels.ravel())
        face_image.filepath_raw = str(lighting / f'courtyard_{face}.exr')
        face_image.file_format = 'OPEN_EXR'
        face_image.save()
        bpy.data.images.remove(face_image)
    bpy.data.orphans_purge(do_recursive=True)
    save_clean_blend(ROOT / 'assets/blender/environments/quarantine_yard.blend')
    runtime = ROOT / 'breach_shift/data/models/environments'
    runtime.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(OUTPUT / 'quarantine_yard.glb',runtime / 'quarantine_yard.glb')
    level['prop_colliders'] = collision_additions
    (ROOT / 'breach_shift/data/levels/01_quarantine_yard.json').write_text(
        json.dumps(level,indent=2)+'\n',encoding='utf-8')
    contract = {'bounds':level['bounds'],
                'blocks':level['shared_blocks']+collision_additions,
                'source':'Poly Haven + Poly Pizza', 'forward':'+Y', 'up':'+Z',
                'units':'metres', 'phase_blocks':phases, **result}
    (runtime / 'quarantine_yard.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8')
    (ROOT / '.cache/courtyard-colliders.json').write_text(json.dumps(collision_additions),encoding='utf-8')
    (ROOT / '.cache/courtyard-build.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__ == "__main__":
    build()
