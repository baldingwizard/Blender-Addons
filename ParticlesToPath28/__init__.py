# Author: Rich Sedman
# Description: Particles to Path - convert a stream of particles into a curve
# Version: (0.05)
# Date: July 2018
################################################### History ######################################################
# 0.01 13/07/2018 : Initial creation
# 0.04 05/03/2019 : Added operator to Add/Curve menu
# 0.05 05/03/2019 : Compatility with Blender 2.8
##################################################################################################################

bl_info = {  
 "name": "Particles to Path",  
 "author": "Rich Sedman",  
 "version": (0, 5),  
 "blender": (2, 80, 0),  
 "location": "3d View operator",  
 "description": "Provides Operator to create a curve from  a stream of particles.",  
 "warning": "",  
 "wiki_url": "https://github.com/baldingwizard/Blender-Addons/wiki",  
 "tracker_url": "https://github.com/baldingwizard/Blender-Addons/issues",  
 "category": "Mesh"} 

import bpy

from .particles_to_path import ParticlesToPath

# See https://b3d.interplanety.org/en/creating-panels-for-placing-blender-add-ons-user-interface-ui/

#class NodeLayoutTools_Panel(bpy.types.Panel):
#    """Tooltip"""
#    bl_idname = "node.node_layout_tools_apply_basic_hierarchical_layout"
#    bl_label = "Node Layout Tools - Apply basic hierarchical layout"
#    bl_space_type = 'NODE_EDITOR'
#    bl_region_type = 'TOOLS'
#    bl_context = 'node'
#    bl_category = 'Layout'
#
#    horiz_spacing = bpy.props.IntProperty(5)
#    vert_stacing = bpy.props.IntProperty(10)
#    
#    def draw(self, context):
#        layout = self.layout
#        layout.label(text="Node Layout Tools")
#        #scene = context.scene
#        layout.label(text=" This is a test panel for NodeLayoutTools")
#        row = layout.row()
#        row.prop(self, "horiz_spacing")
#        row = layout.row()
#        row.prop(self, "vert_spacing")
#        row = layout.row()
#        row.operator("node.node_layout_tools_apply_basic_hierarchical_layout")
#        
#    def do_stuff(self):
#        pass

# Add operator to menu
def menu_draw(self, context):
    self.layout.operator("object.particles_to_path", text='Particles to Nurbs', icon='PARTICLES')
    
    # Edit is not required since we can now edit within the group itself via the custom node
    #self.layout.operator("node.node_dynamic_maths_expression_edit", text='Maths Expression(Edit)')

#bpy.types.INFO_MT_curve_add.append(menu_draw)
bpy.types.VIEW3D_MT_curve_add.append(menu_draw)


class ParticlesToPath_Operator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.particles_to_path"
    bl_label = "Particles To Path - Create curve from a stream of particles"
    bl_space_type = 'VIEW_3D'

    particle_system = bpy.props.IntProperty(name="Particle System #",default=1, min=1, soft_max=10)
    curve_resolution = bpy.props.IntProperty(name="Curve Resolution",default=8, min=1, soft_max=20)
    bevel_resolution = bpy.props.IntProperty(name="Bevel Resolution",default=4, min=1, soft_max=10)
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'VIEW_3D'
        
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        ParticlesToPath_Operator.execute_main(self, context)
        return {'FINISHED'}

    def execute_main(operator, context):
        space = context.space_data
        object_active = context.active_object
        object_selected = context.selected_objects
        
        if len(object_selected) != 1:
            operator.report({'ERROR'}, 'Must select only 1 object')
            return
        
        numParticleSystems = len(object_selected[0].particle_systems)
        
        if numParticleSystems < 1:
            operator.report({'ERROR'}, 'Object does not have any particle systems')
            return
            
        if operator.particle_system > numParticleSystems:
            operator.report({'ERROR'}, 'Particle System out of range (object only has '+str(numParticleSystems)+' particle systems)')
            return
            
        ParticlesToPath.createCurveFromParticles(object_selected[0].name, particleSystem=operator.particle_system-1, curveResolution=operator.curve_resolution,bevelResolution=operator.bevel_resolution,fillMode='FULL')
        

def register():
    #bpy.utils.register_class(NodeLayoutTools_Panel)
    bpy.utils.register_class(ParticlesToPath_Operator)

def unregister():
    #bpy.utils.register_class(ParticlesToPath_Panel)
    bpy.utils.unregister_class(ParticlesToPath_Operator)


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()