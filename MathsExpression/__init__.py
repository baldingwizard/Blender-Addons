# Author: Rich Sedman
# Description: Dynamic Maths Expresion node Blender Add-on
# version: (0.2)

bl_info = {  
 "name": "Dynamic Maths Expression",  
 "author": "Rich Sedman",  
 "version": (0, 3),  
 "blender": (2, 79, 0),  
 "location": "Shader Node Editor",  
 "description": "Adds a custom node that allows you to create a node tree from an arbitrary expression.",  
 "warning": "",  
 "wiki_url": "",  
 "tracker_url": "",  
 "category": "Node"} 

import bpy

from .dynamic_maths_expression_node import DynamicMathsExpressionNode

from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories
from nodeitems_builtins import ShaderNewNodeCategory
	
def register():
    bpy.utils.register_class(DynamicMathsExpressionNode)
    newcatlist = [ShaderNewNodeCategory("SH_NEW_CUSTOM", "Custom Nodes", items=[NodeItem("DynamicMathsExpressionNode"),]),]
    register_node_categories("CUSTOM_NODES", newcatlist)

def unregister():
    unregister_node_categories("CUSTOM_NODES")
    bpy.utils.unregister_class(DynamicMathsExpressionNode)


if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()