# coding: utf-8

"""
Echantillonage : récupérer 1 ligne sur x dans un fichier donné
"""

import csv
from stdf import *

headers = False

def sampling(filename, fract, report):
    if headers:
        next(filename)
    i = 0
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for row in content:
            if i % fract == 0:
                line2report(row, report)
            i += 1

if __name__ == "__main__":
    fract = input("Extraire 1 ligne sur [x] dans un fichier (défaut : 1000): ")
    if fract == "":
        fract = 1000
    else: 
        fract = int(fract)
    filename = input("Nom du fichier en entrée : ")
    suffix = input(f"Suffixe du fichier en sortie (défaut : '-echantillon-{str(fract)}e') : ")
    if suffix == "":
        suffix = f"echantillon-{str(fract)}e"
    report = input2outputfile(filename, suffix)
    sampling(filename, fract, report)