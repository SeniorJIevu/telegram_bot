import os
from collections import OrderedDict
import json

def find_subfolders(directory):
    def inner_function():
        subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
        return subfolders
    return inner_function

def get_files_in_folder(directory):
    files = [f.name for f in os.scandir(directory) if f.is_file()]
    return files

directory_path = 'references'

subfolders_list = find_subfolders(directory_path)()

subfolders_dict = OrderedDict()
for i, folder in enumerate(sorted(subfolders_list)):
    sub_subfolders = find_subfolders(os.path.join(directory_path, folder))()
    sub_subfolders_dict = {}
    for sub_folder in sorted(sub_subfolders):
        files = get_files_in_folder(os.path.join(directory_path, folder, sub_folder))
        sub_subfolders_dict[sub_folder] = files
    subfolders_dict[i + 1] = OrderedDict(sorted(sub_subfolders_dict.items()))
    
output_file = 'references/13.py'
with open(output_file, 'w') as file:
    json.dump(subfolders_dict, file, indent=4)

print(f'Data has been written to {output_file}')