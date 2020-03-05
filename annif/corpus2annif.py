# coding: utf-8

explain = """En entrée, un fichier à 3 colonnes : ID de notice, chaîne de caractères + liste de concepts (sous la forme d'URI)
La 3e colonne peut être vide
Ce script sépare les chaînes de caractères non indexées
Pour les chaînes de caractères indexées, il en met 1/5 (20\%) de côté pour l'évaluation
"""

import csv
from stdf import *


def extract(filename, reports):
    i = 0
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t", doublequote=False)
        i += 1
        for row in content:
            if row[2]:
                i += 1
                if i % 5 == 0:
                    line2report(row[1:], reports["eval"])
                else:
                    line2report(row[1:], reports["train"])
            else:
                line2report(row, reports["suggest"])


if __name__ == "__main__":
    print(explain)
    filename = input("Nom du fichier à traiter : ")
    reports = {"train": input2outputfile(filename, "train"),
             "eval": input2outputfile(filename, "eval"),
             "suggest": input2outputfile(filename, "suggest")}
    extract(filename, reports)