import os
import shutil

import chardet
import codecs
import json
import argparse


###### Default Values ######
DEFAULT_MOD_NAME = "YetAnotherModLad"

DEFAULT_MOD_FOLDER = "Mods"
DEFAULT_OUTPUT_FOLDER = "output"


###### Command Line Arguments ######
# Create the parser
parser = argparse.ArgumentParser(description="Merge JSON files.")

# Add optional arguments for the source and output directories
# If the user does not provide these arguments, default values are used
parser.add_argument('-s', '--source', type=str, nargs='*', default=[DEFAULT_MOD_FOLDER],
                    help="The list of paths to mod source folder containing the JSON files to merge.")
parser.add_argument('-o', '--output', type=str, default=DEFAULT_OUTPUT_FOLDER,
                    help="The directory where the merged JSON file will be saved.")

# Add additional arguments for the mod name
parser.add_argument('-m', '--mod', type=str, default=DEFAULT_MOD_NAME, help="The name of the mod.")

# Simple output to only create the files and not the mod folder structure
parser.add_argument('-n', '--no-structure', action='store_true', help="Do not create the mod folder structure.")

# Add a flag to launch experimental GUI after the merge is complete [NOT IMPLEMENTED]
# parser.add_argument('-g', '--gui', action='store_true', help="Launch the experimental GUI after the merge is complete.")

# Allow duplicate Quirks [NOT IMPLEMENTED]
# parser.add_argument('-d', '--duplicate-quirks', action='store_true', help="Allow duplicate Quirks.")

# Parse the command line arguments
args = parser.parse_args()


#############  Setup values  #############
# Now we can access the source and output directories like so:
mod_folders = args.source
output_directory = args.output

# If mod name is not provided, use the default
if args.mod is None:
    mod_name = DEFAULT_MOD_NAME
else:
    mod_name = args.mod

# If the no structure flag is set, do not create the mod folder structure
if args.no_structure:
    print("No mod folder structure will be created.")
    output_path = output_directory
else:
    # Create the mod folder structure
    print(f"Creating mod folder structure for {mod_name}...")
    output_path = os.path.join(output_directory, mod_name, "Resources")


print(f"Using mod source folders: {mod_folders}")
print(f"Using output folder: {output_directory}")


####### Define functions #######

# Loads a JSON file and ensures that the encoding is UTF-8 so that it can be loaded by json.loads()
def load_json_file(file_path):
    # Detect the encoding
    rawdata = open(file_path, 'rb').read()
    result = chardet.detect(rawdata)
    original_encoding = result['encoding']

    # Open the file with detected encoding
    with codecs.open(file_path, 'r', encoding=original_encoding) as f:
        print(f"Loading {file_path} with encoding {original_encoding}")
        contents = f.read()

    # Encode the contents as UTF-8 and decode them as UTF-8
    contents = contents.encode('utf-8').decode('utf-8')

    # Now you can load the contents with json.loads (not json.load)
    data = json.loads(contents)
    return data


# flattens a list of lists into a single list
def flatten(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten(i))
        else:
            result.append(i)
    return result


# combines two dictionaries into a single dictionary
def join_dicts(dict1, dict2):
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        combined_dict = {**dict1, **dict2}
        if 'quirks' in dict1 and 'quirks' in dict2:
            combined_dict['quirks'] = dict1['quirks'] + dict2['quirks']
        return combined_dict
    elif isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    else:
        return [dict1, dict2]


# combines two indexes of mechs.json files into a single index.
# When there are duplicate keys, they values are merged into a list
def combine_mechs(mechs1, mechs2):
    combined_mechs = {}

    for key in mechs1.keys():
        if key in mechs2.keys():
            combined_mechs[key] = join_dicts(mechs1[key], mechs2[key])
            if 'quirks' in combined_mechs[key] and isinstance(combined_mechs[key]['quirks'], list):
                combined_mechs[key]['quirks'] = flatten(combined_mechs[key]['quirks'])
        else:
            combined_mechs[key] = mechs1[key]
            if isinstance(mechs1[key], dict) and 'quirks' in mechs1[key] and isinstance(mechs1[key]['quirks'], list):
                combined_mechs[key]['quirks'] = flatten(mechs1[key]['quirks'])

    for key in mechs2.keys():
        if key not in combined_mechs.keys():
            combined_mechs[key] = mechs2[key]
            if isinstance(mechs2[key], dict) and 'quirks' in mechs2[key] and isinstance(mechs2[key]['quirks'], list):
                combined_mechs[key]['quirks'] = flatten(mechs2[key]['quirks'])

    return combined_mechs


# Creates the mod folder structure
def create_mod_structure():
    # Ensure the mod folder exists
    os.makedirs(output_path, exist_ok=True)

    # Get the path to the parent folder of the output path
    parent_path = os.path.dirname(output_path)
    # copy the mod.json file to the mod folder
    shutil.copyfile(os.path.join(os.path.dirname(__file__), "Resources", "mod.json")
                    , os.path.join(parent_path, "mod.json"))


####### Search for JSONs #######

# scan the sub-folders of the mod folder for the mechs.json and quirk.json files
mech_files = []
quirk_files = []

for mod_folder in mod_folders:
    for root, dirs, files in os.walk(mod_folder):
        # Exclude the directory
        if mod_name in dirs or os.path.basename(root) == mod_name:
            dirs.remove(mod_name)

        # Check if 'Resources' is a sub-folder of the current folder
        if 'Resources' in dirs:
            resources_dir = os.path.join(root, 'Resources')

            # get all the files in the Resources sub-folder
            for file in os.listdir(resources_dir):
                if file.endswith("mechs.json"):
                    mech_files.append(os.path.join(root, 'Resources', file))
                elif file.endswith("quirks.json"):
                    quirk_files.append(os.path.join(root, 'Resources', file))

print(f"Found {len(mech_files)} mech files.")
print(f"Found {len(quirk_files)} quirk files.")

# Check if there are at least two mechs.json and quirk.json files each
if len(mech_files) < 2:
    print("Not enough mechs.json files found. There needs to be at least two in order to merge files.")
    exit()
if len(quirk_files) < 2:
    print("Not enough quirks.json files found. There needs to be at least two in order to merge files.")
    exit()

####### Create mod folder structure #######

if not args.no_structure:
    print("Creating mod folder structure...")
    create_mod_structure()


####### Mech read, process and output script #######

print("Loading mechs...")
# read the first mech file into the dictionary
mechs = load_json_file(mech_files[0])

# remove the first mech file from the list
mech_files.pop(0)

# read and merge the remaining mech files into the dictionary
for mech_file in mech_files:
    mech_data = load_json_file(mech_file)
    mechs = combine_mechs(mechs, mech_data)

print(f"Loaded {len(mechs)} mechs.")
print(f"writing mechs.json to {os.path.join(output_path, 'mechs.json')}")

# Check if the output folder exists
if not os.path.exists(DEFAULT_OUTPUT_FOLDER):
    os.mkdir(DEFAULT_OUTPUT_FOLDER)

# write the combined mechs to a new file
os.makedirs(output_path, exist_ok=True)
with open(f"{os.path.join(output_path, 'mechs.json')}", "w") as f:
    json.dump(mechs, f, indent=2)


####### Quirk read, process and output script #######

# read the first quirk file into the dictionary
quirks = load_json_file(quirk_files[0])

# remove the first quirk file from the list
quirk_files.pop(0)

# read and merge the remaining quirk files into the dictionary
for quirk_file in quirk_files:
    quirk_data = load_json_file(quirk_file)
    quirks = join_dicts(quirks, quirk_data)

print(f"Loaded {len(quirks)} quirks.")
print(f"writing quirks.json to {os.path.join(output_path, 'quirks.json')}")

os.makedirs(output_path, exist_ok=True)
with open(f"{os.path.join(output_path, 'quirks.json')}", "w") as f:
    json.dump(quirks, f, indent=2)

print("Done.")
