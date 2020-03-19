# coding: utf-8

explain = """
Quand on a scindé un corpus en 2 (entrainement, évaluation) pour Annif :
on peut comparer les deux pour voir s'il y a des concepts présents dans le corpus d'évaluation,
absents du corpus d'entraînement

Les 2 fichiers sont à 2 colonnes (texte, liste d'URI)
"""

from stdf import *

option_text = {"1": "Extraire simplement stats et la liste des URI absentes du corpus d'entraînement",
               "2" : "Extraire stats des URI absentes + régénérer fichier entraînement/évaluation"}

def compare_files(train_file, eval_file, option):
    set_train = set()
    eval_content_to_keep = set()
    with open(train_file, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for row in content:
            for uri in row[1:]:
                set_train.add(uri)
    with open(eval_file, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for row in content:
            for uri in row[1:]:
                if uri not in set_train:
                    eval_content_to_keep.add("\t".join(row))
    comparison_report(train_file, eval_content_to_keep, option)


def comparison_report(train_file, eval_content_to_keep, option):
    print("Nombre de lignes à ajouter : ", len(eval_content_to_keep))
    if option == "2":
        report = input2outputfile(train_file, "complement")
        with open(train_file, encoding="utf-8")  as file:
            content = csv.reader(file, delimiter="\t")
            for row in content:
                line2report(row, report, display=False)
        for row in eval_content_to_keep:
            line2report([row], report)
    

if __name__ == "__main__":
    train_file = input("Nom du fichier pour l'entraînement : ")
    eval_file = input("Nom du fichier pour l'évaluation : ")
    option = input(f"Option : {option_text} : ")
    compare_files(train_file, eval_file, option)