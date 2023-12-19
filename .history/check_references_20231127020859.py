import os

from references.references import SETTINGS

p = False
for n in SETTINGS["BOYS_JPG"]:
    for path in SETTINGS["BOYS_JPG"].get(n):
        if not os.path.isfile(path):
            print(path)
            p = True


for n in SETTINGS["GIRLS_JPG"]:
    for path in SETTINGS["GIRLS_JPG"].get(n):
        if not os.path.isfile(path):
            print(path)
            p = True

if not p:
    print("Ошибок нет!!!!!!")
