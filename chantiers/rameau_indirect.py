# coding: utf-8

"""
Réforme Rameau : étapes post-DPI du 1er mai 2019
Extraction des forces armées + nom de pays
Extraction des 2 $y consécutifs (pour suppression de l'indirect)
"""

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
            ?uriManif a frbr-rda:Manifestation; dcterms:subject ?sujet1; dcterms:subject ?sujet2.
            {?sujet1 dcterms:isPartOf <http://data.bnf.fr/vocabulary/scheme/r167>.
            ?sujet2 dcterms:isPartOf <http://data.bnf.fr/vocabulary/scheme/r167>}
            UNION 
            {?sujet1 dcterms:isPartOf <https://data.bnf.fr/vocabulary/scheme/r167>.
            ?sujet2 dcterms:isPartOf <https://data.bnf.fr/vocabulary/scheme/r167>}
            FILTER (?sujet1 != ?sujet2)
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


def extract_all(report):
    fields = [str(el) for el in range(600,611)]
    fields.pop(fields.index("607"))
    arks = file2list("arks_geoloc_multi.txt")
    i = 1
    for ark in arks:
        ark = clean_ark(ark)
        print(i, "/", len(arks), "-", ark)
        analyse_bib(ark, fields, report)
        i += 1


def clean_ark(ark):
    ark = ark[ark.find("ark"):]
    if "#" in ark:
        ark = ark[:ark.find("#")]
    return ark

def analyse_bib(ark, fields, report):
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
                index_field = sru.IndexField(value, field)
                list_subfields = []
                for subfield in index_field.list_subfields:
                    list_subfields.append(subfield.code)
                list_subfields = " ".join(list_subfields)
                if ("y y" in list_subfields):
                    line = [ark,
                            ark2nn(ark),
                            field,
                            list_subfields,
                            value,
                            index_field.list_subfields[0].nna,
                            index_field.list_subfields[0].init[9:].strip()
                            ]
                    line2report(line, report)


if __name__ == "__main__":
    report = create_file("BIB avec indexation géographique indirecte.txt",
                         ["ARK", "NNB", "Zone", "Sous-zones", "Valeur", "NNA $a", "Libellé $a"])
    extract_all(report)