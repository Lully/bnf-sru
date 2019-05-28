# coding: utf-8

"""
A partir des notices Rameau existantes, extraire la syntaxe
"""

from collections import defaultdict
import re
import string

import SRUextraction as sru
from stdf import *

def query2extract(query, report):
    """
    A partir d'une requête, extraire toutes les notices du SRU
    """
    dict_rules = defaultdict(set)
    result = sru.SRU_result(query)
    for ark in result.dict_records:
        analyse_record(ark, result.dict_records[ark], dict_rules)
    i = 1001
    while i < result.nb_results:
        param_default = {"startRecord": str(i)}
        next_result = sru.SRU_result(query, parametres = param_default)
        for ark in next_result.dict_records:
            analyse_record(ark, next_result.dict_records[ark], dict_rules)
        i += 1000


def analyse_record(ark, xml_record, dict_rules):
    # Analyse d'une notice d'autorité Rameau (Unimarc)
    # Accesspoint : point d'accès affiché dans data.bnf.fr
    # field_value = contenu de la zone MARC
    accesspoint = ""
    field_value = ""
    field_accesspoint = ""
    for datafield in xml_record.xpath("*[@tag]"):
        tag = datafield.get("tag")
        if tag[0] == "2":
            field_accesspoint = tag
            accesspoint, field_value, liste_subfields = extract_accesspoint(ark, datafield)
            extract_rules(accesspoint, field_value, liste_subfields, dict_rules)


def extract_accesspoint(ark, datafield):
    liste_subfields = sru.field2listsubfields(datafield)
    liste_subfields = liste_subfields[liste_subfields.find("a"):]
    field_value = []
    for subfield in datafield.xpath("*[@code]"):
        code = subfield.get("code")
        value = subfield.text
        field_value.append([f"${code} {value}"])
    field_value = " ".join(field_value)
    ark_id = ark.split("/")[-1]
    url_rdf = f"https://data.bnf.fr/sparql?default-graph-uri=&\
query=PREFIX+skos%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2004%2F02%2Fskos%2Fcore%23%3E%0D%0A\
PREFIX+dcterms%3A+%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Fterms%2F%3E%0D%0A\
PREFIX+rdfs%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0D%0A\
select+distinct+%3Flabel+where+%7B%0D%0A++%7B%3Chttps%3A%2F%2Fdata.bnf.fr%2F\
ark%3A%2F12148%2F{ark_id}%3E+skos%3AprefLabel+%3Flabel%7D%0D%0A++\
UNION%0D%0A++\
%7B%3Chttp%3A%2F%2Fdata.bnf.fr%2Fark%3A%2F12148%2F{ark_id}%3E+skos%3AprefLabel+%3Flabel%7D%0D%0A%7D\
&format=application%2Frdf%2Bxml&timeout=0&should-sponge=&debug=on"
    test, result = testURLetreeParse(url_rdf)
    ns = {"skos":"http://www.w3.org/2004/02/skos/core#"}
    label = ""
    if (test
        and result.find("//skos:prefLabel", namespaces=ns) is not None):
        label = result.find("//skos:prefLabel", namespaces=ns).text
    return label, field_value, liste_subfields


def extract_rules(accesspoint, field_value, liste_subfields, dict_rules):
    """
    A partir de la comparaison entre le point d'accès et la
    zone Unimarc, on extrait des règles
    """
    field_value = [el.strip() for el in field_value.split("$") if el.strip()]
    pos = 0
    i = 1
    rule = ""
    for subfield in field_value:
        subf_val = subfield[2:]
        rule += accesspoint[pos:].replace(subf_val, f"\\{i}")
        print(f"chercher '{subf_val}' dans '{accesspoint[pos:]}'", f"i = {i}")
        pos += len(subf_val)
        i += 1
        print("rule", rule)
     
    


if __name__ == "__main__":
    query = input("Requête SRU (Unimarc) :")
    report = create_file("syntaxe-accesspoint-rameau.txt")
    query2extract(query, report)