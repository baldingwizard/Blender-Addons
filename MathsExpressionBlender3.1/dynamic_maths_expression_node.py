# Author: Rich Sedman
# Description: Dynamic Maths Expression node
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
# 0.99b 06/03/2019 : Add properties for 'pruneSockets' and 'autoSequenceInputs'
# 0.99c 11/03/2019 : Position 'custom' node in relation to the Output instead of Input node
# 0.99d 11/03/2019 : Store last 'valid' expression and allow it to be restored in event of invalid expression
# 1.00 14/03/2019 : Some final refinement - I think it's about good enough for version 1.00 now.
# 1.01 25/03/2019 : Add and activate a 'dummy' group output while the internal nodes are being manipulated
#                   to effectively 'mute' the group while it is being changed (to prevent anything accessing the
#                   nodes while they are being added/removed/relinked). Fixed issues with '==' operator and other
#                   expression-parsing refinements.
# 1.02 27/03/2019 : Improve node tree building so as to reuse identical fragments of expressions
# 1.03 29/03/2019 : Allow expression to be sourced from a text block with 'TEXT:<textblock>'. Textblock can
#                   include comments
# 1.04 29/03/2019 : Allow variable defaults to be specified as a sub-expression of the format 'var{default}'
# 1.05 30/03/2019 : Support specifying defaults by including suffix to variable. eg, 'a{5.65}' to init a to 5.65.
# 1.06 01/04/2019 : Enhance Node to provide 'Update from textblock' button when expression is from a text block
# 1.07 01/04/2019 : Support 'combine(...)' to CombineXYZ to build vectors
# 1.08 01/04/2019 : Outputs suffixed with '[]' are added as a Vector
# 1.09 04/04/2019 : Allow suffixes on input variables (and sub-expressions) to allow input Vectors
# 1.10 06/04/2019 : Refine 'poll' so that option is only available if valid node tree is present
# 1.11 06/04/2019 : Read a 'presets' directory to provide sample preset expressions
# 1.12 08/04/2019 : Allow presets to be used to populate to text block to allow easier editing
# 1.13 14/04/2019 : Allow presets to inclulde 'options' which can be switched by user in operator
# 1.14 23/04/2019 : Add exception trap to building of presets to guard against file access issues
# 1.15 23/04/2019 : Improve expression parsing for +,-,*,/ to fix precedence problems
# 1.16 24/04/2019 : Support 'Input.xxx' special variables for Generated, Normal, UV, Object, Window, Reflection,
#                   camera coords. Also, 'object.xxx', 'particle.xxx', 'geom.xxx' for other common inputs
# 1.17 25/04/2019 : Trying to get additional functions working (starting with Noise)
# 1.18 27/04/2019 : Implemented vmult and vdiv functions
# 1.19 29/04/2019 : Fix bug that caused wrong tree to be updated when editing/updating/etc.
# 1.20 30/04/2019 : Removed unnecessary diagnostic output.
# 1.21 01/05/2019 : Put each sub-expression into its own Node Group. This make it look much neater as well as 
#                   significantly improving the UI responsiveness when amending the node tree and node properties
#                    Also, add 'Documentation' button to bring up text area populated with documentation
#                    Also,name newly created sub-groups and automatically remove those being replaced.
#                    Also, make the newly added group the 'active' node
# 1.22 16/05/2019 : Optimise the sub-groups by merging duplicated inputs
#                   Fix bug in 'grouping' logic
# 1.23 17/05/2019 : Tidy up opening of Documentation window
#                   Ensure last sub-expression is in its own group
#                   Pass expression name into build_nodes function to assign to groups and use it to label the 
#                   group node
#                   Remove 'Value' nodes after applying as the 'default_value' to their destination socket
# 1.24 19/05/2019 : Added support for musgrave(...) function and sub-functions (musgrave.mf(...), musgrave.rmf(...), etc.)
#                   Implement voronoi(...) and voronoi.cell(...) functions
#                   Also, started to implement colorramp (but not finished)
#                   Also, implemented 'group' creation for iteration
# 1.25 05/06/2019 : Completed implementation of colorramp (and allowed for upper/lower case options (eg, 'bspline'))
# 1.26 08/06/2019 : Implement undo_push checkpoints when executing operator
# 1.27 01/07/2019 : Implement options on Voronoi texture for new 2.8 modes (eg, Crackle)
# 1.28 05/07/2019 : Set label text on custom node to point to https://baldingwizard.wixsite.com/blog/node-expressions
#                   for info should the add-on not be installed/enabled.
# 1.29 08/07/2019 : Don't merge Value into connected socket if the 'to' node is a 'Group' node.
# 1.30 19/07/2019 : Unset material 'use_nodes' to disable the nodes while we're re-building the tree and enabled afterwards.
#                   Also, revamp hidden output processing to avoid repeated add/remove that appeared to be causing crashes.
#                   Also, revamp node layout (required due to Reroute nodes used for hidden output linking). Also, label
#                   the hidden variable Reroute nodes as they're a useful addition to the tree to indicate content.
# 1.31 20/07/2019 : Don't merge Value nodes into Reroute nodes(!)
# 1.32 24/07/2019 : Temporarily disable all materials by setting use_nodes while we update the group, re-enabling when done.
#                   Also, delay for a short period before removing a group output to allow renderer to have finished with nodes.
# 1.33 29/07/2019 : Added constants as quoted strings to process as "values". Can use this for '"pi"' or '"e"' so
#                   could write expressions as 'sin(value * "pi" * 2)', for example.
# 1.34 12/08/2019 : Added 'inputs(...)' and 'outputs(...)' to allow input/output variables to be defined (instead of having to
#                   prefix hidden variables with '_')
# 1.35 14/08/2019 : Implement 'functions' with 'function:start(<name>, ...)', 'function:end(<name>, ...)', 'fn:<name>(...)'
# 1.36 10/09/2019 : clearSeparateXYZNodes when ending a group to ensure we can handle similarly named vectors in sub-groups/functions
# 1.37 13/09/2019 : Allow 'include ...' or 'import ...' to import text from another text block
# 1.38 29/05/2020 : Make compatible with new 2.82 Maths nodes which can now have more than 2 inputs (which caused a problem
#                   when building the node tree since we used the number of inputs to identify the node type)
# 1.39 27/08/2020 : Make compatible with new 2.83 multi-dimensional texture nodes (caused a problem with the new 'W' input dimension)
##################################################################################################################

#TODO: Additional Voronoi modes - eg, Closest-n Cell (currently only allow for closest-n intensity)
#TODO: Allow expressions in quoted constants - eg, would be nice if could evaluate '"2*pi"' in same way as if typed directly into a field
#TODO: Trap unknown function with a more meaningful message than currently produced - ie, should say something like 'Invalid function "....."'
#TODO: Entering an expression as 'Input.Generated' produces a *scalar* output. Also, entering 'Input.Generated[]' doesn't work.
#TODO: Place all nodes within a frame labelled "Nodes generated by Node Expressions add-on"
#TODO: Group inputs with no input do not generate set value (defaults to 0.5 instead - at least, in 2.8 Eevee). Probably need to ensure there's a Value node attached in those cases
#TODO: When using Input.generated, node gets left behind in Edit mode(s) unless you explicitly set 'pruneSockets'. The linking should remove it automatically if it's no longer used
#TODO: Refine spacing when applying layout - eg, including Color Ramp spreads everything out too far!
#TODO: Implement color socket - eg, by suffixing with '[c]' instead of '[]'

#TODO: Settings panel to be able to indicate whether to use 'latest' functionality or keep 'compatible' (eg, 'ATAN2', 'SQRT', 'CEIL', 'FLOOR', etc.)

#TODO: Change type of existing input socket by adding/removing '[]' (currently it will retain it's previous type unless removed and re-added - eg, add expression 'noise(input, scale)' then change it to 'noise(input[], scale)' - should change the input type to a vector (actually add a new vector input and prune the old one if pruning is enabled) but it actually leaves it as the scalar input))
#TODO: Possibly implement 'BOOLEAN' socket type...? Could use this to indicate whether input coords were 'Object' or 'Generated' for whether it should have origin at zero (eg, for waves presets, whether centred around 0.0 or 0.5)
#TODO: Investigate other socket types as there are Bool, Color, Float, FloatAngle, FloatFactor, FloatPercentage, FloatTime, FloatUnsigned, Int, IntFactor, IntPercentage, IntUnsigned, Shader, Standard, String, Vector, VectorAcceleration, VectorDeceleration, VectorDirection, VectorEuler, VectorTranslation, VectorVelocity, VectorXYZ, Virtual. Phew.
#TODO: Expand usage to be able to use in Compositor as well as Shader node trees
#TODO: Name the sub-group sockets if they're connected to something that already has a name. eg, group inputs or labelled sub-group outputs (currently they're all named as 'Value')

#TODO: Add better diagnostics to advise on the reason for expression parse failure

#TODO: Enhance custom node to store the checkbox states between saves
#TODO: Use Preset Name to populate the name of the created Node Group
#TODO: Add 'debug' mode to allow debug output to be switched (similar to parse expression debug mode)
#TODO: Possibly make the groups hidden from the 'Group' list...?

import bpy
import traceback
import sys
import os
import time

from .parse_expression import Expression
from .node_tree_tools import NodeTreeTools

def get_active_node_tree(context):

    #Get the last path
    return context.space_data.path[-1].node_tree
    
    
#Note: Expression options
#Blank lines and those that start with '#' are ignored.
#Lines that start with '?' are queries for the user, followed by the prompt and a ':', with the
#rest of the line indicating the options. eg, '?Input:XY,Vector,Generated,Object'
#Lines that start with ':<option>:' are the conditional sections, with the rest of the line only
#present in the final output if <option> contains at least one of the selected options. For example,
#':Vector:X = Vector[x], Y = Vector[y]'
def getExpressionTextInputs(text):
    inputs = []
    for line in text.splitlines():
        linetxt = line.strip()
        
        if linetxt.startswith('?') and (':' in linetxt):
            elements = linetxt[1:].split(':')
            inputLabel = elements[0]
            inputOptions = elements[1]
            
            inputs.append((inputLabel, inputOptions))
    
    return inputs

class _DynamicMathsExpression_Operator_common(bpy.types.Operator):
    mode = 'NONE'
    expressionIsValid = True
    storedValidExpression = ""
    #bl_options = {'INTERNAL',}
    bl_options = {'REGISTER', 'GRAB_CURSOR'}


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
        viewWidth = int(viewWidth)
        
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
            if self.mode in ('EDITWITHIN', 'UPDATE','REVERT'):
                if self.node_tree_name != '':
                    #print("Got a 'clickedNode' ("+self.node_tree_name+") - setting it active!");
                    tree = bpy.data.node_groups[self.node_tree_name]
                else:
                    #print("Couldn't determine node_tree - guessing based on currently 'active' node tree");
                    tree = get_active_node_tree(context)
            
                expressionNode = None
                for node in tree.nodes:
                    if hasattr(node, 'bl_name') and node.bl_name=='DynamicMathsExpressionNode':
                        expressionNode = node
                    
                if expressionNode == None:
                    self.report({'ERROR'}, 'Selected node is not an Expression Group Node')
                    return {"CANCELLED"}
                
                if self.mode != 'REVERT':
                    self.expressionText = expressionNode.expressionText
            
                if self.mode == 'UPDATE':
                    self.execute(context)
                    return {"FINISHED"}
                else:
                    return wm.invoke_props_dialog(self, width=viewWidth)
               
            else:
                return wm.invoke_props_dialog(self, width=viewWidth)

    def decodeExpressionText(self,text):
        
        if text[0:5] == 'TEXT:':
        
            try:
                text = bpy.data.texts[text[5:]].as_string()
            except Exception as exception:
                self.report({'ERROR'}, "Unable to open text block '"+text[5:]+"'")
                return "()"
        
        concatenatedText = ""
        for line in text.splitlines():
            linetxt = line.strip()
            if linetxt != "" and not linetxt.startswith('#'):
                
                #Detect 'include ....' line to include another text block or file
                #   The argument must be quoted and should start with 'TEXT:....' to indicate source from text block
                #TODO: Allow import from 'FILE:' (or no suffix to indicate file). Optional file prefix should indicate location (// relative, / absolute, otherwise assume within add-on 'include' library
                #print("LINETXT="+linetxt)
                if linetxt.startswith("include ") or linetxt.startswith("include\t") or linetxt.startswith("import ") or linetxt.startswith("import\t"):
                    #print("INCLUDE/IMPORT")
                    includetext = linetxt[7:].strip()
                    
                    if (includetext.startswith("'") and includetext.endswith("'")) or (includetext.startswith('"') and includetext.endswith('"')):
                        includetext = includetext[1:-1]        #Strip leading and trailing quotes to leave just the include name
                        if includetext.startswith("TEXT:"):
                            textblock = includetext[5:]
                
                            if textblock in bpy.data.texts.keys():
                                #Get content of specified text block as a string
                                linetxt = self.decodeExpressionText(bpy.data.texts[textblock].as_string())
                            else:
                                raise Exception("Include text block '%s' not found" % textblock)
                
                        else:
                            raise Exception("Include must indicate from 'TEXT:' block")
                
                    else:
                        raise Exception("Include argument not valid (%s)" % includetext)
                        
                if concatenatedText != "":
                    if not concatenatedText.endswith(','):
                        concatenatedText += ","
                concatenatedText += linetxt

        return concatenatedText
            
    #TODO: Use this function to translate, calling with "self.enabledOptions" if available
    def applyExpressionTextOptions(self, text, optionString):
        #print("applyExpressionTextOptions('"+text+"','"+optionString+"')")
        convertedText = ""
        #print("optionString = "+optionString)
        enabledOptions = optionString.split(',')
        
        for line in text.splitlines():
            #print("!Line = "+line)
                
            #Check for and process 'optional' sections
            if line.startswith(':'):
                option = line.split(':')[1]
                    
                #print("Option = "+option)
                if option in enabledOptions:
                        
                    #print("Found")
                    line = line.split(':')[2].strip()
                        
                else:
                    line = ""
                
                #....maybe this shouldn't be filtering comments or blank lines (as we want to store them in the text block). Also, 'TEXT:' expression is currently being replaced with the expression, losing the link to the text block.
            #if line != "" and not line.startswith('#') and not line.startswith('?'):
            if not line.startswith('?'):
                if convertedText != "":
                    if not convertedText.endswith(','):
                            convertedText += "\n"
                convertedText += line
                    
        #print("->"+convertedText)
        return convertedText
                

    def execute(self, context):
    
        if self.expressionText.lower() == "wizard@sedman.me.uk":
            #Create flag file to hide popup
            acknowledgedFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),"acknowledged.flag")
            flagfile = open(acknowledgedFile,"w+")
            flagfile.write("I've got a warm glowing feeling")
            flagfile.close()
            return {'FINISHED'}
            
    
        if self.mode == 'CREATE':
            bpy.ops.ed.undo_push(message="Create new Maths Expression node group")
        elif self.mode.startswith("EDIT"):
            bpy.ops.ed.undo_push(message="Edit Maths Expression node group expression")
        elif self.mode == ("REVERT"):
            bpy.ops.ed.undo_push(message="Revert a Maths Expression node back to its previous state")
        elif self.mode == ("UPDATE"):
            bpy.ops.ed.undo_push(message="Update a Maths Expression node from its text block")
        else:
            bpy.ops.ed.undo_push(message="Maths Expression node "+str(self.MODE))
    
        if self.mode == 'CREATE':
            if self.presetExpressionList != 'none':
                if self.presetAsTextBlock:
                    text = bpy.data.texts.new(self.presetExpressionList)
                    text.from_string(self.applyExpressionTextOptions(self.presetText, self.enabledOptions))
                    self.expressionText = "TEXT:"+text.name
                    self.report({'INFO'},"Text block '"+text.name+"' created.")
                else:
                    self.expressionText = self.decodeExpressionText(self.applyExpressionTextOptions(self.presetText, self.enabledOptions))
                    
            #Process the expression to filter based on enabled options
            #self.expressionText = self.applyExpressionTextOptions(self.decodeExpressionText(self.expressionText), self.enabledOptions)
            
        (valid, message) = Expression.valid_expression(self.decodeExpressionText(self.expressionText))
        
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
            return self.execute_main(context)
        return {'FINISHED'}

    # Manage the node's sockets, adding additional ones when needed and removing those no longer required
    def __nodeinterface_setup__(self):
        #print("Node interface setup")
        
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
            
    #-------------------------------------------------------------------------------------------
            
    #List of manually created groups (via 'group:start' call)
    groupList = {}
    groupInstanceList = {}
    
    def clearGroupList(self):
        """Clear the group list"""
        self.groupList = {}
        
    def storeGroup(self, name, group):
        self.groupList[name] = group;
    
    def clearGroupInstanceList(self):
        """Clear the group list"""
        self.groupInstanceList = {}
        
    def storeGroupInstance(self, name, node):
        self.groupInstanceList[name] = node;
    
    #-------------------------------------------------------------------------------------------
    inputsList = []
    outputsList = []
    definedInputsList = []
    definedOutputsList = []
    
    def clearInputs(self):
        """Clear the inputs list"""
        #print("CLEAR INPUTS")
        self.inputsList = []
        self.definedInputsList = []
        
    def clearOutputs(self):
        """Clear the outputs list"""
        #print("CLEAR OUTPUTS")
        self.outputsList = []
        self.definedOutputsList = []
        
    def storeInput(self, name, toSocket, isVector):
        #print("STORE INPUT "+name)
        self.inputsList.append((name, toSocket, isVector))
        
    def storeOutput(self, name, node, isVector):
        #print("STORE OUTPUT "+name)
        self.outputsList.append((name, node, isVector))
    
    def storeDefinedInput(self, name):
        #print("STORE DEFINEDINPUT "+name)
        self.definedInputsList.append(name)
        #print("Stored input '"+name+"'")
    
    def storeDefinedOutput(self, name):
        #print("STORE DEFINEDOUTPUT "+name)
        self.definedOutputsList.append(name)
        #print("Stored output '"+name+"'")
    #-------------------------------------------------------------------------------------------
    
    createSubGroups = True  #TODO: For now just hardcode this to always create sub-groups
    subGroups = {}

    def clearSubGroups(self):
        """Clear the subGroups list"""
        self.subGroups.clear()
        
    def storeSubGroupNode(self, groupNo, name, node):
        """Store a node in the subGroups list against a particular group"""
        if groupNo in self.subGroups.keys():
            #print("!Adding "+node.name+" to group "+str(groupNo))
            self.subGroups[groupNo][1].append(node)
        else:
            #print("Creating new group ("+str(groupNo)+" for "+node.name)
            #print("!Adding "+node.name+" to new group "+str(groupNo))
            self.subGroups[groupNo] = (name, [node,])
        
    def combineDuplicateGroupInputs(self, groupnode):
        """Scan all the inputs of the newly created group and find any that are connected to the same source, merging them together to remove duplicated inputs to the group"""
        
        #....foreach groupnode input
        #    ....scan through the other groupnode inputs and find any that share the same source socket
        #        ....for any found, set the source of the found one to the same as the first one
        #        ....within the group, find the corresponding 'found' socket and re-link it to the matching one
        #        ....remove the 'old' (now unused) socket from the group (leave this bit to last)
                
        #print("combineDuplicateGroupInputs running on node "+groupnode.name)
        #Process all inputs to the group
        for socketno in range(0,len(groupnode.inputs)):
            #print("Socket "+str(socketno))
            origSocket = groupnode.inputs[socketno]
            
            #We'll compare it to all 'later' inputs to the group
            for compareno in range(socketno+1, len(groupnode.inputs)):
                #print("Compare to "+str(compareno))
                compareSocket = groupnode.inputs[compareno]
                
                if len(origSocket.links) == 0 or len(compareSocket.links) == 0:
                    continue
                
                if origSocket.links[0].from_socket == compareSocket.links[0].from_socket:
                    #We've found one that has the same source
                    #print("Socket "+str(socketno)+" shares a source with socket "+str(compareno))
                    
                    #Remove the duplicate link
                    self.node_tree.links.remove(compareSocket.links[0])
                    
                    #Re-link it within the group
                    to_socket = groupnode.node_tree.nodes["Group Input"].outputs[compareno].links[0].to_socket
                    ##Remove old link
                    groupnode.node_tree.links.remove(groupnode.node_tree.nodes["Group Input"].outputs[compareno].links[0])
                    ##Create new link
                    groupnode.node_tree.links.new(groupnode.node_tree.nodes["Group Input"].outputs[socketno],to_socket)
        
        #Remove sockets that are no longer used
        for socketno in reversed(range(0,len(groupnode.inputs))):
            if len(groupnode.inputs[socketno].links) == 0:
                groupnode.node_tree.inputs.remove(groupnode.node_tree.inputs[socketno])
    
    def applyValueNodes(self, node_tree):
        """Process all 'Value' nodes in the tree and set the 'default' value for any socket it connects to before deleting the 'Value' node itself, thereby "applying" that value to each destination node"""
        
        for node in node_tree.nodes:
            if node.bl_idname == "ShaderNodeValue":
                removeNode = True
                for link in node.outputs[0].links:
                    #print("Value node "+node.name+" links to "+link.to_node.name+" on socket "+link.to_socket.name)
                    
                    #print("Node linked to '"+link.to_node.bl_idname+"'")
                    #Don't merge value into Group node or Reroute node
                    if 'Group' in link.to_node.bl_idname or 'Reroute' in link.to_node.bl_idname:
                        #This node will still be connected to something, so don't actually remove it
                        removeNode = False
                        continue
                    
                    #link.to_socket.default_value = node.outputs[0].default_value
                    if link.to_socket.type == 'VECTOR':
                        link.to_socket.default_value = [float(node.outputs[0].default_value),float(node.outputs[0].default_value),float(node.outputs[0].default_value)]
                    else:
                        link.to_socket.default_value = float(node.outputs[0].default_value)
    
                #Now that we've applied the 'default_value' we can remove the node as it's no longer required
                if removeNode:
                    node_tree.nodes.remove(node)

    def makeSubGroups(self):                
        if len(self.subGroups)>1:    #Only create groups if there's more than one expression
                
            #Move the editor 'path' to the top-level of our group (only needed if in Create or Edit(External) mode)
            currentPath = bpy.context.space_data.path[-1] #Store the group path so we can get back to it (TODO: Is this required?)
            if self.mode in ('CREATE', 'EDIT'):
                #Move into the newly created node tree
                bpy.context.space_data.path.append(self.node_tree)
            
            #print("!!Processing subGroups")
            #print("subGroups = "+str(self.subGroups))
            for group in self.subGroups:
                #print("group = "+str(group))
                #print("group "+str(group)+" has "+str(len(self.subGroups[group]))+" nodes")
                
                #deselect all
                bpy.ops.node.select_all(action="DESELECT")
                
                #select all nodes within this 'group'
                nodeCount = 0
                for node in self.subGroups[group][1]:
                    # Select node
                    node.select = True
                    nodeCount += 1
                    
                if nodeCount < 2:
                    #Skip sub-groups with less than 2 nodes
                    continue
                
                #Create group
                lastNodeGroup = bpy.data.node_groups[-1]
                result = bpy.ops.node.group_make()
                newNodeGroup = bpy.data.node_groups[-1]     #Assumes any new group will be at end of list (TODO: detect this in a better way?)
                
                if lastNodeGroup == newNodeGroup:
                    #It seems we've failed to create new group
                    print("Failed to create sub-group")
                    continue
                
                newNodeGroup.name = "DynamicMathsExpressionSubExpression_"+self.subGroups[group][0]
                #print("Created node group "+str(bpy.data.node_groups[-1]))
                
                self.combineDuplicateGroupInputs(self.node_tree.nodes[-1])  #TODO: Better way of getting the last added node
                
                #Layout the group
                NodeTreeTools.arrangeBasedOnHierarchy(bpy.context.space_data.path[-1].node_tree)
                                    
                #Move back to previous path 
                bpy.context.space_data.path.pop()
                bpy.context.active_node.label = self.subGroups[group][0]
                
            #Layout the top-level group
            NodeTreeTools.arrangeBasedOnHierarchy(bpy.context.space_data.path[-1].node_tree)
            
            if self.mode in ('CREATE', 'EDIT'):
                #Move back to the 'parent' path if we started 'outside' the group
                bpy.context.space_data.path.pop()
        
        #TODO: Remove the nodetree if we remove the group node and there are no other users of the data block
        #TODO: Remove any nodes that aren't in *any* group - ie, those without actual outputs (see Hexagon preset)
        #TODO: Combine inputs to a group that link to the same source socket. eg, 'Angle=atan2(x,y)/3.141/2+0.5, Dist=(x*x+y*y)**0.5' the 'Dist' has two inputs for each variable.
        #TODO: Name the groups based on the expression label (if specified)
    
    # Manage the internal nodes to perform the chained operation - clear all the nodes and build from scratch each time.
    def __nodetree_setup__(self):
        #print("Node Setup")
        # Remove all links and all nodes that aren't Group Input or Group Output
        self.node_tree.links.clear()
        for node in self.node_tree.nodes:
            if node.bl_idname == "ShaderNodeGroup":
                #If there is 1 or fewer users then this group isn't in use so remove it.
                if node.node_tree.users <= 1:
                    bpy.data.node_groups.remove(node.node_tree)
            
            if not node.bl_idname in ['NodeGroupInput','NodeGroupOutput', 'DynamicMathsExpressionNode']:
                self.node_tree.nodes.remove(node)
            #else:
            #    node.location = [0,0]   #TODO: Place these a bit nicer (instead of all at zero)
            
        self.clearSubGroups()
        if not self.createSubGroups:
            self.clearNodeCache()
        self.clearVariableDefaults()
        self.clearSeparateXYZNodes()
        self.clearGroupList()
        self.clearGroupInstanceList()
        self.clearInputs()
        self.clearOutputs()
            
        if 'Dynamic Maths Expression' in self.node_tree.nodes.keys():
            exprNode = self.node_tree.nodes['Dynamic Maths Expression']
        else:
            exprNode = self.node_tree.nodes.new('DynamicMathsExpressionNode')
            exprNode.label = 'See https://baldingwizard.wixsite.com/blog/node-expressions'
        exprNode.expressionText  = self.expressionText
        exprNode.enableRevert = (not self.expressionIsValid)
                
        # Start from Group Input and add nodes as required, chaining each new one to the previous level and the next input
        groupinput = self.node_tree.nodes['Group Input']
        previousnode = groupinput

        if self.expressionIsValid:
            exprNode.storedValidExpression = self.storedValidExpression
            
            #print("About to parse expression...")
            operations = Expression.parse_expression(self.decodeExpressionText(self.expressionText))
            
            subExpressionNo = 0
            #outputslot = 0
            while True:
                                
                if self.createSubGroups:
                    #Clear node cache so we don't try and link to nodes in another group
                    self.clearNodeCache()
        
                if operations[0] == ',':
                    
                    if operations[1][0] == 'group:start' or operations[1][0] == 'function:start':
                        #...check that everything is empty (so we aren't mid-group)
                        if len(self.nodeCache) > 0:
                            raise Exception("Incomplete expression when starting new group")
                            
                        #store the existing node_tree
                        self.stored_node_tree = self.node_tree

                        #setup a new node_tree
                        self.node_tree = bpy.data.node_groups.new('group:start','ShaderNodeTree')
                        self.node_tree.nodes.new('NodeGroupInput')
                        self.node_tree.nodes.new('NodeGroupOutput')
                        
                        #set the editor path to this tree
                        bpy.context.space_data.path.append(self.node_tree)
                        
                        if operations[1][1][0] != 'variable':
                            raise Exception("Need to specify node group name in group:start")
                            
                        groupname = operations[1][1][1]
                        #print("GroupName(1) "+groupname)
                        
                        if len(operations[1]) > 2:      #There are further arguments
                            groupstartExpr = operations[1][2]
                            
                            while True:
                                if groupstartExpr[0] == 'variable':
                                    variableName = groupstartExpr[1]
                                    #print("Variable "+variableName)
                                    if variableName.endswith('[]'):
                                        self.node_tree.inputs.new("NodeSocketVector", variableName[:-2])
                                    else:
                                        self.node_tree.inputs.new("NodeSocketFloat", variableName)
                                    break
                                elif groupstartExpr[0] == ',':
                                    if groupstartExpr[1][0] == 'variable':
                                        variableName = groupstartExpr[1][1]
                                        #print("Variable(2) "+variableName)
                                        if variableName.endswith('[]'):
                                            self.node_tree.inputs.new("NodeSocketVector", variableName[:-2])
                                        else:
                                            self.node_tree.inputs.new("NodeSocketFloat", variableName)
                                    else:
                                        raise Exception('Must only specify input variables in group:start(...)')
                                    
                                    groupstartExpr = groupstartExpr[2]
                                
                        
                        self.storeGroup(groupname, self.node_tree)
                        
                        #Skip to next operation
                        operations = operations[2]
                        continue
                        
                    elif operations[1][0] == 'group:end' or operations[1][0] == 'function:end':
                        #check that we're in a group (ie, we've had a 'groupstart' and stored a node_tree
                        if hasattr(self,'stored_node_tree') and self.stored_node_tree != None:
                            
                            self.process_special_named_inputs()

                            #TODO: Check that the supplied 'variable' matches that in the corresponding 'start'

                            # Find the nodes that are the ends of sub-expressions
                            subexpressionNodes = []
                            for o in self.outputsList:
                                subexpressionNodes.append(o[1])
            
                            NodeTreeTools.arrangeBasedOnHierarchy(self.node_tree, additionalNodes = subexpressionNodes)

                            self.process_outputsList()
                            self.clearOutputs()

                            #Join any matching outputs to the respective inputs for sub-expressions
                            self.connect_outputs_to_matching_inputs()
                            self.set_group_inputs_defaults()
                            
                            self.prune_group_inputs()
                            self.prune_group_outputs()
                            self.prune_hidden_group_outputs()
                            self.prune_hidden_group_inputs()

                            #Consider moving this to after making sub-groups...?
                            self.applyValueNodes(self.node_tree)

                            self.makeSubGroups()
                            self.clearSubGroups()

                            self.clearSeparateXYZNodes()

                            #Restore the stored 'node_tree'
                            self.node_tree = self.stored_node_tree
                            self.stored_node_tree = None
                            
                            #set the editor path back to the original tree
                            bpy.context.space_data.path.pop()
                            
                            #Skip to next operation
                            operations = operations[2]
                            continue
                        else:
                            raise Exception("Attempted to end a group before it was started")
                            
                    elif operations[1][0] == 'group:add':
                        
                        if operations[1][1][0] == 'variable':
                            groupname = operations[1][1][1]
                            
                            if operations[1][2][0] == ',' and operations[1][2][1][0] == 'variable':
                                instancename = operations[1][2][1][1]
                            else:
                                raise Exception("Unabled to find instance name for '"+groupname+"'")
                            
                            groupnode = self.node_tree.nodes.new('ShaderNodeGroup')
                            groupnode.label = instancename
                            self.storeGroupInstance(instancename, groupnode)
                            
                            if groupname in self.groupList.keys():
                                groupnode.node_tree = self.groupList[groupname]
                            else:
                                raise Exception("Unknown group name ("+str(groupname)+") in 'group:add'")
                                
                            groupArgExpr = operations[1][2][2]
                            
                            #Process all the arguments, building the expression for each socket
                            socketNo = 0
                            while True:
                                if groupArgExpr[0] == ',':
                                    #This is one of a list of arguments - build this one then move on to next
                                    self.build_nodes(groupArgExpr[1], groupnode.inputs[socketNo], self.node_tree.nodes['Group Output'].location,0)
                                    socketNo += 1
                                    groupArgExpr = groupArgExpr[2]
                                else:
                                    #The last argument - build it and exit
                                    self.build_nodes(groupArgExpr, groupnode.inputs[socketNo], self.node_tree.nodes['Group Output'].location,0)
                                    break
                                    
                        else:
                            raise Exception("Must specify the group name when adding a group with 'group:add'")
                        
                        #Skip to next operation
                        operations = operations[2]
                        continue
                    
                    #TODO: Handle this (and others) as the *last* sub-expression of the expression
                    elif operations[1][0] == 'inputs' or operations[1][0] == 'outputs':
                        #process all arguments. If any are not of type 'variable' throw exception, otherwise storeDefinedInput/Output
                        
                        isInputs = operations[1][0] == 'inputs'

                        if operations[1][1][0] == 'variable':
                            #store the first argument
                            if isInputs:
                                self.storeDefinedInput(operations[1][1][1])
                            else:
                                self.storeDefinedOutput(operations[1][1][1])
                        else:
                            raise Exception("Invalid '"+operations[1][0]+"' definition - must only contain variables")
                            
                        if len(operations[1]) > 2:
                            #there's more expression
                            
                            if operations[1][2][0] == ',':
                                #process command-separated arguments
                                for inoutTerm in Expression.convertCommaExpressionToList(operations[1][2]):
                                    if inoutTerm[0] == 'variable':
                                        if isInputs:
                                            self.storeDefinedInput(inoutTerm[1])
                                        else:
                                            self.storeDefinedOutput(inoutTerm[1])
                                    else:
                                        raise Exception("Invalid '"+operations[1][0]+"' definition - must only contain variables")
                            else:
                                if operations[1][2][0] == 'variable':
                                    if isInputs:
                                        self.storeDefinedInput(operations[1][2][1])
                                    else:
                                        self.storeDefinedOutput(operations[1][2][1])
                                else:
                                    raise Exception("Invalid '"+operations[1][0]+"' definition - must only contain variables")
                        
                        #Skip to next operation
                        operations = operations[2]
                        continue
                        
                    subExpressionNo += 1
                    #print("subExpressionNo incremented to "+str(subExpressionNo))
                    
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
                    
                    #Create a 'reroute' node and store the details in the 'outputs' list to process later
                    reroutenode = self.node_tree.nodes.new('NodeReroute')
                    reroutenode.label = exprname
                    socket = reroutenode.inputs[0]
                    self.storeOutput(exprname, reroutenode, exprIsVector)
                        
                    self.build_nodes(expr, socket, self.node_tree.nodes['Group Output'].location,0, subExpressionNo = subExpressionNo,expressionName = exprname)
                    operations = operations[2]

                    subExpressionNo += 1    #TODO: Fix this fudge - it's only here to ensure the last expression is in its own group
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
                            
                    #Create a 'reroute' node and store the details in the 'outputs' list to process later
                    reroutenode = self.node_tree.nodes.new('NodeReroute')
                    socket = reroutenode.inputs[0]
                    self.storeOutput(exprname, reroutenode, exprIsVector)
                        
                    self.build_nodes(expr, socket, self.node_tree.nodes['Group Output'].location,0, subExpressionNo = subExpressionNo, expressionName = exprname)

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

        self.process_special_named_inputs()

        # Find the nodes that are the ends of sub-expressions
        subexpressionNodes = []
        for o in self.outputsList:
            subexpressionNodes.append(o[1])
            
        NodeTreeTools.arrangeBasedOnHierarchy(self.node_tree, additionalNodes = subexpressionNodes)

        self.process_outputsList()

        #Join any matching outputs to the respective inputs for sub-expressions
        self.connect_outputs_to_matching_inputs()
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
            
        self.applyValueNodes(self.node_tree)
            
        if self.createSubGroups:
        
            self.makeSubGroups()
            
            #TODO: Position the 'main' node more appropriately - preferably put it into 'transform' mode too - like when adding other nodes (if possible)
            
    nodeCache = {}
    
    def clearNodeCache(self):
        self.nodeCache.clear()
        
    def getCachedNode(self, key):
        if key in self.nodeCache:
            return self.nodeCache[key]
        else:
            return None
    
    def storeNodeInCache(self, key, node):
        #Store the key provided we haven't disabled the optimization
        if self.mode == 'EDITWITHIN':
            if self.disableOptimizeTree:
                return
                
        self.nodeCache[key] = node
    
    def processColorRampExpression(self, node, expr):
    
        #Count how many terms we have received in each 'pair' of expressions
        pairCount = 0
        
        #Get rid of *default* color ramp elements (ie, 0,0 and 1,1) - except the first one (since we have to leave at least 1 for the node to be valid)
        if len(node.color_ramp.elements) > 1:
            for element in node.color_ramp.elements[1:]:
                node.color_ramp.elements.remove(element)
        
        usedFirstElement = False
        for exprTerm in Expression.convertCommaExpressionToList(expr):
            pairCount += 1
            
            if exprTerm[0] == 'value':
                #print("COLORRAMP got expression "+exprTerm[0]+":"+str(exprTerm[1]))
                if pairCount == 1:
                    rampPosition = float(exprTerm[1])
                else:
                    #add a 'value' point in the color ramp
                    if not usedFirstElement:
                        element = node.color_ramp.elements[0]
                        element.position = rampPosition
                        usedFirstElement = True
                    else:
                        element = node.color_ramp.elements.new(rampPosition)
                    element.color[0] = float(exprTerm[1])
                    element.color[1] = float(exprTerm[1])
                    element.color[2] = float(exprTerm[1])
                    
                    pairCount = 0
                    
            elif exprTerm[0] == 'variable':
                var = exprTerm[1].upper()
                
                if var == 'BSPLINE':    #Allow alternative B-Spline indicator
                    var = 'B_SPLINE'
                    
                if var in ['RGB', 'HSV', 'HSL']:
                    node.color_ramp.color_mode = var
                elif var in ['NEAR', 'FAR', 'CW', 'CCW']:
                    node.color_ramp.hue_interpolation = var
                elif var in ['EASE', 'CARDINAL', 'LINEAR', 'B_SPLINE', 'CONSTANT']:
                    node.color_ramp.interpolation = var
                else:
                    raise Exception("COLORRAMP invalid term '"+var+"'")
                    
                #Reduce pairCount as we haven't used this term in a pair
                pairCount -= 1
                    
            elif exprTerm[0] == 'combine':
                #print("COLORRAMP got 'combine'")
                if len(exprTerm) < 3:
                    raise Exception("COLORRAMP combine expression too short")
                
                if pairCount == 1:
                    raise Exception("COLORRAMP got 'combine' in place of a position - position must be a plain value")
                else:
                    col = [0.0, 0.0, 0.0]
                    colIdx = 0
                    for combineTerm in Expression.convertCommaExpressionToList(exprTerm[1]) + Expression.convertCommaExpressionToList(exprTerm[2]):
                        if combineTerm[0] == 'value':
                            #print("   Got value "+str(combineTerm[1]))
                            col[colIdx] = float(combineTerm[1])
                            colIdx += 1
                        else:
                            raise Exception("COLORRAMP combine got an unexpected expression ('"+combineTerm[0]+"')")
                    
                    #add a 'color' point in the color ramp
                    if not usedFirstElement:
                        element = node.color_ramp.elements[0]
                        element.position = rampPosition
                        usedFirstElement = True
                    else:
                        element = node.color_ramp.elements.new(rampPosition)
                    element.color[0] = col[0]
                    element.color[1] = col[1]
                    element.color[2] = col[2]
                    
                    pairCount = 0
                    
            else:
                raise Exception("COLORRAMP got an unexpected expression ('"+exprTerm[0]+"')")
                
            
        if pairCount != 0:
            raise Exception("COLORRAMP received the wrong number of arguments - must pair each 'value' with a 'color'")
            
        return True
        
    def processPointDensityExpression(self, node, expr):
        
        argno = 1
        for exprTerm in Expression.convertCommaExpressionToList(expr):
            if exprTerm[0] == 'variable':
                var = exprTerm[1].upper()
                
                if var == 'PARTICLE':    # 'Particle' mode
                    node.point_source = 'PARTICLE_SYSTEM'
                elif var == 'VERTEX':    # 'Vertex' mode
                    node.point_source = 'OBJECT'
                elif var == 'OBJECT':    # Object space
                    node.space = "OBJECT"
                elif var == 'WORLD':     # World space
                    node.space = "WORLD"
                elif var == 'LINEAR':    # Linear interpolation
                    node.interpolation = 'Linear'
                elif var == 'CLOSEST':   # Closest interpolation
                    node.interpolation = 'Closest'
                elif var == 'CUBIC':     # Cubic interpolation
                    node.interpolation = 'Cubic'
                elif var == 'COLOR':     # Vertex color
                    node.vertex_color_source = 'VERTEX_COLOR'
                elif var == 'WEIGHT':    # Vertex weight
                    node.vertex_color_source = 'VERTEX_WEIGHT'
                elif var == 'NORMAL':    # Vertex normal
                    node.vertex_color_source = 'VERTEX_NORMAL'
                elif var == 'VELOCITY':  # Particle velocity
                    node.particle_color_source = 'PARTICLE_VELCITY'
                elif var == 'SPEED':     # Particle speed
                    node.particle_color_source = 'PARTICLE_SPEED'
                elif var == 'AGE':       # Particle age
                    node.particle_color_source = 'PARTICLE_AGE'
                else:
                    raise Exception("PointDensity unknown option '"+var+"'")
            
            elif exprTerm[0] == 'value':
                val = exprTerm[1]
                
                #count the argument and assign to relevant property
                if argno == 1:
                    #object
                    if val.startswith('"') and val.endswith('"'):
                        objName = val[1:-1]
                        
                        if objName in bpy.data.objects.keys():
                            node.object = bpy.data.objects[objName]
                        else:
                            raise Exception("PointDensity specified object ("+objName+") not found")
                    else:
                        raise Exception("PointDensity expected a string for Object");
                        
                elif argno == 2:
                    if node.point_source == 'PARTICLE_SYSTEM':
                        pno = int(val)
                        
                        if len(node.object.particle_systems) < pno:
                            raise Exception("PointDensity particle system ("+str(pno)+") doesn't exist on that object")
                        else:
                            node.particle_system = node.object.particle_systems[pno-1]
                    else:
                        node.radius = float(val)
                        
                elif argno == 3:
                    if node.point_source == 'PARTICLE_SYSTEM':
                        node.radius = float(val)
                    else:
                        node.resolution = int(val)
                
                elif argno == 4:
                    if node.point_source == 'PARTICLE_SYSTEM':
                        node.resolution = int(val)
                    else:
                        if val.startswith('"') and val.endswith('"'):
                            node.vertex_attribute_name = val[1:-1]      #TODO: Check that 'mode' allows this property (only allowed in 'Weights' mode)
                        else:
                            raise Exception("PointDensity expected a string for Vertex Attribute")
                    
                argno += 1
                
    def processImageExpression(self, node, expr):
        
        argno = 1
        for exprTerm in Expression.convertCommaExpressionToList(expr):
            if exprTerm[0] == 'variable':
                var = exprTerm[1].upper()
                
                if var == 'LINEAR':       # Interpolation:Linear
                    node.interpolation = 'Linear'
                elif var == 'CLOSEST':    # Interpolation:Closest
                    node.interpolation = 'Closest'
                elif var == 'CUBIC':      # Interpolation:Cubic
                    node.interpolation = 'Cubic'
                elif var == 'SMART':      # Interpolation:Smart
                    node.interpolation = 'Smart'

                elif var == 'FLAT':       # Projection:Flat
                    node.projection = 'FLAT'
                elif var == 'BOX':        # Projection:Box
                    node.projection = 'BOX'
                elif var == 'SPHERE':     # Projection:Sphere
                    node.projection = 'SPHERE'
                elif var == 'TUBE':       # Projection:Tube
                    node.projection = 'TUBE'

                elif var == 'REPEAT':     # Extension:Repeat
                    node.extension = 'REPEAT'
                elif var == 'EXTEND':     # Extension:Extend
                    node.extension = 'EXTEND'
                elif var == 'CLIP':       # Extension:Clip
                    node.extension = 'CLIP'
                elif var in ('COLOR', 'SRGB'):
                    if 'color_space' in node.keys():
                        node.color_space = 'COLOR'
                    else:
                        raise Exception ("Image: Don't need to set colorspace in Blender 2.80+")
                elif var in ('NON_COLOR','NONE'):
                    if 'color_space' in node.keys():
                        node.color_space = 'NONE'
                    else:
                        raise Exception ("Image:  Don't need to set colorspace in Blender 2.80+")
                #TODO: Implement other colorspace settings? (Filmic, Linear, Linear Aces, Raw, XYZ) Actually, colorspace is now specific to the image rather than the node
                else:
                    raise Exception("Image unknown option '"+var+"'")
            
            elif exprTerm[0] == 'value':
                val = exprTerm[1]
                
                #count the argument and assign to relevant property
                if argno == 1:
                    #object
                    if val.startswith('"') and val.endswith('"'):
                        imgName = val[1:-1]
                        
                        if imgName in bpy.data.images.keys():
                            node.image = bpy.data.images[imgName]
                        else:
                            raise Exception("Image specified image ("+imgName+") not found")
                    else:
                        raise Exception("Image expected a string for Image");
                else:
                    raise Exception("Image unexpected value argument");                
                        
                argno += 1
                #TODO: Trap invalid arguments properly (currently still creates the node)
                #TODO: Support BOX projection_blend argument
                #TODO: Support 'source'
                #TODO: Support Color Space
                
        
    def build_nodes(self, nested_operations, to_output, output_location,depth,lastoperation=None, subExpressionNo=0, expressionName = ""):
        depth+=1
        #print("build_nodes with subExpressionNo set to "+str(subExpressionNo))

        #print("Build Nodes")
        if len(nested_operations) == 0:
            return
        
        cachedNode = self.getCachedNode(Expression.stringRepresentation(nested_operations))
        if cachedNode != None:
            #Found a node for the same expression - link it instead of building a new one
            self.node_tree.links.new(cachedNode.outputs[0],to_output)
            return
        
        operation = nested_operations[0]
        
        #print("Build Nodes "+str(nested_operations)+" : "+str(operation))
        
        if operation == 'variable':
            #....link to 'group input'
            variableName = nested_operations[1]
            
            #Allow variable name to include "{<default>}" suffix to set its default (so 'a{123.45}' indicates socket 'a' should default to 123.45)
            (variableName, variableDefault) = Expression.extractVariableDefault(variableName)
            if variableDefault != None:
                #print("!!Variable "+variableName+" = "+variableDefault)
                self.storeVariableDefault(variableName, variableDefault)
            
            #TODO: Move 'subscript' processing here - create SeparateXYZ node as needed and link to relevant place
            (variableName, variableSubscript) = Expression.extractVariableSubscript(variableName)
            #TODO: Get this working with non-subscripted variables.
            #Handle 'group:<name>[<socket>]' format - to link to a specific socket on a specific instance of a group
            if variableName.startswith('group:'):
                groupInstanceName = variableName[6:]
                groupSocketName = variableSubscript
                
                #get the instance, find the socket, link it
                node = self.groupInstanceList[groupInstanceName]
                socket = node.outputs[groupSocketName]
                
                #Create a link from the specified instance socket to to_output
                self.node_tree.links.new(socket,to_output)
            else:
                if variableSubscript != None:
                    separateNode = self.getSeparateXYZNode(variableName)
                    
                    if separateNode == None:
                        separateNode = self.node_tree.nodes.new('ShaderNodeSeparateXYZ')
                        separateNode.location = (-250,250)      #Move it out of the way in case it's not actually used
                        self.storeSeparateXYZNode(variableName, separateNode)
                        
                        #Link separateXYZ node to Group Input
                        if variableName in self.node_tree.nodes['Group Input'].outputs.keys():      #TODO: Make sure existing socket is a Vector - otherwise we need to create a new one.... but what if something already connected to the 'old' (non-vector) one.... perhaps re-link them to the new one...?
                            self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[variableName],separateNode.inputs[0])
                        else:
                            # Add a new socket
                            self.node_tree.inputs.new("NodeSocketVector", variableName)
                            self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[-2],separateNode.inputs[0])  # Add link to group input we just added (-1 is 'blank' socket, -2 is last 'real' socket)
                            #self.node_tree.nodes['Group Input'].outputs[-2].hide_value = True   #TODO: Get the input value to hide as not working properly at Blender 2.8 when set manually (but works when a vector socket is connected - and also works at 2.7!!)
                            
                        
                    if variableSubscript in ('0', 'x', 'r'):
                        subnum = 0
                    elif variableSubscript in ('1', 'y', 'g'):
                        subnum = 1
                    elif variableSubscript in ('2', 'z', 'b'):
                        subnum = 2
                    elif variableSubscript == '':   #No subscript - use the whole vector
                        subnum = -1
                    else:
                        raise Exception("build_nodes : Bad subscript '"+str(variableSubscript)+"'")
                        #TODO: This error seems to cause it to drop out after creating some nodes, but leaving it unfinished. Should ideally tidy up after itself - or trap it in 'validate' so it effectively never actually gets here!
                    
                    #Link node to relevant output of SeparateXYZ node
                    if subnum >= 0:
                        self.node_tree.links.new(separateNode.outputs[subnum],to_output)
                    else:
                        self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[variableName],to_output)
                        
                else:
                
                    if variableName in self.node_tree.nodes['Group Input'].outputs.keys():
                        self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[variableName],to_output)
                    else:
                        # Add a new socket
                        #TODO: Create as a vector if it's added as whole vector as in 'Input[]' but we haven't used any sub-scripts (eg, mandelbulb example)
                        self.node_tree.inputs.new("NodeSocketFloat", variableName)
                        self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[-2],to_output)  # Add link to group input we just added (-1 is 'blank' socket, -2 is last 'real' socket)
        
        elif operation == 'value':
            #create new 'Value' node and link to to_output
            newnode = self.node_tree.nodes.new('ShaderNodeValue')
            #print("Value = '"+str(nested_operations[1])+"'")
            if nested_operations[1] == '"pi"':
                newnode.outputs[0].default_value = 3.14159265359
            elif nested_operations[1] == '"e"':
                newnode.outputs[0].default_value = 2.71828182846
            else:
                newnode.outputs[0].default_value = float(nested_operations[1])
            self.node_tree.links.new(newnode.outputs[0],to_output)
            self.storeNodeInCache(Expression.stringRepresentation(nested_operations), newnode)
            
            #Don't store it in the group since we're going to 'apply' it to the nodes it links to later anyway
            ##self.storeSubGroupNode(subExpressionNo, expressionName, newnode)
            
            #####TODO: I think the 'combine' node is getting put into the wrong group!?!
        elif operation == 'combine':
            #create new 'combineXYZ' node and link to output
            newnode = self.node_tree.nodes.new('ShaderNodeCombineXYZ')
            self.node_tree.links.new(newnode.outputs[0],to_output)
            self.storeNodeInCache(Expression.stringRepresentation(nested_operations), newnode)
            self.storeSubGroupNode(subExpressionNo, expressionName, newnode)

            # Repeat for sub-nodes
            self.build_nodes(nested_operations[1], newnode.inputs[0], [0,0],depth, subExpressionNo = subExpressionNo, expressionName = expressionName)
            if len(nested_operations) > 2:
                if nested_operations[2][0] != ',':
                    self.build_nodes(nested_operations[2], newnode.inputs[1], [0,0],depth,lastoperation=lastoperation, subExpressionNo = subExpressionNo, expressionName = expressionName)
                else:
                    self.build_nodes(nested_operations[2][1], newnode.inputs[1], [0,0],depth,lastoperation=lastoperation, subExpressionNo = subExpressionNo, expressionName = expressionName)
                    self.build_nodes(nested_operations[2][2], newnode.inputs[2], [0,0],depth,lastoperation=lastoperation, subExpressionNo = subExpressionNo, expressionName = expressionName)
                

        else:
            
            # If operation is for additional function arguments (',') then use same operation as before (eg, for max(x,y,z,....)
            if operation == ',' and lastoperation != None:
                operation = lastoperation
            
            skipSubExpressions = False
            inputSocket = 0
            outputSocket = 0
            # set the operation
            if operation == '+':
                nodetype = "ShaderNodeMath"
                nodeop = "ADD"
            elif operation == '-':
                nodetype = "ShaderNodeMath"
                nodeop = "SUBTRACT"
            elif operation == '*':
                nodetype = "ShaderNodeMath"
                nodeop = "MULTIPLY"
            elif operation == '/':
                nodetype = "ShaderNodeMath"
                nodeop = "DIVIDE"
            elif operation == '**':
                nodetype = "ShaderNodeMath"
                nodeop = "POWER"
            elif operation == 'sin':
                nodetype = "ShaderNodeMath"
                nodeop = "SINE"
            elif operation == 'cos':
                nodetype = "ShaderNodeMath"
                nodeop = "COSINE"
            elif operation == 'tan':
                nodetype = "ShaderNodeMath"
                nodeop = "TANGENT"
            elif operation == 'asin':
                nodetype = "ShaderNodeMath"
                nodeop = "ARCSINE"
            elif operation == 'acos':
                nodetype = "ShaderNodeMath"
                nodeop = "ARCCOSINE"
            elif operation == 'atan':
                nodetype = "ShaderNodeMath"
                nodeop = "ARCTANGENT"
            elif operation == 'min':
                nodetype = "ShaderNodeMath"
                nodeop = "MINIMUM"
            elif operation == 'max':
                nodetype = "ShaderNodeMath"
                nodeop = "MAXIMUM"
            elif operation == '>':
                nodetype = "ShaderNodeMath"
                nodeop = "GREATER_THAN"
            elif operation == '<':
                nodetype = "ShaderNodeMath"
                nodeop = "LESS_THAN"
            elif operation == 'log':
                nodetype = "ShaderNodeMath"
                nodeop = "LOGARITHM"
            elif operation == 'round':
                nodetype = "ShaderNodeMath"
                nodeop = "ROUND"
            elif operation == 'mod':
                nodetype = "ShaderNodeMath"
                nodeop = "MODULO"
            elif operation == 'abs':
                nodetype = "ShaderNodeMath"
                nodeop = "ABSOLUTE"
            elif operation == 'noise':
                nodetype = "ShaderNodeTexNoise"
            elif operation.startswith('musgrave'):
                nodetype = "ShaderNodeTexMusgrave"
                if '.' in operation:
                    nodeop = operation.split('.')[1]
                else:
                    nodeop = 'fbm'
            elif operation.startswith('voronoi'):
                nodetype = "ShaderNodeTexVoronoi"
                if '.' in operation:
                    nodeop = operation.split('.')[1]
                else:
                    nodeop = 'intensity'
            elif operation.startswith('point'):
                nodetype = "ShaderNodeTexPointDensity"
                if '.' in operation:
                    nodeop = operation.split('.')[1]
                else:
                    nodeop = 'color'
            elif operation.startswith('image'):
                nodetype = "ShaderNodeTexImage"
                if '.' in operation:
                    nodeop = operation.split('.')[1]
                else:
                    nodeop = 'color'
            elif operation == 'vadd':
                nodetype = "ShaderNodeVectorMath"
                nodeop = 'ADD'
            elif operation == 'vsub':
                nodetype = "ShaderNodeVectorMath"
                nodeop = 'SUBTRACT'
            elif operation == 'vdot':
                nodetype = "ShaderNodeVectorMath"
                nodeop = 'DOT_PRODUCT'
                outputSocket = 1
            elif operation == 'vcross':
                nodetype = "ShaderNodeVectorMath"
                nodeop = 'CROSS_PRODUCT'
            elif operation == 'vnorm':
                nodetype = "ShaderNodeVectorMath"
                nodeop = 'NORMALIZE'
            elif operation == 'vmult':
                nodetype = "ShaderNodeMixRGB"
                nodeop = "MULTIPLY"
                inputSocket = 1
            elif operation == 'vdiv':
                nodetype = "ShaderNodeMixRGB"
                nodeop = "DIVIDE"
                inputSocket = 1
            elif operation == 'mix':
                nodetype = "ShaderNodeMixRGB"
                nodeop = "MIX"
            elif operation == 'colorramp':
                #First argument is input, all rest must be Value pairs defining the color points (can't use variables for colorramp)
                nodetype = "ShaderNodeValToRGB"
            elif operation == ',':
                #newnode.operation = "***unexpected comma***"
                raise Exception('build_nodes : Unexpected comma')
            
            elif operation.startswith("fn:"):
                fnName = operation[3:]
                
                #Create a new group instance for this function and link it
                newnode = self.node_tree.nodes.new('ShaderNodeGroup')
                newnode.label = fnName

                if fnName in self.groupList.keys():
                    newnode.node_tree = self.groupList[fnName]
                else:
                    raise Exception("Unknown group name ("+str(fnName)+") in 'fn:add'")
                            
                if len(nested_operations)>2:
                    #Function has more than 1 argument - use a 'comma' operator to combine first arg with rest
                    groupArgExpr = (',', nested_operations[1], nested_operations[2])
                else:
                    #Function has a single argument - just use it as-is.
                    groupArgExpr = nested_operations[1]
                            
                #Process all the arguments, building the expression for each socket
                socketNo = 0
                while True:
                    if groupArgExpr[0] == ',':
                        #This is one of a list of arguments - build this one then move on to next
                        self.build_nodes(groupArgExpr[1], newnode.inputs[socketNo], self.node_tree.nodes['Group Output'].location,0)
                        socketNo += 1
                        groupArgExpr = groupArgExpr[2]
                    else:
                        #The last argument - build it and exit
                        self.build_nodes(groupArgExpr, newnode.inputs[socketNo], self.node_tree.nodes['Group Output'].location,0)
                        break

                socket = newnode.outputs[0]
                
                #Create a link from the new group to to_output
                self.node_tree.links.new(socket,to_output)
                nodetype = "(FunctionGroup)"
                
            else:
                #print("Unknown operation '"+ str(operation)+"'")
                #newnode.operation = "Unknown"
                raise Exception('build_nodes : Unknown operation '+str(operation))

            # create a new 'Maths' node
            if nodetype == 'ShaderNodeMath' or nodetype == 'ShaderNodeVectorMath':
                newnode = self.node_tree.nodes.new(nodetype)
                newnode.operation = nodeop
            elif nodetype == 'ShaderNodeMixRGB':
                newnode = self.node_tree.nodes.new(nodetype)
                newnode.blend_type = nodeop
                newnode.inputs[0].default_value = 1.0   #Set Factor to 1.0
            elif nodetype.startswith('ShaderNodeTex'):
                newnode = self.node_tree.nodes.new(nodetype)
                
                if nodetype == "ShaderNodeTexMusgrave":
                    if nodeop == "mf":
                        newnode.musgrave_type = "MULTIFRACTAL"
                    elif nodeop == "rmf":
                        newnode.musgrave_type = "RIDGED_MULTIFRACTAL"
                    elif nodeop == "hmf":
                        newnode.musgrave_type = "HYBRID_MULTIFRACTAL"
                    elif nodeop == "ht":
                        newnode.musgrave_type = "HETERO_TERRAIN"
                    else:
                        newnode.musgrave_type = "FBM"
                
                elif nodetype == "ShaderNodeTexVoronoi":
                    if nodeop == "cell":
                        newnode.coloring = "CELLS"
                    elif nodeop == "crackle":
                        newnode.coloring = "INTENSITY"
                        newnode.distance = "DISTANCE"
                        newnode.feature = "F2F1"
                    elif nodeop == "distance":
                        newnode.coloring = "INTENSITY"
                        newnode.distance = "DISTANCE"
                        newnode.feature = "F1"
                    elif nodeop == "distance2":
                        newnode.coloring = "INTENSITY"
                        newnode.distance = "DISTANCE"
                        newnode.feature = "F2"
                    elif nodeop == "distance3":
                        newnode.coloring = "INTENSITY"
                        newnode.distance = "DISTANCE"
                        newnode.feature = "F3"
                    elif nodeop == "distance4":
                        newnode.coloring = "INTENSITY"
                        newnode.distance = "DISTANCE"
                        newnode.feature = "F4"
                    else:
                        newnode.coloring = "INTENSITY"

                elif nodetype == "ShaderNodeTexPointDensity":
                    if nodeop == "density":
                        outputSocket = 1
                        
                    result = self.processPointDensityExpression(newnode, nested_operations[2])
                    skipSubExpressions = True
                        
                elif nodetype == "ShaderNodeTexImage":
                    if nodeop == "alpha":
                        outputSocket = 1
                        
                    result = self.processImageExpression(newnode, nested_operations[2])
                    skipSubExpressions = True
                        
            elif nodetype == 'ShaderNodeValToRGB':      #ColorRamp
                newnode = self.node_tree.nodes.new(nodetype)
                #Use any remaining expression to populate the colors (value terms only!)
                result = self.processColorRampExpression(newnode, nested_operations[2])
                skipSubExpressions = True
                
                newnode.width = 150     #Force node to be similar size to maths nodes to avoid upsetting layout
                                
            lastoperation = operation
            
            # link output to to_output
            self.node_tree.links.new(newnode.outputs[outputSocket],to_output)

            self.storeNodeInCache(Expression.stringRepresentation(nested_operations), newnode)
            self.storeSubGroupNode(subExpressionNo, expressionName, newnode)
            
            newlocation = output_location
            newlocation[0] -= 1/depth
            newnode.location = newlocation

            # Repeat for sub-nodes
            self.build_nodes(nested_operations[1], newnode.inputs[inputSocket+0], newlocation,depth, subExpressionNo = subExpressionNo, expressionName = expressionName)
            print(nodetype)
            print(nested_operations[0])
            ####FIXED - might want to check other node types... maybe need to deal with vector maths also... how to identify nodes that we can chain if we can't use the number of sockets...? Actually, vector functions don't allow >2 inputs anyway!
            #if (nodetype.startswith('ShaderNodeTex') or nodetype == "(FunctionGroup)" or len(newnode.inputs)>=3) and not skipSubExpressions:
            if (nodetype.startswith('ShaderNodeTex') or nodetype == "(FunctionGroup)" or nodetype != "ShaderNodeMath")and not skipSubExpressions:
            ####FIXED
                if len(nested_operations) > 2:  #There's more than just one argument - could be second argument or ',' for more
                    socketNo = inputSocket+1
                    
                    ####FIXED
                    if newnode.inputs[socketNo].name == 'W':
                        #If socket is named 'W' then it's the additional input for 1D/4D textures - so skip it
                        socketNo = socketNo + 1
                    ####FIXED
                    
                    nextNestedOp = nested_operations[2]
                    while (nextNestedOp[0] == ','):
                        newlocation[1]+=1/depth
                        self.build_nodes(nextNestedOp[1], newnode.inputs[socketNo], newlocation,depth, subExpressionNo = subExpressionNo, expressionName = expressionName)

                        socketNo += 1
                        depth += 1
                        nextNestedOp = nextNestedOp[2]

                    newlocation[1]+=1/depth
                    self.build_nodes(nextNestedOp, newnode.inputs[socketNo], newlocation,depth, subExpressionNo = subExpressionNo, expressionName = expressionName)
            else:
                if len(nested_operations) > 2 and not skipSubExpressions:     #(for colorramp we'll have already processed sub-expressions as configuration for the node)
                    newlocation[1]+=1/depth
                    self.build_nodes(nested_operations[2], newnode.inputs[inputSocket+1], newlocation,depth,lastoperation=lastoperation, subExpressionNo = subExpressionNo, expressionName = expressionName)
                
    def prune_group_inputs(self):
        #run through the 'Group Input' sockets and remove any that are no longer connected
        #print("Prune Group Inputs(...)")
        for output in self.node_tree.nodes['Group Input'].outputs:
            if len(output.name) > 0 and len(output.links) == 0:
                #print("Need to remove "+str(output))
                #self.node_tree.nodes['Group Input'].outputs.remove(output)  ### This doesn't appear to be working!!!!
                for input in self.node_tree.inputs:
                    if input.name == output.name:
                        self.node_tree.inputs.remove(input)
                        #print("Removed "+input.name)
                
    def prune_group_outputs(self):
        #TODO: Use the new 'outputs' array to build actual outputs, adding/removing as required... might want to do something similar for inputs
        #run through the 'Group Output' sockets and remove any that are no longer connected
        #print("Prune Group Outputs(...)")
        
        #Keep track of whether we have slept to allow renderer to have finished with the nodes
        haveSlept = False
        
        socketNo = -1
        for input in self.node_tree.nodes['Group Output'].inputs:
            socketNo += 1
            if len(input.name) > 0 and len(input.links) == 0:
                #for output in self.node_tree.outputs:
                    output = self.node_tree.outputs[socketNo]   #Use socketNo to use socket in same 'slot', instead of scanning just by name 
                    if output.name == input.name:                             

                        if not haveSlept:
                            if self.mode != 'CREATE':       # Only need to consider sleeping if not in 'create' mode
                                print("prune_group_outputs sleeping to allow renderer to have finished with node group...")
                                time.sleep(5)
                                print("prune_group_outputs awake")
                                haveSlept = True
                        self.node_tree.outputs.remove(output)

                        #print("Removed "+output.name)
                        
    def prune_hidden_group_outputs(self):
        #TODO: Remove this function completely - it shouldn't be required now since we don't add them at all
        pass
        #for output in self.node_tree.outputs:
        #    if output.name[0] == '_':
        #        self.node_tree.outputs.remove(output)
        #        #print("Removed "+output.name)
                
    def prune_hidden_group_inputs(self):
        #Remove any outputs that start with '_' (these are 'hidden' outputs to be internal to the node group) or not defined in 'inputs' list
        for input in self.node_tree.inputs:
            if input.name[0] == '_' or (len(self.definedInputsList)>0 and not input.name in self.definedInputsList):
                self.node_tree.inputs.remove(input)
                #print("Removed "+input.name)

    def process_outputsList(self):
        """Process 'outputsList' and link any matching outputs to corresponding inputs and create any missing sockets on the Group Output node"""
        
        for o in self.outputsList:
            exprname        = o[0]
            node            = o[1]
            outputIsVector  = o[2]
            
            #Search for a matching 'input' for this and link it if found
            for o in self.node_tree.nodes["Group Input"].outputs:
                #TODO: Change this to use 'inputsList' instead of relying on Group Input
                if o.name == exprname and len(o.links) != 0:
                    if (o.type == 'VECTOR' and outputIsVector) or (o.type != 'VECTOR' and not outputIsVector):
                        for link in o.links:
                            self.node_tree.links.new(node.outputs[0],link.to_socket)
            
            if exprname.startswith("_") or (len(self.definedOutputsList)>0 and not exprname in self.definedOutputsList):
                #Don't add it to Group Output if it's a 'hidden' variable
                continue
            
            #Look for this exprname in the outputs
            found = -1
            for n in range(0,len(self.node_tree.outputs)):
                input = self.node_tree.nodes["Group Output"].inputs[n]
                if input.name == exprname and len(input.links) == 0:
                    if (input.type == 'VECTOR' and outputIsVector) or (input.type != 'VECTOR' and not outputIsVector):
                        found = n
                        break
            
            if found < 0:
                #Not found - so create a new one
                if outputIsVector:
                    self.node_tree.outputs.new("NodeSocketVector", exprname)
                else:
                    self.node_tree.outputs.new("NodeSocketFloat", exprname)
                socket = self.node_tree.nodes["Group Output"].inputs[len(self.node_tree.nodes["Group Output"].inputs)-2]  #TODO: Fix this fudge
            else:
                socket = self.node_tree.nodes["Group Output"].inputs[found]

            self.node_tree.links.new(node.outputs[0],socket)
                
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

    def process_special_named_inputs(self):
        """Process all group inputs and replace any that have 'special' names with the assocated input node"""
        pass
        for groupinput in self.node_tree.nodes['Group Input'].outputs:
            nodeid = None
            if groupinput.name.lower() == 'input.generated':
                nodeid = 'ShaderNodeTexCoord'
                socket = 'Generated'
            elif groupinput.name.lower() == 'input.normal':
                nodeid = 'ShaderNodeTexCoord'
                socket = 'Normal'
            elif groupinput.name.lower() == 'input.uv':
                nodeid = 'ShaderNodeTexCoord'
                socket = 'UV'
            elif groupinput.name.lower() == 'input.object':
                nodeid = 'ShaderNodeTexCoord'
                socket = 'Object'
            elif groupinput.name.lower() == 'input.camera':
                nodeid = 'ShaderNodeTexCoord'
                socket = 'Camera'
            elif groupinput.name.lower() == 'input.window':
                nodeid = 'ShaderNodeTexCoord'
                socket = 'Window'
            elif groupinput.name.lower() == 'input.reflection':
                nodeid = 'ShaderNodeTexCoord'
                socket = 'Reflection'
            elif groupinput.name.lower() == 'particle.index':
                nodeid = 'ShaderNodeParticleInfo'
                socket = 'Index'
            elif groupinput.name.lower() == 'particle.age':
                nodeid = 'ShaderNodeParticleInfo'
                socket = 'Age'
            elif groupinput.name.lower() == 'particle.lifetime':
                nodeid = 'ShaderNodeParticleInfo'
                socket = 'Lifetime'
            elif groupinput.name.lower() == 'particle.location':
                nodeid = 'ShaderNodeParticleInfo'
                socket = 'Location'
            elif groupinput.name.lower() == 'particle.size':
                nodeid = 'ShaderNodeParticleInfo'
                socket = 'Size'
            elif groupinput.name.lower() == 'particle.velocity':
                nodeid = 'ShaderNodeParticleInfo'
                socket = 'Velocity'
            elif groupinput.name.lower() == 'particle.angularvelocity':
                nodeid = 'ShaderNodeParticleInfo'
                socket = 'Angular Velocity'
            elif groupinput.name.lower() == 'particle.random':
                nodeid = 'ShaderNodeParticleInfo'
                socket = 'Random'
            elif groupinput.name.lower() == 'object.location':
                nodeid = 'ShaderNodeObjectInfo'
                socket = 'Location'
            elif groupinput.name.lower() == 'object.index':
                nodeid = 'ShaderNodeObjectInfo'
                socket = 'Object Index'
            elif groupinput.name.lower() == 'object.material':
                nodeid = 'ShaderNodeObjectInfo'
                socket = 'Material Index'
            elif groupinput.name.lower() == 'object.random':
                nodeid = 'ShaderNodeObjectInfo'
                socket = 'Random'
            elif groupinput.name.lower() == 'geom.position':
                nodeid = 'ShaderNodeNewGeometry'
                socket = 'Position'
            elif groupinput.name.lower() == 'geom.normal':
                nodeid = 'ShaderNodeNewGeometry'
                socket = 'Normal'
            elif groupinput.name.lower() == 'geom.truenormal':
                nodeid = 'ShaderNodeNewGeometry'
                socket = 'True Normal'
            elif groupinput.name.lower() == 'geom.tangent':
                nodeid = 'ShaderNodeNewGeometry'
                socket = 'Tangent'
            elif groupinput.name.lower() == 'geom.incoming':
                nodeid = 'ShaderNodeNewGeometry'
                socket = 'Incoming'
            elif groupinput.name.lower() == 'geom.parametric':
                nodeid = 'ShaderNodeNewGeometry'
                socket = 'Parametric'
            elif groupinput.name.lower() == 'geom.backfacing':
                nodeid = 'ShaderNodeNewGeometry'
                socket = 'Backfacing'
            elif groupinput.name.lower() == 'geom.pointiness':
                nodeid = 'ShaderNodeNewGeometry'
                socket = 'Pointiness'
                
            #TODO: Add Camera Data, Light Path, Hair Info
            #TODO: Other 'input' nodes as functions?
                
            if nodeid != None:
                
                node = self.node_tree.nodes.new(nodeid)
                for groupinputlink in groupinput.links:
                    self.node_tree.links.new(node.outputs[socket],groupinputlink.to_socket)
            
    def connect_outputs_to_matching_inputs(self):
        # Look for inputs (variables) which have the same name as an output and connect them together
        
        # Process each 'output' from the group (ie, the Group Output node's inputs)
        #for groupoutput in self.node_tree.nodes['Group Output'].inputs:
        #    if len(groupoutput.name) > 0 and len(groupoutput.links) > 0:
        #        groupoutputlink = groupoutput.links[0]
        #        
        #        #search group inputs for one matching this name
        #        for groupinput in self.node_tree.nodes['Group Input'].outputs:
        #            if len(groupinput.name) > 0  and groupinput.name == groupoutput.name and len(groupinput.links) > 0:
        #                for groupinputlink in groupinput.links:
        #                
        #                    #Connect them together
        #                    self.node_tree.links.new(groupoutputlink.from_socket,groupinputlink.to_socket)
        for o in self.outputsList:
            oName  = o[0]
            oSoc   = o[1].outputs[0]
            oIsVec = o[2]
           
            #search group inputs for one matching this name
            #TODO: Possibly need to also consider *type*...?
            for groupinput in self.node_tree.nodes['Group Input'].outputs:
                if len(groupinput.name) > 0  and groupinput.name == oName and len(groupinput.links) > 0:
                    for groupinputlink in groupinput.links:
                        
                        #Connect them together
                        self.node_tree.links.new(oSoc,groupinputlink.to_socket)

                
                
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
                    #self.report({'INFO'},"Comparing to the one above")
                    compareSocketNo = compareSocketNo - 1
                else:
                    #self.report({'INFO'},"Stopped search")
                    break
            
            if (compareSocketNo+1) == socketNo:
                #It's already in the correct place
                pass
            else:
                #move it - move socketNo to position compareSocketNo+1
                inputs.move(socketNo, compareSocketNo+1);
                #self.report({'INFO'},"Moved socket "+str(socketNo)+" to position "+str(compareSocketNo+1))
                
        
    #Compare 'first' with 'second'. Short values will always be before "long" ones (>2 chars)
    #and numerics will be ignored when determining length - so 'x' will be before 'abc' but
    #'x2' will be after 'x1'. This way, single or double letter variables will appear towards
    #the top of the list while more descriptive values will be towards the bottom.
    #(eg, dx,dy,dz,x,x2,y,y2,z,z2,amplitude,scale,width)
    def resequence_inputs_comparator(self, first, second):
  
        #self.report({'INFO'},"Compare '"+first+"' with '"+second+"'")
  
        # strip trailing numerics to create firstStripped, secondStripped
        firstStripped = self.resequence_inputs_strip_numerics(first)
        secondStripped = self.resequence_inputs_strip_numerics(second)

        #TODO: Use numeric suffix to further group eg, x,y,z,dx,dy,dz,x2,y2,z2,dx2,dy2,dz2
        
        if len(firstStripped)<=2 and len(secondStripped)>2:
            #'first' is short while 'second' is long
            #self.report({'INFO'},"Less")
            return -1   #Less than
            
        if len(firstStripped)>2 and len(secondStripped)<=2:
            #'first' is long while 'second' is short
            #self.report({'INFO'},"Greater")
            return 1    #Greater than
                
        #'first' is similar length to 'second' so simply compare
        if first < second:
            #self.report({'INFO'},"Less2")
            return -1    #Less than
        if first > second:
            #self.report({'INFO'},"Greater2")
            return 1   #Greater than
            
        #self.report({'INFO'},"Same")
        return 0 #Same
        
    def resequence_inputs_strip_numerics(self, s):
        #TODO: Strip numerics
        return s
            
    def execute_main(self, context):
        space = context.space_data
        node_active = context.active_node
        node_selected = context.selected_nodes

        returnState = {'FINISHED'}

        #print(context)
        if context.space_data.type == 'NODE_EDITOR' and context.space_data.node_tree is not None:
            
            if self.mode == 'CREATE':
                # Create a new node group
                groupnode = get_active_node_tree(context).nodes.new('ShaderNodeGroup')
                groupnode.node_tree=bpy.data.node_groups.new("DynamicMathsExpressionGroup", 'ShaderNodeTree')
                groupnode.node_tree.nodes.new('NodeGroupInput')
                groupnode.node_tree.nodes.new('NodeGroupOutput')
                
                # Position in centre
                #groupnode.location = context.region.view2d.region_to_view(context.region.width/2-groupnode.width/2, context.region.height/2+groupnode.height/2)
                #groupnode.location = context.region.view2d.region_to_view(0,0)
                #print("x="+str(context.region.x)+", y="+str(context.region.y)+", width="+str(context.region.width)+", height="+str(context.region.height))
                #print("bpy:x="+str(bpy.context.region.x)+", y="+str(bpy.context.region.y)+", width="+str(bpy.context.region.width)+", height="+str(bpy.context.region.height))
                #...possibly use space.cursor_location_from_region to set cursor to position of node.... need to set the node position based on the editor window also..... 
                groupnode.location = context.space_data.cursor_location
                #groupnode.location = context.region.view2d.region_to_view(context.region.x+context.region.width/2, context.region.y+context.region.height/2)
                
                # Ensure only the new node is selected
                for node in context.selected_nodes:
                    node.select = False
                groupnode.select = True
                
                #Make it the 'active' object
                get_active_node_tree(context).nodes.active = groupnode

                # Put it in 'grab' mode
                # Drop into 'modal' operator mode so as to allow mouse movement to position the newly added node
                self.first_mouse_x = None
                self.first_mouse_y = None
                context.window_manager.modal_handler_add(self)
                returnState = {'RUNNING_MODAL'}

                
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
                
        ##Add a dummy 'Group Output' and make it active to effectively 'mute' this group while we make changes
        #dummyGroupOutputNode = self.node_tree.nodes.new('NodeGroupOutput')
        #dummyGroupOutputNode.name = 'Dummy Group Output'
        #dummyGroupOutputNode.is_active_output = True
        #self.node_tree.nodes["Group Output"].is_active_output = False
        #Disabled the material so that Blender doesn't try and use it
        ##Disabled this since it doesn't seem to be supported at 2.79 and I don't think this was the cause of the crashes anyway.
        ##old_use_nodes = context.material.use_nodes
        ##context.material.use_nodes = False
        self.setRenderingUseNodes(False)
        
        try:
            self.__nodeinterface_setup__()
            self.__nodetree_setup__()
        except Exception as exception:
            self.report({'ERROR'},'Build of node tree failed : '+str(exception))
            traceback.print_exc()
        
        ##Activate the actual output node and remove the dummy one
        #self.node_tree.nodes["Group Output"].is_active_output = True
        #dummyGroupOutputNode.is_active_output = False
        #self.node_tree.nodes.remove(dummyGroupOutputNode)
        ##Disabled this since it doesn't seem to be supported at 2.79 and I don't think this was the cause of the crashes anyway.
        ##context.material.use_nodes = old_use_nodes
        self.setRenderingUseNodes(True)
        
        print("execute_main exiting with "+str(returnState))
        return returnState
        
    useNodesDisabledList = {}
    def setRenderingUseNodes(self, enable):
        """Find all materials that use this tree and enable/disable use_nodes to enable/disable rendering. This is to prevent apparent race conditions where the renderer is trying to access the nodes while they are being manipulated - particularly a problem when manipulating the Group Output sockets."""
        
        if enable:
            #Re-enable those materials that were previously disabled
            for m in self.useNodesDisabledList:
                m.use_nodes = True
                print("setRenderingUseNodes enabled material "+str(m.name))
            
        else:
            #We *could* be more targetted and only disable those materials where there is a Group node using our tree. However, for now we'll just blanket disable everything - but keep track of which we disable so we can put them back once done.
            self.useNodesDisabledList = {}
            for m in bpy.data.materials:
                if m.use_nodes:
                
                    #Disable material nodes
                    m.use_nodes = False
                    
                    #Store it in the list so we can re-enable it later
                    self.useNodesDisabledList[m] = m
                
                    print("setRenderingUseNodes disabled material "+str(m.name))
        
    def modal(self, context, event):
        bpy.context.window.cursor_set("SCROLL_XY")
        #print("MODALEVENT="+str(event))
        
        if event.type == 'MOUSEMOVE':
            if self.first_mouse_x == None:
                self.first_mouse_x = event.mouse_x
                self.first_mouse_y = event.mouse_y
            deltax = self.first_mouse_x - event.mouse_x
            deltay = self.first_mouse_y - event.mouse_y
            #context.object.location.x = self.first_value + delta * 0.01
            self.groupnode.location = (context.space_data.cursor_location[0]-self.groupnode.width/2, context.space_data.cursor_location[1]+self.groupnode.height/2)
            #print("DELTAX="+str(deltax))
            #print("DELTAY="+str(deltay))

        elif event.type == 'LEFTMOUSE':
            self.show_acknowledgeme_textbox(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            #context.object.location.x = self.first_value
            #Set to default
            self.show_acknowledgeme_textbox(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}
 
######################################
    def show_acknowledgeme_textbox(self, context):
        
        acknowledgedFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),"acknowledged.flag")
        
        if not "Acknowledge Node Expressions Author" in bpy.data.texts.keys():
            if not os.path.isfile(acknowledgedFile):
                #We haven't shown the acknowledgement message and the 'acknowledged' flag file isn't present
                textblock = bpy.data.texts.new("Acknowledge Node Expressions Author")
                
                textblock.from_string("\
Dear user,\n\
This add-on is provided free for all to use - and I hope\n\
it is useful for whatever purpose you put it to.\n\n\
It has taken considerable effort to get it to the point\n\
where I'm happy to release it into the community and I\n\
don't ask for anything in return. However, if you can,\n\
please take the time to drop me a line - send me an email\n\
to 'wizard@sedman.me.uk' to let me know a little about\n\
yourself; who you are (no personal specifics) and what you\n\
do (again, nothing specific or personally identifiable),\n\
what you think of this software and what you'd like to see\n\
in the future - this will make me feel appreciated and give\n\
you a warm glow inside.\n\
Once you have sent me an email, simply enter my email in the\n\
expression window and this popup will not bother you again.\n\
Thanks for reading and have a great day.\n\n\
P.S. Want to contribute a little bit more...?\n\
Paypal donations to 'wizard@sedman.me.uk' are always very much appreciated!\n\
:-)\n\n\
Best wishes,\n\
Rich")

                bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
        
                otherarea = context.area                  #Instead of using the new one, use original (the right-hand split)
                newarea = context.screen.areas[-1]      #Assumed it's the last one in the stack (which it should be)
        
                newarea.type = 'TEXT_EDITOR'
                
                editor = newarea.spaces[0]
                editor.text = textblock
        
                editor.top = 1
                bpy.ops.text.jump({"area":newarea}, line=1)
                bpy.ops.text.move({"area":newarea}, type="LINE_BEGIN")
                
######################################
 
    def check(self, context):
        return True     # For now, always redraw    #TODO: Detect when we need to redraw
        
    def draw(self, context):
        layout = self.layout
        split = layout.split()
        split.label(text="Maths Expression")

        #TODO: Get the documentation window properly working and popping out to seperate window
        documentationFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),"documentation.txt")
        if os.path.isfile(documentationFile): # and not "Node Expressions Documentation" in bpy.data.texts.keys():
            split.operator(operator="node.node_dynamic_maths_expression_showdocumentation",text="View Documentation")

        if self.mode == 'EDIT':
            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(self, "createNew")
            
        row = layout.row()
        row.prop(self, "expressionText")
        if self.mode == 'CREATE' and self.presetExpressionList != 'none': # and self.presetAsTextBlock:
            row.enabled = False
            
        if self.mode == 'EDIT' or self.mode == 'EDITWITHIN':
            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(self, "pruneSockets")
            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(self, "resequenceInputs")
            
        if self.mode == 'EDITWITHIN':
            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(self, "disableOptimizeTree")
            
        if self.mode == 'CREATE':
            row = layout.row()
            row.prop(self, "presetExpressionList")
            
            if not self.presetExpressionList == 'none':
                row = layout.row()
                row.alignment = 'RIGHT'
                row.prop(self, "presetAsTextBlock")
            
                inputs = getExpressionTextInputs(self.presetText)
                #print("Inputs = "+str(inputs))
                propindex=0
                for (input, values) in inputs:
                    propindex += 1
                    row = layout.row()
                    row.prop(self, 'inputProp'+str(propindex), text=input)

            
class DynamicMathsExpression_Operator(_DynamicMathsExpression_Operator_common):
    """Create a new Maths Expression Group"""
    bl_idname = "node.node_dynamic_maths_expression"
    bl_label = "Node Group - Dynamic Maths Expression"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamice Maths Expression'
    mode = 'CREATE'
    #bl_options = {}
    bl_options = {'REGISTER', 'GRAB_CURSOR'}

    #presetItems=[('none', 'None', 'No preset selected'),]
    def presetItems(self, context):
        items = []
        
        try:
            #print("presetItems called")
        
            items.append(('none', 'None', "No preset selected"))
        
            addonDir = os.path.dirname(os.path.abspath(__file__))
            presetsDir = os.path.join(addonDir,"presets")
            
            #print("addonDir = "+addonDir)
            #print("presetsDir = "+presetsDir)
            
            if not os.path.isdir(presetsDir):
                return
            
            #print("Reading files...")
            for filename in os.listdir(presetsDir):
                #print("Filename = "+filename)
          
                firstline = open(os.path.join(presetsDir,filename)).readline()
                
                if firstline.startswith("#"):
                    title = firstline[1:].split(':')[0].strip()
                    description = firstline[1:].split(':')[1].strip()
                    
                    items.append((filename, title, description))

        except Exception as exception:
            print("Exepction caught while trying to read presets : "+exception)
            items.append(('unknown', '*** Unknown ***', 'Failed to read presets - check console output for details'))
                    
        return items
            
    #TODO: Come up with a more elegant way of getting multiple item generator functions working
    def inputPropItems1(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>0:
            for input in inputs[0][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems2(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>1:
            for input in inputs[1][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems3(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>2:
            for input in inputs[2][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems4(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>3:
            for input in inputs[3][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems5(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>4:
            for input in inputs[4][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems6(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>5:
            for input in inputs[5][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems7(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>6:
            for input in inputs[6][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems8(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>7:
            for input in inputs[7][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems9(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>8:
            for input in inputs[8][1].split(','):
                items.append((input, input, input))
        
        return items

    def inputPropItems10(self, context):
        inputs = getExpressionTextInputs(self.presetText)
        items = []
        
        if len(inputs)>9:
            for input in inputs[9][1].split(','):
                items.append((input, input, input))
        
        return items

    def presetExpressionUpdate(self, context):
        if self.presetExpressionList == 'none':
            self.expressionText = ""
            self.presetText = ""
            self.inputProps = ""
        else:
            addonDir = os.path.dirname(os.path.abspath(__file__))
            presetsDir = os.path.join(addonDir,"presets")
            file = os.path.join(presetsDir, self.presetExpressionList)

            self.presetText = open(file).read()
            if self.presetAsTextBlock:
                self.expressionText = ""
            #TODO: Remove if no longer needed
            #else:
            #    #print("File = "+file)
            #    self.expressionText = packExpressionText(open(file).read())
                
            #print("DIR(self) = "+str(dir(self)))
            #....setup the input properties here  #TODO: Perhaps tidy this up and make less "hacky"
            inputs = getExpressionTextInputs(self.presetText)
            propindex=0
            for (input, values) in inputs:
                #print("!!!input = "+input)
                propindex += 1
                prop = getattr(self,"inputProp"+str(propindex))
                #prop.text = "Text"+input
                #self.inputProp1.text = "Text"+input
                #...setup "inputProp'+str(propindex)" values
                
            
        #def inputPropUpdate(self, context):
        #build and store a string containing all the selected 'options'
        self.enabledOptions = ''
        
        #print("Building 'enabledOptions'")
        if self.presetExpressionList != 'none':
            inputs = getExpressionTextInputs(self.presetText)
            options = ""
            
            if len(inputs) > 0:
                options += inputs[0][0]+"."+self.inputProp1+","
                
            if len(inputs) > 1:
                options += inputs[1][0]+"."+self.inputProp2+","
                
            if len(inputs) > 2:
                options += inputs[2][0]+"."+self.inputProp3+","
                
            if len(inputs) > 3:
                options += inputs[3][0]+"."+self.inputProp4+","
                
            if len(inputs) > 4:
                options += inputs[4][0]+"."+self.inputProp5+","
                
            if len(inputs) > 5:
                options += inputs[5][0]+"."+self.inputProp6+","
                
            if len(inputs) > 6:
                options += inputs[6][0]+"."+self.inputProp7+","
                
            if len(inputs) > 7:
                options += inputs[7][0]+"."+self.inputProp8+","
                
            if len(inputs) > 8:
                options += inputs[8][0]+"."+self.inputProp9+","
                
            if len(inputs) > 9:
                options += inputs[9][0]+"."+self.inputProp10+","
                
            self.enabledOptions = options
            #print("EnabledOptions = "+self.enabledOptions)
        

    #TODO: Blank string seems to cause parser to fail
    
    expressionText: bpy.props.StringProperty(description='Enter the expression', name='Expression')
    presetText: bpy.props.StringProperty(description='Enter the expression', name='Expression')
    resequenceInputs: bpy.props.BoolProperty(name='Auto-sequence Inputs', description='Automatically resequence input sockets')
    presetExpressionList: bpy.props.EnumProperty(name ='Preset Expression', description='Select a preset expression', items=presetItems,update=presetExpressionUpdate)
    presetAsTextBlock: bpy.props.BoolProperty(name='Create as Text block', description='Create a textblock for this expression to allow easier editing', update=presetExpressionUpdate)
    inputProps: bpy.props.StringProperty(name='Input Properties') # NOTE: This is a bit of a hack to store additional details about the expression inputs
    inputProp1: bpy.props.EnumProperty(name='Option 1', items=inputPropItems1, update=presetExpressionUpdate) #inputPropUpdate)
    inputProp2: bpy.props.EnumProperty(name='Option 2', items=inputPropItems2, update=presetExpressionUpdate) #update=inputPropUpdate)
    inputProp3: bpy.props.EnumProperty(name='Option 3', items=inputPropItems3, update=presetExpressionUpdate) #update=inputPropUpdate)
    inputProp4: bpy.props.EnumProperty(name='Option 4', items=inputPropItems4, update=presetExpressionUpdate) #update=inputPropUpdate)
    inputProp5: bpy.props.EnumProperty(name='Option 5', items=inputPropItems5, update=presetExpressionUpdate) #update=inputPropUpdate)
    inputProp6: bpy.props.EnumProperty(name='Option 6', items=inputPropItems6, update=presetExpressionUpdate) #update=inputPropUpdate)
    inputProp7: bpy.props.EnumProperty(name='Option 7', items=inputPropItems7, update=presetExpressionUpdate) #update=inputPropUpdate)
    inputProp8: bpy.props.EnumProperty(name='Option 8', items=inputPropItems8, update=presetExpressionUpdate) #update=inputPropUpdate)
    inputProp9: bpy.props.EnumProperty(name='Option 9', items=inputPropItems9, update=presetExpressionUpdate) #update=inputPropUpdate)
    inputProp10: bpy.props.EnumProperty(name='Option 10', items=inputPropItems10, update=presetExpressionUpdate) #update=inputPropUpdate)
    enabledOptions: bpy.props.StringProperty(name='Enabled Options')
    
    def __init__(self):
        super().__init__()
        self.resequenceInputs = True
        
        # If we're re-opening the operator and 'preset' is set, then reset back to nothing selected and blank expression (otherwise leave as set)
        if self.presetExpressionList != 'none':
            self.presetExpressionList = 'none'
            self.expressionText = ''

    
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
    disableOptimizeTree: bpy.props.BoolProperty(description='Disable automatic tree optimization', name='Disable Node Re-use')
    node_tree_name: bpy.props.StringProperty(name='Currently active node tree')

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
    node_tree_name: bpy.props.StringProperty(name='Currently active node tree')

    def __init__(self):
        super().__init__()

        #print("Doing revert")
        #find Dynamic Maths Node
        node_tree = get_active_node_tree(bpy.context)
        if 'Dynamic Maths Expression' in node_tree.nodes.keys():
            exprNode = node_tree.nodes['Dynamic Maths Expression']
            self.expressionText = exprNode.storedValidExpression
            #print("Set expression text to "+self.expressionText)
        else:
            self.expressionText = "!!! Can't retrieve expression"
        
        #trigger re-build - continue with execution of the operator
        
class DynamicMathsExpressionUpdate_Operator(_DynamicMathsExpression_Operator_common):
    """Update the expression (from the text block)"""
    
    bl_idname = "node.node_dynamic_maths_expression_update"
    bl_label = "Node Group - Dynamic Maths Expression(Update)"
    bl_space_type = 'NODE_EDITOR'
    label = 'Dynamic Maths Expression(Revert)'
    mode = 'UPDATE'
    bl_options = {'INTERNAL',}


    pruneSockets: bpy.props.BoolProperty(name='Prune Inputs/Outputs', description='Automatically remove unused sockets')
    resequenceInputs: bpy.props.BoolProperty(name='Auto-sequence Inputs', description='Automatically resequence input sockets')
    expressionText: bpy.props.StringProperty(description='Enter the expression', name='Expression')
    node_tree_name: bpy.props.StringProperty(name='Currently active node tree')

    def __init__(self):
        super().__init__()

        #Do nothing, just...
        #trigger re-build - continue with execution of the operator ('mode' will dictate update only)
    
class DynamicMathsExpressionShowDocumentation_Operator(bpy.types.Operator):
    """Split the current editor window and show the documentation"""
    
    bl_idname = "node.node_dynamic_maths_expression_showdocumentation"
    bl_label = "Node Group - Dynamic Maths Expression(Show Documentation)"
    bl_space_type = 'NODE_EDITOR'
    label = 'Show Documentation'
    bl_options = {'INTERNAL',}

    def __init__(self):
        #Do nothing
        pass
        
    def execute(self, context):
        pass
        bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
        #bpy.ops.screen.new()  #TODO: Create new window for the new area.
        
        otherarea = context.area                  #Instead of using the new one, use original (the right-hand split)
        newarea = context.screen.areas[-1]      #Assumed it's the last one in the stack (which it should be)
        
        newarea.type = 'TEXT_EDITOR'
        
        if "Node Expressions Documentation" in bpy.data.texts.keys():
            textblock = bpy.data.texts["Node Expressions Documentation"]
        else:
            textblock = bpy.data.texts.new("Node Expressions Documentation")
        
            documentationFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),"documentation.txt")
            if os.path.isfile(documentationFile):
                textblock.from_string(open(documentationFile).read())
            else:
                textblock.from_string("*** Failed to load the documentation file ***")

        editor = newarea.spaces[0]
        editor.text = textblock
        
        editor.top = 1
        bpy.ops.text.jump({"area":newarea}, line=1)
        bpy.ops.text.move({"area":newarea}, type="LINE_BEGIN")
        #TODO: Disable button if already visible
        #TODO: Don't re-load if already loaded (just re-show)
        
        #bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
        
        #Merge areas as if dragged top-right widget to right
        #print("BeforeMerge:"+str(otherarea.x)+","+str(otherarea.y)+","+str(newarea.x)+","+str(newarea.y))
        #print("BeforeDimensions:"+str(otherarea.width)+","+str(otherarea.height)+","+str(newarea.width)+","+str(newarea.height))
        #bpy.ops.screen.area_join({"area":otherarea}, min_x=otherarea.x, min_y=otherarea.y, max_x=newarea.x, max_y=newarea.y)
        #bpy.ops.screen.area_join({"area":newarea}, min_x=otherarea.x, min_y=newarea.y, max_x=newarea.x, max_y=newarea.y)
        #bpy.ops.screen.area_join({"area":otherarea}, min_x=0, min_y=0, max_x=-50, max_y=-50)
        #bpy.ops.screen.area_join({"area":newarea}, min_x=newarea.x, min_y=newarea.y, max_x=newarea.x+100, max_y=newarea.y)
        #print("AfterMerge:"+str(otherarea.x)+","+str(otherarea.y)+","+str(newarea.x)+","+str(newarea.y))
        #print("AfterDimensions:"+str(otherarea.width)+","+str(otherarea.height)+","+str(newarea.width)+","+str(newarea.height))
        
        return {'FINISHED'}
    
class DynamicMathsExpressionNode(bpy.types.NodeCustomGroup):
    """Node to hold the expression text and provide Edit button"""
    
    expressionText: bpy.props.StringProperty(description='', name='Expression')
    storedValidExpression: bpy.props.StringProperty(description='', name='Saved Expression')
    enableRevert: bpy.props.BoolProperty()
    
    bl_name='DynamicMathsExpressionNode'
    bl_label='Dynamic Maths Expression'

    # Setup the node - setup the node tree and add the group Input and Output nodes
    def init(self, context):
        #print("Node Init")
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
        #row=layout.row()
        #row.label(text='Saved Expression: '+str(self.storedValidExpression))
        row=layout.row()
        row.operator('node.node_dynamic_maths_expression_editwithin', text='Edit').node_tree_name = self.id_data.name; #Get group this node resides in

        layout.alert = self.enableRevert
        if self.enableRevert and self.storedValidExpression != "":
            row=layout.row()
            row.operator('node.node_dynamic_maths_expression_revert', text='Node is invalid! - Click to Revert').node_tree_name = self.id_data.name; #Get group this node resides in
            
        if self.expressionText.startswith("TEXT:"):
            row=layout.row()
            row.operator('node.node_dynamic_maths_expression_update', text='Update expression from Text block').node_tree_name = self.id_data.name; #Get group this node resides in
            
        
