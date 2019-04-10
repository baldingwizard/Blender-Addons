# Author: Rich Sedman
# Description: Dynamic Maths Expresion node
# Version: (0.99)
# Date: May 2018
################################################### History ######################################################
# 0.4  01/06/2018 : Remove old redundant code
# 0.41 02/06/2018 : Fix pruning of group inputs that are no longer required
# 0.42 06/06/2018 : Start to support multiple expressions and improve auto-layout
# 0.43 11/06/2018 : Move node layout tools into a separate class
# 0.44 11/06/2018 : Prune inputs and outputs no longer required for multi-expressions
# 0.45 15/06/2018 : Fix allocation of name when adding multiple new outputs
# 0.61 20/02/2019 : Redesign to use Operator for create/edit instead of custom node. Implemented as normal NodeGroup.
# 0.90 01/03/2019 : Implement Edit and tidy up placement of created node.
# 0.92 03/03/2019 : Include custom node within group to hold expression
# 0.99 04/03/2019 : Implement Edit mode from custom node within group
##################################################################################################################

# New design for Blender 2.8 :
#
# 1) Create as a modal operator - new option in Group menu to Add Expression Group
# 2) Selecting this will popup a dialog box prompting for the expression
# 3) Accepting the window with a valid expression will build the group
# 4) If within an existing group then an option to 'edit expression' will be available (need to determine how we'll pickup the 'old' expression for editing since we won't actually be holding it anywhere... could use the 'group' name...?)
# 5) Editing the expression will update the expression similar to how editing the expression already does



import bpy
import traceback
import sys

from .parse_expression import Expression
from .node_tree_tools import NodeTreeTools

def get_active_node_tree(context):
    tree = context.space_data.node_tree

    # Get nodes from currently edited tree.
    # If user is editing a group, space_data.node_tree is still the base level (outside group).
    # context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
    # the same as context.active_node, the user is in a group. (code from somewhere - can't remember where to credit)
    # Check recursively until we find the real active node_tree:
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

    return tree

class _DynamicMathsExpression_Operator_common(bpy.types.Operator):
    mode = 'NONE'

    def __init__(self):
        super().__init__()

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR'
        
    def invoke(self, context, event):
        wm = context.window_manager
        if self.mode == 'EDIT':
            
            node_active = context.active_node
            node_selected = context.selected_nodes
        
            if len(node_selected) < 1:
                self.report({'ERROR'}, 'Must select Expression Group Node to edit')
                return {"CANCELLED"}
            
            if len(node_selected) > 1:
                self.report({'ERROR'}, 'Must select only 1 node')
                return {"CANCELLED"}
                
            #if node_selected[0].label[0:5] != 'Expr:':
            #    self.report({'ERROR'}, 'Selected node is not an Expression Group Node')
            #    return {"CANCELLED"}
            
            # Check that the group has a DynamicMathsExpressionNode within (this indicates it's an editable node tree)
            tree = node_selected[0].node_tree
            
            expressionNode = None
            for node in tree.nodes:
                if hasattr(node, 'bl_name') and node.bl_name=='DynamicMathsExpressionNode':
                    expressionNode = node
                    
            if expressionNode == None:
                self.report({'ERROR'}, 'Selected node is not an Expression Group Node')
                return {"CANCELLED"}
                
            self.expressionText = expressionNode.expressionText
            
            return wm.invoke_props_dialog(self)
               
        else:
            if self.mode == 'EDITWITHIN':
                tree = get_active_node_tree(context)
            
                expressionNode = None
                for node in tree.nodes:
                    if hasattr(node, 'bl_name') and node.bl_name=='DynamicMathsExpressionNode':
                        expressionNode = node
                    
                if expressionNode == None:
                    self.report({'ERROR'}, 'Selected node is not an Expression Group Node')
                    return {"CANCELLED"}
                
                self.expressionText = expressionNode.expressionText
            
                return wm.invoke_props_dialog(self)
               
            else:
                return wm.invoke_props_dialog(self)

    def execute(self, context):
        self.execute_main(context)
        return {'FINISHED'}

    # Manage the node's sockets, adding additional ones when needed and removing those no longer required
    def __nodeinterface_setup__(self):
        print("Node interface setup")
        
        # Add the output socket
        if len(self.node_tree.outputs) < 1:
            self.node_tree.outputs.new("NodeSocketFloat", "Value")
        
        return

    # Manage the internal nodes to perform the chained operation - clear all the nodes and build from scratch each time.
    def __nodetree_setup__(self):
        print("Node Setup")
        # Remove all links and all nodes that aren't Group Input or Group Output
        self.node_tree.links.clear()
        for node in self.node_tree.nodes:
            if not node.name in ['Group Input','Group Output']:
                self.node_tree.nodes.remove(node)
            else:
                node.location = [0,0]

        exprNode = self.node_tree.nodes.new('DynamicMathsExpressionNode')
        exprNode.expressionText  = self.expressionText
        #exprNode.width = 300    #TODO : Set width to full width of all nodes and position it above them all, spanning Group Input to Group Output
        #exprNode.location = self.node_tree.nodes['Group Output'].location

                
        # Start from Group Input and add nodes as required, chaining each new one to the previous level and the next input
        groupinput = self.node_tree.nodes['Group Input']
        previousnode = groupinput

        print("About to parse expression...")
        operations = Expression.parse_expression(self.expressionText)
        outputslot = 0
        while True:
            if operations[0] == ',':
                # Multiple expressions - assign the first one then continue with the next
                exprname = 'Value'
                expr = operations[1]
                if expr[0] == '=':
                    # In the form '<var>=<expression>' - use <var> as the name
                    if expr[1][0] == 'variable':
                        exprname = expr[1][1]
                        expr = expr[2]
                        
                if len(self.node_tree.outputs) < (outputslot+2):
                    self.node_tree.outputs.new("NodeSocketFloat", exprname)
                
                self.node_tree.outputs[outputslot].name = exprname;
                    
                self.build_nodes(expr, self.node_tree.nodes['Group Output'].inputs[outputslot], self.node_tree.nodes['Group Output'].location,0)
                operations = operations[2]
            else:
                # Single expression - process it and then exit

                exprname = 'Value'
                expr = operations
                if expr[0] == '=':
                    # In the form '<var>=<expression>' - use <var> as the name
                    if expr[1][0] == 'variable':
                        exprname = expr[1][1]
                        expr = expr[2]

                self.node_tree.outputs[outputslot].name = exprname;
                self.build_nodes(expr, self.node_tree.nodes['Group Output'].inputs[outputslot], self.node_tree.nodes['Group Output'].location,0)
                break
                
            outputslot += 1
        
        self.prune_group_inputs()
        self.prune_group_outputs()
        
        NodeTreeTools.arrangeBasedOnHierarchy(self.node_tree)

        # Position the Expression Node above the nodes, spanning the Input->Output node distance
        groupInputNode = self.node_tree.nodes['Group Input']
        groupOutputNode = self.node_tree.nodes['Group Output']
        
        exprNode.location[0] = groupInputNode.location[0]
        exprNode.location[1] = groupInputNode.location[1]+150
        exprNode.width = groupOutputNode.location[0]+groupOutputNode.width-groupInputNode.location[0]
        
    def build_nodes(self, nested_operations, to_output, output_location,depth):
        depth+=1

        print("Build Nodes")
        if len(nested_operations) == 0:
            return
        
        operation = nested_operations[0]
        
        print("Build Nodes "+str(nested_operations)+" : "+str(operation))
        
        if operation == 'variable':
            #....link to 'group input'
            variablename = nested_operations[1]
            
            if variablename in self.node_tree.nodes['Group Input'].outputs.keys():
                 self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[variablename],to_output)
            else:
                # Add a new socket
                self.node_tree.inputs.new("NodeSocketFloat", variablename)
                self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[-2],to_output)  # Add link to group input we just added (-1 is 'blank' socket, -2 is last 'real' socket)
        
        elif operation == 'value':
            #create new 'Value' node and link to to_output
            newnode = self.node_tree.nodes.new('ShaderNodeValue')
            print("Value = '"+str(nested_operations[1])+"'")
            newnode.outputs[0].default_value = float(nested_operations[1])
            self.node_tree.links.new(newnode.outputs[0],to_output)

        else:
            # create a new 'Maths' node
            newnode = self.node_tree.nodes.new('ShaderNodeMath')
            
            # set the operation
            if operation == '+':
                newnode.operation = "ADD"
            elif operation == '-':
                newnode.operation = "SUBTRACT"
            elif operation == '*':
                newnode.operation = "MULTIPLY"
            elif operation == '/':
                newnode.operation = "DIVIDE"
            elif operation == '**':
                newnode.operation = "POWER"
            elif operation == 'sin':
                newnode.operation = "SINE"
            elif operation == 'cos':
                newnode.operation = "COSINE"
            elif operation == 'tan':
                newnode.operation = "TANGENT"
            elif operation == 'asin':
                newnode.operation = "ARCSINE"
            elif operation == 'acos':
                newnode.operation = "ARCCOSINE"
            elif operation == 'atan':
                newnode.operation = "ARCTANGENT"
            elif operation == 'min':
                newnode.operation = "MINIMUM"
            elif operation == 'max':
                newnode.operation = "MAXIMUM"
            elif operation == '>':
                newnode.operation = "GREATER_THAN"
            elif operation == '<':
                newnode.operation = "LESS_THAN"
            elif operation == 'log':
                newnode.operation = "LOGARITHM"
            elif operation == 'round':
                newnode.operation = "ROUND"
            elif operation == 'mod':
                newnode.operation = "MODULO"
            elif operation == 'abs':
                newnode.operation = "ABSOLUTE"
            elif operation == ',':
                newnode.operation = "***Not yet implemented***"
            else:
                print("Unknown operation '"+ str(operation)+"'")
                newnode.operation = "Unknown"
            
            # link output to to_output
            self.node_tree.links.new(newnode.outputs[0],to_output)

            newlocation = output_location
            newlocation[0] -= 1/depth
            newnode.location = newlocation

            # Repeat for sub-nodes
            self.build_nodes(nested_operations[1], newnode.inputs[0], newlocation,depth)
            if len(nested_operations) > 2:
                newlocation[1]+=1/depth
                self.build_nodes(nested_operations[2], newnode.inputs[1], newlocation,depth)
                
    def prune_group_inputs(self):
        #run through the 'Group Input' sockets and remove any that are no longer connected
        print("Prune Group Inputs(...)")
        for output in self.node_tree.nodes['Group Input'].outputs:
            if len(output.name) > 0 and len(output.links) == 0:
                print("Need to remove "+str(output))
                #self.node_tree.nodes['Group Input'].outputs.remove(output)  ### This doesn't appear to be working!!!!
                for input in self.node_tree.inputs:
                    if input.name == output.name:
                        self.node_tree.inputs.remove(input)
                        print("Removed "+input.name)
                
    def prune_group_outputs(self):
        #run through the 'Group Output' sockets and remove any that are no longer connected
        print("Prune Group Outputs(...)")
        for input in self.node_tree.nodes['Group Output'].inputs:
            if len(input.name) > 0 and len(input.links) == 0:
                for output in self.node_tree.outputs:
                    if output.name == input.name:
                        self.node_tree.outputs.remove(output)
                        print("Removed "+output.name)
                        
    def execute_main(self, context):
        space = context.space_data
        node_active = context.active_node
        node_selected = context.selected_nodes

        print(context)
        if context.space_data.type == 'NODE_EDITOR' and context.space_data.node_tree is not None:
            
            if self.mode == 'CREATE':
                # Create a new node group
                groupnode = get_active_node_tree(context).nodes.new('ShaderNodeGroup')
                groupnode.node_tree=bpy.data.node_groups.new("DynamicMathsExpressionGroup", 'ShaderNodeTree')
                groupnode.node_tree.nodes.new('NodeGroupInput')
                groupnode.node_tree.nodes.new('NodeGroupOutput')
                
                # Position in centre
                groupnode.location = context.region.view2d.region_to_view(context.region.width/2-groupnode.width/2, context.region.height/2+groupnode.height/2)
                
                # Ensure only the new node is selected
                for node in context.selected_nodes:
                    node.select = False
                groupnode.select = True
                
                # TODO: Put it in 'grab' mode?
                #...
                
                self.node_tree = groupnode.node_tree
            
            else:
                if self.mode == 'EDIT':
                # Update existing node group (assume selected node is the one to edit)
                    groupnode = context.selected_nodes[0]
                    self.node_tree = groupnode.node_tree

                    if self.createNew:
                        groupnode.node_tree=bpy.data.node_groups.new("DynamicMathsExpressionGroup", 'ShaderNodeTree')
                        groupnode.node_tree.nodes.new('NodeGroupInput')
                        groupnode.node_tree.nodes.new('NodeGroupOutput')

                else:   #EDITWITHIN
                    self.node_tree = get_active_node_tree(context)
                
            #groupnode.label = 'Expr: '+str(self.expressionText)
                
        
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()
        
    
class DynamicMathsExpression_Operator(_DynamicMathsExpression_Operator_common):
    """Create a new Maths Expresion Group"""
    bl_idname = "node.node_dynamic_maths_expression"
    bl_label = "Node Group - Dynamic Maths Expression"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamice Maths Expression'
    mode = 'CREATE'

    expressionText: bpy.props.StringProperty(description='Enter the expression', name='Expression')

    def __init__(self):
        super().__init__()

    
class DynamicMathsExpressionEdit_Operator(_DynamicMathsExpression_Operator_common):
    """Edit the selected Maths Expression Group"""
    
    bl_idname = "node.node_dynamic_maths_expression_edit"
    bl_label = "Node Group - Dynamic Maths Expression(Edit)"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamic Maths Expression(Edit)'
    mode = 'EDIT'

    createNew: bpy.props.BoolProperty(name='Create New Group', description='Create a new group rather than updating the existing one (which would affect all group nodes using this group)')
    expressionText: bpy.props.StringProperty(description='Enter the expression', name='Expression')
    
    def __init__(self):
        super().__init__()
        
class DynamicMathsExpressionEditWithin_Operator(_DynamicMathsExpression_Operator_common):
    """Edit the Maths Expression Group from within the group"""
    
    bl_idname = "node.node_dynamic_maths_expression_editwithin"
    bl_label = "Node Group - Dynamic Maths Expression(Edit(Within))"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamic Maths Expression(Edit(Within))'
    mode = 'EDITWITHIN'

    #createNew: bpy.props.BoolProperty(name='Create New Group', description='Create a new group rather than updating the existing one (which would affect all group nodes using this group)')
    expressionText: bpy.props.StringProperty(description='Enter the expression', name='Expression')
    
    def __init__(self):
        super().__init__()
        
class DynamicMathsExpressionNode(bpy.types.NodeCustomGroup):
    """Node to hold the expression text and provide Edit button"""
    
    expressionText: bpy.props.StringProperty(description='', name='Expression')
    
    bl_name='DynamicMathsExpressionNode'
    bl_label='Dynamic Maths Expression'

    # Setup the node - setup the node tree and add the group Input and Output nodes
    def init(self, context):
        print("Node Init")
        self.node_tree=bpy.data.node_groups.new(self.bl_name, 'ShaderNodeTree')
        if hasattr(self.node_tree, 'is_hidden'):
            self.node_tree.is_hidden=False
        self.node_tree.nodes.new('NodeGroupInput')
        self.node_tree.nodes.new('NodeGroupOutput')

    # Draw the node components
    def draw_buttons(self, context, layout):
        #print("draw_buttons(...)")
        #row=layout.row()
        #row.prop(self, 'expressionText', text='Expression')
        row=layout.row()
        row.label(text='Expression: '+str(self.expressionText))
        row=layout.row()
        row.operator('node.node_dynamic_maths_expression_editwithin', text='Edit')
        
        