# coding: utf-8

explain = """Script pour identifier le cas de traitement des zones de note 300$a 
dans le cadre de la migration Noemi
En entrée : une liste de notices BIB (ARK)
"""

import csv
import re
import SRUextraction as sru

def analyse_file(filename, report, regex_dict):
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for ark in content:
            full_xml_record = sru.SRU_result(f"idPerenne any {ark}", 
                                        "https://noticesservices.bnf.fr",
                                        {"recordSchema": "InterXMarc_Complet"}).firstRecord
            for record in full_xml_record.xpath(".//local-name()='record'"):
                zones300 = sru.record2fieldvalue(record, "300$a").split("¤")
                niveau_anl = get_anl_level(record, full_xml_record)
                for zone300 in zones300:
                    case, entity_target = analyse_zone300(zone300, regex_dict)
                    line = [ark, niveau_anl, zone300, case, entity_target]

def get_anl_level(record, full_xml_record):
    # renvoie le niveau ANL (numéro d'ANL, et numéro d'ANL supérieur si ANL de niveau 2)
    return "0"


def analyse_zone300(zone300, regex_dict):
    # renvoie 
    #   "case": l'expression régulière à laquelle correspond la zone
    #   "entity_target" : l'entité cible
    zone300 = zone300.lower()
    case = []
    entity_target = []
    for reg in regex_dict:
        if re.fullmatch(reg, zone300) is not None:
            case.append(reg)
            entity_target.append(regex_dict[reg])
    if len(set(case)) == 1 and len(set(entity_target)) == 1:
        case = list(set(case))
        entity_target = list(set(entity_target))
    case = " // ".join(case)
    entity_target = " // ".join(entity_target) 
    return case, entity_target


def file2dict_regex(regex_file):
    # Récupère un fichier texte tabulé à trois colonnes :
    # 1. Règle (en langage naturel) pour traitement de la zone
    # 2. regex
    # 3. entité cible
    regex_dict = {}
    with open(regex_file, "r", encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        header = next(content)
        for row in content:
            regex = row[1]
            entity_target = row[2]
            regex_dict[regex] = entity_target
    return regex_dict


if __name__ == "__main__":
    filename = input("Nom du fichier contenant la liste des ARK BIB (sans en-tête")
    regex_file = input("Nom du fichier contenant les expressions régulières (3 colonnes : consigne, regex, entité cible")
    regex_dict = file2dict_regex(regex_file)
    report = open(f"{filename[:-4]}-analyse.txt")
    analyse_file(filename, report, regex_dict)
