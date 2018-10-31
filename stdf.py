# coding: utf-8

"""
Ensemble de fonctions standard pour la génération de rapports
la manipulation de fichiers, etc.
"""

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


def close_files(files_list)
    for file in files_list:
        file.close()


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
