import os
import chardet
import codecs
import json
import argparse

MOD_NAME = "YetAnotherModLad"

DEFAULT_MOD_FOLDER = "Mods"
DEFAULT_OUTPUT_FOLDER = "output"


# Create the parser
parser = argparse.ArgumentParser(description="Merge JSON files.")

# Add optional arguments for the source and output directories
# If the user does not provide these arguments, default values are used
parser.add_argument('-s', '--source', type=str, nargs='*', default=[DEFAULT_MOD_FOLDER],
                    help="The list of paths to mod source folder containing the JSON files to merge.")
parser.add_argument('-o', '--output', type=str, default=DEFAULT_OUTPUT_FOLDER,
                    help="The directory where the merged JSON file will be saved.")

# Parse the command line arguments
args = parser.parse_args()

# Now you can access the source and output directories like so:
mod_folders = args.source
output_directory = args.output
output_path = os.path.join(output_directory, MOD_NAME, "Resources")

print(f"Using mod folder: {mod_folders}")
print(f"Using output folder: {output_directory}")


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


# scan the sub-folders of the mod folder for the mechs.json and quirk.json files
mech_files = []
quirk_files = []

for mod_folder in mod_folders:
    for root, dirs, files in os.walk(mod_folder):
        # Exclude the directory
        if MOD_NAME in dirs or os.path.basename(root) == MOD_NAME:
            dirs.remove(MOD_NAME)

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

# Check if there are at least two mechs.json files
if len(mech_files) < 2:
    print("Not enough mechs.json files found. There needs to be at least two in order to merge files.")
    exit()


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
    # return {**dict1, **dict2}


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


# read the first mech file into the dictionary
with open(mech_files[0]) as f:
    mechs = json.load(f)

# remove the first mech file from the list
mech_files.pop(0)

# read and merge the remaining mech files into the dictionary
for mech_file in mech_files:
    mech_data = load_json_file(mech_file)
    mechs = combine_mechs(mechs, mech_data)

print(f"Loaded {len(mechs)} mechs.")

# Check if the output folder exists
if not os.path.exists(DEFAULT_OUTPUT_FOLDER):
    os.mkdir(DEFAULT_OUTPUT_FOLDER)

# write the combined mechs to a new file
os.makedirs(output_path, exist_ok=True)
with open(f"{output_path}\\mechs.json", "w") as f:
    json.dump(mechs, f, indent=2)


# read the first quirk file into the dictionary
with open(quirk_files[0]) as f:
    quirks = json.load(f)

# remove the first quirk file from the list
quirk_files.pop(0)

# read and merge the remaining quirk files into the dictionary
for quirk_file in quirk_files:
    quirk_data = load_json_file(quirk_file)
    quirks = join_dicts(quirks, quirk_data)

print(f"Loaded {len(quirks)} quirks.")

os.makedirs(output_path, exist_ok=True)
with open(f"{output_path}\\quirks.json", "w") as f:
    json.dump(quirks, f, indent=2)

print("Done.")
