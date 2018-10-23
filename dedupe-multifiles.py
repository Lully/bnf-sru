# coding: utf-8

"""
Programme d'identification de doublons entre plusieurs fichiers
Cas envisagé : plusieurs fichiers au même format (tabulé, colonnes aux mêmes positions)
contenant une liste d'exemplaires en colonne X.
Le programme ouvre chacun des fichiers et récupère l'ensemble des codes-barres, qu'il associe
dans un dictionnaire à ce fichier

Puis il ouvre le fichier suivant et enrichit le même dictionnaire.
S'il rencontre le même code-barre, il va enrichir l'entrée déjà existante du dictionnaire

Les fichiers en entrée ont des en-têtes de colonne

Le dictionnaire ressemble à :
dic_ids = {
            "14727841318": ("fichier1.txt"),
            "14725418718": ("fichier1.txt"),
            "71561516510": ("fichier1.txt", "fichier2.txt"),
            "12217785424": ("fichier2.txt")
            } 

Ensuite, le programme extrait du dictionnaire les valeurs multiples
"""


from collections import defaultdict
import csv


dic_ids = defaultdict(set)


def representsInt(s):
    """
    Vérifie si s est un nombre
    """
    test = True
    try:
        int(s)
    except ErrorValue:
        test = False
    return test


def select_column(select_input, headers):
    """Vérifie si la valeur du 2e input est un chiffre (n° de colonne)
    ou non (en-tête de colonne)"""
    if (select_input == ""):
        return 0
    if (representsInt(select_input)):
        return int(select_input)-1
    else:
        return headers.index(select_input)


def file2dic(filename, select_col):
    with open(filename, encoding="utf-8") as csvfile:
        content  = csv.reader(csvfile, delimiter='\t')
        headers = next(content)
        column_id = select_column(select_col, headers)
        for row in content:
            identifier = row[column_id]
            dic_ids[identifier].add(filename)


if __name__ =="__main__":
    filelist = input("Nom des fichiers à comparer (séparés par des ';') : ")
    select_col = input("Nom ou numéro de colonne (numérotation commençant à 1) servant d'identifiant (par défaut : 1ère colonne) : ")
    output_filename = input("Nom du rapport de doublons : ")
    report = open(output_filename, "w", encoding="utf-8")
    report.write("\t".join["Identifiant doublon", "fichiers concernés"] + "\n")
    for filename in filelist.split(";"):
        file2dic(filename, select_col)
    for entry in dic_ids:
        if len(dic_ids[entry]) > 1:
            line = [entry, ",".join(list(dic_ids[entry]))]
            print(line)
            report.write("\t".join(line) + "\n")