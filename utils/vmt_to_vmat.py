# Converts Source 1 .vmt material files to simple Source 2 .vmat files.
#
# Copyright (c) 2016 Rectus
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Usage Instructions:
# Place all vmts and vtfs in their proper folder structure up till "materials"
# (we'd recomend you just drop it in the content folder for ease of use)
# Using VTFCmd or VTFEdit, use Tools->Convert Folder and convert your entire .vtf folder to .tgas
# cmd: python vmt_to_vmat.py PATH
# i.e.: python vmt_to_vmat.py "C:\Program Files (x86)\Steam\steamapps\common\Half-Life Alyx\content\hl2\materials\models\alyx"
# OR
# i.e.: python vmt_to_vmat.py "C:\Program Files (x86)\Steam\steamapps\common\Half-Life Alyx\content\hl2\materials\models\alyx\alyx_faceandhair.vmt"

import sys
import os
import os.path
from os import path
import re
from shutil import copyfile

from PIL import Image
import PIL.ImageOps

#import numpy as np
#from blend_modes import blending_functions

#for the future
#from VTFLibWrapper.VTFLibEnums import ImageFlag
#from VTFLibWrapper import VTFLib
#from VTFLibWrapper import VTFLibEnums
#vtf_lib = VTFLib.VTFLib()

# File format of the textures.
TEXTURE_FILEEXT = '.tga'
# Extension added to the end of the target folder for these new materials. Valve uses _imported, so we're using it here too
TARGET_FOLDER_EXTENSION = "_imported"
# For some reason, VR Complex doesn't have proper pbr support (as in no support for reflectivity maps or glossiness)
# Because of this, we are just hacking so when compiling for VR_Complex, we set this to true
PBR_HACK = False
# A lot of looks for Source games seem to hinge on Reflectance Range being correct, so for now, we're making
# a seperate variable for it to make it easier to modify on a per-game basis. HL2 seems to be 0.5
reflRange = 0.5
# If the user wishes, they can also generate .vmats for tools files (so debug, tools, dev, etc.) but usually this
# causes compatibility issues since S2 already has it's own versions.
skipDebugFiles = True

debugPauseOnError = False   #

modPath = ""

# material types need to be lowercase because python is a bit case sensitive
# TODO: later, we will convert these to be in a dictionary with something like
# "shaderName": ("HLATargetShader", "SVRHTargetShader", "DOTATargetShader"),
# We will also have a flag for HLA, SVRH (steamtours), and DOTA)
# For now though, just pretend everything uses TextureColor and fuck everything else
vmtSupportedShaders = [
"vertexlitgeneric",         # + Convert to VR Complex
"unlitgeneric",             # TODO: Convert to VR Complex, selfIllum with white mask
"unlittwotexture",          # TODO: Vr Simple 2layer Parallax?
"patch",                    # TODO: ughhhhhhhhhhhhhhhhhhhhhhhhh
"teeth",                    # + Convert to VR Complex
"eyes",                     # + Convert to VR Complex
"eyeball",                  # + Convert to VR Complex
"eyerefract",               # + Convert to VR Complex
"modulate",                 # TODO: Refract/Glass Shader?
"water",                    # TODO: Ditto
"refract",                  # TODO: Ditto
"worldvertextransition",    # TODO: Vr Simple 2way Blend
"lightmappedgeneric",       # + Convert to VR Complex
"lightmapped_4wayblend",    # TODO: 4 Way Blend. No good shader for this, maybe just Vr Simple 2way Blend?
"multiblend",               # TODO: Ditto
"hero",                     # TODO: DOTA Shader: to be worked on for compatibility
"lightmappedtwotexture",    # TODO: Vr Simple 2layer Parallax?
"lightmappedreflective",    # + Convert to VR Complex
"decalmodulate",            # TODO: See if this needs extra work
"cables"                    # TODO: Find appropriate shader or maybe just vr_complex?
]
ignoreList = [
"vertexlitgeneric_hdr_dx9",
"vertexlitgeneric_dx9",
"vertexlitgeneric_dx8",
"vertexlitgeneric_dx7",
"lightmappedgeneric_hdr_dx9",
"lightmappedgeneric_dx9",
"lightmappedgeneric_dx8",
"lightmappedgeneric_dx7",
]

###
### Classes
###
class RGBAImage:
    r = None
    g = None
    b = None
    a = None

    def __init__(self, size, col):
        self.r,self.g,self.b,self.a = Image.new("RGBA", size, col).split()

    def resizeAll(self, newSize):
        self.r = self.r.resize(newSize)
        self.g = self.g.resize(newSize)
        self.b = self.b.resize(newSize)
        self.a = self.a.resize(newSize)

    def setRG(self, image, flip = False):
        self.r.resize(image.size)
        self.g.resize(image.size)
        if (flip):
            self.r = PIL.ImageOps.invert(image)
            self.g = PIL.ImageOps.invert(image)
        else:
            self.r = image
            self.g = image

    def setRGB(self, image, flip = False):
        self.r.resize(image.size)
        self.g.resize(image.size)
        self.b.resize(image.size)

        if(flip):
            self.r = PIL.ImageOps.invert(image)
            self.g = PIL.ImageOps.invert(image)
            self.b = PIL.ImageOps.invert(image)
        else:
            self.r = image
            self.g = image
            self.b = image

    def setRGBA(self, image, flip = False):
        self.r.resize(image.size)
        self.g.resize(image.size)
        self.b.resize(image.size)
        self.a.resize(image.size)

        if(flip):
            self.r = PIL.ImageOps.invert(image)
            self.g = PIL.ImageOps.invert(image)
            self.b = PIL.ImageOps.invert(image)
            self.a = PIL.ImageOps.invert(image)
        else:
            self.r = image
            self.g = image
            self.b = image
            self.a = image

    def saveFile(self, filePath):
        imageOut = Image.merge('RGBA', (self.r, self.g, self.b, self.a))
        imageOut.save(filePath)
        imageOut.close()

###
### Small Functions
###

def parseDir(dirName):
    files = []
    for root, dirs, fileNames in os.walk(dirName):
        if not os.path.exists(addFolderExtension(root)):
            print(" + Target Directory not found for folder " + os.path.basename(root) + ". Creating!")
            os.makedirs(addFolderExtension(root))
        for fileName in fileNames:
            if fileName.lower().endswith('.vmt'):
                files.append(os.path.join(root,fileName))
    return files

def parseLine(inputString):
    #TODO: REGEX????
    inputString = inputString.lower().replace('"', '').replace("'", "").replace("\n", "").replace("\t", "").replace("{", "").replace("}", "").replace(" ", "")
    return inputString

def fixTexturePath(p, addonString = ""):
    retPath = p.strip().strip('"')
    retPath = retPath.replace('\\', '/') # Convert paths to use forward slashes.
    retPath = retPath.replace('.vtf', '') # remove any old extensions
    retPath = '"materials/' + retPath + addonString + TEXTURE_FILEEXT + '"'
    return retPath

def fixVector(s, divVar = 1):
    s = s.strip('"][}{ ').strip("'").replace("  ", " ").replace("   ", " ") # some VMT vectors use {}
    parts = [str(float(i) / divVar) for i in s.split(' ')]
    extra = (' 0.0' * max(3 - s.count(' '), 0) )
    return '"[' + ' '.join(parts) + extra + ']"'

def vectorToArray(s, divVar = 1):
    s = s.strip('"][}{ ') # some VMT vectors use {}
    parts = [float(i) / divVar for i in s.split(' ')]
    #extra = (' 0.0' * max(3 - s.count(' '), 0) )
    return parts

def text_parser(filepath, separator="="):
    return_dict = {}
    with open(filepath, "r") as f:
        for line in f:
            if not line.startswith("//"):
                line = line.replace('\t', '').replace('\n', '')
                line = line.split(separator)
                return_dict[line[0]] = line[1]
    return return_dict

def parseVMTPath(inputPath):
    inputPath = inputPath.lower().replace(".vtf", "")
    return inputPath

def addFolderExtension(filePath):
    outPath = filePath.split('\\materials')[0] + TARGET_FOLDER_EXTENSION + "\\materials" + filePath.split('materials')[1]
    return outPath

###
### Big Functions
###
def parseVMTParameter(line, parameters):
    words = []

    if line.startswith('\t') or line.startswith(' '):
        words = re.split(r'\s+', line, 2)
    else:
        words = re.split(r'\s+', line, 1)

    words = list(filter(len, words))
    if len(words) < 2:
        return

    key = words[0].strip('"').lower() # we process all values and keys as lowercase

    if key.startswith('/'):
        return

    if not key.startswith('$'):
        if not key.startswith('include'):
            return

    val = words[1].strip('\n').lower() # we process all values and keys as lowercase

    commentTuple = val.partition('//')

    if (val.strip('"' + "'") == ""):
        print("+ WARNING: No value found in parameter " + key + ", skipping!")
        return
    # So I chose this to be simple in code later, so I don't have to check if a value exists in vmtParameters AND check it's value
    # But, this should be fine cuz .vmt seems to treat any 0 values as the default parameter. If there's a value out there though
    # that relies on 0, we can add it here as an exception.
    if (val.strip('"' + "'") == "0"):
        print("+ WARNING: Value of " + key + " found to be 0, skipping!")
        return

    if not commentTuple[0] in parameters:
        #TODO: Tidy this up with regex
        parameters[key] = commentTuple[0].replace("'", "").replace('"', '').replace("\n", "").replace("\t", "")
        # reports back as dict with the format $basetexture models/alyx/alyx_faceandhair

###
### Main Execution
###

print('--------------------------------------------------------------------------------------------------------\n'
      'Source 2 Material Conveter! By Rectus via Github.\nInitially forked by Alpyne, this version by caseytube.\n'
      '--------------------------------------------------------------------------------------------------------\n')
print(" + As a reminder, please extract all of your .vtfs to .tga using VTFEdit's 'Convert Folder' before running! + \n")
# Start by asking some basic questions
yes = {'yes','y', 'ye'}
no = {'no','n', ''}
validS2Shaders = {'vr_complex','vr_standard'}
convertVTFs = False

targetFolder = input("What folder would you like to convert? Valid Format: C:\\Steam\\steamapps\\Half-Life Alyx\\content\\tf\\materials: ").lower()
if not os.path.exists(targetFolder):
    print("Please respond with a valid folder or file path! Quitting Process!")
    quit()

overwriteInput = input("Would you like to overwrite any existing .vmat files? (y/n): ").lower()
if overwriteInput in yes:
    OVERWRITE_VMAT = True
elif overwriteInput in no:
    OVERWRITE_VMAT = False
elif overwriteInput == "": # debug: casey's favorite default value
    OVERWRITE_VMAT = True
else:
    print("Please respond with 'yes' or 'no.' Quitting process!")
    quit()

overwriteTGAInput = input("Would you like to overwrite any existing .tga files? (y/n): ").lower()
if overwriteTGAInput in yes:
    OVERWRITE_TGA = True
elif overwriteTGAInput in no:
    OVERWRITE_TGA = False
elif overwriteTGAInput == "": # debug: casey's favorite default value
    OVERWRITE_TGA = False
else:
    print("Please respond with 'yes' or 'no.' Quitting process!")
    quit()

'''convertInput = input("Would you like to convert .vtf files to .tga? (y/n): ").lower()
if convertInput in yes:
    convertVTFs = True
elif convertInput in no:
    convertVTFs = False
elif convertInput == "": # debug: casey's favorite default value
    convertVTFs = False
else:
    print("Please respond with 'yes' or 'no.' Quitting process!")
    quit()'''

SHADER = input("What is your target shader? Valid Options: vr_complex (vr_standard support coming soon) - ").lower()
if SHADER == "":
    SHADER = "vr_complex"
elif SHADER not in validS2Shaders:
    print("Please respond with a valid shader! Quitting process!")
    quit()

# Verify file paths
fileList = []
vtfList = []

# HACK; See note under PBR_HACK
if SHADER.lower() == "vr_complex":
    PBR_HACK = True

# TODO: make this work so that when parsing directories, skip tools/debug stuff
foldersToSkip = [
    "materials\\tools",
    "materials\\debug"
]

if(targetFolder):
    absFilePath = os.path.abspath(targetFolder)
    if os.path.isdir(absFilePath):
        fileList.extend(parseDir(absFilePath))
    elif(absFilePath.lower().endswith('.vmt')):
        fileList.append(absFilePath)
    elif(absFilePath.lower().endswith('.vtf')):
        vtfList.append(absFilePath)
    else:
        print('ERROR: File path is invalid. required format: "vmt_to_vmat.py C:\\path\\to\\folder_or_vmt"')
        quit()
else:
    print('ERROR: CMD Arguments are invalid. Required format: "vmt_to_vmat.py C:\\path\\to\\folder_or_vmt"')
    quit()

if (len(fileList) == 0):
    print('INFO: Did not find any .vmt or .vtf files in target folder. Make sure you .tga, .vmt, and .vtf files are together.')
    quit()
    
for vmtFileName in fileList:
    print("+ Processing .vmt file: " + vmtFileName)
    baseFileName  = os.path.basename(vmtFileName.replace('.vmt', ''))
    if modPath == "":
        modPath = vmtFileName.split('materials')[0]
    vmtParameters = {}
    vmtShader = ""

    vmatFileName = addFolderExtension(vmtFileName).replace('.vmt', '.vmat')
    if os.path.exists(vmatFileName) and not OVERWRITE_VMAT:
        print('+ WARNING: File already exists. Skipping!')
        continue

    basePath = 'materials' + vmtFileName.split('materials', 1)[1].replace('.vmt', '')

    with open(vmtFileName, 'r') as vmtFile:
        for line in vmtFile.readlines():
            if parseLine(line) in vmtSupportedShaders:
                vmtShader = parseLine(line)
            else:
                parseVMTParameter(line, vmtParameters)

        if vmtShader == "": # vmt shader not supported
            print("- ERROR: Unsupported shader in " + baseFileName + ". Skipping!")
            if debugPauseOnError:
                input("Press the <ENTER> key to continue...")
            continue #skip!

    print('+ Parsing ' + os.path.basename(vmtFileName))
    
    # default image, to later check if we actually found something 
    nullImage = Image.new("RGB", (4, 4))
    nullImage.info['is_null'] = True
    
    baseMap = nullImage
    bumpMap = nullImage
    phongMap = nullImage
    phongExpMap = nullImage
    envMap = nullImage
    illumMap = nullImage
    transMap = nullImage
    aoMap = nullImage
    maskMap = nullImage
    detailMap = nullImage

    # Prep TextureColor
    if "$basetexture" in vmtParameters:
        tgaPath = modPath + "materials\\" + parseVMTPath(vmtParameters["$basetexture"]) + ".tga"
        try:
            baseTexture = Image.open(tgaPath)
            baseMap = baseTexture

            if "$basemapalphaphongmask" in vmtParameters:
                phongMap = baseTexture.getchannel('A')
            if "$basemapalphaenvmapmask" in vmtParameters:
                envMap = baseTexture.getchannel('A')
            if "$selfillum" in vmtParameters and "$selfillummask" not in vmtParameters:
                illumMap = baseTexture.getchannel('A')
            if "$translucent" in vmtParameters or "$alphatest" in vmtParameters:
                transMap = baseTexture.getchannel('A')
            if "$basealphaenvmapmask" in vmtParameters:
                envMap = baseTexture.getchannel('A')
            if "$blendtintbybasealpha" in vmtParameters:
                maskMap = baseTexture.getchannel('A')
        except:
            print("- ERROR: $basetexture file " + parseVMTPath(vmtParameters["$basetexture"]) + " in TGA does not exist. Skipping!")

    # Prep TextureNormal for normal/bump maps
    if "$bumpmap" in vmtParameters or "$normalmap" in vmtParameters:
        if "$bumpmap" in vmtParameters:
            tgaPath = modPath + "materials\\" + parseVMTPath(vmtParameters["$bumpmap"]) + ".tga"
        elif "$normalmap" in vmtParameters:
            tgaPath = modPath + "materials\\" + parseVMTPath(vmtParameters["$normalmap"]) + ".tga"

        try:
            bumpTexture = Image.open(tgaPath)
            bumpMap = bumpTexture
            if "$basemapalphaphongmask" in vmtParameters:
                phongMap = bumpTexture.getchannel("A")

            if "$normalmapalphaenvmapmask" in vmtParameters:
                envMap = bumpTexture.getchannel("A")
        except:
            print("- ERROR: $bumpmap/$normalmap file " + tgaPath.split(modPath + "materials\\")[1] + " in TGA does not exist. Skipping!")

    if "$envmap" in vmtParameters and "$envmapmask" in vmtParameters:
        tgaPath = modPath + "materials\\" + parseVMTPath(vmtParameters["$envmapmask"]) + ".tga"
        try:
            envTexture = Image.open(tgaPath)
            envMap = envTexture.convert("RGB")
        except:
            print("- ERROR: $envmapmask file " + parseVMTPath(vmtParameters["$envmapmask"]) + " in TGA does not exist. Skipping!")

    # Prep Glossiness Map using Phong Exponent
    if "$phongexponenttexture" in vmtParameters:
        tgaPath = modPath + "materials\\" + parseVMTPath(vmtParameters["$phongexponenttexture"]) + ".tga"
        try:
            phongTexture = Image.open(tgaPath)
            phongExpMap = phongTexture
        except:
            print("- ERROR: $phongexponenttexture file " + parseVMTPath(vmtParameters["$phongexponenttexture"]) + " in TGA does not exist. Skipping!")

    # Prep TextureSelfIllum using selfillum stuff
    if "$selfillum" in vmtParameters and "$selfillummask" in vmtParameters:
        tgaPath = modPath + "materials\\" + parseVMTPath(vmtParameters["$selfillummask"]) + ".tga"
        try:
            illumTexture = Image.open(tgaPath)
            illumMap = illumTexture
        except:
            print("- ERROR: $selfillummask file " + parseVMTPath(vmtParameters["$selfillummask"]) + " in TGA does not exist. Skipping!")

    # Rarely used, but ambient occlusion maps are sometimes available
    if "$ambientoccltexture" in vmtParameters or "$ambientocclusiontexture" in vmtParameters:
        if "$ambientoccltexture" in vmtParameters:
            tgaPath = modPath + "materials\\" + vmtParameters["$ambientoccltexture"] + ".tga"
        elif "$ambientocclusiontexture" in vmtParameters:
            tgaPath = modPath + "materials\\" + vmtParameters["$ambientocclusiontexture"] + ".tga"
        try:
            aoTexture = Image.open(tgaPath)
            aoMap = aoTexture
        except:
            print("- ERROR: $ambientoccltexture/$ambientocclusiontexture file " + tgaPath.split(modPath + "materials\\")[1] + " in TGA does not exist. Skipping!")

    if SHADER == "vr_complex":
        print('+ Creating ' + os.path.basename(vmatFileName))
        with open(vmatFileName, 'w') as vmatFile:
            # VMT Maps are now parsed. Moving onto creating the vmat!
            vmatFile.write('// Converted with vmt_to_vmat.py\n\n')
            vmatFile.write('Layer0\n{\n\tshader "' + SHADER + '.vfx"\n\n')

            # move onto writing materials if they exist
            # Prep TextureColor
            if 'is_null' not in baseMap.info:
                if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_color.tga')):
                    #baseMap.save(vmatFileName.replace('.vmat', '_color.tga'))
                    baseMap.save(vmatFileName.replace('.vmat', '_color.tga'))
                    print(os.path.basename(vmatFileName.replace('.vmat', '_color.tga')) + " saved!")
                vmatFile.write('\tTextureColor "' + basePath + '_color.tga' + '"\n')

            # Prep TextureNormal for normal/bump maps
            if 'is_null' not in bumpMap.info:
                if "$ssbump" in vmtParameters and "1" in vmtParameters["$ssbump"]:
                    print("- WARNING: " + os.path.basename(vmtFileName) + " uses $ssbump, which is not supported in Source 2. Skipping normal maps.")
                    vmatFile.write('\t// $ssbump in original .vmt used, which are unsupported in Source 2. Normal maps skipped to retain visual quality.\n')
                else:
                    if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_normal.tga')):
                        bumpMap.save(vmatFileName.replace('.vmat', '_normal.tga'))
                        print(os.path.basename(vmatFileName.replace('.vmat', '_normal.tga')) + " saved!")
                    # For normal maps, we produce a file called fileName.txt that tells Source 2 to flip the green channel
                    bumpSettingsFileName = vmatFileName.replace(".vmat", "_normal.txt")
                    with open(bumpSettingsFileName, 'w') as bumpSettings:
                        bumpSettings.write('"settings"\n'
                                           '{\n'
                                           '\t"legacy_source1_inverted_normal"\t"1"\n'
                                           '}')
                    vmatFile.write('\tTextureNormal "' + basePath + '_normal.tga' + '"\n')
            
            # Rarely used, but ambient occlusion maps are sometimes available
            # However, since we use a hack in vr_complex for phong masks, we prioritize that over custom AO textures
            if 'is_null' not in phongMap.info:
                if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_ao.tga')):
                    phongMap.save(vmatFileName.replace('.vmat', '_ao.tga'))
                    print(os.path.basename(vmatFileName.replace('.vmat', '_ao.tga')) + " saved!")
                if "$phongboost" in vmtParameters:
                    # For phong boost, we scale brightness of the roughness/phong map which seems to be a 1:1 ratio
                    aoSettingsFileName = vmatFileName.replace(".vmat", "_ao.txt")
                    with open(aoSettingsFileName, 'w') as aoSettings:
                        aoSettings.write('"settings"\n'
                                           '{\n'
                                           '\t"brightness"\t"' + vmtParameters["$phongboost"] + '"\n'
                                           '}')
                vmatFile.write('\tg_vReflectanceRange "[0.000 ' + str(reflRange) + ']"\n')
                vmatFile.write('\tTextureAmbientOcclusion "' + basePath + '_ao.tga' + '"\n')
                vmatFile.write('\tg_flAmbientOcclusionDirectSpecular "1.000"\n')
            elif 'is_null' not in envMap.info: # unsure if this is the correct way to handle this, will have to see how HLA truly handles cubemaps in materials
                if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_ao.tga')):
                    envMap.save(vmatFileName.replace('.vmat', '_ao.tga'))
                    print(os.path.basename(vmatFileName.replace('.vmat', '_ao.tga')) + " saved!")
                vmatFile.write('\tTextureAmbientOcclusion "' + basePath + '_ao.tga' + '"\n')
                vmatFile.write('\tg_flAmbientOcclusionDirectSpecular "0.000"\n')
            elif "$ambientoccltexture" in vmtParameters or "$ambientocclusiontexture" in vmtParameters:
                if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_ao.tga')):
                    aoMapConvert = aoMap.convert("L")
                    aoMapConvert.save(vmatFileName.replace('.vmat', '_ao.tga'))
                    print(os.path.basename(vmatFileName.replace('.vmat', '_ao.tga')) + " saved!")
                vmatFile.write('\tTextureAmbientOcclusion "' + basePath + '_ao.tga' + '"\n')
            
            # This value is a guess on comparing strengths of Phong exponent.
            # https://developer.valvesoftware.com/wiki/Phong_materials
            # My current theory is that $phongexponent's equvalent range (of usable numbers is 5-150 in Source 1)
            # is an exponential value (duh) which lands between 60 and 255. I've produced a really quick and dirty
            # expression with some online tools to help decide this, but we should probably find a cleaner solution.
            # y = -10642.28 + (254.2042 - -10642.28)/(1 + (x/2402433000000)^0.1705696)
            phongExpDivider = 150
            if "$phong" in vmtParameters:
                vmatFile.write('\tF_SPECULAR 1\n')
                if 'is_null' not in phongExpMap.info:
                    if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_rough.tga')):
                        phongExpMapFlip = phongExpMap.convert('RGB')
                        phongExpMapFlip = PIL.ImageOps.invert(phongExpMapFlip)
                        phongExpMapFlip.save(vmatFileName.replace('.vmat', '_rough.tga'))
                        print(os.path.basename(vmatFileName.replace('.vmat', '_rough.tga')) + " saved!")
                    vmatFile.write('\tTextureRoughness "' + basePath + '_rough.tga' + '"\n')
                elif "$phongexponent" in vmtParameters:
                    specValue = vmtParameters["$phongexponent"]
                    finalSpec = (-10642.28 + (254.2042 - -10642.28)/(1 + (float(specValue)/2402433000000)**0.1705696))/255
                    vmatFile.write('\tTextureRoughness "[' + str(finalSpec) + ' ' + str(finalSpec) + ' ' + str(finalSpec) + ' 0.000]"\n')
                else: # VDC says the default value for $phongexponent is 5.0, but in my testing, I think it's actually 150, at least in SFM. TODO: Check this
                    finalSpec = 60
                    vmatFile.write('\tTextureRoughness "[' + str(finalSpec) + ' ' + str(finalSpec) + ' ' + str(finalSpec) + ' 0.000]"\n')
            
            # Prep TextureSelfIllum using selfillum stuff
            if "$selfillum" in vmtParameters:
                vmatFile.write('\tF_SELF_ILLUM 1\n')
                vmatFile.write('\tTextureSelfIllumMask "' + basePath + '_selfillum.tga' + '"\n')
                if "$selfillumtint" in vmtParameters:
                    vmatFile.write('\tg_vSelfIllumTint ' + fixVector(vmtParameters["$selfillumtint"]) + '\n')
                if "$selfillummaskscale" in vmtParameters:
                    vmatFile.write('\tg_flSelfIllumScale "' + vmtParameters['$selfillummaskscale'] + '"\n')
                if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_selfillum.tga')):
                    illumMapConvert = illumMap.convert("L")
                    illumMapConvert.save(vmatFileName.replace('.vmat', '_selfillum.tga'))
                    print(os.path.basename(vmatFileName.replace('.vmat', '_selfillum.tga')) + " saved!")

            # Prep TextureTransparancy using either alphatest or translucent
            if "$translucent" in vmtParameters or "$alphatest" in vmtParameters:
                if "$translucent" in vmtParameters:
                    vmatFile.write('\tF_TRANSLUCENT 1\n')
                elif "$alphatest" in vmtParameters:
                    vmatFile.write('\tF_ALPHA_TEST 1\n')
                if "$additive" in vmtParameters:
                    vmatFile.write('\tF_ADDITIVE_BLEND 1\n')
                if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_trans.tga')):
                    transMapConvert = transMap.convert("L")
                    transMapConvert.save(vmatFileName.replace('.vmat', '_trans.tga'))
                    print(os.path.basename(vmatFileName.replace('.vmat', '_trans.tga')) + " saved!")
                vmatFile.write('\tTextureTranslucency "' + basePath + '_trans.tga' + '"\n')

            # Setting up Color Tint
            if "$color" in vmtParameters:
                if "{" in vmtParameters["$color"]:
                    vmatFile.write('\tg_vColorTint ' + fixVector(vmtParameters["$color"], 255) + '\n')  # process as int
                elif "[" in vmtParameters["$color"]:
                    vmatFile.write('\tg_vColorTint ' + fixVector(vmtParameters["$color"]) + '\n')  # process as float
            elif "$color2" in vmtParameters:
                # $blendtintbybasealpha does what it says on the tin, and is used by TF to tint items for team colors
                if "$blendtintbybasealpha" in vmtParameters:
                    if not OVERWRITE_TGA or OVERWRITE_TGA and not os.path.exists(vmatFileName.replace('.vmat', '_colormask.tga')):
                        maskMapConvert = maskMap.convert("L")
                        maskMapConvert.save(vmatFileName.replace('.vmat', '_colormask.tga'))
                        print(os.path.basename(vmatFileName.replace('.vmat', '_colormask.tga')) + " saved!")
                        vmatFile.write('\tF_TINT_MASK 1\n\tTextureTintMask "' + basePath + '_colormask.tga' + '"\n')
                if "{" in vmtParameters["$color2"]:
                    vmatFile.write('\tg_vColorTint ' + fixVector(vmtParameters["$color2"], 255) + '\n')  # process as int
                elif "[" in vmtParameters["$color2"]:
                    vmatFile.write('\tg_vColorTint ' + fixVector(vmtParameters["$color2"]) + '\n')  # process as float

            # Setting up Detail Parameters
            if "$detail" in vmtParameters:
                # Detail textures are unique since they're almost always shared with other materials,
                # So in this case we just copy it once and then continue to process like normal
                tgaPath = modPath + "materials\\" + parseVMTPath(vmtParameters["$detail"]) + ".tga"
                if not os.path.exists(addFolderExtension(tgaPath)):
                    try:
                        copyfile(tgaPath, addFolderExtension(tgaPath))
                        print("+ " + addFolderExtension(tgaPath) + " copied to target directory!")
                    except:
                        print("- ERROR: $detail file " + parseVMTPath(vmtParameters["$detail"]) + " in TGA does not exist. Skipping!")

                vmatFile.write('\tTextureDetail "' + 'materials/' + parseVMTPath(vmtParameters["$detail"]) + '.tga"\n')
                if "$detailblendmode" in vmtParameters:
                    vmatFile.write('\tF_DETAIL_TEXTURE 2\n')  # Overlay
                else:
                    vmatFile.write('\tF_DETAIL_TEXTURE 1\n')  # Mod2X
                if "$detailscale" in vmtParameters:
                    vmatFile.write('\tg_vDetailTexCoordScale "[' + vmtParameters["$detailscale"] + ' ' + vmtParameters["$detailscale"] + ']"\n')
                if "$detailblendfactor" in vmtParameters:
                    vmatFile.write('\tg_flDetailBlendFactor "' + vmtParameters["$detailblendfactor"] + '"\n')

            vmatFile.write('}\n')

    elif SHADER == "vr_standard":
        # die
        print("die in real")
    elif SHADER == "globallitsimple":
        # die 2.0
        print("die in real for real")
    elif SHADER == "customhero":
        # die 3: the finale
        print("death death death death death")

    print('+ Finished Writing ' + vmatFileName)

input("Press the <ENTER> key to close...")
