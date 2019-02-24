# Author: Rich Sedman
# Description: Dynamic Maths Expresion node
# Version: (0.45)
# Date: May 2018
################################################### History ######################################################
# 0.4  01/06/2018 : Remove old redundant code
# 0.41 02/06/2018 : Fix pruning of group inputs that are no longer required
# 0.42 06/06/2018 : Start to support multiple expressions and improve auto-layout
# 0.43 11/06/2018 : Move node layout tools into a separate class
# 0.44 11/06/2018 : Prune inputs and outputs no longer required for multi-expressions
# 0.45 15/06/2018 : Fix allocation of name when adding multiple new outputs
##################################################################################################################

# New design for Blender 2.8 :
#
# New NodeCustomGroup node can be added to a nodetree as now. However, when expression entered,
# instead of changing its own internal nodetree for the expression, create a new node group
# and replace the current node with a 'Group' node with that new group, named 'Expr:<expresion>'
# Within the group, add the 'custom' node which will reside within the group and act as a
# 'controller', detecting changes to the expression (either via its own Expression field or by the
# user changing the name of the NodeGroup. The 'custom' node should size and place itself over the
# top of the internal nodes. The node should also have an 'apply' button that will turn it into a
# 'normal' group so it can no longer be dynamically updated.
#
# Development strategy :
# 1) Change the existing node so that when entering an expression it replaces itself with a Group node
#    and moves itself within that group. The expression should update the internal nodes of that group
#    which should automatically create sockets for input/output - as now.
# 2) Enhance the Custom node so as to position itself over the nodes and changing the expression changes
#    those nodes.
# 3) Enhance the Custom node to detect changes in group name and automatically update its Expression and
#    thus its associated nodes.
# 4) Create 'Apply' to remove the Custom node and leave it as a 'normal' group. This should probably
#    remove the 'Expr:' prefix also.
# 5) Cater for multiple groups with the same name (by allowing for any '.001' suffix.
# 6) Relocate the 'Add' menu so it's in the Group menu rather than 'Custom Nodes'.
#
# NOTE : I'm having trouble integrating with NodeCustomGroup... therefore, suggest an alternative approach
# 1) Create as a modal operator - new option in Group menu to Add Expression Group
# 2) Selecting this will popup a dialog box prompting for the expression
# 3) Accepting the window with a valid expression will build the group
# 4) If within an existing group then an option to 'edit expression' will be available (need to determine how we'll pickup the 'old' expression for editing since we won't actually be holding it anywhere... could use the 'group' name...?)
# 5) Editing the expression will update the expression similar to how editing the expression already doesn



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
    # the same as context.active_node, the user is in a group.
    # Check recursively until we find the real active node_tree:
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

    return tree


class DynamicMathsExpression_Operator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "node.node_dynamic_maths_expression"
    bl_label = "Node Group - Dynamic Maths Expression"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamice Maths Expression'

    expressionText: bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR'
        
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        DynamicMathsExpression_Operator.execute_main(self, context)
        return {'FINISHED'}

    def execute_main(self, context):
        space = context.space_data
        #node_tree = space.node_tree
        node_active = context.active_node
        node_selected = context.selected_nodes
        
        #validate the expression?
        #expression = Expression.parse_expression(self.expressionText)
        #print("TODO: need to check that the entered expression was valid!!")
        
        #    ...create 'group'
        #    ...update the new group node's nodetree
        print(context)
        if context.space_data.type == 'NODE_EDITOR' and context.space_data.node_tree is not None:
            #newnode = self.parent.node_tree.nodes.new('ShaderNodeGroup')
            tree = context.space_data.node_tree #TODO : This seems unnecessary as we don't need this tree now
            newnode = get_active_node_tree(context).nodes.new('ShaderNodeGroup')
            
            #TODO: Position and size the node in centre of window and preferably put it in 'Grab' mode
            #newnode.location = self.location
            #newnode.width = self.width
            
            # Point the nodegroup at our new node group
            #newnode.node_tree = new bpy.types.ShaderNodeTree(name = 'DynamicMathsExpressionNodeTree')
            newnode.node_tree=bpy.data.node_groups.new("DynamicMathsExpressionGroup", 'ShaderNodeTree')
            newnode.node_tree.nodes.new('NodeGroupInput')
            newnode.node_tree.nodes.new('NodeGroupOutput')
            
            
            # TODO :  need to move the Custom node into the nodegroup. For now, just (try and) remove it
            #print("Adding...")
            #newCustomNode = newnode.node_tree.nodes.new(self.bl_idname)
            #newCustomNode.__init__()
            #newCustomNode.location = (-250,250)
            #print("Create: newCustomNode.mode = "+str(newCustomNode.mode))
            #newCustomNode.set_mode('Active')
            #print("Create(after): newCustomNode.mode = "+str(newCustomNode.mode))
            #print("ID : "+str(newCustomNode.as_pointer()))
            #TODO : (this causes infinite looping) newCustomNode.expressionText = self.expressionText
            #print(self.bl_idname)
            #print("Added")
            #print("Removing...")
            #self.get_active_node_tree(context).nodes.remove(self)
            #print("Removed")#    ...create 'group'
        
        #!!!NOTE : Need to have checks that there is only one 'selected'
        #NodeTreeTools.arrangeBasedOnHierarchy(node_selected[0])
        self.node_tree = newnode.node_tree
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()
        
        #TODO : Put all 'inner' nodes in a Frame with a label based on the expression.
        #(eg, select 'Group Output', select all 'linked' nodes, trigger 'create Frame')
        
        #TODO : Implement 'edit' mode where we can pickup the expression (from frame label) and edit it.
        #(ensure just one node is selected, ensure it's a Group node with a 'label' frame, retrieve expression, pre-populate field
        # also, could provide checkbox to indicate whether should edit existing or create new. Edit existing should alter existing
        # Group Input/Output to preserve links)
        
#Added code to trim down to produce operator version
    # Manage the node's sockets, adding additional ones when needed and removing those no longer required
    def __nodeinterface_setup__(self):
        print("Node interface setup")
        # No operators --> no inpout or output sockets
        #if self.inputSockets < 1:
        #self.node_tree.inputs.clear()
        #self.node_tree.outputs.clear()
        
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
        
        #for l in range(1,100):
        #    print("Arrange("+str(l)+")")
        #    NodeTreeTools.arrange_nodes(self.node_tree, l>2, True)
        NodeTreeTools.arrangeBasedOnHierarchy(self.node_tree)
        
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

    #End of added code

class DynamicMathsExpressionNode(bpy.types.NodeCustomGroup):

    bl_name='DynamicMathsExpression'
    bl_label='Dynamic Maths Expression'
    _debug = True
    mode = None
    
    def __init__(self):
        #Prevent re-calling of __init__ (shouldn't be required! TODO)
        if self.mode == None:
            self.mode = 'Inactive'
            print("__init__ called")
        else:
            print("!!! __init__ called out of sequence")
        
    # Manage the node's sockets, adding additional ones when needed and removing those no longer required
    def __nodeinterface_setup__(self):
        print("Node interface setup")
        # No operators --> no inpout or output sockets
        #if self.inputSockets < 1:
        #self.node_tree.inputs.clear()
        #self.node_tree.outputs.clear()
        
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
        
        #for l in range(1,100):
        #    print("Arrange("+str(l)+")")
        #    NodeTreeTools.arrange_nodes(self.node_tree, l>2, True)
        NodeTreeTools.arrangeBasedOnHierarchy(self.node_tree)
        
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
                
    # Expression has changed - update the nodes and links
    def update_expression(self, context):
        
        if self.mode == 'Active':
            return
        
        print("update_expression(...)")
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()
        
        #...instead of the above...
        #    ...create 'group'
        #    ...move this node into the 'group'
        #    ...update the new group node's nodetree
        print(context)
        if context.space_data.type == 'NODE_EDITOR' and context.space_data.node_tree is not None:
            #newnode = self.parent.node_tree.nodes.new('ShaderNodeGroup')
            tree = context.space_data.node_tree #TODO : This seems unnecessary as we don't need this tree now
            newnode = self.get_active_node_tree(context).nodes.new('ShaderNodeGroup')
            newnode.location = self.location
            newnode.width = self.width
            
            # Point the nodegroup at our new node group
            newnode.node_tree = self.node_tree.copy()
            
            # TODO :  need to move the Custom node into the nodegroup. For now, just (try and) remove it
            print("Adding...")
            newCustomNode = newnode.node_tree.nodes.new(self.bl_idname)
            newCustomNode.__init__()
            newCustomNode.location = (-250,250)
            print("Create: newCustomNode.mode = "+str(newCustomNode.mode))
            newCustomNode.set_mode('Active')
            print("Create(after): newCustomNode.mode = "+str(newCustomNode.mode))
            print("ID : "+str(newCustomNode.as_pointer()))
            #TODO : (this causes infinite looping) newCustomNode.expressionText = self.expressionText
            print(self.bl_idname)
            print("Added")
            print("Removing...")
            self.get_active_node_tree(context).nodes.remove(self)
            print("Removed")
        
    expressionText: bpy.props.StringProperty(name="Expression", update=update_expression)


    # Adapted from Node Wrangler add-on function
    def get_active_node_tree(self, context):
        tree = context.space_data.node_tree

        # Get nodes from currently edited tree.
        # If user is editing a group, space_data.node_tree is still the base level (outside group).
        # context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
        # the same as context.active_node, the user is in a group.
        # Check recursively until we find the real active node_tree:
        if tree.nodes.active:
            while tree.nodes.active != context.active_node:
                tree = tree.nodes.active.node_tree

        return tree

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
        row=layout.row()
        row.prop(self, 'expressionText', text='Expression')
        
        if self._debug:
            row = layout.row()
            row.label(text = 'Debug: ')
            row.label(text = str(self._debug))
            row = layout.row()
            row.label(text = 'Mode: ')
            row.label(text = str(self.mode))
            row = layout.row()
            row.label(text = 'ID')
            row.label(text = str(self.as_pointer()))
            row = layout.row()
            row.label(text = 'NodeTree')
            row.label(text = str(self.node_tree))

    #def dumpstack(self):
    #    exc_type, exc_value, exc_traceback = sys.exc_info()
    #    print(traceback.format_list(traceback.extract_stack()))

    def set_mode(self, mode):
        self.mode = mode
        
    # Copy
    def copy(self, node):
        # Should not be needed - but it seems this can be called before __init__ (TODO)
        if self.mode == None:
            print("!!! copy(...) called before __init__")
            return
            
        print("copy(...)")

        #self.node_tree=node.node_tree.copy()
        #NOTE : This is wrong as it produces two nodes that use the same tree
        
        print("Self mode = "+str(self.mode) + ", Node mode = "+str(node.mode))
        
        self.node_tree=node.node_tree
        self.mode = node.mode
        self.mode = 'Clone'
        
        if (self == node):
            print("Same!")
        else:
            print("Different!")
        
        #self.dumpstack()
        
    # Free (when node is deleted)
    def free(self):
        print("Node Deleted")
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)
