# coding: utf-8

"""
Extraction des zones 606 : combinaisons à retourner
"""

import SRUextraction as sru
from stdf import *

def extract_all(filename, report606, report607):
    listeNNA = file2list(filename)
    for nna in listeNNA:
        extract_nna(nna, report606, report607)

def extract_nna(nna, report606, report607):
    query = f"bib.subject2bib any {nna}"
    param_default = {"recordSchema": "intermarcxchange"}
    result = sru.SRU_result(query, parametres=param_default)
    for bib in result.dict_records:
        analyse_bib(nna, bib, result.dict_records[bib], report606, report607)
    i = 1001
    while i < result.nb_results:
        param_default["startRecord"] = str(i)
        next_result = sru.SRU_result(query, parametres=param_default)
        for bib in next_result.dict_records:
            analyse_bib(nna, bib, next_result.dict_records[bib], report606, report607)
        i += 1000


def analyse_bib(nna, arkbib, bib_record, report606, report607):
    for f606 in bib_record.xpath("*[@tag='606']"):
        val = sru.field2value(f606)
        if f"{nna} $x" in val and "$y" in val:
            analyse_field("606", val, nna, arkbib, report606)
    for f607 in bib_record.xpath("*[@tag='607']"):
        val = sru.field2value(f607)
        if f"{nna} $x" in val:
            analyse_field("607", val, nna, arkbib, report607)

def analyse_field(zone, field_value, nna, arkbib, report):
    subfields = field_value.split("$3 ")[1:]
    subf_subdiv = ""
    liste_codes = [el[10] for el in subfields]
    pos_subf = 0
    i = 0
    for el in subfields:
        if el.startswith(nna):
            subf_subdiv = el[10]
            pos_subf = i
        i += 1
    liste_codes[pos_subf] = liste_codes[pos_subf] + "SL"
    liste_codes = " ".join(liste_codes)
    line2report([nna, arkbib, zone, liste_codes, field_value], report)


if __name__ == "__main__":
    filename = input("Nom du fichier contenant la liste des NNA de subdivs à chercher en 606/607 : ")
    report606 = input2outputfile(filename, "extraction606.txt")
    report607 = input2outputfile(filename, "extraction607.txt")
    line2report("NNA,ARK BIB,Zone,Sous-zones,valeur".split(","), report606)
    line2report("NNA,ARK BIB,Zone,Sous-zones,valeur".split(","), report607)
    extract_all(filename, report606, report607)

