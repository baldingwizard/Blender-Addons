# Author: Rich Sedman
# Description: Tools to convert a stream of particles to a curve
# Version: (0.01)
# Date: July 2018
################################################### History ######################################################
# 0.01  13/07/2018 : Initial version based on script developed for https://blender.stackexchange.com/questions/93921/how-to-add-trailing-light-effect-to-finger-tips/94976#94976
##################################################################################################################


import bpy

class ParticlesToPath():

    def createCurveFromParticles(objName, tracks=1, particleSystem=0, curveResolution=0, bevelDepth=0.1,bevelResolution=4,fillMode='FULL'):

        object = bpy.context.scene.objects[objName]

        particles = object.particle_systems[particleSystem].particles

        trackNo = 0
        trackPoint = 0
        curves = []
        splines = []

        for p in particles:
            if trackPoint == 0:
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
                splines[trackNo].points.add()
                splines[trackNo].points[trackPoint].co = (p.location[0], p.location[1], p.location[2],1)

            trackNo += 1

            if trackNo >= tracks:
                trackNo = 0
                trackPoint += 1

        # deselect all
        for curve in curves:
            curveObject = bpy.data.objects.new('particlePath', curve)
            curveObject.data.resolution_u = bevelResolution      # Required otherwise it's not updated in object (other attributes work though!)
            bpy.context.scene.objects.link(curveObject)
            curveObject.update_from_editmode()

