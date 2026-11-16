"""Transfer generated PBR detail to a small weapon mesh using local Cycles baking."""
import math

import bpy
import numpy as np


def bake_weapon(high_meshes, low_mesh, size=1024):
    """Keep source UVs and add a packed game UV channel with rebaked PBR maps."""
    mesh=low_mesh.data
    source_uv=[]
    for layer in mesh.uv_layers:
        values=np.empty(len(mesh.loops)*2,dtype=np.float32)
        layer.data.foreach_get('uv',values)
        source_uv.append((layer.name,values))
    for layer in list(mesh.uv_layers):
        mesh.uv_layers.remove(layer)
    mesh.uv_layers.new(name='GameUV')
    for name,values in source_uv:
        layer=mesh.uv_layers.new(name=name)
        layer.data.foreach_set('uv',values)
    mesh.uv_layers.active_index=0
    mesh.uv_layers[0].active_render=True
    for polygon in mesh.polygons:
        polygon.use_smooth=True
    bpy.ops.object.select_all(action='DESELECT')
    low_mesh.select_set(True)
    bpy.context.view_layer.objects.active=low_mesh
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.018)
    bpy.ops.object.mode_set(mode='OBJECT')

    target=bpy.data.materials.new('Rodin_game_baked_PBR')
    target.use_nodes=True
    mesh.materials.clear();mesh.materials.append(target)
    for polygon in mesh.polygons:
        polygon.material_index=0
    nodes,links=target.node_tree.nodes,target.node_tree.links
    shader=nodes.get('Principled BSDF')
    target_node=nodes.new('ShaderNodeTexImage')
    target_node.name='Bake_target'
    nodes.active=target_node

    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=1
    scene.render.bake.use_selected_to_active=True
    scene.render.bake.cage_extrusion=.025
    scene.render.bake.max_ray_distance=.06
    scene.render.bake.margin=8
    scene.render.bake.use_clear=True
    scene.render.bake.normal_space='TANGENT'
    materials={mat for obj in high_meshes for mat in obj.data.materials if mat}
    saved=[]
    for material in materials:
        material.use_nodes=True
        tree=material.node_tree
        output=next(node for node in tree.nodes if node.type=='OUTPUT_MATERIAL')
        surface=output.inputs['Surface'].links[0].from_socket
        bsdf=next(node for node in tree.nodes if node.type=='BSDF_PRINCIPLED')
        emission=tree.nodes.new('ShaderNodeEmission')
        saved.append((tree,output,surface,bsdf,emission))

    def select_for_bake():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in high_meshes:
            obj.hide_set(False);obj.hide_render=False;obj.select_set(True)
        low_mesh.select_set(True)
        bpy.context.view_layer.objects.active=low_mesh

    images={}
    for channel,socket_name in (('albedo','Base Color'),('roughness','Roughness'),('metallic','Metallic')):
        image=bpy.data.images.new('rifle_baked_'+channel,width=size,height=size,
                                  alpha=True,float_buffer=False,is_data=channel!='albedo')
        if channel!='albedo':image.colorspace_settings.name='Non-Color'
        target_node.image=image;nodes.active=target_node
        for tree,output,surface,bsdf,emission in saved:
            color=emission.inputs['Color']
            for link in list(color.links):tree.links.remove(link)
            source=bsdf.inputs[socket_name]
            if source.is_linked:
                tree.links.new(source.links[0].from_socket,color)
            else:
                value=source.default_value
                color.default_value=tuple(value) if socket_name=='Base Color' else (value,value,value,1)
            tree.links.new(emission.outputs[0],output.inputs['Surface'])
        select_for_bake()
        bpy.ops.object.bake(type='EMIT')
        image.pack();images[channel]=image
    for tree,output,surface,bsdf,emission in saved:
        tree.links.new(surface,output.inputs['Surface'])
        tree.nodes.remove(emission)
    image=bpy.data.images.new('rifle_baked_normal',width=size,height=size,
                              alpha=True,float_buffer=False,is_data=True)
    image.colorspace_settings.name='Non-Color'
    target_node.image=image;nodes.active=target_node
    select_for_bake()
    bpy.ops.object.bake(type='NORMAL')
    image.pack();images['normal']=image
    # Pack roughness/metallic into glTF's standard ORM channels.
    pixels=np.ones((size*size,4),dtype=np.float32)
    values=np.empty(size*size*4,dtype=np.float32)
    images['roughness'].pixels.foreach_get(values);pixels[:,1]=values.reshape((-1,4))[:,0]
    images['metallic'].pixels.foreach_get(values);pixels[:,2]=values.reshape((-1,4))[:,0]
    orm=bpy.data.images.new('rifle_baked_ORM',width=size,height=size,alpha=True,is_data=True)
    orm.colorspace_settings.name='Non-Color';orm.pixels.foreach_set(pixels.ravel());orm.pack()
    nodes.remove(target_node)
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='GameUV'
    def texture(image):
        node=nodes.new('ShaderNodeTexImage');node.image=image
        links.new(uv.outputs['UV'],node.inputs['Vector'])
        return node
    color=texture(images['albedo']);links.new(color.outputs['Color'],shader.inputs['Base Color'])
    normal_tex=texture(images['normal']);normal=nodes.new('ShaderNodeNormalMap')
    normal.uv_map='GameUV';links.new(normal_tex.outputs['Color'],normal.inputs['Color'])
    links.new(normal.outputs['Normal'],shader.inputs['Normal'])
    combined=texture(orm);separate=nodes.new('ShaderNodeSeparateColor')
    links.new(combined.outputs['Color'],separate.inputs['Color'])
    links.new(separate.outputs['Green'],shader.inputs['Roughness'])
    links.new(separate.outputs['Blue'],shader.inputs['Metallic'])
    # The source remains hidden in the editable scene for repeatable local bakes.
    for obj in high_meshes:
        obj.hide_set(True);obj.hide_render=True
    for unused in (images['roughness'],images['metallic']):
        bpy.data.images.remove(unused)
    scene.render.engine='BLENDER_EEVEE'
    return {'texture_transfer':'local Cycles bake','game_uv':'GameUV',
            'source_uv_layers_retained':[name for name,_ in source_uv]}
