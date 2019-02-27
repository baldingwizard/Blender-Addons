# Author: Rich Sedman
# Description: Dynamic Maths Expresion node Blender Add-on
# Version: (0.60)
# Date: May 2018
################################################### History ######################################################
# 0.4  01/06/2018 : Fix problems in parse_expression (parse_expression v0.3)
# 0.41 02/06/2018 : Fix problem with pruning of group input nodes that are no longer part of the expression.
#                   (dynamic_maths_expression_node v0.41)
# 0.42 09/06/2018 : Support multiple expressions and improve automatic layout (dynamic_maths_expression_node)
# 0.49 11/06/2018 : Separate out node layout tools and implement simpler hierarchy layout
# 0.50 11/06/2018 : Support multi-expressions including naming with 'Name=expression' format.
# 0.51 15/06/2018 : Improve operator precedence in parse_expression (v0.4)
# 0.52 15/06/2018 : Fix minor bug in naming output sockets when multiple outputs added
# 0.60 05/02/2019 : Bring up to date for Blender 2.8 API changes
##################################################################################################################

bl_info = {  
 "name": "Dynamic Maths Expression",  
 "author": "Rich Sedman",  
 "version": (0, 60),  
 "blender": (2, 80, 0),  
 "location": "Node Editor > Add > Custom_Nodes",  
 "description": "Adds a custom node that allows you to create a node tree from an arbitrary expression.",  
 "warning": "",  
 "wiki_url": "https://github.com/baldingwizard/Blender-Addons/wiki",  
 "tracker_url": "https://github.com/baldingwizard/Blender-Addons/issues",  
 "category": "Node"} 

import bpy

from .dynamic_maths_expression_node import DynamicMathsExpression_Operator, DynamicMathsExpressionEdit_Operator

from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories
from nodeitems_builtins import ShaderNodeCategory

def menu_draw(self, context):
    self.layout.operator("node.node_dynamic_maths_expression")
    self.layout.operator("node.node_dynamic_maths_expression_edit")

bpy.types.NODE_MT_add.append(menu_draw)
#TODO : Need to remove the menu when unregistered. Also, need to add it to Add/Group rather than Add

#classes = ( DynamicMathsExpressionNode, )
classes = ( DynamicMathsExpression_Operator, DynamicMathsExpressionEdit_Operator)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    #newcatlist = [ShaderNodeCategory("SH_NEW_CUSTOM", "Custom Nodes", items=[NodeItem("DynamicMathsExpressionNode"),DynamicMathsExpression_Operator])]
    #newcatlist = [ShaderNodeCategory("SH_NEW_CUSTOM", "Custom Nodes", items=[NodeItem("DynamicMathsExpressionNode"),])]
    #
    #register_node_categories("CUSTOM_NODES", newcatlist)

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