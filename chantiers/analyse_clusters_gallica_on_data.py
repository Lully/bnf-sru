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
    def __init__(self, cluster):
        self.arkAUT = row[1]
        self.recordAUT = ark2autrecord(arkAUT)
        self.names = autrec2accesspoint(self.recordAUT)
        self.title = String(row[header.find("Titre Oeuvre")])
        

class String:
    def __init__(self, string):
        self.init = string
        self.nett = clean_string(string, False, True)


def autrec2accesspoint(aut_record):
    names = sru.record2fieldvalue(aut_record, "100$a").split("¤") + sru.record2fieldvalue(aut_record, "400$a").split("¤")
    names = [String(name) for name in names]
    return names

def controles_titres(record):
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
    


def analyse_files(clustersTIC_filename, clustersMON_sans_TIC_filename, clustersAGR_sans_TIC_filename, report):
    dict_works_keys = defaultdict(dict)




if __name__ == "__main__":
    clustersTIC_filename = "lien1TIC.txt"
    clustersMON_sans_TIC_filename = "sansagregats_sansTIC.txt"
    clustersAGR_sans_TIC_filename = "agregats_sansTIC.txt"
    report = create_file("Liste_tous_clusters.txt",
                         "ARK AUT,Nom AUT,ClusterID,TitreOeuvre,TIC ?,PEX NUM ?,Manif avec PEX NUM liée à TIC?".split(","))
    analyse_files(clustersTIC_filename, clustersMON_sans_TIC_filename, clustersAGR_sans_TIC_filename, report)