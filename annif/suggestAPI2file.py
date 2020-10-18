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

import os

import SRUextraction as sru



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

def analyse_file(project, filename, limit, threshold, display_option, report):
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        headers = next(content)
        for row in content:
            analyse_row(project, row, limit, threshold, display_option, report)

def analyse_row(project, row, limit, threshold, display_option, report):
    record = sru.SRU_result(f"bib.persistentid any \"{row[0]}\"", parametres={"recordSchema": "intermarcxchange", "maximumRecords": "1"})
    record = record.firstRecord

    f009_3 = " "
    for f009 in record.xpath("*[@tag='009']"):
        value = f009.text
        if value[0] == "a":
            f009_3 = value[3]
    if len(row) == 2:
        recordid, metas = row
    elif (len(row) > 2):
        recordid, metas = row[0], " ".join(row[1:])
    line = [recordid, metas]
    if f009_3 == "f":
        line.append("Fiction")
    else:
        for proj in project.split(";"):
            os.environ['NO_PROXY'] = '127.0.0.1'
            session = requests.Session()
            session.trust_env = False
            url = f"http://localhost:5000/v1/projects/{proj}/suggest"
            r = session.post(url, data={'text': metas})
            datas = json.loads(r.text)
        # print(datas)
            if display_option == "2":
                try:
                    for result in datas["results"]:
                        if result["score"] > threshold:        
                            line.extend([result["label"], result["uri"], result["score"], proj])
                            line2report(line, report)
                except KeyError:
                    line2report(line, report)
            else:
                results = sort_by_score(datas["results"], limit, threshold)
                results = complete_line(results, limit)
                line.extend(results)
    if display_option == "1":
        line2report(line, report)


def complete_line(results, limit):
    # Compléter la ligne de résultats avec des colonnes vides
    # 3 colonnes supplémentaire par résultat manquant (libellé, uri, score)
    nbcols = limit * 3
    nbcols_manquants = nbcols - len(results)
    results.extend([""]*nbcols_manquants)
    return results

def sort_by_score(dict_results, limit, threshold):
    temp_list = []
    results = []
    for el in dict_results:
        if el["score"] > threshold:
            val = "\t".join([str(el["score"]), el["label"], el["uri"]])
            temp_list.append(val)
    temp_list = sorted(temp_list, reverse=True)
    if len(temp_list) > limit:
        temp_list = temp_list[:limit]
    for el in temp_list:
        el = el.split("\t")
        results.extend([el[1], el[2], el[0]])
    return results



if __name__ == "__main__":
    project = input("Project ID (si plusieurs : séparateur ';'): ")
    filename = input("Input file (2 columns : ID and metadata) : ")
    suffix = input("Suffixe du fichier en sortie (default : -results) : ")
    if suffix == "":
        suffix = "-results"
    limit = int(controle_param(input("Param limit (default : 4) : "), 4))
    threshold = float(controle_param(input("Param threshold (default : 0.6) : "), 0.6))
    display_option = input("1 row by record [1] \nor 1 row by suggest [2] (default 1) : ")
    if display_option == "":
        display_option = "1"
    report = create_file(filename[:-4] +  suffix + filename[-4:])
    headers = ["ARK", "métas"]
    if display_option == "1":
        for i in range(1, limit+1):
            headers.extend([f"Concept {str(i)} : libellé",
                            f"Concept {str(i)} : URI",
                            f"Concept {str(i)} : score"])
    else:
        headers.extend(["Libellé", "URI", "score"])
    line2report(headers, report)
    analyse_file(project, filename, limit, threshold, display_option, report)