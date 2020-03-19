# coding: utf-8

explain = """
Ajout du libellé Dewey pour les URI identifiées
Fichier à X colonnes, dont certaines ont dans l'en-tête le mot "URI"
"""

from stdf import *
import csv

def add_labels(filename, dewey_file):
    report = input2outputfile(filename, "with-labels")
    list_dewey = file2list(dewey_file, True)
    dict_dewey = {}
    for el in list_dewey:
        key = el[1].replace("<", "").replace(">", "")
        dict_dewey[key] = el[0]
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        headers = next(content)
        cols_uri = []
        i = 0
        for el in headers:
            if "URI" in el:
                cols_uri.append(i)
            i += 1
        headers = rewrite(headers, cols_uri)
        line2report(headers, report)
        for row in content:
            for col in cols_uri[-1::-1]:
                try:
                    row.insert(col+1, dict_dewey[row[col]])
                except KeyError:
                    row.insert(col+1, "")
                except IndexError:
                    pass
            line2report(row, report)


def rewrite(headers, cols_uri):
    print(headers)
    for col in cols_uri[-1::-1]:
        head = headers[col]
        new_head = head.replace("URI", "label")
        headers.insert(col+1, new_head)
    return headers



if __name__ == "__main__":
    filename = input("Fichier en entrée : ")
    dewey_file = input("Fichier Dewey (URI - label) : ")
    add_labels(filename, dewey_file)