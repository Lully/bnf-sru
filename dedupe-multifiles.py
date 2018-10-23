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

import string
import os 
from collections import defaultdict
import csv
from openpyxl import Workbook, load_workbook


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
    if ("xls" in filetype):
        # ouverture du fichier Excel
        excel_file2dict(filename, select_col)
    else:
        csv_file2dict(filename, select_col)


def select_column_xls(select_col, headers):
    col = 1
    if (representsInt(select_input)):
        col = int(select_input)
    else:
        i = 0
        for el in headers:
            i += 1
            if (headers[el] == select_col):
                col = i
    # Conversion de l'indice de colonne en lettre de colonne
    col = string.ascii_uppercase[i]
    return col


def excel_file2dict(input_filename, select_col):
    xlsfile = load_workbook(filename=input_filename)
    xls_table = xlsfile.sheetnames[0]
    column_id = select_column_xls(select_col, xls_table.rows[1])
    for row in range(2, xls_table.max_row + 1):
        cell_name = f"{column_id}{str(row)}"
        identifier = xls_table[cell_name].value
        dic_ids[identifier].add(filename)


def csv_file2dict(filename, select_col):
    with open(filename, encoding="utf-8") as csvfile:
            content  = csv.reader(csvfile, delimiter='\t')
            headers = next(content)
            column_id = select_column(select_col, headers)
            for row in content:
                identifier = row[column_id]
                dic_ids[identifier].add(filename)


def create_report(output_filename, output_filetype):
    if ("csv" in output_filetype):
        report = open(output_filename, "w", encoding="utf-8")
        report.write("\t".join["Identifiant doublon", "fichiers concernés"] + "\n")
        return report
    else:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        report = Workbook(write_only=False)
        report.save(os.path.join(dir_path, output_filename))
        report.guess_type = False
        report_table = report.create_sheet(title="liste_doublons")
        report_table['A1'], report_table["B1"] = ["Identifiant doublon", "fichiers concernés"]
        


def line2report(line, report, output_filetype, i):
    if (output_filetype == "csv"):
        report.write("\t".join(line) + "\n")
    else:
        cellA = "A" + str(i)
        cellB = "B" + str(i)
        report[cellA], report[cellB] = line[0], line[1]


if __name__ =="__main__":
    filelist = input("Nom des fichiers à comparer (séparés par des ';') : ")
    select_col = input("Nom ou numéro de colonne (numérotation commençant à 1) \
    servant d'identifiant (par défaut : 1ère colonne) : ")
    output_filename = input("Nom du rapport de doublons : ")
    output_filetype = "csv"
    if (".xls" in output_filename):
        output_filetype = "xlsx"
    report = create_report(output_filename, output_filetype)
    for filename in filelist.split(";"):
        file2dic(filename, select_col)
    for entry in dic_ids:
        i = 1
        if len(dic_ids[entry]) > 1:
            line = [entry, ",".join(list(dic_ids[entry]))]
            print(line)
            i += 1
            line2report(line, report, output_filetype, i)
            