# coding: utf-8
"""
En entrée, un lot de fichiers JSON d'oeuvres extraits du ZIP
d'un run de RobotDonnées
Le programme ouvre tous les fichiers, et identifie les clusters
qui font doublon (ou sont des sous-ensembles) d'un autre
"""

from collections import defaultdict
import zipfile
import os
import json


def zip2files(zip_file_name):
    dict_clusters2manifs = defaultdict(dict)
    dict_clusters2filename = defaultdict(str)
    dict_manifs2clusters = defaultdict(set)
    dict_jsonfile2content = defaultdict()
    zip_file = zipfile.ZipFile(zip_file_name, "r")
    

    for json_filename in zip_file.namelist():
        with open(json_filename) as jsonfile:
            work = json.load(jsonfile)
            dict_jsonfile2content[json_filename]["json"] = work
            dict_jsonfile2content[json_filename]["id"] = work["id"]
            id_work = work["id"]
            manifs = work["manifs"]
            nb_manifs = len(manifs)
            dict_clusters2filename[id_work] = json_filename
            for manif in manifs:
                dict_manifs2clusters[manif]["list_works"][id_work] = nb_manifs
                dict_clusters2manifs[id_work].add(manif)

    # On réécrit ensuite un fichier ZIP avec uniquement les oeuvres
    # qui ne font pas doublon
    zip_file_filter = zipfile.ZipFile(zip_file_name[:-4]+"-filter.zip", "w")
    selected_works = set()
    for manif in dict_manifs2clusters:
        dict_manifs2clusters[manif]["selected_work"] = max(dict_manifs2clusters[manif]["list_works"], 
                                                    key=lambda key: dict_manifs2clusters[manif]["list_works"][key])
        selected_works.add(dict_manifs2clusters[manif]["selected_work"])

    selected_works = list(selected_works)
    for id_work in selected_works:
        json_filename =  dict_clusters2filename[id_work]
        work = dict_jsonfile2content[json_filename]["json"]
        file = open(json_filename, "w", encoding="utf-8")
        zip_file_filter.write(file)
        os.remove(file)

if __name__ == "__main__":
    zip_file_name = "clusters.zip"
    zip2files(zip_file_name)