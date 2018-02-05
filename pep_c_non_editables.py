# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 18:24:11 2018

@author: Lully
"""

import csv

entry_filename = "PEP_008_pos64-1.tsv"
entry_filename = "test_pep_c_1.txt"

selection = open("liste_pep_c_non_editables.txt","w",encoding="utf-8")
stats = open("stats_pep_c_non_editables.txt","w",encoding="utf-8")

dic = {"1":0,"non 1":0}

with open(entry_filename, newline='\n',encoding="utf-8") as csvfile:
    entry_file = csv.reader(csvfile, delimiter='\t')
    next(entry_file)
    i = 1
    for row in entry_file:
        f008 = row[3]
        editable = f008[64]
        print(str(i) + ". " + row[0] )
        if (editable == "1"):
            dic["1"] += 1
            selection.write("\t".join(row) + "\n")
        else:
            dic["non 1"] += 1

stats.write("\t".join(["Valeur 008 pos.64","Nombre PEP complètes"]) + "\n")
               
for key in dic:
    stats.write("\t".join([key, str(dic[key])]) + "\n")

stats.close()