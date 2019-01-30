# coding: utf-8

"""
Ensemble de fonctions standard pour la génération de rapports
la manipulation de fichiers, etc.
"""
import csv
from pprint import pprint

import SRUextraction as sru

def create_file(filename, mode="w", headers=[], display=True):
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

def file2dict(inputfilename, col_key=0, col_val=-1):
    """
    Convertit un fichier en dictionnaire : prend la 1ère colonne comme clé
    et la colonne 'col' comme valeur
    """
    dict = {}
    with open(inputfilename, encoding="utf-8") as  csvfile:
        entry_file = csv.reader(csvfile, delimiter='\t')
        for row in entry_file:
            dict[row[col_key]] = row[col_val]
    return dict


def close_files(files_list):
    for file in files_list:
        file.close()


def nn2ark(nna_nnb):
    """
    Convertit un NNB ou un NNA en ARK
    En entrée, le NNB ou NNA, nettoyé, de type str
    """
    type = "bib"
    if (nna_nnb.startswith("1") or nna_nnb.startswith("2")):
        type = "aut"
    query = f'{type}.recordid any "{nna_nnb}"'
    if (type == "aut"):
        query += ' and aut.status any "sparse validated"'
    results = sru.SRU_result(query)
    return results.list_identifiers


def input2outputfile(inputfilename, suffix):
    """
    A partir d'un nom de fichier (TXT ou CSV en général) en entrée,
    génération d'un fichier d'écriture en sortie, avec ajout d'un suffixe
    """
    outputfilename = inputfilename[:-4] + "-" + suffix + ".txt"
    outputfile = create_file(outputfilename)
    return outputfile


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
    report.write("\t".join(line) + "\n")


def ddprint(defaultdict):
    """
    Formation d'impression de defaultdict (pprint ne le prévoit pas)
    """
    tempdict = dict(defaultdict)
    pprint(tempdict)
    return tempdict


def sparql2dict(endpoint, sparql_query, liste_el):
    sparql = SPARQLWrapper(endpoint)
    """
    En entrée, une requête Sparql et la liste des variables
    à récupérer. La première de ces variables est la clé dans le dictionnaire
    Les autres correspondent à des listes (plusieurs valeurs possibles)
    {"ark:///": {
                 "id_wikidata": ["Q6321654", "QS321"]   
                 "coordonnees_geo": ["48.54656, 12.354684", "45.156165, 27.5165165"]
                 }
    }
    """
    dict_results = {}
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        dataset = results["results"]["bindings"]
        
        for el in dataset:
            key_name = liste_el[0]
            key_value= el.get(key_name).get("value")
            dict_results[key_value] = defaultdict(list)
            for el_ in liste_el[1:]:
                dict_results[key_value][el_].append(el.get(el_).get("value"))
    except error.HTTPError as err:
        print(err)
        print(query)
    return dict_results
