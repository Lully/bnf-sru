# coding: utf-8

"""
A partir des notices Rameau existantes, extraire la syntaxe

Résultat sur quelques milliers de notices :
'a b f x': {'\\1, \\2 (\\3) -- \\4'}, 
'a y': {'\\1 -- \\2},
'a y x': {'\\1 -- \\2 -- \\3'},
'a y y': {'\\1 -- \\2 -- \\3'},
'a b x': {'\\1. \\2 -- \\3'},
'a x x': {'\\1 -- \\2 -- \\3'},
'a c b x': {'\\1. \\3 (\\2) -- \\4',
'a y z': {'\\1 -- \\2 -- \\3'},
'a c': {'\\1 (\\2)'},
'a c f x': {'\\1 (\\2 ; \\3) -- \\4'},
'a b c x': {'\\1. \\2 (\\3) -- \\4'},
'a x y': {'\\1 -- \\2 -- \\3'},
'a b c': {'\\1, \\2 (\\3)'},
'a y y z': {'\\1 -- \\2 -- \\3 -- \\4'},
'a z x': {'\\1 -- \\3 -- \\2'},
'a b x x': {'\\1. \\2 -- \\3 -- \\4'},
'a c x x': {'\\1 (\\2) -- \\3 -- \\4'},
'a b d x': {'\\1, \\2 \\3 -- \\4'},
'a f x': {'\\1 (\\2) -- \\3'},
'a b c b x': {'\\1. \\2 (\\3) -- \\5'}})

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
    if query.startswith("aut."):
        result = sru.SRU_result(query)
        for ark in result.dict_records:
            analyse_record(ark, result.dict_records[ark], dict_rules)
        i = 1001
        while i < result.nb_results:
            param_default = {"startRecord": str(i)}
            next_result = sru.SRU_result(query, parametres = param_default)
            print(next_result.url)
            for ark in next_result.dict_records:
                analyse_record(ark, next_result.dict_records[ark], dict_rules)
            i += 1000
            print(dict_rules)
    else:
        listeArks = file2list(query)
        for ark in listeArks:
            record = ark2autrecord(ark)
            analyse_record(ark, record, dict_rules)
    eot(report, dict_rules)

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
        if code in string.ascii_lowercase:
            field_value.append(f"${code} {value}")
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
    ns = {"skos":"http://www.w3.org/2004/02/skos/core#",
          "res": "http://www.w3.org/2005/sparql-results#"}
    label = ""
    if (test
       and result.find("//res:value", namespaces=ns) is not None):
        label = result.find("//res:value", namespaces=ns).text
    return label, field_value, liste_subfields


def extract_rules(accesspoint, field_value, liste_subfields, dict_rules):
    """
    A partir de la comparaison entre le point d'accès et la
    zone Unimarc, on extrait des règles
    """
    field_value = [el.strip() for el in field_value.split("$") if el.strip()]
    i = 1
    rule = accesspoint
    for subfield in field_value:
        subf_val = subfield[2:]
        rule = rule.replace(subf_val, f"\\{i}", 1)
        i += 1
    dict_rules[liste_subfields].add(rule)
     
def eot(report, dict_rules):
    for entry in dict_rules:
        values = list(dict_rules[entry])
        for value in values:
            print(entry, value)
            line2report([entry, value], report)
    close_files([report])

if __name__ == "__main__":
    query = input("Requête SRU (Unimarc) : ")
    report = create_file("syntaxe-accesspoint-rameau.txt")
    query2extract(query, report)