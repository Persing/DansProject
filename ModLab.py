import os
import sys
import json
import argparse

DEFAULT_MOD_FOLDER = "mods"
DEFAULT_OUTPUT_FOLDER = "output"


# Create the parser
parser = argparse.ArgumentParser(description="Merge JSON files.")

# Add optional arguments for the source and output directories
# If the user does not provide these arguments, default values are used
parser.add_argument('-s', '--source', type=str, default=DEFAULT_MOD_FOLDER,
                    help="The mods' source directory containing the JSON files to merge.")
parser.add_argument('-o', '--output', type=str, default=DEFAULT_OUTPUT_FOLDER,
                    help="The directory where the merged JSON file will be saved.")

# Parse the command line arguments
args = parser.parse_args()

# Now you can access the source and output directories like so:
mod_folder = args.source
output_directory = args.output

# Check if the user specified a file path to the mod folders
if len(sys.argv) > 1:
    mod_folder = sys.argv[1]
else:
    mod_folder = DEFAULT_MOD_FOLDER

print(f"Using mod folder: {mod_folder}")
print(f"Using output folder: {output_directory}")

# scan the subfolders of the mod folder for the mechs.json and quirk.json files
mech_files = []
quirk_files = []

for root, dirs, files in os.walk(mod_folder):
    for file in files:
        if file.endswith("mechs.json"):
            mech_files.append(os.path.join(root, file))
        elif file.endswith("quirks.json"):
            quirk_files.append(os.path.join(root, file))

print(f"Found {len(mech_files)} mech files.")

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
            if isinstance(mechs1[key], dict) and 'quirks' in mechs1[key] and isinstance(mechs1[key]['quirks'], list):
                combined_mechs[key] = flatten(mechs1[key]['quirks'])

    for key in mechs2.keys():
        if key not in combined_mechs.keys():
            if isinstance(mechs2[key], dict) and 'quirks' in mechs2[key] and isinstance(mechs2[key]['quirks'], list):
                combined_mechs[key] = flatten(mechs2[key]['quirks'])

    return combined_mechs


# read the first mech file into the dictionary
with open(mech_files[0]) as f:
    mechs = json.load(f)

# remove the first mech file from the list
mech_files.pop(0)

# read and merge the remaining mech files into the dictionary
for mech_file in mech_files:
    with open(mech_file) as f:
        mech_data = json.load(f)
        mechs = combine_mechs(mechs, mech_data)

print(f"Loaded {len(mechs)} mechs.")

# Check if the output folder exists
if not os.path.exists(DEFAULT_OUTPUT_FOLDER):
    os.mkdir(DEFAULT_OUTPUT_FOLDER)

# write the combined mechs to a new file
with open(f"{DEFAULT_OUTPUT_FOLDER}/mechs.json", "w") as f:
    json.dump(mechs, f, indent=2)


# read the first quirk file into the dictionary
with open(quirk_files[0]) as f:
    quirks = json.load(f)

# remove the first quirk file from the list
quirk_files.pop(0)

# read and merge the remaining quirk files into the dictionary
for quirk_file in quirk_files:
    with open(quirk_file) as f:
        quirk_data = json.load(f)
        quirks = join_dicts(quirks, quirk_data)

print(f"Loaded {len(quirks)} quirks.")

# write the combined quirks to a new file
with open(f"{DEFAULT_OUTPUT_FOLDER}/quirks.json", "w") as f:
    json.dump(quirks, f, indent=2)

print("Done.")
