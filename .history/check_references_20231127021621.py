import os

from references.references import REFERENCES1

p = False
for n in REFERENCES1["BOYS_JPG"]:
    for path in REFERENCES1["BOYS_JPG"].get(n):
        if not os.path.isfile(path):
            print(path)
            p = True


for n in REFERENCES1["GIRLS_JPG"]:
    for path in REFERENCES1["GIRLS_JPG"].get(n):
        if not os.path.isfile(path):
            print(path)
            p = True

if not p:
    print("Ошибок нет!!!!!!")
