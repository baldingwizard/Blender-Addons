# Author: Rich Sedman
# Description: Tools to manage node trees
# Version: (0.02)
# Date: June 2018
################################################### History ######################################################
# 0.01  09/06/2018 : Initial version based on function originally in DynamicMathsExpressionNode class
# 0.02  11/06/2018 : Enhanced to provide simple hierarchy layout
# 0.03  10/06/2019 : Implement spacingFactor for hierarchical layout
# 0.04  18/07/2019 : Allow 'lastNode' and 'additionalNodes' to be specified when calling hierarchical layout.
#                    The 'additionalNodes' can be used to position sub-sections of the tree to 'fold' it into a
#                    shorter space.
#                    Change to use dictionary instead of array for storing node levels.
# 0.05  13/09/2019 : Cut down unnecessary scans of the heirarchy if parent already processed at a better level.
##################################################################################################################


import bpy

class NodeTreeTools():

    def arrange_nodes(self, node_tree, repulse, use_links):
        
        forces = {}
        for node in node_tree.nodes:

            forcex = 0
            forcey = 0

            for node2 in node_tree.nodes:
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
                        forcex += separation[0] / (distance+1) * 2
                        forcey += separation[1] / (distance+1) * 8
                        #print(node.name+" force = ("+str(forcex)+","+str(forcey)+")" + " SEP="+str(separation)+", DIST="+str(distance))
                
                if use_links:
                    #check if connected. If so, apply x-force to move them
                    if len(node.inputs) > 0:
                        idx = -1
                        for inp in node.inputs:
                            idx+=1
                    
                            #if node2.name in forces:
                            #    node2_force = forces[node2.name]
                            
                            #    node2_forcex = node2_force[0]
                            #    node2_forcey = node2_force[1]
                            #else:
                            node2_forcex = 0
                            node2_forcey = 0
                                
                            for link in inp.links:
                                #print("Looking..."+str(link)+":"+str(link.from_socket.node)+":"+str(node2))
                                if link.from_socket.node == node2:
                                    #if node2.location[0] > node.location[0]-node.width*1.3:
                                    #    node2_forcex -= 10
                                    #    #print("GOT! "+str(node2.location)+","+str(node.location))
                                    #else:
                                    #    node2_forcex += 5
                                    ##    #print("Not got! "+str(node2.location)+","+str(node.location))
                                    delta = node2.location[0] - (node.location[0]-node.width*2.3)
                                    node2_forcex -= delta/200+1
                                    forcex += delta/200+1
                    
                                    # Get index and apply y-force to separate multiple inputs
                                    if idx > 0:
                                        if node2.location[1] > node.location[1]-node.height*1.3:
                                            #print(node2.name+": "+str(node2.location[1])+", "+node.name+": "+str(node.location[1])+"("+str(node.height)+")")
                                            node2_forcey -= 10*idx
                                            forcey += 10*idx
                                            #print(str(node2.name)+" ForceY = "+str(node2_forcey)+", idx="+str(idx))
                                        else:
                                            node2_forcey += 10
                                            forcey -= 10
                                    else:
                                        if node2.location[1] < node.location[1]+node.height*1.3:
                                            #print(node2.name+": "+str(node2.location[1])+", "+node.name+": "+str(node.location[1])+"("+str(node.height)+")")
                                            node2_forcey += 10
                                            forcey -= 10
                                            #print(str(node2.name)+" ForceY = "+str(node2_forcey)+", idx="+str(idx))
                                        else:
                                            node2_forcey -= 10
                                            forcey += 10
                                            
                            if node2.name in forces:
                                forces[node2.name] = (forces[node2.name][0]+node2_forcex, forces[node2.name][1]+node2_forcey)
                            else:
                                forces[node2.name] = (node2_forcex, node2_forcey)
                            #print("Node2 Forces = "+str(forces[node2.name]))

            if node.name in forces:
                forces[node.name] = (forces[node.name][0]+forcex, forces[node.name][1]+forcey)
                #print("ForceUpd(1) "+node.name+"("+str(node.width)+","+str(node.height)+")"+" = ("+str(forces[node.name][0])+","+str(forces[node.name][1])+")")
            else:
                forces[node.name] = (forcex, forcey)
                #print("ForceNew(1) "+node.name+"("+str(node.width)+","+str(node.height)+")"+" = ("+str(forcex)+","+str(forcey)+")")

        #move based on combined force
        for node in node_tree.nodes:
            #print("force on node "+str(node)+" = "+str(forces[node.name]))
            node.location[0] += forces[node.name][0]*5
            node.location[1] += forces[node.name][1]*5
            
    _node_levels = {}
    def arrangeBasedOnHierarchy(node_tree, lastNode=None, additionalNodes=None, spacingFactor=1.5):
        #print("Arrange based on Hierarchy start")
        NodeTreeTools._node_levels = {}
    
        # Get 'Group Output' as the 'end' of the tree
        if lastNode == None:
            endNode = node_tree.nodes['Group Output']
        else:
            endNode = lastNode

        # Scan back from the 'end', assigning levels along the way
        NodeTreeTools._recursivelyScanTreeForLevelsFromEnd(endNode,0)
        
        if additionalNodes != None:
            for node in additionalNodes:
                NodeTreeTools._recursivelyScanTreeForLevelsFromEnd(node,1, replaceLevel = True)
        
        levelMaxHeight = {}
        levelMaxWidth = {}
        
        # Process the 'levels', positioning each node and its predecessors
        maxLevel = -1
        maxNodeWidth = -1
        maxNodeHeight = -1
        for name in NodeTreeTools._node_levels.keys():
            level = NodeTreeTools._node_levels[name]
            #print("NodeLevel : "+str(rec))
            if level>maxLevel:
                maxLevel = level
            node = node_tree.nodes[name]
            #print("Node "+node.name+", IDName "+str(node.bl_idname)+", Level "+str(level)+" Width="+str(node.dimensions[0])+", Height="+str(node.dimensions[1]))
            #print ("Node.bl_width_default = "+str(node.bl_width_default))
            
            #For some reason, NodeReroute nodes are reporting as 140x100 which, obviously, they are not - so override with more reasonable size
            if node.bl_idname == 'NodeReroute':
                nodeWidth = 10
                nodeHeight = 10
            else:
                nodeWidth = node.width
                nodeHeight = node.height
                
            #Add some additional spacing
            nodeWidth += 80
            nodeHeight += 100
                
            if nodeWidth > maxNodeWidth:
                maxNodeWidth = nodeWidth
            if nodeHeight > maxNodeHeight:
                maxNodeHeight = nodeHeight
                
            if level in levelMaxHeight.keys():
                if nodeHeight > levelMaxHeight[level]:
                    levelMaxHeight[level] = nodeHeight
            else:
                levelMaxHeight[level] = nodeHeight
            
            if level in levelMaxWidth.keys():
                if nodeWidth > levelMaxWidth[level]:
                    levelMaxWidth[level] = nodeWidth
            else:
                levelMaxWidth[level] = nodeWidth
            
        #TODO: Better to size each 'level' properly based on the nodes at that level

        sumOfWidths = 0
        for l in range(0,maxLevel+1):
            sumOfWidths += levelMaxWidth[l]

        x = sumOfWidths/2
        for l in range(0,maxLevel+1):
            x -= levelMaxWidth[l]
            maxNodeWidth = levelMaxWidth[l]
            maxNodeHeight = levelMaxHeight[l]
            #print("Level "+str(l)+" Width="+str(maxNodeWidth)+", Height="+str(maxNodeHeight))
            y = 0
            for name in NodeTreeTools._node_levels.keys():
                if NodeTreeTools._node_levels[name] == l:
                    node = node_tree.nodes[name]
                    node.location[0] = x        #(maxLevel/2 - l) * maxNodeWidth*spacingFactor
                    node.location[1] = y
                    y -= maxNodeHeight          #*2
        #print("Arrange based on Hierarchy finished")
                
    def _recursivelyScanTreeForLevelsFromEnd(node, level, replaceLevel = False):
    
        #if level > 100:
        #    print("node_tree_tools._recursivelyScanTreeForLevelsFromEnd: Reached 100 node depth - stopping scan")
        #    return
        
        _found = False
        if node.name in NodeTreeTools._node_levels.keys():
            _found = True
        
        if _found:
            if (NodeTreeTools._node_levels[node.name] < level) or replaceLevel:
                NodeTreeTools._node_levels[node.name] = level
            else:
                #This node was already processed at a 'lower' level - so no need to re-scan
                return
                
        else:
            NodeTreeTools._node_levels[node.name] = level
        
        for linkedNode in NodeTreeTools._getUpstreamNodes(node):
            NodeTreeTools._recursivelyScanTreeForLevelsFromEnd(linkedNode, level+1)
            
    def _getUpstreamNodes(node):
        #....return list of nodes feeding into this one
        nodelist = []
        
        for inp in node.inputs:
            for l in inp.links:
                nodelist.append(l.from_socket.node)
                
        return nodelist