# Script to convert a fluid simulation into an OpenEXR image

# RAS 26/06/2019 : Added 'pack' and 'use_fake_user' for newly generated images
# RAS 26/08/2019 : Improve efficiency of 'pack', add better diagnostics as to progress, implement 'multiRow' mode
#                  - all changes developed as part of the MRI Raw to EXR script.
# RAS 28/08/2019 : Implement hires capture

#TODO: multiple frames to one exr. Also, image compression... - actually, now 'multirow', can't do multiple frames... perhaps that could be a sub-mode for single-row mode only.

# Inspiration for the re-write taken from https://blender.stackexchange.com/a/182868/29586 by Leander
#
# 1.00 30/08/2020 : Use '...._grid' data direct from the modifier rather than read from Pointcache files

import bpy
import os
import sys
import math
import numpy as np

#def convert_volume_to_exr(object, oPattern, oframeno, multiRow=False, hiresMultiplier=1):
def convert_volume_to_exr(object, oPattern, oframeno, multiRow=False):

    #Set the frame
    bpy.context.scene.frame_set(oframeno)
    
    #Get populated domain settings
    domain_settings = object.evaluated_get(bpy.context.evaluated_depsgraph_get()).modifiers["Fluid"].domain_settings
        
    #if ...not smoke: 
    #
    #    print("Only 'smoke' type is currently processed - found "+str(flavor))
    #else:
    #    smokeversion = ....
    #    print("Smoke version = "+str(smokeversion))
    #    
    #    (fluid_fields,active_fields, res_x, res_y, res_z, dx) = ......
    #    print("Got fields %i\t%i\t%i\t%i\t%i\t%f" % (fluid_fields,active_fields, res_x, res_y, res_z, dx))
    res_x = domain_settings.domain_resolution[0]
    res_y = domain_settings.domain_resolution[1]
    res_z = domain_settings.domain_resolution[2]
    lowresgridsize = res_x * res_y * res_z
    
    if domain_settings.use_noise:
        hires_x = res_x * (domain_settings.noise_scale)
        hires_y = res_y * (domain_settings.noise_scale)
        hires_z = res_z * (domain_settings.noise_scale)
        hiresgridsize = hires_x * hires_y * hires_z
    else:
        hiresgridsize = lowresgridsize
    
    SM_ACTIVE_HEAT		= 1
    SM_ACTIVE_FIRE		= 2
    SM_ACTIVE_COLORS	= 4
    SM_ACTIVE_COLOR_SET	= 8

    #shadow = ....
    density = domain_settings.density_grid

    heat = None
    heatold = None
    #if (...doing heat) > 0:
    #    heat = ....
    #    heatold = ....
        
    flame = None
    fuel = None
    react = None
    #if (....doing burny...) > 0:
    #    flame = ....
    #    fuel = ....
    #    react = ....
    flame = domain_settings.flame_grid
    heat = domain_settings.heat_grid
    #...what about 'temperature_grid'?
    velocity = domain_settings.velocity_grid
    
    #Now use numpy to split the x,y,z array into 3 separate arrays
    velocityxyz = np.array(velocity)  #The basic numpy array
    
    #rgb_r = None
    #rgb_g = None
    #rgb_b = None
    colorrgb = np.array(domain_settings.color_grid)
    #    rgb_r = ....
    #    rgb_g = ....
    #    rgb_b = ....
        
    #obstacles = ....

    #extrafields = f.read(45*4)
    #rec = struct.unpack("fffffffffffiiifffffffffffffffffffiiiiiiiiifff",extrafields)
    #print("Extra Fields = "+str(rec))
    
    #hires_density = ....
    #hires_flame = ....
    #hires_fuel = ....
    #hires_react = ....

    #hires_rgb_r = None
    #hires_rgb_g = None
    #hires_rgb_b = None
    #if (....doing colours(hires)...) > 0:
    #    hires_rgb_r = ....
    #    hires_rgb_g = ....
    #    hires_rgb_b = ....

    #tcu = ....
    #tcv = ....
    #tcw = ....

    if len(density) == lowresgridsize:
        build_exr_from_buffers(gen_filename("smoke",oPattern, oframeno), (res_x, res_y, res_z), density, density, density, None, multiRow=multiRow)
    elif len(density) == hiresgridsize:
        build_exr_from_buffers(gen_filename("hires_smoke",oPattern, oframeno), (hires_x, hires_y, hires_z), density, density, density, None, multiRow=multiRow)
    else:
        print("density_grid unexpected size (%i)" % len(density))

    if len(flame) == lowresgridsize:
        build_exr_from_buffers(gen_filename("flame",oPattern, oframeno), (res_x, res_y, res_z), flame, flame, flame, None, multiRow=multiRow)
    elif len(flame) == hiresgridsize:
        build_exr_from_buffers(gen_filename("hires_flame",oPattern, oframeno), (hires_x, hires_y, hires_z), flame, flame, flame, None, multiRow=multiRow)
    else:
        print("flame_grid unexpected size (%i)" % len(flame))

    if len(heat) == lowresgridsize:
        build_exr_from_buffers(gen_filename("heat",oPattern, oframeno), (res_x, res_y, res_z), heat, heat, heat, None, multiRow=multiRow)
    elif len(heat) == hiresgridsize:
        build_exr_from_buffers(gen_filename("hires_heat",oPattern, oframeno), (hires_x, hires_y, hires_z), heat, heat, heat, None, multiRow=multiRow)
    else:
        print("heat_grid unexpected size (%i)" % len(heat))

    if velocityxyz.any() and len(velocityxyz > 0):
        velocityx = velocityxyz[0::3].tolist()   #Every 3rd element, starting at 0
        velocityy = velocityxyz[1::3].tolist()   #Every 3rd element, starting at 1
        velocityz = velocityxyz[2::3].tolist()   #Every 3rd element, starting at 2

        if len(velocityxyz) == lowresgridsize*3:
            build_exr_from_buffers(gen_filename("velocity",oPattern, oframeno), (res_x, res_y, res_z), velocityx, velocityy, velocityz, None, multiRow=multiRow)
        elif len(velocityxyz) == hiresgridsize*3:
            build_exr_from_buffers(gen_filename("hires_velocity",oPattern, oframeno), (hires_x, hires_y, hires_z), velocityx, velocityy, velocityz, None, multiRow=multiRow)
        else:
            print("velocity_grid unexpected size (%i)" % len(velocityxyz))

    if colorrgb.any() and len(colorrgb) > 0:
        colorr = colorrgb[0::4].tolist()   #Every 4th element, starting at 0
        colorg = colorrgb[1::4].tolist()   #Every 4th element, starting at 1
        colorb = colorrgb[2::4].tolist()   #Every 4th element, starting at 2
        colora = colorrgb[3::4].tolist()   #Every 4th element, starting at 3

        if len(colorrgb) == lowresgridsize*4:
            build_exr_from_buffers(gen_filename("color",oPattern, oframeno), (res_x, res_y, res_z), colorr, colorg, colorb, colora, multiRow=multiRow)
        elif len(colorrgb) == hiresgridsize*4:
            build_exr_from_buffers(gen_filename("hires_color",oPattern, oframeno), (hires_x, hires_y, hires_z), colorr, colorg, colorb, colora, multiRow=multiRow)
        else:
            print("color_grid unexpected size (%i)" % len(colorrgb))

    #TODO: Get HIRES working correctly
    #print("WARNING: HIRES not working for flame, fuel, react")
    #hires_rgb_b = None
    #hires_flame = None
    #hires_density = None

    #if rgb_b != None:
    #    build_exr_from_buffers(gen_filename("smoke",oPattern, oframeno), (res_x, res_y, res_z), rgb_r, rgb_g, rgb_b, None, multiRow=multiRow)
    #else:
    #    build_exr_from_buffers(gen_filename("smoke",oPattern, oframeno), (res_x, res_y, res_z), density, density, density, None, multiRow=multiRow)

    #if hires_rgb_b != None:
    #    build_exr_from_buffers(gen_filename("hires_smoke",oPattern, oframeno), (res_x*hiresmult, res_y*hiresmult, res_z*hiresmult), hires_rgb_r, hires_rgb_g, hires_rgb_b, None, multiRow=multiRow)          #TODO: This also seems to be 'wrong' if multi-colored!!!!
    #else:
    #    if hires_density != None:
    #        build_exr_from_buffers(gen_filename("hires_smoke",oPattern, oframeno), (res_x*hiresmult, res_y*hiresmult, res_z*hiresmult), hires_density, hires_density, hires_density, None, multiRow=multiRow)

    #if velocity_grid != None:
    #    build_exr_from_buffers(gen_filename("velocity",oPattern, oframeno), (res_x, res_y, res_z), vx, vy, vz, None, multiRow=multiRow)

    #if flame != None:
    #    build_exr_from_buffers(gen_filename("flame_heat_fuel",oPattern, oframeno), (res_x, res_y, res_z), flame, heat, fuel, None, multiRow=multiRow)
            
    #if hires_flame != None:
    #    #build_exr_from_buffers(gen_filename("hires_flame_react_fuel",oPattern, oframeno), (res_x*hiresmult, res_y*hiresmult, res_z*hiresmult), hires_flame, hires_react, hires_fuel, None, multiRow=multiRow)
        #build_exr_from_buffers(gen_filename("hires_flame_react_fuel",oPattern, oframeno), (res_x, res_y, res_z), hires_flame, hires_react, hires_fuel, None, multiRow=multiRow)     #TODO: Determine why these buffers aren't hires and what they are... something to do with hires turbulence?!!!
    #    build_exr_from_buffers(gen_filename("hires_flame_react_fuel",oPattern, oframeno), (res_x*hiresmult, res_y*hiresmult, res_z*hiresmult), hires_flame, hires_react, hires_fuel, None, multiRow=multiRow)     #TODO: Determine why these buffers aren't hires and what they are... something to do with hires turbulence?!!!


    #f.close()

# Generate filename by combining name, pattern, frameno
def gen_filename(name, pattern, frameno):
    return pattern % (name, frameno)


def build_exr_from_buffers(filename, dimensions, bufferR, bufferG, bufferB, bufferA, multiRow=False):

    #...want to re-write this to use numpy functions.... could work something like this...
    #1) split the array into 3-dimensional representation of pixels (should be one-liner, I think)
    #2) add elements such that it will form a complete 'grid' of images (eg, 10x10)
    #3) convert to a 4-d array with gridx, gridy, x, y*dimensions
    #4) take each 'gridy' set and split the lines of each sub-array
    #5) interleave those lines
    #6) flatten it
    #7) combine them all

    if multiRow:
        numColumns = math.ceil(math.sqrt(dimensions[2]))
        numRows = math.ceil(dimensions[2] / numColumns)
    else:
        numColumns = dimensions[2]
        numRows = 1

    filename = str(dimensions[2])+"_"+str(numColumns)+"x"+str(numRows)+"_"+filename

    print("Building image %s" % filename)

    # Size the image to allow space for Z images of size X by Y
    width = (dimensions[0]+1)*numColumns
    if numRows >1:
        height = (dimensions[1]+1)*numRows
    else:
        height = dimensions[1]

    # Create the image
    image = bpy.data.images.new(filename, width=width, height=height,float_buffer=True)

    # Create an empty array of pixel data (each will hold R, G, B, A values as floats)
    print("Clearing image...")
    pixels = [None] * width * height
    for x in range(0,width):
        for y in range(0,height):
            pixels[y*width+x] = [0.0,0.0,0.0,0.0]
            
    print("File '"+filename+"', Dimensions = ("+str(dimensions[0])+","+str(dimensions[1])+","+str(dimensions[2])+")")
 
    yrange = range(0,dimensions[1])
    xrange = range(0,dimensions[0])
 
    for z in range(0,dimensions[2]):
        print("Processing layer "+str(z))
        
        #Calculate the location of this 'tile'
        tileNoX = z % numColumns
        tileNoY = int((z - tileNoX) / numColumns)
        tileOffset = tileNoX*(dimensions[0]+1)+tileNoY*width*(dimensions[1]+1)

        #for y in range(0,dimensions[1]):
        for y in yrange:
        
            poffset = y*dimensions[0]+z*dimensions[0]*dimensions[1]
        
            #for x in range(0,dimensions[0]):
            for x in xrange:
            
                #p = x+y*dimensions[0]+z*dimensions[0]*dimensions[1]
                p = poffset + x

                # If R, G, or B are 'none' then 0.0 is assumed
                valR = 0
                valG = 0
                valB = 0
                if bufferR != None:
                    #valR = struct.unpack('f',bufferR[p*4:p*4+4])[0]
                    valR = bufferR[p]
                    
                if bufferG != None:
                    #valG = struct.unpack('f',bufferG[p*4:p*4+4])[0]
                    valG = bufferG[p]

                if bufferB != None:
                    #valB = struct.unpack('f',bufferB[p*4:p*4+4])[0]
                    valB = bufferB[p]

                # bufferA can be None to indicate not used (in which case 1.0 is assumed)
                if bufferA != None:
                    #valA = struct.unpack('f',bufferA[p*4:p*4+4])[0]
                    valA = bufferA[p]
                else:
                    valA = 1.0
                
                #pixels[(y*width)+x+z*(dimensions[0]+1)] = [valR,valG,valB,valA]
                pixels[tileOffset + x + y*width] = [valR,valG,valB,valA]

    # 'flatten' the array - so [R1,G1,B1,A1], [R2,G2,B2,A2], [R3,G3,B3,A3],.... becomes R1,B1,G1,A1,R2,G2,B2,A2,R3,G3,B3,A3,....    
    # Store the pixels in the image
    print("Image build complete, storing pixels...")
    image.pixels = [chan for px in pixels for chan in px]
    print("Updating image...")
    image.update()

    print("Saving image...")
    # Save image to temporary file and pack it (from answer by @sambler)
    scn = bpy.data.scenes.new('img_settings')
    scn.render.image_settings.file_format = 'OPEN_EXR'
    scn.render.image_settings.exr_codec = 'ZIP'
    scn.render.image_settings.color_mode = 'RGBA'
    scn.render.image_settings.color_depth = '32'
    img_path = bpy.path.abspath('//')
    img_file = image.name+'.exr'
    image.save_render(img_path+img_file, scene=scn)
    try:
        # Remove the scene (pre-2.78)
        bpy.data.scenes.remove(scn)
    except:
        # Remove the scene, (Blender 2.78+)
        bpy.data.scenes.remove(scn, do_unlink=True)
        
    #Pack the images (needs to be saved and re-opened)
    if bpy.app.version_string.startswith('2.79'):
        bpy.data.images.remove(image)
        bpy.ops.image.open(filepath=img_path+img_file)
        image = bpy.data.images[img_file]
        
    image.pack()
    if bpy.app.version_string.startswith('2.79'):
        os.remove(img_path+img_file)
    
    image.use_fake_user = True
    print("Complete.")

class Fluid2EXR_Operator(bpy.types.Operator):
    """Convert a fluid domain into an EXR image file"""
    
    bl_idname = "operator.smoke2exr"
    bl_label = "Smoke2EXR - Convert smoke domain into an EXR image"
    bl_space_type = 'VIEW_3D'
    label = 'Smoke2EXR'
    #bl_options = {}

    frameNo: bpy.props.IntProperty(description='Enter the frame to convert', name='Frame')
    #smokeCacheName: bpy.props.StringProperty(description="The selection object's smoke cache name", name="Cache Name")
    multiRow: bpy.props.BoolProperty(description='Create multi-row image instead of a single row of tiles', name="Multi-Row")
       

    def __init__(self):
        super().__init__()
        self.multiRow = True
        

    @classmethod
    def poll(cls, context):
        #space = context.space_data
        #return space.type == 'VIEW_3D'
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        
        self.frameNo = context.scene.frame_current
        
        #viewWidth = bpy.context.area.width * 0.8
        #
        object_active = context.active_object
        objects_selected = context.selected_objects
        
        if len(objects_selected) < 1:
            self.report({'ERROR'}, 'Must select the smoke domain object')
            return {"CANCELLED"}
        
        if len(objects_selected) > 1:
            self.report({'ERROR'}, 'Must select only the single smoke domain object')
            return {"CANCELLED"}
            
        selected_object = objects_selected[0]
        
        if not 'Fluid' in selected_object.modifiers.keys():
            self.report({'ERROR'}, "Object must include a Fluid modifier named 'Fluid'")
            return {"CANCELLED"}
        
        #TODO: Use the modifier type rather than name and also check that it's set to a *smoke domain*
        
        #smokeCache = selected_object.modifiers['Fluid'].domain_settings.point_cache
        
        #self.smokeCacheName = smokeCache.name
        #print("Smoke cache name = "+str(self.smokeCacheName))
        
        #self.smokeCache = smokeCache
        #self.domainSettings = smokeCache = selected_object.modifiers['Smoke'].domain_settings
        self.domainSettings = selected_object.modifiers['Fluid'].domain_settings
        self.domainObject = selected_object
        
        return wm.invoke_props_dialog(self)

    def execute(self, context):
  
        #smokeCacheName = str(self.smokeCacheName)
        #
        #if len(smokeCacheName) == 0:
        #    self.report({'ERROR'}, "Smoke cache must be baked to a *named* cache.")
        #    return {"CANCELLED"}
        #    #TODO: Pickup the "random" generated name if we don't find an explicit name
            
        #cachefile = bpy.path.abspath("//blendcache_%s/%s_%06i_00.bphys" % (bpy.path.basename(bpy.context.blend_data.filepath[:-6]),smokeCacheName,self.frameNo))
        
        #hiresMultiplier = self.domainSettings.amplify + 1
        #hiresMultiplier = 1
        
        #convert_volume_to_exr(self.domainObject, "%s_%06i", self.frameNo, self.multiRow, hiresMultiplier=hiresMultiplier)
        convert_volume_to_exr(self.domainObject, "%s_%06i", self.frameNo, self.multiRow)
        return {'FINISHED'}
    

#Run it....
#for frame in range(10,11):
#    cachefile = bpy.path.abspath("//blendcache_%s/smoke_%06i_00.bphys" % (bpy.path.basename(bpy.context.blend_data.filepath[:-6]),frame))
#    convert_pointcache_volume_to_exr(cachefile, "output/%s_%06i", frame)

#Possibly build up the filename using the name of the pointcache from :
# bpy.data.objects["Smoke Domain"].modifiers["Smoke"].domain_settings.point_cache.name
#...also, need to ensure the cache is set to a compatible 'mode' so that we can uncompress and interpret it.