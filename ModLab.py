import os
import sys
import json

# Check if the user specified a file path to the mod folders
if len(sys.argv) > 1:
    mod_folder = sys.argv[1]
else:
    mod_folder = "mods"

print(f"Using mod folder: {mod_folder}")

# scan the subfolders of the mod folder for the mechs.json files
mech_files = []

for root, dirs, files in os.walk(mod_folder):
    for file in files:
        if file.endswith("mechs.json"):
            mech_files.append(os.path.join(root, file))

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
    return {**dict1, **dict2}


# combines two indexes of mechs.json files into a single index.
# When there are duplicate keys, they values are merged into a list
def combine_mechs(mechs1, mechs2):
    combined_mechs = {}

    for key in mechs1.keys():
        if key in mechs2.keys():
            combined_mechs[key] = join_dicts(mechs1[key], mechs2[key])
            if 'quirks' in combined_mechs[key]:
                combined_mechs[key]['quirks'] = flatten(combined_mechs[key]['quirks'])
        else:
            combined_mechs[key] = mechs1[key]

    for key in mechs2.keys():
        if key not in combined_mechs.keys():
            combined_mechs[key] = mechs2[key]

    return combined_mechs

# def combine_mechs(mechs1, mechs2):
#     combined_mechs = {}
#
#     for key in mechs1.keys():
#         if key in mechs2.keys():
#             combined_mechs[key] = join_dicts(mechs1[key], mechs2[key])
#         else:
#             combined_mechs[key] = mechs1[key]
#
#     for key in mechs2.keys():
#         if key not in combined_mechs.keys():
#             combined_mechs[key] = mechs2[key]
#
#     return combined_mechs


# read the first mech file into the dictionary
with open(mech_files[0]) as f:
    mechs = json.load(f)

# read and merge the remaining mech files into the dictionary
for mech_file in mech_files:
    with open(mech_file) as f:
        mech_data = json.load(f)
        mechs = combine_mechs(mechs, mech_data)

print(f"Loaded {len(mechs)} mechs.")