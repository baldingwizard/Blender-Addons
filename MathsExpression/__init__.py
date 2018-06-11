# Author: Rich Sedman
# Description: Dynamic Maths Expresion node Blender Add-on
# Version: (0.49)
# Date: May 2018
################################################### History ######################################################
# 0.4  01/06/2018 : Fix problems in parse_expression (parse_expression v0.3)
# 0.41 02/06/2018 : Fix problem with pruning of group input nodes that are no longer part of the expression.
#                   (dynamic_maths_expression_node v0.41)
# 0.42 09/06/2018 : Support multiple expressions and improve automatic layout (dynamic_maths_expression_node)
# 0.49 11/06/2018 : Separate out node layout tools and implement simpler hierarchy layout
##################################################################################################################

bl_info = {  
 "name": "Dynamic Maths Expression",  
 "author": "Rich Sedman",  
 "version": (0, 49),  
 "blender": (2, 79, 0),  
 "location": "Node Editor > Add > Custom_Nodes",  
 "description": "Adds a custom node that allows you to create a node tree from an arbitrary expression.",  
 "warning": "",  
 "wiki_url": "https://github.com/baldingwizard/Blender-Addons/wiki",  
 "tracker_url": "https://github.com/baldingwizard/Blender-Addons/issues",  
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