"""Render a finished, embedded GLB locally for the review gallery."""
import argparse
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def render(source, output, category):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
    bpy.context.view_layer.update()
    scene=bpy.context.scene
    points=[]
    graph=bpy.context.evaluated_depsgraph_get()
    for obj in scene.objects:
        if obj.type!='MESH':continue
        evaluated=obj.evaluated_get(graph)
        mesh=evaluated.to_mesh()
        points.extend(evaluated.matrix_world@vertex.co for vertex in mesh.vertices)
        evaluated.to_mesh_clear()
    low=Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    high=Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    center=(low+high)/2;span=max(high-low)
    if category=='characters':
        center.z+=span*.15
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x,scene.render.resolution_y=(1440,900) if category=='weapons' else (960,1200)
    scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.025,.035,.05,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    if category=='characters':
        scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.10,.13,.17,1)
    for name,position,power,color in (
            ('key',(2,3,3),1100,(1,.86,.7)),
            ('fill',(-2,2,2),750,(.62,.78,1)),
            ('rim',(0,-3,3),1500,(.8,.9,1))):
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.size=span*1.6
        obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
        obj.location=center+Vector(position)*span*(.55 if category=='characters' else 1)
        obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Review_camera');camera=bpy.data.objects.new('Review_camera',data)
    bpy.context.collection.objects.link(camera)
    camera.location=center+Vector((2,-1,.7) if category=='weapons' else (1.2,3,.25))*span
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=span*(1.25 if category=='weapons' else 1.0)
    scene.camera=camera
    output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(output)
    bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--category',choices=('weapons','characters'),required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    render(args.source,args.output,args.category)
