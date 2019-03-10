# Author: Rich Sedman
# Description: Blend vertex colors over a mesh
# Version: (0.02)
# Date: July 2018
################################################### History ######################################################
# -.01 10/03/2019 : Initial creation
# 0.02 10/03/2019 : Amend to allow for 3 or 4 elements of vertex color
##################################################################################################################


import bpy

class VertexColorBlend():

    def color_vertices_rgb(obj, vertexGroup, iterations, initialColor=(0.5,0.5,0.5)):
        """Merges the colors assigned to the specified vertex group across the rest of the mesh"""

        obj.update_from_editmode()

        mesh = obj.data 
        scn = bpy.context.scene

        #check if our mesh already has Vertex Colors, and if not add some... (first we need to make sure it's the active object)
        scn.objects.active = obj
        obj.select = True
        mesh.vertex_colors.new()
        vert_cols = mesh.vertex_colors[0]

        fixed_vertices = []
        vert_colors = {}
        vert_links = {}

        print("Capturing data...")
        for vert in obj.data.vertices:
            print(str(vert.index))
            vertidx = vert.index
            if  VertexColorBlend.vertex_in_group(obj,vertidx, vertexGroup):
                fixed_vertices.append(vertidx)
                vert_colors[str(vertidx)] = VertexColorBlend.get_vertex_color(obj, vertidx)
            else:
                vert_colors[str(vertidx)] = initialColor

            vert_links[str(vertidx)] = VertexColorBlend.get_linked_verts(obj, vertidx)

        print("Captured.")
        for p in range(0,iterations):
            print("Pass "+str(p))
            new_colors = {}

            for vert in obj.data.vertices:
                vertidx = vert.index

                color = VertexColorBlend.average_color(vert_colors, vert_links, vertidx)
                red = color[0]
                green = color[1]
                blue = color[2]

                if vertidx in fixed_vertices:
                    red = vert_colors[str(vertidx)][0]
                    green = vert_colors[str(vertidx)][1]
                    blue = vert_colors[str(vertidx)][2]

                new_colors[str(vertidx)] = (red,green,blue,1.0)

            #Copy new colors back to vert_colors 
            for vert in obj.data.vertices:
                vertidx = vert.index
                vert_colors[str(vertidx)] = new_colors[str(vertidx)]

        print("Storing colors...")
        for vert in obj.data.vertices:
            vertidx = vert.index

            VertexColorBlend.set_vertex_color(obj, vertidx, vert_colors[str(vertidx)])

    def vertex_in_group(obj, vertidx, group):
        """Looks for the named vertex 'group' on the specified 'obj'
           and returns true or false depending on whether the specified
           'vert' is in that 'group'"""

        groupindex = obj.vertex_groups[group].index

        for v in obj.data.vertices:
            if v.index == vertidx:
                for g in v.groups:
                    if g.group == groupindex:
                        return True
        return False

    def get_vertex_color(obj, vertid):
        for loop in obj.data.loops:
            if loop.vertex_index == vertid:
                #NOTE : It seems the vertex color includes Alpha in newer Blender versions
                #       so just return the first 3 elements to be consistent.
                c = obj.data.vertex_colors[0].data[loop.index].color
                return (c[0],c[1],c[2])
        return (0.0,0.0,0.0)

    def set_vertex_color(obj, vertid, color):
        for loop in obj.data.loops:
            if loop.vertex_index == vertid:
                #NOTE : It seems the vertex color includes Alpha in newer Blender versions
                #       Try assigning 3 elements first and if that fails, try 4.
                try:
                    obj.data.vertex_colors[0].data[loop.index].color = (color[0],color[1],color[2])
                except:
                    obj.data.vertex_colors[0].data[loop.index].color = (color[0],color[1],color[2],1.0)

    def average_color(vert_colors, vert_links, vertid):

        r = 0.0
        g = 0.0
        b = 0.0
        num_verts = 0

        for linkedvertid in vert_links[str(vertid)]:
            col = vert_colors[str(linkedvertid)]
            r = r + col[0]
            g = g + col[1]
            b = b + col[2]
            num_verts += 1
        return (r/num_verts, g/num_verts, b/num_verts)

    def get_linked_verts(obj, vertid):
        verts = []
        for edge in obj.data.edges:
            if edge.vertices[0] == vertid:
                verts.append(edge.vertices[1])
            elif edge.vertices[1] == vertid:
                verts.append(edge.vertices[0])

        return verts
