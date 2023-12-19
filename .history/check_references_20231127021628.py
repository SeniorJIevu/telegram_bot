import os

from references.references import REFERENCES

p = False
for n in REFERENCES["BOYS_JPG"]:
    for path in REFERENCES["BOYS_JPG"].get(n):
        if not os.path.isfile(path):
            print(path)
            p = True


for n in REFERENCES["GIRLS_JPG"]:
    for path in REFERENCES["GIRLS_JPG"].get(n):
        if not os.path.isfile(path):
            print(path)
            p = True

if not p:
    print("Ошибок нет!!!!!!")
