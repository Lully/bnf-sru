# coding: utf-8

"""
Extraire 1 à n utilisations d'une indexation à partir d'un corpus initial
afin d'entraîner une ML
"""
import csv
from collections import Counter, OrderedDict
from stdf import *


def sample_file(filename, threshold, report, stats):
    content = file2list(filename, True)
    keywords_treated = {}
    nb_lines_init = 0
    nb_lines_output = 0
    for row in content:
        label = row[0]
        nb_lines_init += 1
        for kw in row[1].split(" "):
            if kw not in keywords_treated:
                keywords_treated[kw] = 1
                line2report([label, kw], report)
                nb_lines_output += 1
            elif keywords_treated[kw] < threshold:
                keywords_treated[kw] += 1
                line2report([label, kw], report, display=False)
                nb_lines_output += 1
            else:
                keywords_treated[kw] += 1
    stats_dict = Counter([keywords_treated[kw] for kw in keywords_treated])
    print(stats_dict)
    stats_dict = dict(stats_dict)
    print("Fichier en entrée : ", nb_lines_init, "lignes")
    print("Fichier en sortie : ", nb_lines_output, "lignes")
    for key in sorted(stats_dict):
        line = [key, stats_dict[key]]
        line2report(line, stats)
    stats.write("\n"*2)
    stats.write(f"Nombre de concepts distints : {str(len(keywords_treated))}")
    stats.write("\n"*4)
    stats.write(f"Fichier en entrée : {str(nb_lines_init)} lignes")
    stats.write(f"Fichier en sortie : {str(nb_lines_output)} lignes")

if __name__ == "__main__":
    threshold = input2default(input("Nombre max d'occurrences à retenir pour chaque indexation (défaut : 2) : "), 2)
    filename = input("Nom du fichier en entrée à filtrer (2 colonnes : texte/index) : ")
    suffix = input("Suffixe du fichier en sortie : ")
    report = input2outputfile(filename, suffix)
    stats = input2outputfile(filename, f"{suffix}-stats")
    sample_file(filename, threshold, report, stats)