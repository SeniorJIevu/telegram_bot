
import os

def find_subfolders(directory):
    def inner_function():
        subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
        return subfolders
    return inner_function

directory_path = 'references'

subfolders_list = find_subfolders(directory_path)()[:2]

subfolders_dict = {}
for folder in subfolders_list:
    sub_subfolders = find_subfolders(os.path.join(directory_path, folder))()
    subfolders_dict[folder] = sub_subfolders

print(subfolders_dict)

