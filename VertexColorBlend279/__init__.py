# Author: Rich Sedman
# Description: Particles to Path - convert a stream of particles into a curve
# Version: (0.01)
# Date: March 2019
################################################### History ######################################################
# 0.01 13/07/2018 : Initial creation
##################################################################################################################

#TODO: Add a tool panel for easy re-do

bl_info = {  
 "name": "Vertex Color Blend",  
 "author": "Rich Sedman",  
 "version": (0, 1),  
 "blender": (2, 79, 0),  
 "location": "3d View/Paint/Blend Vertex Colors",  
 "description": "Provides Operator to blend an object's vertex colors.",  
 "warning": "",  
 "wiki_url": "https://github.com/baldingwizard/Blender-Addons/wiki",  
 "tracker_url": "https://github.com/baldingwizard/Blender-Addons/issues",  
 "category": "Mesh"} 

import bpy

from .vertex_color_blend import VertexColorBlend

# Add operator to menu
def menu_draw(self, context):
    self.layout.operator("object.vertex_color_blend", text='Blend Vertex Colors', icon='BRUSH_SMEAR')
    
    # Edit is not required since we can now edit within the group itself via the custom node
    #self.layout.operator("node.node_dynamic_maths_expression_edit", text='Maths Expression(Edit)')

bpy.types.VIEW3D_MT_paint_vertex.append(menu_draw)
#TODO : Need to add it to Add/Group rather than Add

class VertexColorBlend_Operator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.vertex_color_blend"
    bl_label = "Vertex Color Blend - Blend Vertex Colors to surrounding geometry"
    bl_space_type = 'VIEW_3D'

    iterations = bpy.props.IntProperty(name="Number of steps",default=1, min=1, soft_max=999)
    initialRed = bpy.props.FloatProperty(name="'Background' color red",default=0.5, min=0.0, max=1.0)
    initialGreen = bpy.props.FloatProperty(name="'Background' color green",default=0.5, min=0.0, max=1.0)
    initialBlue = bpy.props.FloatProperty(name="'Background' color blue",default=0.5, min=0.0, max=1.0)
    fixedVertexGroup = bpy.props.StringProperty(name="Vertex Group for 'Fixed' colors",default="FIXEDCOLORS")
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'VIEW_3D'
        
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        VertexColorBlend_Operator.execute_main(self, context)
        return {'FINISHED'}

    def execute_main(operator, context):
        space = context.space_data
        object_active = context.active_object
        object_selected = context.selected_objects
        
        if len(object_selected) != 1:
            operator.report({'ERROR'}, 'Must select only 1 object')
            return
        
        if not operator.fixedVertexGroup in object_selected[0].vertex_groups.keys():
            operator.report({'ERROR'}, "Vertex Group '"+str(operator.fixedVertexGroup)+"' does not exist")
            return
            
        VertexColorBlend.color_vertices_rgb(object_selected[0], operator.fixedVertexGroup, operator.iterations, (operator.initialRed,operator.initialGreen,operator.initialBlue,1.0))
        

def register():
    #bpy.utils.register_class(NodeLayoutTools_Panel)
    bpy.utils.register_class(VertexColorBlend_Operator)

def unregister():
    #bpy.utils.register_class(ParticlesToPath_Panel)
    bpy.utils.unregister_class(VertexColorBlend_Operator)


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()