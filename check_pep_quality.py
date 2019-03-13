# coding: utf-8

import csv
from stdf import input2outputfile, line2report
import SRUextraction as sru

def file2records(input_filename):
    """
    Extraction de chaque ligne du fichier pour analyse
    Récupération au passage de la notice XML
    """
    outputfile = input2outputfile(input_filename, "report")
    line2report(["ARK", "NNA/NNB", "Zone concernée", "Valeur", "Problème"])
    with open(input_filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        header = content.pop(0)
        for row in content:
            ark = row[0]
            dict_record = {}
            i = 0
            for el in header:
                dict_record[el] = row[i]
                i += 1
            analyse_row(ark, dict_record, outputfile)
            except IndexError as err:
                pass

def analyse_row(ark, dict_record, outputfile):
    if ("autorité" in dict_record["type"]):
        analyse_aut(ark, dict_record, outputfile)


def analyse_aut(ark, dict_record):
    if ("personne physique" in dict_record["type"]):
        analyse_pep(ark, dict_record, outputfile)


def analyse_pep(ark, dict_record):
    analyse_pep_100_400mde(ark, dict_record, outputfile)
    analyse_pep_100_400ed(ark, dict_record, outputfile)
    analyse_pep_no_610(ark, dict_record, outputfile)
    

def analyse_pep_100_400mde(ark, dict_record, outputfile):
    """
    Vérification : si la PEP a un 100$m, un 100$e et pas de 100$e
    """
    multi_val_100 = dict_record["100"].split("¤").strip()
    multi_val_400 = dict_record["400"].split("¤").strip()
    for val in multi_val_100:
        if ("$m" in val
            and "$e" in val
            and "$d" not in val):
            line = [ark, dict_record["NNA/NNB"] "100", val,
                    "100 avec $m et $d mais pas de $e"]
            line2report(line, outputfile)
    for val in multi_val_400:
        if ("$m" in val
            and "$e" in val
            and "$d" not in val):
            line = [ark, dict_record["NNA/NNB"] "400", val,
                    "400 avec $m et $d mais pas de $e"]
            line2report(line, outputfile)


def analyse_pep_100de(ark, dict_record, outputfile):
    multi_val_100 = dict_record["100"].split("¤").strip()
    multi_val_400 = dict_record["400"].split("¤").strip()
    for val in multi_val_100:
        if ("$e" in val
            and "$d" in val[val.find("$e"):]):
            line = [ark, dict_record["NNA/NNB"] "100", val,
                    "100 avec un $d après un $e"]
            line2report(line, outputfile)
    for val in multi_val_400:
        if ("$e" in val
            and "$d" in val[val.find("$e"):]):
            line = [ark, dict_record["NNA/NNB"] "400", val,
                    "400 avec un $d après un $e"]
            line2report(line, outputfile)


def analyse_pep_no_610(ark, dict_record, outputfile):
    if ("610" in dict_record
        and if dict_record["610"] == ""):
        line = [ark, dict_record["NNA/NNB"] "610", dict_record["610"], "Pas de zone 610"]
        line2report(line, outputfile)


if __name__ == "__main__":
    input_filename = input("Nom du fichier en entrée (Rapport d'ExtractionCatalogue):\n")
    file2records(input_filename)