# Author: Rich Sedman
# Description: Dynamic Maths Expresion node Blender Add-on
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
# 0.61 05/02/2019 : Bring up to date for Blender 2.8 API changes
# 0.90 01/03/2019 : Implement Edit and tidy up placement of created node.
# 0.91 01/03/2019 : Remove unnecessary import of ShaderNodeCategory (no longer used)
# 0.99 04/03/2019 : Implement Edit mode from custom node within group
# 1.00 14/03/2019 : Final polishing and bug fixing
# 1.10 29/03/2019 : Bug fixes (fixed '==' operator, linked to 'dummy' output node for changes, etc.), optimize
#                   tree, allow text to be sourced from text block.
# 1.11 05/04/2019 : Include 'combine' to create vectors (and '[]' suffix on output variables to indicate vector)
#                   and splitting of input vector into individual elements with '[...]' suffix (x,y,z,r,g,b,0,1,2)
# 1.12 06/04/2019 : Refine checks to enable operators only if valid node tree
# 1.13 06/04/2019 : Implement 'presets', stored in a 'presets' subdirectory
# 1.14 08/04/2019 : Presets can be imported to text block to allow easier editing and update of node
# 1.15 19/04/2019 : Allow presets to include "options" where the user can decide which features to enable/disable
# 1.16 23/04/2019 : Add checking to presets build and fix problems with operator precedence
# 1.17 23/04/2019 : Fix bug in expressions for negative values (eg, "x/-y")
#                   Support 'Input.XXX' variables for Texture Coordinate node
#                   Specify INVOKE_DEFAULT when adding to menu to support calling from Shift+A shortcut
# 1.18 26/04/2019 : Added additional functions (noise, clamp/clip, vadd, vsub, vdot, vcross, vnorm, fract, ceil, floor)
# 1.19 30/04/2019 : Added vmult and vdiv functions and refine selection of active node tree
# 1.20 15/05/2019 : Create a separate group per sub-expression. This produces a node that is far more responsive in the
#                   Node Editor as well as making it more manageble.
#                   Also, added documentation viewable from button on 'Create' operator.
#                   Also, make the newly added node the 'active' one
# 1.21 16/05/2019 : Optimise generated groups.
#                   Also, fix bug in grouping (it was getting confused and mixing groups)
# 1.22 18/05/2019 : Tidy up opening of documentation window, minor fix with sub-grouping and assign labels to sub-groups,
#                   Optimise node tree by applying 'Value' nodes to destination sockets
# 1.23 31/05/2019 : Added support for 'musgrave(...)' function and sub-functions as well as 'voronoi' and 'voronoi.cell'.
#                   Tidied up parse_expression to use functionList instead of defining functions in two places.
#                   Fixed problem with vector definition (using '[]' to force input to a vector), introduced 'group'
#                   functionality to define sub-groups and allow iteration (included mandelbulb preset). 
# 1.24 08/06/2019 : Support negative values in variable defaults (by balancing {} brackets and ignoring '-' in string
#                   when checking functions).
#                   Also, implement 'colorramp(...)'
#                   Implement 'undo' checkpoint at start of action
# 1.25 06/07/2019 : Implement extended modes on Voronoi texture for Blender 2.8+. Also, set position of newly 
#                   added group node by positioning at mouse cursor and allowing it to be repositioned on mouse move.
# 1.26 09/07/2019 : Don't merge value node into 'group' nodes (at 2.8/Eevee, default_value of group nodes don't seem to
#                   work properly; leaving the Value node connected works fine. This allows expressions with just single
#                   values such as 'Factor1 = 1.0')
# 1.27 19/07/2019 : Fix 'mix4' preset to use vectors instead of scalars for color inputs and output. Remove redundant internal
#                   variables from 'hexagon' preset. Revamp processing of 'hidden' output variables so as to not repreatedly
#                   add/remove them from Group Output node (this should avoid some race condition crashes), add labelled
#                   reroute nodes to tree (added originally as part of new hidden outputs processing). Enhance layout of nodes
#                   to allow for new reroute and processing changes.
#                   Amended documentation to fix typos on Special Variable section (all had 'Input' as the prefix but should
#                   be 'Input', 'Geom', 'Object' or 'Particle')
#                   Disable all material's 'use_nodes' for the duration of any updates to the group and revert back once changes
#                   are complete and introduce a delay when removing group output sockets - this is to avoid apparent race
#                   conditions with the renderer when the interface with the group changes.
# 1.28 06/09/2019 : Add quoted value support and implement '"pi"' and '"e"', added PointDensity,
#                   implemented inputs(...) and outputs(...) calls,
#                   Implement 'functions' with 'function:start(<name>, ...)', 'function:end(<name>, ...)', 'fn:<name>(...)'
# 1.29 13/09/2019 : Can use 'include "TEXT:<block>"' to import from other text blocks (eg, used to import pre-written functions)
#                   This allows you to include pre-written groups, functions, even complete sub-expressions to use in the current
#                   expression. Can also use 'import ....' as an alternative syntax.
#                   Tweaked the auto-layout scan of the tree to try to significantly improve performance with large, multi-branched trees.
# 1.30 04/10/2019 : Improve performance on 'create' since we don't need to be careful of removing sockets that aren't actually in use yet.
#                   Introduce Image Texture node function (image(input, "imagename", ....))
#                   Implement mix(factor, c1, c2) function
#                   Fix problem with changing output socket type (eg, scalar to vector by adding '[]' - would previously have to
#                   update twice - once would remove the socket, again would add the new one)
#                   Change some presets to include additional options (such as Generated or Object coordinates for input)
# 1.31 19/10/2019 : Add popup that asks for some contact/feedback/acknowledgement/thanks/etc.
# 1.32 29/05/2020 : Make compatible with Blender version 2.82 (updated Maths node functionality had broken node tree build)
# 1.33 27/08/2020 : Make compatible with Blender version 2.83 (4D texture nodes broke noise, musgrave, voronoi, etc. due to extra socket)
##################################################################################################################

#TODO: Possibly enhance to make it work in the compositor...? Could have different presets for compositor and one of those could be Halftone


bl_info = {  
 "name": "Dynamic Maths Expression",
 "author": "Rich Sedman",  
 "version": (1, 33),  
 "blender": (2, 80, 0),  
 "location": "Node Editor > Add",  
 "description": "Provide an option to create a new group from a typed maths expression.",  
 "warning": "",  
 "wiki_url": "https://blendermarket.com/products/node-expressions",  
 "tracker_url": "",  
 "category": "Node"} 

import bpy

from .dynamic_maths_expression_node import DynamicMathsExpression_Operator, DynamicMathsExpressionEdit_Operator, DynamicMathsExpressionEditWithin_Operator, DynamicMathsExpressionRevert_Operator, DynamicMathsExpressionUpdate_Operator, DynamicMathsExpressionShowDocumentation_Operator, DynamicMathsExpressionNode

from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories

def menu_draw(self, context):
    #Force 'invoke' when calling operator
    self.layout.operator_context = "INVOKE_DEFAULT"
    
    self.layout.operator("node.node_dynamic_maths_expression", text='Maths Expression')
    
    # Edit is not required since we can now edit within the group itself via the custom node
    #self.layout.operator("node.node_dynamic_maths_expression_edit", text='Maths Expression(Edit)')

bpy.types.NODE_MT_add.append(menu_draw)
#TODO : Need to add it to Add/Group rather than Add

classes = ( DynamicMathsExpression_Operator, DynamicMathsExpressionEdit_Operator, DynamicMathsExpressionEditWithin_Operator, DynamicMathsExpressionRevert_Operator ,DynamicMathsExpressionUpdate_Operator, DynamicMathsExpressionShowDocumentation_Operator, DynamicMathsExpressionNode)

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