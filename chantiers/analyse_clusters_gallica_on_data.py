# coding: utf-8

"""
Générer un tableau 
	* Auteur
	* ClusterID
	* TIC existante ? (ARK)
	* PEX NUM dans une des manifs du cluster ?
	* Manif avec PEX NUM liée à la TIC ?

"""

from collections import defaultdict
import csv
import re

import SRUextraction as sru
from cleanstring import clean_string
from stdf import *

class Work:
    def __init__(self, clusterid, dict_cluster):
        row_ref = dict_cluster["row"]["0"]
        self.arkAUT = row_ref[2]
        self.recordAUT = ark2autrecord(arkAUT)
        self.names = autrec2accesspoint(self.recordAUT)
        self.title = String(row_ref[header.find("Titre de l'oeuvre")])
        

class String:
    def __init__(self, string):
        self.init = string
        self.nett = clean_string(string, False, True)


def autrec2accesspoint(aut_record):
    names = sru.record2fieldvalue(aut_record, "100$a").split("¤") + sru.record2fieldvalue(aut_record, "400$a").split("¤")
    names = [String(name) for name in names]
    return names

def controles_titres(Work):
    """
    Ensembles de contrôles qui permettent d'identifier des cas où les 
    oeuvres générées sont suspectes
    """
    alerts = []
    if len(record.title.init) > 250:
        alerts.append("Titre très long")
    testAUT = False
    for name in record.names:
        if name.nett in record.title.nett:
            testAUT = True
    if testAUT:
        alerts.append("Nom d'auteur dans le titre")

    return alerts
    


def analyse_files(dict_files, report):
    dict_keys2works = defaultdict(set)
    dict_clustersid2content = defaultdict(dict)
    for filename in dict_files:
        with open(dict_files[filename], encoding="utf-8") as file:
            content = csv.reader(file, delimiter="\t")
            headers = next(content)
            for row in content:
                clusterid = row[headers.find("clusterid")]
                ark_manif = row[headers.find("ark manifestation")]
                work_title = row[headers.find("Titre de l'oeuvre")]
                if clusterid in dict_clustersid2content:
                    dict_clustersid2content[clusterid]["row"].append(row)
                    dict_clustersid2content[clusterid]["key"].add(ark_manif)
                    dict_clustersid2content[clusterid]["arks_manifs"].add(ark_manif)
                    dict_clustersid2content[clusterid]["key"].add(work_title)
                    dict_clustersid2content[clusterid]["tic"].add(row2tic(row, headers))
                else:
                    dict_clustersid2content[clusterid] = {"row": [row],
                                                           "filename": filename,
                                                           "arks_manifs": {ark_manif},
                                                           "tic" = {row2tic(row, headers)}
                                                           "key": {ark_manif, work_title}}
    for clusterid in dict_clustersid2content:
        hashid = sorted(list(dict_clustersid2content[clusterid]["key"]))
        hashid = hash(hashid)
        dict_clustersid2content[clusterid]["hash"] = hashid
        tic = [el for el in list(dict_clustersid2content[clusterid]["tic"]) if el]
        tic = ",".join(tic)
        dict_clustersid2content[clusterid]["tic"] = tic
    for clusterid in dict_clustersid2content:
        dict_keys2works[dict_clustersid2content[clusterid]["hash"]].add(clusterid)
    analyse_dicts(dict_keys2works, dict_clustersid2content, dict_files, report)


def row2tic(row, headers):
    if "ark Oeuvre" in headers and row[headers.find("ark Oeuvre")]:
        return row[headers.find("ark Oeuvre")]
    else:
        return ""


def analyse_dicts(dict_keys2works, dict_clustersid2content, dict_files, report):
    for work_key in dict_keys2works:
        multi_aut = False
        test_pexnum = False
        test_lienmanif_pexnum = False
        test_tic = False
        tic = ""
        if count(list(dict_keys2works[work_key])) > 1:
            multi_aut = True
        for clusterid in dict_keys2works[work_key]:
            work = Work(clusterid, dict_clustersid2content[clusterid])
            if dict_clustersid2content[clusterid]["tic"]:
                test_tic = True
                tic = dict_clustersid2content[clusterid]["tic"]
            controles = controles_titres(work)
            test_pexnum = check_pexnum(dict_clustersid2content[clusterid]["arks_manifs"])

            

def check_pexnum(arks_manifs):
    test = False
    



if __name__ == "__main__":
    clustersTIC_filename = "lien1TIC.txt"
    clustersMON_sans_TIC_filename = "sansagregats_sansTIC.txt"
    clustersAGR_sans_TIC_filename = "agregats_sansTIC.txt"
    report = create_file("Liste_tous_clusters.txt",
                         "ARK AUT,Nom AUT,ClusterID,TitreOeuvre,TIC ?,PEX NUM ?,Manif avec PEX NUM liée à TIC?".split(","))
    dict_files = {"clustersTIC": clustersTIC_filename,
                  "clustersMONsansTIC": clustersMON_sans_TIC_filename,
                  "clustersAGRsansTIC": clustersAGR_sans_TIC_filename}
    analyse_files(dict_files, report)