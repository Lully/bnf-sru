# coding: utf-8

"""
Réforme Rameau : étapes post-DPI du 1er mai 2019
Extraction des forces armées + nom de pays
Extraction des 2 $y consécutifs (pour suppression de l'indirect)
"""

import re
import SRUextraction as sru
from stdf import *
from SPARQLWrapper import SPARQLWrapper, JSON

def sparql2list():
    sparql = SPARQLWrapper("https://data.bnf.fr/sparql")
    """
    En entrée, une requête Sparql qui récupère une seule variable
    --> liste des résultats dans la liste
    """
    arks = []
    sparql_query = """
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX frbr-rda: <http://rdvocab.info/uri/schema/FRBRentitiesRDA/>
    select distinct ?uriManif where {
        ?uriManif a frbr-rda:Manifestation; dcterms:subject <http://data.bnf.fr/ark:/12148/cb11952003d>; dcterms:subject ?sujet2.
        {?sujet2 dcterms:isPartOf <http://data.bnf.fr/vocabulary/scheme/r167>}
        UNION 
        {?sujet2 dcterms:isPartOf <https://data.bnf.fr/vocabulary/scheme/r167>}
    }
    """
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        dataset = results["results"]["bindings"]
        for el in dataset:
            ark = clean_ark(el.get("uriManif").get("value"))
            arks.append(ark)
    except error.HTTPError as err:
        print(err)
    return arks


def extract_all(report, report_non_retournees):
    fields = [str(el) for el in range(600,611)]
    arks = sparql2list()
    i = 1
    for ark in arks:
        print(i, "/", len(arks), "-", ark)
        analyse_bib(ark, fields, report, report_non_retournees)
        i += 1


def clean_ark(ark):
    ark = ark[ark.find("ark"):]
    if "#" in ark:
        ark = ark[:ark.find("#")]
    return ark

def analyse_bib(ark, fields, report, report_non_retournees):
    param_default = {"recordSchema": "intermarcxchange"}
    record = sru.SRU_result(f'bib.persistentid any "{ark}"', parametres=param_default)
    if record.list_identifiers:
        record = record.dict_records[record.list_identifiers[0]]
    else:
        record = None
    if record is not None:
        for field in fields:
            for field_occ in record.xpath(f"*[@tag='{field}']"):
                value = sru.field2value(field_occ)
                print(value)
                index_field = sru.IndexField(value, field)
                list_subfields = []
                for subfield in index_field.list_subfields:
                    list_subfields.append(subfield.code)
                list_subfields = " ".join(list_subfields)
                if (re.fullmatch(r".+11952003 \$. Forces armées \$3 \d+ \$y.+", value) is not None):
                    pos = 0
                    i = 1
                    for el in index_field.list_subfields:
                        if el.nna == "11952003":
                            pos = i
                        i += 1
                    pays = [index_field.list_subfields[pos].nna, index_field.list_subfields[pos].init]
                    line = [ark,
                            ark2nn(ark),
                            field,
                            list_subfields,
                            value,
                            pays[0],
                            pays[1]
                            ]
                    line2report(line, report)
                elif (field == "607"
                      and len(index_field.list_subfields) > 1
                      and "11952003 $x Forces armées" in index_field.list_subfields[1].init):
                    pays = [index_field.list_subfields[0].nna, 
                            index_field.list_subfields[0].init]
                    line = [ark,
                            ark2nn(ark),
                            field,
                            list_subfields,
                            value,
                            pays[0],
                            pays[1]
                            ]
                    line2report(line, report_non_retournees)  


if __name__ == "__main__":
    report = create_file("Forces armées.txt",
                         ["ARK", "NNB", "Zone", "Sous-zones", "Valeur",
                         "NNA Pays", "Libellé Pays"])
    report_non_retournees = create_file("Forces armées - non retournées.txt",
                                        ["ARK", "NNB", "Zone", "Sous-zones", "Valeur",
                                        "NNA Pays", "Libellé Pays"])
    extract_all(report, report_non_retournees)