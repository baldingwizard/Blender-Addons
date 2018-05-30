import bpy

from .parse_expression import Expression

class DynamicMathsExpressionNode(bpy.types.NodeCustomGroup):

    bl_name='DynamicMathsExpression'
    bl_label='Dynamic Maths Expression'

    # Return the list of valid operators
    def modes(self, context):
        nt=context.space_data.edit_tree
        list=[('CLOSED','Closed',"Don't allow access to internal nodes"),('OPEN', 'Open', 'Allow access to internal nodes') ]
        return list            

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

        ## Look for input sockets that are no longer required and remove them
        #for i in range(len(self.node_tree.inputs),0,-1):
        #    if i > self.inputSockets:
        #        self.node_tree.inputs.remove(self.node_tree.inputs[-1])
        #
        ## Add any additional input sockets that are now required
        #for i in range(0, self.inputSockets):
        #    if i > len(self.node_tree.inputs):
        #        self.node_tree.inputs.new("NodeSocketFloat", "Value")

    def arrange_nodes(self, repulse, use_links):
        
        forces = {}
        for node in self.node_tree.nodes:

            forcex = 0
            forcey = 0

            for node2 in self.node_tree.nodes:
                if node == node2:
                    continue
                
                nodeCentre = [node.location[0] + node.width/2, node.location[1] + node.height/2]
                node2Centre = [node2.location[0] + node2.width/2, node2.location[1] + node2.height/2]
                
                if repulse:
                    #check if overlapping or 'too close'. If so, apply force to move them
                    separation = [nodeCentre[0] - node2Centre[0], nodeCentre[1] - node2Centre[1]]
                    distance = (separation[0]**2 + separation[1]**2) ** 0.5
                    targetDistance = (node2.width+node2.height)/2 * 2
                    
                    if distance > 0 and distance < targetDistance:
                        forcex += separation[0] / (distance+1) * 10
                        forcey += separation[1] / (distance+1) * 10
                
                if use_links:
                    #check if connected. If so, apply x-force to move them
                    if len(node.inputs) > 0:
                        idx = -1
                        for inp in node.inputs:
                            idx+=1
                    
                            if node2.name in forces:
                                node2_force = forces[node2.name]
                                   
                                node2_forcex = node2_force[0]
                                node2_forcey = node2_force[1]
                            else:
                                node2_forcex = 0
                                node2_forcey = 0
                                
                            for link in inp.links:
                                #print("Looking..."+str(link)+":"+str(link.from_socket.node)+":"+str(node2))
                                if link.from_socket.node == node2:
                                    if node2.location[0] > node.location[0]-node.width*1.3:
                                        node2_forcex -= 10
                                        #print("GOT! "+str(node2.location)+","+str(node.location))
                                    #else:
                                    #    #print("Not got! "+str(node2.location)+","+str(node.location))
                    
                                    # Get index and apply y-force to separate multiple inputs
                                    if idx > 0:
                                        if node2.location[1] > node.location[1]-node.height*1.3:
                                            #print(node2.name+": "+str(node2.location[1])+", "+node.name+": "+str(node.location[1])+"("+str(node.height)+")")
                                            node2_forcey -= 2
                                            #print(str(node2.name)+" ForceY = "+str(node2_forcey)+", idx="+str(idx))
                                        else:
                                            node2_forcey += 1
                                    else:
                                        if node2.location[1] < node.location[1]+node.height*1.3:
                                            #print(node2.name+": "+str(node2.location[1])+", "+node.name+": "+str(node.location[1])+"("+str(node.height)+")")
                                            node2_forcey += 2
                                            #print(str(node2.name)+" ForceY = "+str(node2_forcey)+", idx="+str(idx))
                                        else:
                                            node2_forcey -= 1
                                            
                            forces[node2.name] = (node2_forcex, node2_forcey)
                            #print("Node2 Forces = "+str(forces[node2.name]))
 
            if node.name in forces:
                forces[node.name] = (forces[node.name][0], forces[node.name][1])
            else:
                forces[node.name] = (forcex, forcey)

        #move based on combined force
        for node in self.node_tree.nodes:
            #print("force on node "+str(node)+" = "+str(forces[node.name]))
            node.location[0] += forces[node.name][0]*5
            node.location[1] += forces[node.name][1]*5
            

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
        #if self.inputSockets <= 1:
        #    # Special case <= 1 input --> link input directly to output
        #    self.node_tree.links.new(previousnode.outputs[0],self.node_tree.nodes['Group Output'].inputs[0])
        #else:
        #    # Create one node for each input socket > 1
        #    for i in range(1, self.inputSockets):
        #        newnode = self.node_tree.nodes.new('ShaderNodeMath')
        #        newnode.operation = self.selectOperator
        #        self.node_tree.links.new(previousnode.outputs[0],newnode.inputs[0])
        #        self.node_tree.links.new(groupinput.outputs[i],newnode.inputs[1])
        #        previousnode = newnode
        #
        #    # Connect the last one to the output
        #    self.node_tree.links.new(previousnode.outputs[0],self.node_tree.nodes['Group Output'].inputs[0])

        print("About to parse expression...")
        operations = Expression.parse_expression(self.expressionText)
        self.build_nodes(operations, self.node_tree.nodes['Group Output'].inputs[0], self.node_tree.nodes['Group Output'].location,0)
        
        for l in range(1,40):
            print("Arrange("+str(l)+")")
            self.arrange_nodes(True, True)
        
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
                
        #run through the 'Group Input' sockets and remove any that are no longer connected
        for output in self.node_tree.nodes['Group Input'].outputs:
            if len(output.name) > 0 and len(output.links) == 0:
                print("Need to remove "+str(output))
                self.node_tree.nodes['Group Input'].outputs.remove(output)  ### This doesn't appear to be working!!!!

    # Chosen operator has changed - update the nodes and links
    def update_mode(self, context):
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()

#    # Number of inputs has changed - update the nodes and links
#    def update_inpSockets(self, context):
#        self.__nodeinterface_setup__()
#        self.__nodetree_setup__()

    # Expression has changed - update the nodes and links
    def update_expression(self, context):
        
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()

    # The node properties - Operator (Add, Subtract, etc.) and number of input sockets
    selectMode=bpy.props.EnumProperty(name="selectMode", items=modes, update=update_mode)    
    expressionText = bpy.props.StringProperty(name="Expression", update=update_expression)

    # Setup the node - setup the node tree and add the group Input and Output nodes
    def init(self, context):
        self.node_tree=bpy.data.node_groups.new(self.bl_name, 'ShaderNodeTree')
        if hasattr(self.node_tree, 'is_hidden'):
            self.node_tree.is_hidden=True
        self.node_tree.nodes.new('NodeGroupInput')
        self.node_tree.nodes.new('NodeGroupOutput') 

    # Draw the node components
    def draw_buttons(self, context, layout):
        row=layout.row()
        row.alert=(self.selectMode=='None')
        row.prop(self, 'selectMode', text='')
        row=layout.row()
        row.prop(self, 'expressionText', text='Expression')

    # Copy
    def copy(self, node):
        self.node_tree=node.node_tree.copy()

    # Free (when node is deleted)
    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)
