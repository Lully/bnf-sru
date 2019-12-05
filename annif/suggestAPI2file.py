# coding: utf-8

"""
Exploitation de l'API REST (méthode POST) de Annif
pour analyser un lot de résultats

Il faut lancer Annif 
>annif run
Puis construire une URL racine de type : http://localhost:5000/v1/projects/annif-discovery/suggest
+ paramètres text, limit et threshold en POST
"""

import csv
import requests
import json

def line2report(line, report, i=0, display=True):
    """
    Envoie une line (liste) dans un fichier.
    Sauf demande contraire, affiche la ligne
    dans le terminal avec un compteur
    """
    if display:
        if i:
            print(i, line)
        else:
            print(line)
    try:
        report.write("\t".join(line) + "\n")
    except TypeError:
        report.write("\t".join([str(el) for el in line]) + "\n")


def create_file(filename, headers=[], mode="w", display=True):
    """
    Crée un fichier à partir d'un nom. 
    Renvoie le fichier en objet
    """
    file = open(filename, mode, encoding="utf-8")
    if headers:
        if display:
            print(headers)
        file.write("\t".join(headers) + "\n")
    return file

def controle_param(param, default):
    if param == "":
        param = default
    return param

def analyse_file(project, filename, limit, threshold, report):
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        headers = next(content)
        for row in content:
            analyse_row(project, row, limit, threshold, report)

def analyse_row(project, row, limit, threshold, report):
    if len(row) == 2:
        recordid, metas = row
    elif (len(row) > 2):
        recordid, metas = row[0], " ".join(row[1:])    
    r = requests.post(f"http://localhost:5000/v1/projects/{project}/suggest", 
                      data={'text': metas, 'limit': limit, threshold: threshold})
    datas = json.loads(r.text)
    for result in datas["results"]:
        if result["score"] > threshold:
            line = [recordid, metas, result["label"], result["uri"], result["score"]]
            line2report(line, report)



if __name__ == "__main__":
    project = input("Project ID : ")
    filename = input("Input file (2 columns : ID and metadata) : ")
    limit = int(controle_param(input("Param limit (default : 8) : "), 8))
    threshold = float(controle_param(input("Param threshold (default : 0.6) : "), 0.6))
    report = create_file(filename[:-4] +  "-results" + filename[-4:])
    analyse_file(project, filename, limit, threshold, report)