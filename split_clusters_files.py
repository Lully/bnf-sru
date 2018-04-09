# -*- coding: utf-8 -*-
"""
Created on Fri Apr  6 20:21:50 2018

@author: Lully

Exploitation d'un fichier de clusters extrait de RobotDonnées : découpe en fichiers
de X clusters à charger dans WorksBuilder


"""

import csv
from collections import defaultdict

liste_clusterids = []
liste_files = defaultdict()
liste_clusters = defaultdict(set)
clusterid2file = defaultdict(int)

def create_file(filename):
    file = open(filename,"w",encoding="utf-8")
    return file

        

def import_file():
    entry_filename = input("nom du fichier de clusters à découper : ")
    split_value = int(input("Combien de clusters par fichier ?\n"))
    with open(entry_filename, newline='\n',encoding="utf-8") as csvfile:
            entry_file = csv.reader(csvfile, delimiter='\t')
            i = 1
            headers = []
            clusterid_column = 0
            for row in entry_file:
                if ("clusterid" in row):
                    clusterid_column = row.index("clusterid")
                    headers = row
                else:
                    clusterid = row[clusterid_column]
                    liste_clusters[i].add(clusterid)
                    if (clusterid not in clusterid2file):
                        clusterid2file[clusterid] = i
                    filename = "Fichier-de-" + str(split_value) + "-clusters-" + str(i) + ".txt"
                    if (filename not in liste_files):    
                        liste_files[filename] = create_file(filename)
                        liste_files[filename].write("\t".join(headers) + "\n")
                    if (len(liste_clusters[i]) > split_value):
                        i += 1
                    file_of_cluster = "Fichier-de-" + str(split_value) + "-clusters-" + str(clusterid2file[clusterid]) + ".txt"
                    print(clusterid,file_of_cluster)
                    liste_files[file_of_cluster].write("\t".join(row) + "\n")
                        
    for file in liste_files:
        liste_files[file].close()
                        
if __name__ == '__main__':
    import_file()
    
