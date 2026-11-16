"""Optimize a real Rodin weapon GLB; this never generates substitute geometry."""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production import (apply_transforms, export_glb, prepare_game_textures,
                        save_clean_blend, triangle_count)


def optimize(source, output, kind, length, yaw):
    if not source.is_file() or source.suffix.lower() != ".glb":
        raise ValueError("A completed Hyper3D Rodin GLB is required")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
    meshes = apply_transforms(list(bpy.context.scene.objects))
    if not meshes or any(not obj.data.uv_layers for obj in meshes):
        raise ValueError("The Rodin result must include visible meshes and UV maps")
    original_count = triangle_count(meshes)
    uv_names = {obj.name: set(layer.name for layer in obj.data.uv_layers) for obj in meshes}
    for _ in range(5):
        count = triangle_count(meshes)
        if count < 5000:
            break
        ratio = min(.95, 4800/count)
        for obj in meshes:
            bpy.context.view_layer.objects.active = obj
            modifier = obj.modifiers.new("Rodin game budget, retain UV boundaries", "DECIMATE")
            modifier.decimate_type = "COLLAPSE"
            modifier.ratio = ratio
            modifier.use_collapse_triangulate = True
            modifier.delimit = {"UV", "SEAM", "MATERIAL"}
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    if triangle_count(meshes) >= 5000:
        raise ValueError("Unable to reach the strict weapon triangle budget")
    for obj in meshes:
        if not uv_names[obj.name].issubset({layer.name for layer in obj.data.uv_layers}):
            raise ValueError("Decimation lost a UV layer")
    rotation = Matrix.Rotation(__import__('math').radians(yaw),4,'Z')
    for obj in meshes:
        obj.data.transform(rotation)
    points = [vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    if high.y-low.y < .001 or length <= 0:
        raise ValueError("Orient the weapon along +Y and supply a positive metre length")
    center = (low+high)/2
    factor = length/(high.y-low.y)
    for obj in meshes:
        for vertex in obj.data.vertices:
            vertex.co = (vertex.co-center)*factor
        obj.name = "RODIN_" + kind + "_" + obj.name
    prepare_game_textures([mat for obj in meshes for mat in obj.data.materials if mat])
    output.mkdir(parents=True,exist_ok=True)
    report = export_glb(meshes,output/(kind+'.glb'))
    report.update(provider="Hyper3D Rodin",source_triangles=original_count,
                  uv_layers_preserved=True,forward="+Y",up="+Z",units="metres")
    (output/(kind+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    save_clean_blend(output/(kind+'.blend'))
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--kind",choices=("pistol","smg","rifle","shotgun"),required=True)
    parser.add_argument("--length",type=float,required=True,help="full length in metres")
    parser.add_argument("--yaw",type=float,default=0,help="source rotation to face +Y, in degrees")
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    optimize(args.source,args.output,args.kind,args.length,args.yaw)
