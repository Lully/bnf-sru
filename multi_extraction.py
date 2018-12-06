# coding: utf-8

"""
Extraction d'un ensemble de notices pour différents chantiers envisageables
(la faisabilité du chantier sera analysée après extraction)
"""

import SRUextraction as sru
from stdf import create_file, line2report

def sru2records(query, id_extraction):
    firstpage = sru.SRU_result(query)
    for ark in firstpage.dict_records:
        analyse(ark, firstpage.dict_records[ark], id_extraction)
    i = 1001
    while i < firstpage.nb_results:
        param = {"startRecord": str(i)}
        page = sru.SRU_result(query, param)
        for ark in firstpage.dict_records:
            analyse(ark, firstpage.dict_records[ark], id_extraction)

def analyse(ark, firstpage.dict_records[ark], id_extraction):
    return None


if __name__ == "__main__":
    query = "bib.recordtype any \"m\" and bib.doctype any \"a\""
    id_extraction = input("Identifiant de traitement : ")
    sru2records(query, id_extraction)
