"""Optimize a supplied or existing humanoid and bind its local game skeleton."""
import argparse
import json
import math
from hashlib import sha256
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production import (apply_transforms, decimate_preserving_uvs, export_glb,
                        prepare_game_textures, save_clean_blend)


def bind_skeleton(meshes, height, physique='standard'):
    bpy.ops.object.select_all(action='DESELECT')
    data = bpy.data.armatures.new('Survival_humanoid')
    rig = bpy.data.objects.new('Game_humanoid_rig', data)
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
        shoulder, elbow, wrist = (.225, .28, .31) if physique == 'bulky' else (.12, .175, .19)
        hip, knee = (.105, .14) if physique == 'bulky' else (.065, .075)
        specs.extend([
            ('arm-'+side,(sign*shoulder,0,.77),(sign*elbow,0,.57),'spine'),
            ('forearm-'+side,(sign*elbow,0,.57),(sign*wrist,0,.41),'arm-'+side),
            ('hand-'+side,(sign*wrist,0,.41),(sign*(wrist-.005),.01,.34),'forearm-'+side),
            ('leg-'+side,(sign*hip,0,.47),(sign*knee,.01,.27),'hips'),
            ('shin-'+side,(sign*knee,.01,.27),(sign*(knee+.005),0,.065),'leg-'+side),
            ('foot-'+side,(sign*(knee+.005),0,.065),(sign*(knee+.005),.12,.035),'shin-'+side),
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


def optimize(source, output, kind, height, yaw, *, texture_size=1024,
             physique='standard', provenance='generated', provider=None):
    if not source.is_file() or source.suffix.lower() != '.glb' or height <= 0:
        raise ValueError('A completed humanoid GLB and a positive metre height are required')
    if provider is None:
        provider={'generated':'Hyper3D Rodin','user-supplied':'User-supplied',
                  'local-authored':'Locally authored'}[provenance]
    # Hidden retained source meshes are not selected by select_all. Remove
    # every object in this build scene when reusing one background process.
    for obj in list(bpy.context.scene.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
    meshes=apply_transforms(list(bpy.context.scene.objects))
    if len(meshes) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0]
        bpy.ops.object.join()
        meshes=[bpy.context.object]
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
        obj.name='GAME_'+kind+'_skin'
    for obj in high_meshes:
        obj.hide_set(True);obj.hide_render=True
    rig=bind_skeleton(meshes,height,physique)
    apply_transforms(meshes+[rig])
    # Parenting is identity at this point; reattach after transform application.
    for obj in meshes:
        obj.parent=rig
    prepare_game_textures([mat for obj in meshes for mat in obj.data.materials if mat],texture_size)
    output.mkdir(parents=True,exist_ok=True)
    report=export_glb(meshes+[rig],output/(kind+'.glb'))
    report.update(provider=provider,source_triangles=original_count,
                  uv_layers_preserved=True,forward='+Y',up='+Z',units='metres',
                  height=height,rig='skinned-humanoid',
                  source_sha256=sha256(source.read_bytes()).hexdigest(),
                  provenance=provenance,texture_size=texture_size,physique=physique,
                  high_source_retained=True,
                  animation_joints=['arm-left','arm-right','leg-left','leg-right'])
    points=[vertex.co for obj in meshes for vertex in obj.data.vertices]
    low=[min(point[axis] for point in points) for axis in range(3)]
    high=[max(point[axis] for point in points) for axis in range(3)]
    report.update(bounds=[low,high],dimensions=[b-a for a,b in zip(low,high)])
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
    parser.add_argument('--texture-size',type=int,choices=(1024,2048),default=1024)
    parser.add_argument('--physique',choices=('standard','bulky'),default='standard')
    parser.add_argument('--provenance',choices=('generated','user-supplied','local-authored'),default='generated')
    parser.add_argument('--provider')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    optimize(args.source,args.output,args.kind,args.height,args.yaw,
             texture_size=args.texture_size,physique=args.physique,provenance=args.provenance,
             provider=args.provider)
