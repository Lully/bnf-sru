# coding: utf-8

"""
Extraction d'un ensemble de notices pour différents chantiers envisageables
(la faisabilité du chantier sera analysée après extraction)

* volumétrie des notices avec une zone 142 et pas de zone 041
* volumétrie des notices sans zone 142 et avec une 245 ["-----"] (ce qui est entre les guillemets est le titre original : sauf "sic")
* volumétrie notices SU, sans zone 280, avec un 260$d contenant un point > ce qu'il y a après le point
* volumétrie BIB liées 2 fois à la même PEP
* extraction balises +:

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
