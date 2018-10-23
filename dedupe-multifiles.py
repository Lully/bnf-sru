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

dir_path = os.path.dirname(os.path.realpath(__file__))

dic_ids = defaultdict(set)
dic_id2metas = defaultdict(list)

def representsInt(s):
    """
    Vérifie si s est un nombre
    """
    test = True
    try:
        int(s)
    except ValueError:
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
    if ("xls" in filename):
        # ouverture du fichier Excel
        excel_file2dict(filename, select_col)
    else:
        csv_file2dict(filename, select_col)


def select_column_xls(select_input, headers):
    col = 0
    if (representsInt(select_input)):
        col = int(select_input)-1
    else:
        i = 0
        for cell in headers:
            if (cell.value == select_input):
                col = i
            i += 1
    # Conversion de l'indice de colonne en lettre de colonne
    col = string.ascii_uppercase[col]
    print(col)
    return col


def excel_file2dict(input_filename, select_col):
    xlsfile = load_workbook(filename=input_filename)
    xls_table_name = xlsfile.sheetnames[0]
    xls_table = xlsfile[xls_table_name]
    column_id = select_column_xls(select_col, list(xls_table.rows)[0])
    for row in range(2, xls_table.max_row + 1):
        cell_name = f"{column_id}{str(row)}"
        identifier = xls_table[cell_name].value
        if (identifier):
            dic_ids[identifier].add(filename)
            dic_id2metas[identifier+input_filename] = row


def csv_file2dict(input_filename, select_col):
    with open(input_filename, encoding="utf-8") as csvfile:
            content  = csv.reader(csvfile, delimiter='\t')
            headers = next(content)
            column_id = select_column(select_col, headers)
            for row in content:
                identifier = row[column_id]
                dic_ids[identifier].add(input_filename)
                dic_id2metas[identifier+input_filename] = row


    

def create_csv_report(output_filename, output_filetype):
    report = open(output_filename, "w", encoding="utf-8")
    report.write("\t".join["Identifiant doublon", "fichiers concernés"] + "\n")
    return report


def create_xls_report(output_filename, output_filetype):
    report = Workbook(write_only=False)
    report.guess_type = False
    report_table = report.create_sheet(title="liste_doublons")
    report_table["A1"] = "Identifiant doublon"
    report_table["B1"] =  "fichiers concernés"
    report.save(os.path.join(dir_path, output_filename))
    return report, report_table
        


def line2report(line, report, output_filetype, i):
    if (output_filetype == "csv"):
        report.write("\t".join(line) + "\n")
    else:
        cellA = "A" + str(i)
        cellB = "B" + str(i)
        report[cellA] = str(line[0])
        report[cellB] = str(line[1])


def dict_entry2report(report, entry, entry_value, i):
    line = [entry, ",".join(list(dic_ids[entry]))]
    print(line)
    line2report(line, report, output_filetype, i)
    


if __name__ =="__main__":
    filelist = input("Nom des fichiers à comparer (séparés par des ';') : ")
    select_col = input("Nom ou numéro de colonne (numérotation commençant à 1) \
servant d'identifiant (par défaut : 1ère colonne) : ")
    output_filename = input("Nom du rapport de doublons : ")
    output_filetype = "csv"
    for filename in filelist.split(";"):
        file2dic(filename, select_col)

    if (".xls" in output_filename):
        output_filetype = "xlsx"
        report, sheet = create_xls_report(output_filename, output_filetype)
    else:
        report = create_csv_report(output_filename, output_filetype)
    
    i = 2
    if (".xls" in output_filename):
        for entry in dic_ids:
            if len(dic_ids[entry]) > 1:
                dict_entry2report(sheet, entry, dic_ids[entry], i)
                i += 1
        report.save(os.path.join(dir_path, output_filename))
    else:
        for entry in dic_ids:
            if len(dic_ids[entry]) > 1:
                dict_entry2report(report, entry, dic_ids[entry], i)