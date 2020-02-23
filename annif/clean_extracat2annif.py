# coding: utf-8

explain = """A partir d'une extraction catalogue tabulée (ExtraCat)
nettoyage des chaînes de caractères"""

import csv
from stdf import *
from extractandfilter import clean_title_field, clean_content_field
from string import digits

def clean_file(filename, reportid, report):
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        header = next(content)
        for row in content:
            clean_row(row, header, reportid, report)


def clean_row(row, header, reportid, report):
    i = 0
    content = []
    index = []
    ark = row[0]
    for el in row:
        if (header[i][0] == "8"
           or header[i][0] == "3"):
        # alors c'est du contenu
            el = clean_content_field(el)
            content.append(el)
        elif (header[i][0] == "6"):
            el = format_dollar3(el)
        # alors c'est de l'indexation
            index.append(el)
        elif (header[i][0] in digits):
            el = clean_title_field(el)
            content.append(el)
        i += 1
    content = " ".join([el for el in content if el.strip()])
    index = " ".join(index)
    line2report([content, index], report)
    line2report([ark, content, index], reportid)


def format_dollar3(value):
    # Récupération d'une colonne en sortie d'extraCat contenant des $3
    # On ne récupère que les $3, et on les restructure en URI
    subfields = value.split("$")
    subf3 = []
    for el in subfields:
        if el and el[0] == "3":
            el = el[2:10].strip()
            el = f"<http://data.bnf.fr/{el}>"
            subf3.append(el)
    subf3 = "\t".join(subf3)
    return subf3


if __name__ == "__main__":
    print(explain)
    filename = input("Nom du fichier en entrée : ")
    reportid = input2outputfile(filename, "clean_avecid.tsv")
    report = input2outputfile(filename, "clean_sansid.tsv")
    clean_file(filename, reportid, report)