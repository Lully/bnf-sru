# coding: utf-8

"""
Ensemble de fonctions standard pour la génération de rapports
la manipulation de fichiers, etc.
"""

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
