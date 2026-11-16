"""Optimize a real Rodin weapon GLB; this never generates substitute geometry."""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production import (apply_transforms, decimate_preserving_uvs, export_glb,
                        prepare_game_textures, save_clean_blend)
from bake_rodin import bake_weapon


def optimize(source, output, kind, length, yaw, offset=(0, 0, 0)):
    if not source.is_file() or source.suffix.lower() != ".glb":
        raise ValueError("A completed Hyper3D Rodin GLB is required")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
    meshes = apply_transforms(list(bpy.context.scene.objects))
    high_meshes=[]
    for obj in meshes:
        high=obj.copy();high.data=obj.data.copy()
        bpy.context.collection.objects.link(high)
        high.name='SOURCE_HIGH_'+kind
        high_meshes.append(high)
    original_count = decimate_preserving_uvs(meshes, 5000)
    rotation = Matrix.Rotation(__import__('math').radians(yaw),4,'Z')
    for obj in meshes+high_meshes:
        obj.data.transform(rotation)
    points = [vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    if high.y-low.y < .001 or length <= 0:
        raise ValueError("Orient the weapon along +Y and supply a positive metre length")
    center = (low+high)/2
    factor = length/(high.y-low.y)
    for obj in meshes+high_meshes:
        for vertex in obj.data.vertices:
            vertex.co = (vertex.co-center)*factor + Vector(offset)
    for obj in meshes:
        obj.name = "RODIN_" + kind + "_game"
    source_textured=any(node.type=='TEX_IMAGE' for obj in high_meshes for mat in obj.data.materials if mat and mat.use_nodes for node in mat.node_tree.nodes)
    transfer={}
    if source_textured:
        if len(meshes)>1:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in meshes:obj.select_set(True)
            bpy.context.view_layer.objects.active=meshes[0]
            bpy.ops.object.join();meshes=[bpy.context.object]
        transfer=bake_weapon(high_meshes,meshes[0])
    else:
        for obj in high_meshes:bpy.data.objects.remove(obj,do_unlink=True)
        prepare_game_textures([mat for obj in meshes for mat in obj.data.materials if mat])
    output.mkdir(parents=True,exist_ok=True)
    report = export_glb(meshes,output/(kind+'.glb'))
    report.update(provider="Hyper3D Rodin",source_triangles=original_count,
                  uv_layers_preserved=True,forward="+Y",up="+Z",units="metres",**transfer)
    points = [vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = [min(point[axis] for point in points) for axis in range(3)]
    high = [max(point[axis] for point in points) for axis in range(3)]
    muzzle = [point for point in points if point.y > high[1] - length*.012]
    report['bounds'] = [low, high]
    report['muzzle'] = [(min(p.x for p in muzzle)+max(p.x for p in muzzle))/2,
                        high[1], (min(p.z for p in muzzle)+max(p.z for p in muzzle))/2]
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
    parser.add_argument("--offset",type=float,nargs=3,default=(0,0,0),help="local origin adjustment in metres")
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    optimize(args.source,args.output,args.kind,args.length,args.yaw,args.offset)
