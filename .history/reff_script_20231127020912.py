import os
from collections import OrderedDict
import json

def find_references_path(directory):
    def inner_function():
        subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
        return subfolders
    return inner_function

def get_files_in_folder(directory):
    files = [os.path.join(directory, f.name).replace('\\', '/') for f in os.scandir(directory) if f.is_file()]
    return files

directory_path = 'references'

references_list_directory = find_references_path(directory_path)()[:2]

subfolders_dict = OrderedDict()
for references_info in sorted(references_list_directory):
    sub_subfolders = find_references_path(os.path.join(directory_path, references_info))()
    sub_subfolders_dict = {}
    for sub_folder in sub_subfolders:
        files = get_files_in_folder(os.path.join(directory_path, references_info, sub_folder))
        sub_subfolders_dict[sub_folder] = files
    subfolders_dict[references_info] = OrderedDict(sorted(sub_subfolders_dict.items(), key=lambda x: int(x[0])))

    
output_file = 'references/references.py'
with open(output_file, 'w') as file:
    file.write("REFERENCES = ")
    json.dump(subfolders_dict, file, indent=4)

print(f'Data has been written to {output_file}')