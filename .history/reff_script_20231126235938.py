
import os

def find_subfolders(directory):
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
    return subfolders

directory_path = 'references'


subfolders_list = find_subfolders(directory_path)[:2]


folders_dict = {i: subfolders_list[i] for i in range(len(subfolders_list))}
print(folders_dict)
# Записываем словарь в другой файл
