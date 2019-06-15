# Author: Rich Sedman
# Description: Smoke to EXR - convert the pointcloud from a smoke domain into an EXR image
# Date: June 2019
################################################### History ######################################################
# 0.10 14/06/2019 : Initial creation as an add-on based on previously developed scripts
##################################################################################################################

bl_info = {  
 "name": "Smoke2EXR",
 "author": "Rich Sedman",  
 "version": (0, 10),  
 "blender": (2, 76, 0),  
 "location": "(operators)",  
 "description": "Provide a means of converting a smoke simulation into an image that can be used to access the smoke data independently of the simulation",  
 "warning": "",  
 "wiki_url": "",  
 "tracker_url": "",  
 "category": "Operator"}    #TODO: Don't know if this is correct!! 

import bpy

from .smoke2exr import Smoke2EXR_Operator

#def menu_draw(self, context):
#    #Force 'invoke' when calling operator
#    self.layout.operator_context = "INVOKE_DEFAULT"
#    
#    self.layout.operator("node.node_dynamic_maths_expression", text='Maths Expression')
#    
#    # Edit is not required since we can now edit within the group itself via the custom node
#    #self.layout.operator("node.node_dynamic_maths_expression_edit", text='Maths Expression(Edit)')
#
#bpy.types.NODE_MT_add.append(menu_draw)
##TODO : Need to add it to Add/Group rather than Add

classes = ( Smoke2EXR_Operator, )

def add_to_panel(self, context):
    layout = self.layout
    layout.operator("operator.smoke2exr", text='Convert Smoke to EXR')

bpy.types.PHYSICS_PT_smoke_cache.append(add_to_panel)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()