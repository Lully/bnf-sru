# coding: utf-8

explain = """
Pour un corpus Annif déjà exporté et mis au format 2 colonnes,
nettoyage des valeurs (règles de nettoyage gérées dans extractandfilter)
"""

import csv
import extractandfilter as ext
from stdf import *

def analyse_file(filename, col1_id, report):
    content = file2list(filename, True)
    for row in content:
        analyse_row(row, col1_id, report)

def analyse_row(row, col1_id, report):
    if col1_id:
        line = [row.pop(0)]
    else:
        line = []
    vals = []
    for el in row:
        try:
            if el[0] == "<" and el[-1] == ">":
                line.append(el)
            else:
                clean_el = ext.clean_content_field(el)
                line.append(clean_el)
                vals.append(clean_el)
        except IndexError:
            pass
    if ("".join(vals) != ""
        and len("".join(vals)) > 39):

        line2report(line, report)

if __name__ == "__main__":
    print(explain)
    filename = input("Nom du fichier à traiter : ")
    col1_id = input2default(input("ID en première colonne ? (True/[False]) : "), False)
    report = input2outputfile(filename, "clean")
    analyse_file(filename, col1_id, report)