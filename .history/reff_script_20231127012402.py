import os
import json

def save_json_to_variable(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        REFERENCES = json.dumps(result, indent=4)
        return REFERENCES
    return wrapper

def find_subfolders(directory):
    def inner_function():
        subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
        return subfolders
    return inner_function

def get_files_in_folder(directory):
    files = [f.name for f in os.scandir(directory) if f.is_file()]
    return files

@save_json_to_variable
def get_subfolders_data(directory_path, num_folders):
    subfolders_list = find_subfolders(directory_path)()[:num_folders]

    subfolders_dict = {}
    for folder in subfolders_list:
        sub_subfolders = find_subfolders(os.path.join(directory_path, folder))()
        sub_subfolders_dict = {}
        for sub_folder in sub_subfolders:
            files = get_files_in_folder(os.path.join(directory_path, folder, sub_folder))
            sub_subfolders_dict[sub_folder] = files
        subfolders_dict[folder] = sub_subfolders_dict

    return subfolders_dict

directory_path = 'references'
num_folders = 2

REFERENCES = get_subfolders_data(directory_path, num_folders)
