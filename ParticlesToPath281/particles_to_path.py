# Author: Rich Sedman
# Description: Tools to convert a stream of particles to a curve
# Version: (0.02)
# Date: July 2018
################################################### History ######################################################
# 0.01  13/07/2018 : Initial version based on script developed for https://blender.stackexchange.com/questions/93921/how-to-add-trailing-light-effect-to-finger-tips/94976#94976
# 0.02  04/03/2019 : Amended for compatibility with Blender 2.8
# 0.03  21/07/2020 : Amended for compatibility with Blender 2.81
##################################################################################################################


import bpy

class ParticlesToPath():

    def createCurveFromParticles(objName, tracks=1, particleSystem=0, curveResolution=0, bevelDepth=0.1,bevelResolution=4,fillMode='FULL'):

        object = bpy.context.scene.objects[objName]
        print("Object = "+str(object))
        
        # NOTE : It seems the particle access requires an additional step in Blender 2.8. See https://developer.blender.org/T58792
        #eval_ob = bpy.context.depsgraph.objects.get(object.name, None)
        eval_ob = bpy.context.evaluated_depsgraph_get().objects.get(object.name, None)
        object = eval_ob
        
        particles = object.particle_systems[particleSystem].particles
        print("Particles = "+str(particles))
        print("Particle length = "+str(len(particles)))
        print("object.particle_systems length = "+str(len(object.particle_systems)))
        
        print("Here")
        trackNo = 0
        trackPoint = 0
        curves = []
        splines = []

        for p in particles:
            print("Here2")
            if trackPoint == 0:
                print("Here3")
                # Create new track
                curve = bpy.data.curves.new('particlePath', type='CURVE')
                curve.dimensions = '3D'
                curve.resolution_u = curveResolution
                curve.bevel_depth = bevelDepth
                curve.bevel_resolution = bevelResolution
                curve.fill_mode = fillMode
                spline = curve.splines.new('NURBS')
                curves.append(curve)
                splines.append(spline)

                #set first point
                print(spline.points[0])
                print(spline.points[0].co)
                spline.points[0].co = (p.location[0], p.location[1], p.location[2],1)
            else:
                # Add point
                print("Here4")
                splines[trackNo].points.add(1)  # Added 'count' for Blender 2.8
                splines[trackNo].points[trackPoint].co = (p.location[0], p.location[1], p.location[2],1)

            trackNo += 1

            if trackNo >= tracks:
                trackNo = 0
                trackPoint += 1

        print("Here5")
        # deselect all
        for curve in curves:
            print("Here6")
            curveObject = bpy.data.objects.new('particlePath', curve)
            curveObject.data.resolution_u = bevelResolution      # Required otherwise it's not updated in object (other attributes work though!)
            
            #bpy.context.scene.objects.link(curveObject)
            bpy.context.collection.objects.link(curveObject)   # See https://blender.stackexchange.com/questions/95408
            
            curveObject.update_from_editmode()

