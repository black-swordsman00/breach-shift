"""Optimize a generated humanoid and bind a local skeleton for the game animation."""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production import (apply_transforms, decimate_preserving_uvs, export_glb,
                        prepare_game_textures, save_clean_blend)


def bind_skeleton(meshes, height):
    bpy.ops.object.select_all(action='DESELECT')
    data = bpy.data.armatures.new('Survival_humanoid')
    rig = bpy.data.objects.new('RODIN_humanoid_rig', data)
    bpy.context.collection.objects.link(rig)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    specs = [('root',(0,0,0),(0,0,.1),None),
             ('hips',(0,0,.46),(0,0,.55),'root'),
             ('spine',(0,0,.55),(0,0,.77),'hips'),
             ('neck',(0,0,.77),(0,0,.86),'spine'),
             ('head',(0,0,.86),(0,0,.98),'neck')]
    for side,sign in (('left',-1),('right',1)):
        specs.extend([
            ('arm-'+side,(sign*.12,0,.77),(sign*.175,0,.57),'spine'),
            ('forearm-'+side,(sign*.175,0,.57),(sign*.19,0,.41),'arm-'+side),
            ('hand-'+side,(sign*.19,0,.41),(sign*.185,.01,.34),'forearm-'+side),
            ('leg-'+side,(sign*.065,0,.47),(sign*.075,.01,.27),'hips'),
            ('shin-'+side,(sign*.075,.01,.27),(sign*.08,0,.065),'leg-'+side),
            ('foot-'+side,(sign*.08,0,.065),(sign*.08,.12,.035),'shin-'+side),
        ])
    for name,head,tail,parent in specs:
        bone=data.edit_bones.new(name)
        bone.head, bone.tail = Vector(head)*height, Vector(tail)*height
        bone.use_deform = name != 'root'
        if parent:
            bone.parent=data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    deform=[bone for bone in data.bones if bone.use_deform]
    # Limit and normalize skin weights locally, filling any isolated eye/teeth
    # vertices not reached by Blender's heat weighting with the closest bone.
    def distance(point,bone):
        start,end=bone.head_local,bone.tail_local
        direction=end-start
        t=max(0,min(1,(point-start).dot(direction)/direction.length_squared))
        return (point-(start+direction*t)).length_squared
    for obj in meshes:
        names={group.index:group.name for group in obj.vertex_groups}
        allowed={bone.name for bone in deform}
        weights=[]
        for vertex in obj.data.vertices:
            entries=[(names[item.group],item.weight) for item in vertex.groups
                     if names[item.group] in allowed and item.weight > .0001]
            entries=sorted(entries,key=lambda item:item[1],reverse=True)[:4]
            if not entries:
                bone=min(deform,key=lambda item:distance(vertex.co,item))
                entries=[(bone.name,1.0)]
            total=sum(weight for _,weight in entries)
            weights.append([(name,weight/total) for name,weight in entries])
        all_indices=list(range(len(obj.data.vertices)))
        for name in allowed:
            group=obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
            group.remove(all_indices)
        for index,entries in enumerate(weights):
            for name,weight in entries:
                obj.vertex_groups[name].add([index],weight,'REPLACE')
    rig.show_in_front=True
    return rig


def optimize(source, output, kind, height, yaw):
    if not source.is_file() or source.suffix.lower() != '.glb' or height <= 0:
        raise ValueError('A completed Rodin GLB and a positive metre height are required')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
    meshes=apply_transforms(list(bpy.context.scene.objects))
    high_meshes=[]
    for obj in meshes:
        high=obj.copy();high.data=obj.data.copy()
        for index,material in enumerate(high.data.materials):
            if material:high.data.materials[index]=material.copy()
        high.name='SOURCE_HIGH_'+kind
        bpy.context.collection.objects.link(high)
        high_meshes.append(high)
    original_count=decimate_preserving_uvs(meshes,12000)
    rotation=Matrix.Rotation(math.radians(yaw),4,'Z')
    for obj in meshes+high_meshes:
        obj.data.transform(rotation)
    points=[vertex.co for obj in meshes for vertex in obj.data.vertices]
    low=Vector(tuple(min(point[a] for point in points) for a in range(3)))
    high=Vector(tuple(max(point[a] for point in points) for a in range(3)))
    origin=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    factor=height/(high.z-low.z)
    for obj in meshes+high_meshes:
        for vertex in obj.data.vertices:
            vertex.co=(vertex.co-origin)*factor
        obj.data.update()
    for obj in meshes:
        obj.name='RODIN_'+kind+'_skin'
    for obj in high_meshes:
        obj.hide_set(True);obj.hide_render=True
    rig=bind_skeleton(meshes,height)
    prepare_game_textures([mat for obj in meshes for mat in obj.data.materials if mat])
    output.mkdir(parents=True,exist_ok=True)
    report=export_glb(meshes+[rig],output/(kind+'.glb'))
    report.update(provider='Hyper3D Rodin',source_triangles=original_count,
                  uv_layers_preserved=True,forward='+Y',up='+Z',units='metres',
                  height=height,rig='skinned-humanoid',
                  high_source_retained=True,
                  animation_joints=['arm-left','arm-right','leg-left','leg-right'])
    (output/(kind+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    save_clean_blend(output/(kind+'.blend'))
    print(json.dumps(report))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--kind',required=True)
    parser.add_argument('--height',type=float,required=True)
    parser.add_argument('--yaw',type=float,default=0)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    optimize(args.source,args.output,args.kind,args.height,args.yaw)
