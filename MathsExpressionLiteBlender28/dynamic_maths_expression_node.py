# Author: Rich Sedman
# Description: Dynamic Maths Expression node (Lite)
# Date: May 2018
################################################### History ######################################################
# 1.0  09/04/2019 : Initial (Lite) version
##################################################################################################################

import bpy
import traceback
import sys
import os

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
    expressionIsValid = True
    storedValidExpression = ""
    #bl_options = {'INTERNAL',}

    def __init__(self):
        super().__init__()

    @classmethod
    def poll(cls, context):
        space = context.space_data

        # Check that it's a ShaderNodeTree, editing 'OBJECT' type and that a node tree (with nodes) exists
        return (space.type == 'NODE_EDITOR') and (space.tree_type == 'ShaderNodeTree') and (space.shader_type == 'OBJECT') and (hasattr(space,"node_tree")) and (hasattr(space.node_tree,"nodes"))

    def invoke(self, context, event):
        wm = context.window_manager
        
        viewWidth = bpy.context.area.width * 0.8
        
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
            
            return wm.invoke_props_dialog(self,width=viewWidth)
               
        else:
            if self.mode in ('EDITWITHIN', 'UPDATE'):
                tree = get_active_node_tree(context)
            
                expressionNode = None
                for node in tree.nodes:
                    if hasattr(node, 'bl_name') and node.bl_name=='DynamicMathsExpressionNode':
                        expressionNode = node
                    
                if expressionNode == None:
                    self.report({'ERROR'}, 'Selected node is not an Expression Group Node')
                    return {"CANCELLED"}
                
                self.expressionText = expressionNode.expressionText
            
                if self.mode == 'UPDATE':
                    self.execute(context)
                    return {"FINISHED"}
                else:
                    return wm.invoke_props_dialog(self, width=viewWidth)
               
            else:
                return wm.invoke_props_dialog(self, width=viewWidth)

    def execute(self, context):
    
        (valid, message) = Expression.valid_expression(self.expressionText)
        
        if not valid:
            self.report({'ERROR'}, 'Invalid expression : '+message)
            self.expressionIsValid = False
            #if 'DynamicMathsExpressionNode' in self.node_tree.nodes.keys():
            #    self.node_tree.nodes['DynamicMathsExpressionNode'].enableRevert = True
            #return {'FINISHED'} # Note : Return 'FINISHED' so as to store the (invalid) entered expression in the operator for re-use next time.
        else:
            self.expressionIsValid = True
            self.storedValidExpression = self.expressionText
        
        if not self.mode in ('CREATE','EDIT') or valid:
            self.execute_main(context)
        return {'FINISHED'}

    # Manage the node's sockets, adding additional ones when needed and removing those no longer required
    def __nodeinterface_setup__(self):
        print("Node interface setup")
        
        # Add the output socket
        if len(self.node_tree.outputs) < 1:
            self.node_tree.outputs.new("NodeSocketFloat", "Value")
        
        return

    variableDefaults = {}
    
    def clearVariableDefaults(self):
        self.variableDefaults.clear()
        
    def storeVariableDefault(self, variable, default):
        self.variableDefaults[variable] = default
        
    def getVariableDefault(self, variable):
        if variable in self.variableDefaults:
            return self.variableDefaults[variable]
        else:
            return None
            
    separateXYZNodes = {}
    
    def clearSeparateXYZNodes(self):
        self.separateXYZNodes.clear()
        
    def storeSeparateXYZNode(self, variable, node):
        self.separateXYZNodes[variable] = node
        
    def getSeparateXYZNode(self, variable):
        if variable in self.separateXYZNodes:
            return self.separateXYZNodes[variable]
        else:
            return None
            
    
        
    # Manage the internal nodes to perform the chained operation - clear all the nodes and build from scratch each time.
    def __nodetree_setup__(self):
        print("Node Setup")
        # Remove all links and all nodes that aren't Group Input or Group Output
        self.node_tree.links.clear()
        for node in self.node_tree.nodes:
            if not node.bl_idname in ['NodeGroupInput','NodeGroupOutput', 'DynamicMathsExpressionNode']:
                self.node_tree.nodes.remove(node)
            #else:
            #    node.location = [0,0]   #TODO: Place these a bit nicer (instead of all at zero)
            
        self.clearVariableDefaults()
        self.clearSeparateXYZNodes()
            
        if 'Dynamic Maths Expression' in self.node_tree.nodes.keys():
            exprNode = self.node_tree.nodes['Dynamic Maths Expression']
        else:
            exprNode = self.node_tree.nodes.new('DynamicMathsExpressionNode')
        exprNode.expressionText  = self.expressionText
        exprNode.enableRevert = (not self.expressionIsValid)
                
        # Start from Group Input and add nodes as required, chaining each new one to the previous level and the next input
        groupinput = self.node_tree.nodes['Group Input']
        previousnode = groupinput

        if self.expressionIsValid:
            exprNode.storedValidExpression = self.storedValidExpression
            
            print("About to parse expression...")
            operations = Expression.parse_expression(self.expressionText)
            
            #outputslot = 0
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
                    
                    exprIsVector = False
                    if exprname.endswith('[]'):
                        exprname = exprname[:-2]
                        exprIsVector = True
                    
                    #Look for this exprname in the outputs
                    found = -1
                    for n in range(0,len(self.node_tree.outputs)):
                        input = self.node_tree.nodes["Group Output"].inputs[n]
                        if input.name == exprname and len(input.links) == 0:
                            found = n
                            break
                    
                    if found < 0:
                        #Not found - so create a new one
                        if exprIsVector:
                            self.node_tree.outputs.new("NodeSocketVector", exprname)
                        else:
                            self.node_tree.outputs.new("NodeSocketFloat", exprname)
                        socket = self.node_tree.nodes["Group Output"].inputs[len(self.node_tree.nodes["Group Output"].inputs)-2]  #TODO: Fix this fudge
                    else:
                        socket = self.node_tree.nodes["Group Output"].inputs[found]
                        
                    self.build_nodes(expr, socket, self.node_tree.nodes['Group Output'].location,0)
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

                    exprIsVector = False
                    if exprname.endswith('[]'):
                        exprname = exprname[:-2]
                        exprIsVector = True
                            
                    #Look for this exprname in the outputs
                    #TODO: Remove this repeated code (it's same as in the ',' processing above)
                    found = -1
                    for n in range(0,len(self.node_tree.outputs)):
                        input = self.node_tree.nodes["Group Output"].inputs[n]
                        if input.name == exprname and len(input.links) == 0:
                            found = n
                            break
                            #TODO: What if multiple Output vectors with same name (ie, this one is found but has 'links'.... Hex example 8 triggers this issue (duplicated elsewhere also!)
                    if found < 0:
                        #Not found - so create a new one
                        if exprIsVector:
                            self.node_tree.outputs.new("NodeSocketVector", exprname)
                        else:
                            self.node_tree.outputs.new("NodeSocketFloat", exprname)
                        
                        socket = self.node_tree.nodes["Group Output"].inputs[len(self.node_tree.nodes["Group Output"].inputs)-2]  #TODO: Fix this fudge
                    else:
                        socket = self.node_tree.nodes["Group Output"].inputs[found]
                        
                    self.build_nodes(expr, socket, self.node_tree.nodes['Group Output'].location,0)

                    break
                    
                #outputslot += 1
            
        
        # Position the Expression Node above the nodes, spanning the Input->Output node distance
        groupInputNode = self.node_tree.nodes['Group Input']
        groupOutputNode = self.node_tree.nodes['Group Output']
        
        exprNode.location[1] = groupOutputNode.location[1]+150                                          # Position at top
        exprNode.width = 500        #Make it reasonably wide
        
        groupOutputNode.location[0] = exprNode.location[0]+exprNode.width-groupOutputNode.width     # Position output at right-edge of exprNode
        #groupOutputNode.location[1] = exprNode.location[1] - 350                                                # Position output just below exprNode
        
        groupInputNode.location[0] = exprNode.location[0]                                           # Position input at left-edge of exprNode
        groupInputNode.location[1] = groupOutputNode.location[1]                                    # Position input just below exprNode

        NodeTreeTools.arrangeBasedOnHierarchy(self.node_tree)

        self.set_group_inputs_defaults()
        
        if self.mode in {'EDIT','EDITWITHIN'}:
            if self.pruneSockets:
                self.prune_group_inputs()
                self.prune_group_outputs()
                
            self.prune_hidden_group_outputs()
            self.prune_hidden_group_inputs()
            
        else:
            self.prune_group_inputs()
            self.prune_group_outputs()
            self.prune_hidden_group_outputs()
            self.prune_hidden_group_inputs()

        if self.resequenceInputs:
            self.resequence_inputs()
            
    
    def build_nodes(self, nested_operations, to_output, output_location,depth,lastoperation=None):
        depth+=1

        print("Build Nodes")
        if len(nested_operations) == 0:
            return
        
        
        operation = nested_operations[0]
        
        print("Build Nodes "+str(nested_operations)+" : "+str(operation))
        
        if operation == 'variable':
            #....link to 'group input'
            variableName = nested_operations[1]
            
            #Allow variable name to include "{<default>}" suffix to set its default (so 'a{123.45}' indicates socket 'a' should default to 123.45)
            (variableName, variableDefault) = Expression.extractVariableDefault(variableName)
            if variableDefault != None:
                print("!!Variable "+variableName+" = "+variableDefault)
                self.storeVariableDefault(variableName, variableDefault)
            
            #TODO: Move 'subscript' processing here - create SeparateXYZ node as needed and link to relevant place
            (variableName, variableSubscript) = Expression.extractVariableSubscript(variableName)
            
            if variableSubscript != None:
                separateNode = self.getSeparateXYZNode(variableName)
                
                if separateNode == None:
                    separateNode = self.node_tree.nodes.new('ShaderNodeSeparateXYZ')
                    self.storeSeparateXYZNode(variableName, separateNode)
                    
                    #Link separateXYZ node to Group Input
                    if variableName in self.node_tree.nodes['Group Input'].outputs.keys():
                        self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[variableName],separateNode.inputs[0])
                    else:
                        # Add a new socket
                        self.node_tree.inputs.new("NodeSocketVector", variableName)
                        self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[-2],separateNode.inputs[0])  # Add link to group input we just added (-1 is 'blank' socket, -2 is last 'real' socket)
        
                    
                if variableSubscript in ('0', 'x', 'r'):
                    subnum = 0
                elif variableSubscript in ('1', 'y', 'g'):
                    subnum = 1
                elif variableSubscript in ('2', 'z', 'b'):
                    subnum = 2
                else:
                    subnum = -1     # No subscript - throw an error?
                
                #Link node to relevant output of SeparateXYZ node
                self.node_tree.links.new(separateNode.outputs[subnum],to_output)
                
            else:
            
                if variableName in self.node_tree.nodes['Group Input'].outputs.keys():
                    self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[variableName],to_output)
                else:
                    # Add a new socket
                    self.node_tree.inputs.new("NodeSocketFloat", variableName)
                    self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[-2],to_output)  # Add link to group input we just added (-1 is 'blank' socket, -2 is last 'real' socket)
        
        elif operation == 'value':
            #create new 'Value' node and link to to_output
            newnode = self.node_tree.nodes.new('ShaderNodeValue')
            print("Value = '"+str(nested_operations[1])+"'")
            newnode.outputs[0].default_value = float(nested_operations[1])
            self.node_tree.links.new(newnode.outputs[0],to_output)
            
        elif operation == 'combine':
            #create new 'combineXYZ' node and link to output
            newnode = self.node_tree.nodes.new('ShaderNodeCombineXYZ')
            self.node_tree.links.new(newnode.outputs[0],to_output)

            # Repeat for sub-nodes
            self.build_nodes(nested_operations[1], newnode.inputs[0], [0,0],depth)
            if len(nested_operations) > 2:
                if nested_operations[2][0] != ',':
                    self.build_nodes(nested_operations[2], newnode.inputs[1], [0,0],depth,lastoperation=lastoperation)
                else:
                    self.build_nodes(nested_operations[2][1], newnode.inputs[1], [0,0],depth,lastoperation=lastoperation)
                    self.build_nodes(nested_operations[2][2], newnode.inputs[2], [0,0],depth,lastoperation=lastoperation)
                

        else:
            # create a new 'Maths' node
            newnode = self.node_tree.nodes.new('ShaderNodeMath')
            
            # If operation is for additional function arguments (',') then use same operation as before (eg, for max(x,y,z,....)
            if operation == ',' and lastoperation != None:
                operation = lastoperation
            
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
                #newnode.operation = "***unexpected comma***"
                raise Exception('build_nodes : Unexpected comma')
                
            else:
                #print("Unknown operation '"+ str(operation)+"'")
                #newnode.operation = "Unknown"
                raise Exception('build_nodes : Unknown operation '+str(operation))
            
            lastoperation = operation
            
            # link output to to_output
            self.node_tree.links.new(newnode.outputs[0],to_output)
            
            newlocation = output_location
            newlocation[0] -= 1/depth
            newnode.location = newlocation

            # Repeat for sub-nodes
            self.build_nodes(nested_operations[1], newnode.inputs[0], newlocation,depth)
            if len(nested_operations) > 2:
                newlocation[1]+=1/depth
                self.build_nodes(nested_operations[2], newnode.inputs[1], newlocation,depth,lastoperation=lastoperation)
                
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
                        
    def prune_hidden_group_outputs(self):
        for output in self.node_tree.outputs:
            if output.name[0] == '_':
                self.node_tree.outputs.remove(output)
                print("Removed "+output.name)
                
    def prune_hidden_group_inputs(self):
        #Remove any outputs that start with '_' (these are 'hidden' outputs to be internal to the node group
        for input in self.node_tree.inputs:
            if input.name[0] == '_':
                self.node_tree.inputs.remove(input)
                print("Removed "+input.name)
                
    def set_group_inputs_defaults(self):
        #Process all the group inputs, setting the default for that socket
        for input in self.node_tree.inputs:
            defaultValue = self.getVariableDefault(input.name)
            
            if defaultValue != None:
                if input.type == 'VECTOR':
                    input.default_value = [float(defaultValue),float(defaultValue),float(defaultValue)]   #TODO: Perhaps support defaulting to an actual vector rather than a float converted to a vector. Also, possibly support other types....?
                else:
                    input.default_value = float(defaultValue)   #TODO: Detect socket type and handle different types (int, string?, Vector, etc.)

            if self.groupnode != None and self.mode in ('CREATE', 'EDIT'):
                #Set the 'groupnode' value for unconnected node
                if input.name in self.groupnode.inputs:
                    self.groupnode.inputs[input.name].default_value = input.default_value
                
            else:
                if input.type == 'VECTOR':
                    input.default_value = [0,0,0]
                else:
                    input.default_value = 0
                
            
    def resequence_inputs(self):
        # Resequence the inputs based on label length and content
        # 'Short' fields (two or less alpha chars) will be sorted to the top
        #outputs = self.node_tree.nodes['Group Input'].outputs
        inputs = self.node_tree.inputs
        for socketNo in range(1,len(inputs)):
            compareSocketNo = socketNo - 1
            while compareSocketNo >= 0:
                thisSocketName = inputs[socketNo].name
                compareSocketName = inputs[compareSocketNo].name
                
                if self.resequence_inputs_comparator(thisSocketName, compareSocketName) < 0 :
                    self.report({'INFO'},"Comparing to the one above")
                    compareSocketNo = compareSocketNo - 1
                else:
                    self.report({'INFO'},"Stopped search")
                    break
            
            if (compareSocketNo+1) == socketNo:
                #It's already in the correct place
                pass
            else:
                #move it - move socketNo to position compareSocketNo+1
                inputs.move(socketNo, compareSocketNo+1);
                self.report({'INFO'},"Moved socket "+str(socketNo)+" to position "+str(compareSocketNo+1))
                
        
    #Compare 'first' with 'second'. Short values will always be before "long" ones (>2 chars)
    #and numerics will be ignored when determining length - so 'x' will be before 'abc' but
    #'x2' will be after 'x1'. This way, single or double letter variables will appear towards
    #the top of the list while more descriptive values will be towards the bottom.
    #(eg, dx,dy,dz,x,x2,y,y2,z,z2,amplitude,scale,width)
    def resequence_inputs_comparator(self, first, second):
  
        self.report({'INFO'},"Compare '"+first+"' with '"+second+"'")
  
        # strip trailing numerics to create firstStripped, secondStripped
        firstStripped = self.resequence_inputs_strip_numerics(first)
        secondStripped = self.resequence_inputs_strip_numerics(second)

        #TODO: Use numeric suffix to further group eg, x,y,z,dx,dy,dz,x2,y2,z2,dx2,dy2,dz2
        
        if len(firstStripped)<=2 and len(secondStripped)>2:
            #'first' is short while 'second' is long
            self.report({'INFO'},"Less")
            return -1   #Less than
            
        if len(firstStripped)>2 and len(secondStripped)<=2:
            #'first' is long while 'second' is short
            self.report({'INFO'},"Greater")
            return 1    #Greater than
                
        #'first' is similar length to 'second' so simply compare
        if first < second:
            self.report({'INFO'},"Less2")
            return -1    #Less than
        if first > second:
            self.report({'INFO'},"Greater2")
            return 1   #Greater than
            
        self.report({'INFO'},"Same")
        return 0 #Same
        
    def resequence_inputs_strip_numerics(self, s):
        #TODO: Strip numerics
        return s
            
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
                self.groupnode = groupnode
            
            else:
                if self.mode == 'EDIT':
                # Update existing node group (assume selected node is the one to edit)
                    groupnode = context.selected_nodes[0]
                    self.node_tree = groupnode.node_tree
                    self.groupnode = groupnode

                    if self.createNew:
                        groupnode.node_tree=bpy.data.node_groups.new("DynamicMathsExpressionGroup", 'ShaderNodeTree')
                        groupnode.node_tree.nodes.new('NodeGroupInput')
                        groupnode.node_tree.nodes.new('NodeGroupOutput')

                else:   #EDITWITHIN
                    self.node_tree = get_active_node_tree(context)
                    self.groupnode = None
                
            #groupnode.label = 'Expr: '+str(self.expressionText)
                
        #Add a dummy 'Group Output' and make it active to effectively 'mute' this group while we make changes
        dummyGroupOutputNode = self.node_tree.nodes.new('NodeGroupOutput')
        dummyGroupOutputNode.name = 'Dummy Group Output'
        dummyGroupOutputNode.is_active_output = True
        self.node_tree.nodes["Group Output"].is_active_output = False
        
        try:
            self.__nodeinterface_setup__()
            self.__nodetree_setup__()
        except Exception as exception:
            self.report({'ERROR'},'Build of node tree failed : '+str(exception))
            
        #Activate the actual output node and remove the dummy one
        self.node_tree.nodes["Group Output"].is_active_output = True
        dummyGroupOutputNode.is_active_output = False
        self.node_tree.nodes.remove(dummyGroupOutputNode)
        
    def check(self, context):
        return True     # For now, always redraw    #TODO: Detect when we need to redraw
        
    def draw(self, context):
        layout = self.layout
        layout.label(text="Maths Expression")

        if self.mode == 'EDIT':
            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(self, "createNew")
            
        row = layout.row()
        row.prop(self, "expressionText")
                
        if self.mode == 'EDIT' or self.mode == 'EDITWITHIN':
            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(self, "pruneSockets")
            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(self, "resequenceInputs")
            
            
            
class DynamicMathsExpression_Operator(_DynamicMathsExpression_Operator_common):
    """Create a new Maths Expression Group"""
    bl_idname = "node.node_dynamic_maths_expression"
    bl_label = "Node Group - Dynamic Maths Expression"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamice Maths Expression'
    mode = 'CREATE'
    #bl_options = {}

    
    expressionText: bpy.props.StringProperty(description='Enter the expression', name='Expression')
    resequenceInputs: bpy.props.BoolProperty(name='Auto-sequence Inputs', description='Automatically resequence input sockets')
    
    def __init__(self):
        super().__init__()
        self.resequenceInputs = True
        
    
class DynamicMathsExpressionEdit_Operator(_DynamicMathsExpression_Operator_common):
    """Edit the selected Maths Expression Group"""
    
    bl_idname = "node.node_dynamic_maths_expression_edit"
    bl_label = "Node Group - Dynamic Maths Expression(Edit)"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamic Maths Expression(Edit)'
    mode = 'EDIT'
    #bl_options = {}


    createNew: bpy.props.BoolProperty(name='Create New Group', description='Create a new group rather than updating the existing one (which would affect all group nodes using this group)')
    pruneSockets: bpy.props.BoolProperty(name='Prune Inputs/Outputs', description='Automatically remove unused sockets')
    resequenceInputs: bpy.props.BoolProperty(name='Auto-sequence Inputs', description='Automatically resequence input sockets')
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
    bl_options = {'INTERNAL',}


    #createNew: bpy.props.BoolProperty(name='Create New Group', description='Create a new group rather than updating the existing one (which would affect all group nodes using this group)')
    pruneSockets: bpy.props.BoolProperty(name='Prune Inputs/Outputs', description='Automatically remove unused sockets')
    resequenceInputs: bpy.props.BoolProperty(name='Auto-sequence Inputs', description='Automatically resequence input sockets')
    expressionText: bpy.props.StringProperty(description='Enter the expression', name='Expression')
    
    def __init__(self):
        super().__init__()


class DynamicMathsExpressionRevert_Operator(_DynamicMathsExpression_Operator_common):
    """Revert the Maths Expression back to the last know valid expression"""
    
    bl_idname = "node.node_dynamic_maths_expression_revert"
    bl_label = "Node Group - Dynamic Maths Expression(Revert)"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamic Maths Expression(Revert)'
    mode = 'REVERT'
    bl_options = {'INTERNAL',}


    pruneSockets: bpy.props.BoolProperty(name='Prune Inputs/Outputs', description='Automatically remove unused sockets')
    resequenceInputs: bpy.props.BoolProperty(name='Auto-sequence Inputs', description='Automatically resequence input sockets')
    expressionText: bpy.props.StringProperty(description='Enter the expression', name='Expression')

    def __init__(self):
        super().__init__()

        #find Dynamic Maths Node
        node_tree = get_active_node_tree(bpy.context)
        if 'Dynamic Maths Expression' in node_tree.nodes.keys():
            exprNode = node_tree.nodes['Dynamic Maths Expression']
            self.expressionText = exprNode.storedValidExpression
        else:
            self.expressionText = "!!! Can't retrieve expression"
        
        #trigger re-build - continue with execution of the operator
        
    
class DynamicMathsExpressionNode(bpy.types.NodeCustomGroup):
    """Node to hold the expression text and provide Edit button"""
    
    expressionText: bpy.props.StringProperty(description='', name='Expression')
    storedValidExpression: bpy.props.StringProperty(description='', name='Saved Expression')
    enableRevert: bpy.props.BoolProperty()
    
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

    #def copy(self, node):
    #    self.expressionText = node.expressionText
    #    self.storedValidExpression = node.storedValidExpression
    #    self.enableRevert = node.enableRevert
        
    # Draw the node components
    def draw_buttons(self, context, layout):
        #print("draw_buttons(...)")
        #row=layout.row()
        #row.prop(self, 'expressionText', text='Expression')
        row=layout.row()
        row.label(text='Expression: '+str(self.expressionText))
        row=layout.row()
        #row.label(text='Saved Expression: '+str(self.storedValidExpression))
        #row=layout.row()
        row.operator('node.node_dynamic_maths_expression_editwithin', text='Edit')

        layout.alert = self.enableRevert
        if self.enableRevert and self.storedValidExpression != "":
            row=layout.row()
            row.operator('node.node_dynamic_maths_expression_revert', text='Node is invalid! - Click to Revert')
            
        