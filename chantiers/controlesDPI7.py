# coding: utf-8

"""
Extraction des zones 606 : combinaisons à retourner
"""

import SRUextraction as sru
from stdf import *

def extract_all(filename, report):
    listeNNA = file2list(filename)
    for nna in listeNNA:
        extract_nna(nna, report)

def extract_nna(nna, report):
    query = f"bib.subject any {nna}"
    param_default = {"recordSchema": "intermarcxchange"}
    result = sru.SRU_result(query, parametres=param_default)
    for bib in result.dict_records:
        analyse_bib(nna, bib, result.dict_records[bib], report)


def analyse_bib(nna, arkbib, bib_record, report):
    for f606 in bib_record.xpath("*[@tag='606']"):
        val = sru.field2value(f606)
        if nna in val:
            analyse_field(val, nna, arkbib, report)

def analyse_field(field_value, nna, arkbib, report):
    subfields = field_value.split("$3 ")[1:]
    subf_subdiv = ""
    liste_codes = [el[10] for el in subfields]
    pos_subf = 0
    for el in subfields:
        if el.startswith(nna):
            subf_subdiv = el[10]
            pos_subf = i
        i += 1
    liste_codes[pos_subf] = liste_codes[pos_subf].upper()
    line2report([nna, arkbib, liste_codes, field_value], report)


if __name__ == "__main__":
    filename = input("Nom du fichier contenant la liste des NNA de subdivs à chercher en 606")
    report = input2outputfile(filename, "extraction606.txt")
    line2report("NNA,ARK BIB,Sous-zones,valeur".split(","), report)
    extract_all(filename, report)


