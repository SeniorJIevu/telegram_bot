
import os

def find_subfolders(directory):
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
    return subfolders

directory_path = 'references'


subfolders_list = find_subfolders(directory_path)[:2]


for folder in subfolders_list:
    sub_subfolders = find_subfolders(os.path.join(directory_path, folder))

