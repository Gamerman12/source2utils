# cmd command: python wav_to_sound.py "C:\Program Files (x86)\Steam\steamapps\common\SteamVR\tools\steamvr_environments\content\steamtours_addons\l4d2_converted\sounds"
# MUST run in the sounds folder

import re, sys, os

INPUT_FILE_EXT = '.wav'
OUTPUT_FILE_EXT = '.sound'
    
SOUND_BASE = '''<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
{
	data = 
	{
		sounds = 
		[
			"<sound>",
		]
	}
}
'''

def text_parser(filepath, separator="="):
    return_dict = {}
    with open(filepath, "r") as f:
        for line in f:
            if not line.startswith("//") or line in ['\n', '\r\n'] or line.strip() == '':
                line = line.replace('\t', '').replace('\n', '')
                line = line.split(separator)
                return_dict[line[0]] = line[1]
    return return_dict

def walk_dir(dirname):
    files = []

    for root, dirs, filenames in os.walk(dirname):
        for filename in filenames:
            if filename.lower().endswith(INPUT_FILE_EXT):
                files.append(os.path.join(root,filename))
            
    return files

def putl(f, line, indent = 0):
    f.write(('\t' * indent) + line + '\r\n')

def strip_quotes(s):
    return s.strip('"').strip("'")

def fix_path(s):
    return strip_quotes(s).replace('\\', '/').replace('//', '/').strip('/')

def relative_path(s, base):
    base = base.replace(abspath, '')
    base = base.replace(os.path.basename(base), '')

    return fix_path(os.path.basename(abspath) + base + '/' + fix_path(s))


def get_mesh_name(file):
    return os.path.splitext(os.path.basename(fix_path(file)))[0]

print('--------------------------------------------------------------------------------------------------------')
print('Source 2 Sound Generator! By Rectus via Github.')
print('Initially forked by Alpyne, this version by caseytube.')
print('--------------------------------------------------------------------------------------------------------')
print('Reminder to put your sounds in the same directory structure as Source 1, starting with sounds!\n')
abspath = ''
files = []

PATH_TO_CONTENT_ROOT = input("What folder would you like to convert? Valid Format: C:\\Steam\\steamapps\\Half-Life Alyx\\content\\tf\\sounds\\props_spytech\\: ").lower()
if not os.path.exists(PATH_TO_CONTENT_ROOT):
    print("Please respond with a valid folder or file path! Quitting Process!")
    quit()

# recursively search all dirs and files
abspath = os.path.abspath(PATH_TO_CONTENT_ROOT)
print(abspath)
if os.path.isdir(abspath):
    files.extend(walk_dir(abspath))
#else:
#    if abspath.lower().endswith(INPUT_FILE_EXT):
#        files.append(abspath)

for filename in files:
    out_name = filename.replace(INPUT_FILE_EXT, OUTPUT_FILE_EXT)
    #if os.path.exists(out_name): continue

    print('Importing', os.path.basename(filename))

    out = sys.stdout

    sourcePath = "sounds" + filename.split("sounds", 1)[1] # HACK?
    sound_path = fix_path(sourcePath)
    
    with open(out_name, 'w') as out:
        putl(out, SOUND_BASE.replace('<sound>', sound_path.replace(INPUT_FILE_EXT, ".vsnd") ).replace((' ' * 4), '\t'))

input("Press the <ENTER> key to close...")