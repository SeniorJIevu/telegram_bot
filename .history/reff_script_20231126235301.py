def import os
import os
# Функция для поиска папок внутри указанной директории
def find_subfolders(directory):
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir()]
    return subfolders

# Путь к директории, в которой нужно найти папки
directory_path = '/путь/к/директории'

# Получаем список папок внутри указанной директории
subfolders_list = find_subfolders(directory_path)

# Создаем словарь и записываем в него названия папок
folders_dict = {i: subfolders_list[i] for i in range(len(subfolders_list))}

# Записываем словарь в другой файл
with open('folders_dict.txt', 'w') as file:
    file.write(str(folders_dict))