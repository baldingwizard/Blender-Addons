# Script to convert a smoke simulation PointCache2 into an OpenEXR image

# RAS 26/06/2019 : Added 'pack' and 'use_fake_user' for newly generated images
# RAS 26/08/2019 : Improve efficiency of 'pack', add better diagnostics as to progress, implement 'multiRow' mode
#                  - all changes developed as part of the MRI Raw to EXR script.

#TODO: multiple frames to one exr. Also, image compression... - actually, now 'multirow', can't do multiple frames... perhaps that could be a sub-mode for single-row mode only.

# Supports PointCache smoke version 1.04
#
# Smoke pointcache format :
# Bytes     Content
# 8         'BPHYSICS'
# 4         int - 3 (indicates Smoke)
# 4         int? (!!thought this was size of data... but compressed size exceeds this so one of them is wrong)
# 4         int (2 (???))
# 4         '1.04' (version)
# 4         int (fluid_fields)
# 4         int (active_fields)
# 4         int (res_X)
# 4         int (res_Y)
# 4         int (res_Z)
# 4         float? (dx)
# block - shadow (x * y * z * float)
# block - density (x * y * z * float)
# Optional :
#   block - heat (x * y * z * float)
#   block - heatold (x * y * z * float)
# Optional :
#   block - flame (x * y * z * float)
#   block - fuel (x * y * z * float)
#   block - react (x * y * z * float)
# Optional :
#   block - red (x * y * z * float)
#   block - green (x * y * z * float)
#   block - blue (x * y * z * float)
# block - vx (x * y * z * float)
# block - vy (x * y * z * float)
# block - vz (x * y * z * float)
# block - obstacles (x * y * z * byte?) (!!Doesn't seem to be populated)
# (more fields)
#		ptcache_file_write(pf, &dt, 1, sizeof(float));
#		ptcache_file_write(pf, &dx, 1, sizeof(float));
#		ptcache_file_write(pf, &sds->p0, 3, sizeof(float));
#		ptcache_file_write(pf, &sds->p1, 3, sizeof(float));
#		ptcache_file_write(pf, &sds->dp0, 3, sizeof(float));
#		ptcache_file_write(pf, &sds->shift, 3, sizeof(int));
#		ptcache_file_write(pf, &sds->obj_shift_f, 3, sizeof(float));
#		ptcache_file_write(pf, &sds->obmat, 16, sizeof(float));
#		ptcache_file_write(pf, &sds->base_res, 3, sizeof(int));
#		ptcache_file_write(pf, &sds->res_min, 3, sizeof(int));
#		ptcache_file_write(pf, &sds->res_max, 3, sizeof(int));
#		ptcache_file_write(pf, &sds->active_color, 3, sizeof(float));
# Optional turbulance - hi-res [...size based on number of 'divisions'+1 cubed - so 1 division is 2x2x2 times bigger, 2 divisions is 3x3x3 times bigger, etc.]
#   Optional:
#       block - density (hi-res)
#   Optional :
#       block - flame (hi-res) [TODO: seems to only be populated with 'small' array - need to analyse content - not 'flame']
#       block - fuel (hi-res)  [TODO: seems to only be populated with 'small' array - need to analyse content - not 'fuel']
#       block - react (hi-res) [TODO: seems to only be populated with 'small' array - need to analyse content - not 'react']
#   Optional :
#       block - red (hi-res)
#       block - green (hi-res)
#       block - blue (hi-res)
#   block - tcu (x * y * z * float)
#   block - tcv (x * y * z * float)
#   block - tcw (x * y * z * float)
#
#
# For each 'block', the first byte indicates compression (0=none, 1=low, 2=high). If 'compressed' then next 4 bytes indicate size of compressed data, then bytes of the block.
# Note : Uncompressed blocks do not include the 'size'; straight into the data.... so no indication of block length!
    
'shadow', 'density', 'heat', 'heatold', 'flame', 'fuel', 'react', 'rgb_r', 'rgb_g', 'rgb_b', 'vx', 'vy', 'vz', 'obstacles', 'tcu', 'tcv', 'tcw'
# 1         byte (compressed - 0=none, 1=light, 2=heavy)
# 4         int (size)
# (size)    bytes (data)

#0000000  42  50  48  59  53  49  43  53  03  00  00  00  20  37  00  00
#          B   P   H   Y   S   I   C   S etx nul nul nul  sp   7 nul nul
#0000020  02  00  00  00  31  2e  30  34  01  00  00  00  09  00  00  00
#        stx nul nul nul   1   .   0   4 soh nul nul nul  ht nul nul nul
#0000040  15  00  00  00  15  00  00  00  20  00  00  00  00  00  00  3d
#        nak nul nul nul nak nul nul nul  sp nul nul nul nul nul nul   =
#0000060  01  9e  4d  00  00  00  3a  ed  84  94  3e  df  81  94  3e  32
#        soh  rs   M nul nul nul   :   m eot dc4   >   _ soh dc4   >   2
#
#Note the VERSION string '1.04', followed by 4-byte integers for fluid_fields (1), active_fields (9), res (21,21,32), dx (0x0000003d(float?)), compressed (1(byte)), size (0x0009e4d)
#
#After that 4d9e (19870) bytes of compressed data. Hopefully can decompress that with the above class taken from the scripts directory.
#

import bpy
import imp
import os
import sys
import struct
import math

#imp.load_source("lzo_spec", os.path.join(sys.path[0],"io_scene_fpx"))

################# Copied in from addons_contrib/io_scene_fpx/lzo_spec.py ############################
# From https://blender.stackexchange.com/a/61276/29586

import struct

#### !!!! Copied from lzo_spec.py within the Blender directory structure !!!
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2013 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####

## this is a basic, partial and stripped implementation to read
## [LZO:1X]: Lempel-Ziv-Oberhumer lossless data compression algorithm
## http://www.oberhumer.com/opensource/lzo/
## this python implementation based on the java implementation from:
## http://www.oberhumer.com/opensource/lzo/download/LZO-v1/java-lzo-1.00.tar.gz


class Lzo_Codec:

    LZO_E_OK                  =  0
    LZO_E_ERROR               = -1
    LZO_E_INPUT_OVERRUN       = -4
    LZO_E_LOOKBEHIND_OVERRUN  = -6
    LZO_E_INPUT_NOT_CONSUMED  = -8

    @staticmethod
    def Lzo1x_Decompress(src, src_offset, src_length, dst, dst_offset):
        """
        src = bytes
        dst = bytearray

        returns: error, result_index
        """
        src_index = src_offset
        dst_index = dst_offset
        value = 0
        pos = 0
        error = Lzo_Codec.LZO_E_OK
        result_index = dst_index

        value = src[src_index]
        src_index += 1
        if value > 17:
            value -= 17
            while True: ## do while value > 0
                dst[dst_index] = src[src_index]
                value -= 1
                if value <= 0:
                    break ## do while value > 0
            dst_index += 1
            src_index += 1
            value = src[src_index]
            src_index += 1
            if value < 16:
                error = Lzo_Codec.LZO_E_ERROR
                return error, result_index

        ## loop:
        loop = False
        src_index -= 1 ## 1 for (;;value = src[src_index++])
        while not loop: ## 1 for (;;value = src[src_index++])
            value = src[src_index] ## 1 for (;;value = src[src_index++])
            src_index += 1 ## 1 for (;;value = src[src_index++])
            if value < 16:
                if value == 0:
                    while src[src_index] == 0:
                        value += 255
                        src_index += 1
                    value += 15 + src[src_index]
                    src_index += 1
                value += 3
                while True: ## do while value > 0
                    dst[dst_index] = src[src_index]
                    dst_index += 1
                    src_index += 1
                    value -= 1
                    if value <= 0:
                        break ## do while value > 0
                value = src[src_index]
                src_index += 1
                if value < 16:
                    pos = dst_index - 0x801 - (value >> 2) - (src[src_index] << 2)
                    src_index += 1
                    if pos < dst_offset:
                        error = Lzo_Codec.LZO_E_LOOKBEHIND_OVERRUN
                        loop = True
                        break ## loop
                    value = 3
                    while True: ## do while value > 0
                        dst[dst_index] = dst[pos]
                        dst_index += 1
                        pos += 1
                        value -= 1
                        if value <= 0:
                            break ## do while value > 0
                    value = src[src_index-2] & 3
                    if value == 0:
                        continue ## 1 for (;;value = src[src_index++])
                    while True: ## do while value > 0
                        dst[dst_index] = src[src_index]
                        dst_index += 1
                        src_index += 1
                        value -= 1
                        if value <= 0:
                            break ## do while value > 0
                    value = src[src_index]
                    src_index += 1

            src_index -= 1 ## 2 for (;;value = src[src_index++])
            while not loop: ## 2 for (;;value = src[src_index++])
                value = src[src_index] ## 2 for (;;value = src[src_index++])
                src_index += 1 ## 2 for (;;value = src[src_index++])
                if value >= 64:
                    pos = dst_index - 1 - ((value >> 2) & 7) - (src[src_index] << 3)
                    src_index += 1
                    value = (value >> 5) - 1
                elif value >= 32:
                    value &= 31
                    if value == 0:
                        while src[src_index] == 0:
                            value += 255
                            src_index += 1
                        value += 31 + src[src_index]
                        src_index += 1
                    pos = dst_index - 1 - (src[src_index] >> 2)
                    src_index += 1
                    pos -= (src[src_index] << 6)
                    src_index += 1
                elif value >= 16:
                    pos = dst_index - ((value & 8) << 11)
                    value &= 7
                    if value == 0:
                        while src[src_index] == 0:
                            value += 255
                            src_index += 1
                        value += 7 + src[src_index]
                        src_index += 1
                    pos -= (src[src_index] >> 2)
                    src_index += 1
                    pos -= (src[src_index] << 6)
                    src_index += 1
                    if pos == dst_index:
                        loop = True
                        break ## loop
                    pos -= 0x4000
                else:
                    pos = dst_index - 1 - (value >> 2) - (src[src_index] << 2)
                    src_index += 1
                    value = 0
                if pos < dst_offset:
                    error = Lzo_Codec.LZO_E_LOOKBEHIND_OVERRUN
                    loop = True
                    break ## loop
                value += 2
                while True: ## do while value > 0
                    dst[dst_index] = dst[pos]
                    dst_index += 1
                    pos += 1
                    value -= 1
                    if value <= 0:
                        break ## do while value > 0
                value = src[src_index - 2] & 3
                if value == 0:
                    break
                while True: ## do while value > 0
                    dst[dst_index] = src[src_index]
                    dst_index += 1
                    src_index += 1
                    value -= 1
                    if value <= 0:
                        break ## do while value > 0

        src_index -= src_offset
        dst_index -= dst_offset
        result_index = dst_index
        if error < Lzo_Codec.LZO_E_OK:
            return error, result_index
        if src_index < src_length:
            error = Lzo_Codec.LZO_E_INPUT_NOT_CONSUMED
            return error, result_index
        if src_index > src_length:
            error = Lzo_Codec.LZO_E_INPUT_OVERRUN
            return error, result_index
        if value != 1:
            error = Lzo_Codec.LZO_E_ERROR
            return error, result_index
        return error, result_index

###############################################################################

######## My code start #########

def convert_pointcache_volume_to_exr(fname, oPattern, oframeno, multiRow=False, hiresMultiplier=1):
    
    f = open(fname, "rb")

    magic = f.read(8)
    if magic != b'BPHYSICS':
        raise Exception("not a blender physics cache")

    flavor = f.read(12)
    (flavor,count,something) = struct.unpack("iii", flavor)

    print( "%d\t%d\t%d"%(flavor,count,something))

    if flavor!=3: # Smoke

        print("Only type '3' is currently processed - found "+str(flavor))
    else:
        print("Flavor = %i" % flavor)

        smokeversion = f.read(4)
        print("Smoke version = "+str(smokeversion))
        
        fields = f.read(24)
        (fluid_fields,active_fields, res_x, res_y, res_z, dx) = struct.unpack("iiiiif", fields)
        print("Got fields %i\t%i\t%i\t%i\t%i\t%f" % (fluid_fields,active_fields, res_x, res_y, res_z, dx))

        SM_ACTIVE_HEAT		= 1
        SM_ACTIVE_FIRE		= 2
        SM_ACTIVE_COLORS	= 4
        SM_ACTIVE_COLOR_SET	= 8

        #TODO : ....'amplify' setting determines how many divisions the hires volume has. 1 -> 2x2x2, 2 -> 3x3x3, etc. - so multiply by amplify+1 in each dimension. Need to change the 'size' and also the 'dimension' by this factor.
        hiresmult = hiresMultiplier       # 'amplify'+1

        size = res_x * res_y * res_z * 4
        hiressize = size * hiresmult*hiresmult*hiresmult

        shadow = read_block(f, size)
        density = read_block(f, size)    

        heat = None
        heatold = None
        if (active_fields & SM_ACTIVE_HEAT) > 0:
            heat = read_block(f, size)
            heatold = read_block(f, size)
            
        flame = None
        fuel = None
        react = None
        if (active_fields & SM_ACTIVE_FIRE) > 0:
            flame = read_block(f, size)
            fuel = read_block(f, size)
            react = read_block(f, size)

        rgb_r = None
        rgb_g = None
        rgb_b = None
        if (active_fields & SM_ACTIVE_COLORS) > 0:
            rgb_r = read_block(f, size)
            rgb_g = read_block(f, size)
            rgb_b = read_block(f, size)
            
        vx = read_block(f, size)
        vy = read_block(f, size)
        vz = read_block(f, size)

        obstacles = read_block(f, size)

        extrafields = f.read(45*4)
        rec = struct.unpack("fffffffffffiiifffffffffffffffffffiiiiiiiiifff",extrafields)
        print("Extra Fields = "+str(rec))
        
        hires_density = read_block(f, hiressize)
        hires_flame = read_block(f, hiressize)      #TODO: Need to figure out why these aren't coming back as 'hires' data blocks - I think it's getting confused with other blocks... if enable multi-color (more than one colored emitter) then these seem to be the hires colors!! Otherwise it's "something else" but in *lowres*
        hires_fuel = read_block(f, hiressize)
        hires_react = read_block(f, hiressize)

        hires_rgb_r = None
        hires_rgb_g = None
        hires_rgb_b = None
        if (active_fields & SM_ACTIVE_COLORS) > 0:
            hires_rgb_r = read_block(f, hiressize)
            hires_rgb_g = read_block(f, hiressize)
            hires_rgb_b = read_block(f, hiressize)

        tcu = read_block(f, size)
        tcv = read_block(f, size)
        tcw = read_block(f, size)

        #TODO: Get HIRES working correctly
        #print("WARNING: HIRES not working for flame, fuel, react")
        #hires_rgb_b = None
        #hires_flame = None

        if rgb_b != None:
            build_exr_from_buffers(gen_filename("smoke",oPattern, oframeno), (res_x, res_y, res_z), rgb_r, rgb_g, rgb_b, None, multiRow=multiRow)
        else:
            build_exr_from_buffers(gen_filename("smoke",oPattern, oframeno), (res_x, res_y, res_z), density, density, density, None, multiRow=multiRow)

        if hires_rgb_b != None:
            build_exr_from_buffers(gen_filename("hires_smoke",oPattern, oframeno), (res_x*hiresmult, res_y*hiresmult, res_z*hiresmult), hires_rgb_r, hires_rgb_g, hires_rgb_b, None, multiRow=multiRow)          #TODO: This also seems to be 'wrong' if multi-colored!!!!
        else:
            if hires_density != None:
                build_exr_from_buffers(gen_filename("hires_smoke",oPattern, oframeno), (res_x*hiresmult, res_y*hiresmult, res_z*hiresmult), hires_density, hires_density, hires_density, None, multiRow=multiRow)

        build_exr_from_buffers(gen_filename("velocity",oPattern, oframeno), (res_x, res_y, res_z), vx, vy, vz, None, multiRow=multiRow)

        if flame != None:
            build_exr_from_buffers(gen_filename("flame_heat_fuel",oPattern, oframeno), (res_x, res_y, res_z), flame, heat, fuel, None, multiRow=multiRow)
                
        #if hires_flame != None:
        #    #build_exr_from_buffers(gen_filename("hires_flame_react_fuel",oPattern, oframeno), (res_x*hiresmult, res_y*hiresmult, res_z*hiresmult), hires_flame, hires_react, hires_fuel, None, multiRow=multiRow)
        #    #build_exr_from_buffers(gen_filename("hires_flame_react_fuel",oPattern, oframeno), (res_x, res_y, res_z), hires_flame, hires_react, hires_fuel, None, multiRow=multiRow)     #TODO: Determine why these buffers aren't hires and what they are... something to do with hires turbulence?!!!
        #    build_exr_from_buffers(gen_filename("hires_unknown",oPattern, oframeno), (res_x*hiresmult, res_y*hiresmult, res_z*hiresmult), hires_flame, hires_react, hires_fuel, None, multiRow=multiRow)     #TODO: Determine why these buffers aren't hires and what they are... something to do with hires turbulence?!!!


    f.close()

# Generate filename by combining name, pattern, frameno
def gen_filename(name, pattern, frameno):
    return pattern % (name, frameno)

#read data from the file and uncompress as necessary. Return block as a bytearray
def read_block(f, size):
            compressed = f.read(1)
            #print("compressed = "+str(compressed))
            
            if compressed == b'':
                print("Reached End Of Stream")
                return None

            if compressed == b'\x02':
                print("'Heavy' compression not supported")
                return None
            
            if compressed > b'\x02':
                print("Unknown block type")
                return None
        
            if compressed == b'\x01':
                compsize_bytes = f.read(4)
                compsize = struct.unpack("i",compsize_bytes)[0]
                buffer = f.read(compsize)
                destbuffer = bytearray(size)
                (error, result_index) = Lzo_Codec.Lzo1x_Decompress(buffer, 0, compsize, destbuffer, 0)
                print("Uncompressed from "+str(compsize)+" to a buffer of "+str(size)+" result_index = "+str(result_index))
                return destbuffer
            
            else:
                buffer = f.read(size)
                return buffer
                

def build_exr_from_buffers(filename, dimensions, bufferR, bufferG, bufferB, bufferA, multiRow=False):

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
    
    for z in range(0,dimensions[2]):
        print("Processing layer "+str(z))
        
        #Calculate the location of this 'tile'
        tileNoX = z % numColumns
        tileNoY = int((z - tileNoX) / numColumns)
        tileOffset = tileNoX*(dimensions[0]+1)+tileNoY*width*(dimensions[1]+1)

        for x in range(0,dimensions[0]):
        
            for y in range(0,dimensions[1]):
            
                p = x+y*dimensions[0]+z*dimensions[0]*dimensions[1]

                # If R, G, or B are 'none' then 0.0 is assumed
                valR = 0
                valG = 0
                valB = 0
                if bufferR != None:
                    valR = struct.unpack('f',bufferR[p*4:p*4+4])[0]
                    
                if bufferG != None:
                    valG = struct.unpack('f',bufferG[p*4:p*4+4])[0]

                if bufferB != None:
                    valB = struct.unpack('f',bufferB[p*4:p*4+4])[0]

                # bufferA can be None to indicate not used (in which case 1.0 is assumed)
                if bufferA != None:
                    valA = struct.unpack('f',bufferA[p*4:p*4+4])[0]
                else:
                    valA = 1.0
                
               # pixels[(y*width)+x+z*(dimensions[0]+1)] = [valR,valG,valB,valA]
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

class Smoke2EXR_Operator(bpy.types.Operator):
    """Convert a smoke domain into an EXR image file"""
    
    bl_idname = "operator.smoke2exr"
    bl_label = "Smoke2EXR - Convert smoke domain into an EXR image"
    bl_space_type = 'VIEW_3D'
    label = 'Smoke2EXR'
    #bl_options = {}

    frameNo = bpy.props.IntProperty(description='Enter the frame to convert', name='Frame')
    smokeCacheName = bpy.props.StringProperty(description="The selection object's smoke cache name", name="Cache Name")
    multiRow = bpy.props.BoolProperty(description='Create multi-row image instead of a single row of tiles', name="Multi-Row")
    

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
        
        if not 'Smoke' in selected_object.modifiers.keys():
            self.report({'ERROR'}, "Object must include a SMOKE modifier named 'Smoke'")
            return {"CANCELLED"}
        
        #TODO: Use the modifier type rather than name and also check that it's set to a *smoke domain*
        
        smokeCache = selected_object.modifiers['Smoke'].domain_settings.point_cache
        
        self.smokeCacheName = smokeCache.name
        print("Smoke cache name = "+str(self.smokeCacheName))
        
        self.smokeCache = smokeCache
        self.domainSettings = smokeCache = selected_object.modifiers['Smoke'].domain_settings
        
        return wm.invoke_props_dialog(self)

    def execute(self, context):
  
        smokeCacheName = str(self.smokeCacheName)
        
        if len(smokeCacheName) == 0:
            self.report({'ERROR'}, "Smoke cache must be baked to a *named* cache.")
            return {"CANCELLED"}
            #TODO: Pickup the "random" generated name if we don't find an explicit name
            
        cachefile = bpy.path.abspath("//blendcache_%s/%s_%06i_00.bphys" % (bpy.path.basename(bpy.context.blend_data.filepath[:-6]),smokeCacheName,self.frameNo))
        
        hiresMultiplier = self.domainSettings.amplify + 1
        
        convert_pointcache_volume_to_exr(cachefile, "%s_%06i", self.frameNo, self.multiRow, hiresMultiplier=hiresMultiplier)
        return {'FINISHED'}
    

#Run it....
#for frame in range(10,11):
#    cachefile = bpy.path.abspath("//blendcache_%s/smoke_%06i_00.bphys" % (bpy.path.basename(bpy.context.blend_data.filepath[:-6]),frame))
#    convert_pointcache_volume_to_exr(cachefile, "output/%s_%06i", frame)

#Possibly build up the filename using the name of the pointcache from :
# bpy.data.objects["Smoke Domain"].modifiers["Smoke"].domain_settings.point_cache.name
#...also, need to ensure the cache is set to a compatible 'mode' so that we can uncompress and interpret it.