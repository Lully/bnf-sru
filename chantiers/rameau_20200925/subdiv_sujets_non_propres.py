# coding: utf-8

explain = """Le CNR souhaite une extraction des $x qui "n'existent pas", c'est-à-dire qui n'ont pas un NNA propre mais n'existent que dans des constructions.
Ex NNA 11931912 $a Eau $x Épuration. Épuration n'a pas de NNA."""

from stdf import *
import SRUextraction as sru

def extract_rameau(report):
    query = "aut.type any RAM"
    results = sru.SRU_result(query, parametres={"recordSchema": "intermarcxchange", 
                             "maximumRecords": "500"})
    nb_results = results.nb_results
    subdivs = {}
    for ark in results.dict_records:
        subdivs = analyse_ark(ark, results.dict_records[ark], subdivs, report)


def analyse_ark(ark, xml_record, subdivs, report):
    fields = [str(el) for el in range(160, 170)] + [str(el) for el in range(460, 470)]
    for field in fields:
        for field_occ in xml_record.xpath(f".[@tag='{field}']"):
            field_value = sru.field2value(field_occ)
            for subf_x in field_occ.xpath("*[@code='x']"):
                value = subf_x.text
                subdivs = analyse_value(field, field_value, value, 
                                        ark, xml_record,
                                        subdivs, report)
    return subdivs


def analyse_value(field, field_value, value, ark, xml_record, subdivs, report):
    if value in subdivs:
        if subdivs[value] == "non autonome":
            line2report([ark, nn2ark(ark), field, field_value, value])
    else:
        sparql_query = """PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
select ?ark ?label where {
  ?ark a skos:Concept; dcterms:isPartOf ?ensemble.
  ?ark skos:prefLabel \"""" + value + """\"."""
        if value != value.lower():
            sparql_query += """
  UNION
  {?ark skos:prefLabel \"""" + value.lower() + """\".}"""
        if value.title() not in [value, value.lower()]:
            sparql_query += """
  UNION
  {?ark skos:prefLabel \"""" + value.title() + """\".}"""
        sparql_query += "\n?ark skos:prefLabel ?label.}"
        print(sparql_query)
        result_sparql = sparql2dict(endpoint, sparql_query, ["label", "ark"])
        if result_sparql:
            subdivs[value] = result_sparql
        else:
            subdivs[value] = "non autonome"
    return subdivs

if __name__ == __main__:
    report = create_file("Subdiv Rameau non autonomes.txt", "ARK,NNA,Zone,Label complet,Subdiv".split(","))
    extract_rameau(report)