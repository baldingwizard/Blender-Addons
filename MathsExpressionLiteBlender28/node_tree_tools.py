# Author: Rich Sedman
# Description: Tools to manage node trees
# Version: (0.02)
# Date: June 2018
################################################### History ######################################################
# 0.01  09/06/2018 : Initial version based on function originally in DynamicMathsExpressionNode class
# 0.02  11/06/2018 : Enhanced to provide simple hierarchy layout
# 0.03  10/06/2019 : Implement spacingFactor for hierarchical layout
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
            
    _node_levels = []
    def arrangeBasedOnHierarchy(node_tree, spacingFactor=1.5):

        del(NodeTreeTools._node_levels[:])
    
        # Get 'Group Output' as the 'end' of the tree
        endNode = node_tree.nodes['Group Output']

        # Scan back from the 'end', assigning levels along the way
        NodeTreeTools._recursivelyScanTreeForLevelsFromEnd(endNode,0)
        
        # Process the 'levels', positioning each node and its predecessors
        maxLevel = -1
        maxNodeWidth = -1
        maxNodeHeight = -1
        for rec in NodeTreeTools._node_levels:
            #print("NodeLevel : "+str(rec))
            if rec[1]>maxLevel:
                maxLevel = rec[1]
            node = node_tree.nodes[rec[0]]
            if node.width > maxNodeWidth:
                maxNodeWidth = node.width
            if node.height > maxNodeHeight:
                maxNodeHeight = node.height

        for l in range(0,maxLevel+1):
            y = 0
            for rec in NodeTreeTools._node_levels:
                if rec[1] == l:
                    node = node_tree.nodes[rec[0]]
                    node.location[0] = (maxLevel/2 - l) * maxNodeWidth*spacingFactor
                    node.location[1] = y
                    y -= maxNodeHeight*2
                
    def _recursivelyScanTreeForLevelsFromEnd(node, level):
    
        _found_idx = -1
        for idx in range(0,len(NodeTreeTools._node_levels)):
            if NodeTreeTools._node_levels[idx][0] == node.name:
                _found_idx = idx
        
        if _found_idx >= 0:
            if NodeTreeTools._node_levels[_found_idx][1] < level:
                NodeTreeTools._node_levels[_found_idx] = (node.name, level)
        else:
            NodeTreeTools._node_levels.append((node.name, level))
        
        for linkedNode in NodeTreeTools._getUpstreamNodes(node):
            NodeTreeTools._recursivelyScanTreeForLevelsFromEnd(linkedNode, level+1)
            
    def _getUpstreamNodes(node):
        #....return list of nodes feeding into this one
        nodelist = []
        
        for inp in node.inputs:
            for l in inp.links:
                nodelist.append(l.from_socket.node)
                
        return nodelist