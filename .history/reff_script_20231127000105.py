
import os

def find_subfolders(directory):
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
    return subfolders

directory_path = 'references'


subfolders_list = find_subfolders(directory_path)[:2]



# Записываем словарь в другой файл
