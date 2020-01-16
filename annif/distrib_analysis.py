# coding: utf-8

""" A partir d'un fichier contenant en 2e colonne 
une série de mots-clés, on fait des stats de distribution 
sur les chaînes d'indexation et sur les termes seuls"""

import csv
from collections import Counter
from textwrap import wrap

from stdf import *

def analyse_file(filename, report):
    liste_indexation = []
    liste_kw = []
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for row in content:
            liste_indexation, liste_kw = analyse_row(row, liste_indexation, liste_kw)
    dict_indexation = Counter(liste_indexation)
    distrib_indexation = Counter([dict_indexation[ind] for ind in dict_indexation])
    dict_kw = Counter(liste_kw)
    distrib_kw = Counter([dict_kw[ind] for ind in dict_kw])
    line2report(["Stats pour les chaînes d'indexation"], report)
    line2report(["Nombre de chaînes d'indexation", str(len(liste_indexation))], report)
    line2report(["Nombre de chaînes d'indexation distinctes", str(len(dict_indexation))], report)
    for el in distrib_indexation:
        line2report([el, distrib_indexation[el]], report)
    line2report(["\n"*3], report)
    line2report(["Stats pour les concepts"], report)
    line2report(["Nombre de concepts", str(len(liste_kw))], report)
    line2report(["Nombre de concepts distincts", str(len(dict_kw))], report)
    for el in distrib_kw:
        line2report([el, distrib_kw[el]], report)

def analyse_row(row, liste_indexation, liste_kw):
    ind = row[1].split(" ")
    liste_indexation.extend(ind)
    for kw in ind:
        kw = kw.replace("<http://data.bnf.fr", "").replace("<https://data.bnf.fr", "").replace(">", "")
        kw = wrap(kw, 8)
        liste_kw.extend(kw)
    return liste_indexation, liste_kw



if __name__ == "__main__":
    filename = input("Nom du fichier en entrée : ")
    report = input2outputfile(filename, "distrib_indexation")
    analyse_file(filename, report)