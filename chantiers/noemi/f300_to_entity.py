# coding: utf-8

explain = """
Script pour identifier le cas de traitement des zones de note 300$a 
dans le cadre de la migration Noemi
En entrée : une liste de notices BIB (ARK)

"""

import csv
import re
from lxml import etree
import SRUextraction as sru

def analyse_file(filename, report, regex_dict):
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for ark in content:
            ark = ark[0]
            print(ark)
            full_xml_record = sru.SRU_result(f"idPerenne any \"{ark}\"", 
                                        "http://noticesservices.bnf.fr/SRU?",
                                        {"recordSchema": "InterXMarc_Complet"})
            full_xml_record = full_xml_record.firstRecord
            niveau_anl = "0"
            zones300 = sru.record2fieldvalue(full_xml_record, "300$a").split("¤")
            for zone300 in zones300:
                case, entity_target = analyse_zone300(zone300, regex_dict)
                print(" "*5, zone300)
                print(" "*10, case)
                print(" "*10, entity_target)
                line = [ark, niveau_anl, zone300, case, entity_target]
                report.write("\t".join(line))
                report.write("\n")

            for record in full_xml_record.xpath(".//*[local-name()='record']"):
                zones300 = sru.record2fieldvalue(record, "300$a").split("¤")
                niveau_anl = get_anl_level(record, full_xml_record)
                for zone300 in zones300:
                    case, entity_target = analyse_zone300(zone300, regex_dict)
                    line = [ark, niveau_anl, zone300, case, entity_target]
                    report.write("\t".join(line))
                    report.write("\n")

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
    print(explain)
    filename = input("Nom du fichier contenant la liste des ARK BIB (sans en-tête) : ")
    regex_file = input("Nom du fichier contenant les expressions régulières\n\
(3 colonnes : consigne, regex, entité cible) : ")
    regex_dict = file2dict_regex(regex_file)
    report = open(f"{filename[:-4]}-analyse.txt", "w", encoding="utf-8")
    analyse_file(filename, report, regex_dict)
    report.close()
