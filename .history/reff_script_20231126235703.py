
import os
# Функция для поиска папок внутри указанной директории
def find_subfolders(directory):
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
    return subfolders

# Путь к директории, в которой нужно найти папки
directory_path = 'references'

# Получаем список папок внутри указанной директории
subfolders_list = find_subfolders(directory_path)[:2]

print(subfolders_list)