# coding: utf-8

"""
Objectif : comparer un gros lot d'entités data.bnf.fr et de notices
sources pour générer la table de correspondance entre les
notices Intermarc source et les propriétés RDF
"""

import re
import os
from pprint import pprint
from collections import defaultdict
from lxml import etree
from urllib import parse, request, error



import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON

import SRUextraction as sru
from stdf import create_file, line2report, ddprint

sep = [". -", "--", ".-", ";"]
concat_fields = [["100_m", " ", "100_a"],
                 ["260_a", " : ", "260_c", " , ", "260_d"]
                ]


def xml_record2dict(xml_record):
    """
    Convertit une notice MarcXML en dictionnaire
    """
    dict_record = defaultdict(dict)
    for field in xml_record.xpath("*"):
        tag = ""
        if (field.get("tag") is not None):
            tag = field.get("tag")
        else:
            tag = "000"
        for subfield in field.xpath("*"):
            code = subfield.get("code")
            if (code in dict_record[tag]):
                dict_record[tag][code].append(subfield.text)
            else:
                dict_record[tag][code] = [subfield.text]
        if (field.text is not None):
            i = 0
            for pos in field.text:
                dict_record[tag][f"pos{str(i)}"] = pos
    return dict_record

def rdf_resource2dict(triplets):
    """
    Convertit un ensemble de triplets en dictionnaire
    import rdflib
    g=rdflib.Graph()
    g.load('http://dbpedia.org/resource/Semantic_Web')
    for s,p,o in g:
        print s,p,o
    """
    dict_record = defaultdict(list)
    rdf_resource = rdflib.Graph()
    rdf_resource.parse(data=triplets, format="nt")
    
    for s, p, o in rdf_resource:
        s = s.replace("#about", "")
        if (type(o) == rdflib.term.Literal):
            # Valeur de la propriété = chaîne de caractères  
            dict_record[p.n3()].append(str(o))
        elif (type(o) == rdflib.term.URIRef
            and "data.bnf.fr" in o):
            # Valeur de la propriété = lien vers une autre ressource data
            # ou vers une valeur d'un référentiel interne
            dict_record[p.n3()].append(o.n3())
    dict_record["splitted_values"] = defaultdict(list)
    for key in dict_record:
        for value in dict_record[key]:
            for chars in sep:
                if chars in value:
                    splitted = value.split(chars)

                    for part in splitted:
                        part = part.strip()
                        if part:
                            dict_record["splitted_values"][key].append(part)
    return dict_record


def comparison_1_rdf_marc(marc_record, rdf_resource):
    """
    En entrée une notice MARC au format dictionnaire (sortie de xml_record2dict())
    et une ressource RDF (sortie de rdf_resource2dict())
    En sortie : liste des sources candidates pour chaque propriété
    """
    
    comp_dict = defaultdict(dict)
    marc_record_inversed = marc_inversion(marc_record)  
    rdf_resource = rdf_resource2dict(rdf_resource)
    for prop in rdf_resource:
        for val in rdf_resource[prop]:
            if val in marc_record_inversed:
                for source in marc_record_inversed[val]:
                    if (source in comp_dict[prop]):
                        comp_dict[prop][source] += 1
                    else:
                        comp_dict[prop][source] = 1
            elif val in marc_record_inversed["concat_values"]:
                source = marc_record_inversed["concat_values"][val]
                if (source in comp_dict[prop]):
                    comp_dict[prop][source] += 1
                else:
                    comp_dict[prop][source] = 1
    for prop in rdf_resource["splitted_values"]:
        for val in rdf_resource["splitted_values"][prop]:
            if val in marc_record_inversed:
                for source in marc_record_inversed[val]:
                    if (source in comp_dict[prop]):
                        comp_dict[prop][source] += 1
                    else:
                        comp_dict[prop][source] = 1
            elif val in marc_record_inversed["concat_values"]:
                for source in marc_record_inversed["concat_values"]:
                    if (source in comp_dict[prop]):
                        comp_dict[prop][source] += 1
                    else:
                        comp_dict[prop][source] = 1
    return comp_dict


def global_comparison_rdf_marc(dict_xml_records, dict_rdf_resources):
    """
    On compare notice à notice 2 dictionnaires, dont les clés sont les ark :
        1 dictionnaire de notices XML
        1 dictionnaire de ressources RDF
    """
    general_dict = defaultdict(dict)
    i = 0
    for ark in dict_rdf_resources:
        i += 1
        if dict_rdf_resources[ark]:
            print(i, ark)
            comparison_1_resource = comparison_1_rdf_marc(dict_xml_records[ark],
                                                          dict_rdf_resources[ark])
            for key in comparison_1_resource:
                for key2 in comparison_1_resource[key]:
                    if key2 in general_dict[key]:
                        general_dict[key][key2] += comparison_1_resource[key][key2]
                    else:
                        general_dict[key][key2] = comparison_1_resource[key][key2]
    return general_dict


def marc_inversion(marc_record):
    """
    A partir d'une notice (dictionnaire) dans le sens normal
    on intervertit les valeurs et les clés
    """
    # print("marc", marc_record)
    inversed_dict = defaultdict(list)
    for tag in marc_record:
        for code_pos in marc_record[tag]:
            key = tag + "_" + code_pos
            for val in marc_record[tag][code_pos]:
                inversed_dict[val].append(key)
    
    inversed_dict["concat_values"] = defaultdict(list)
    for concat in concat_fields:
        key = "".join(concat)
        value = ""
        for el in concat:
            if re.fullmatch("\d{3}_\w+", el):
                try:
                    path = marc_record[el.split("_")[0]][el.split("_")[1]]
                    value += "".join(path)
                except KeyError:
                    pass
            else:
                value += el
        inversed_dict["concat_values"][value] = key
    return inversed_dict

triple_example = "triplets.nt"
xml_record_example = "record.xml"

def sru2arks(query):
    param_default = {"recordSchema": "intermarcxchange"}
    sru_arks = sru.SRU_result(query, parametres = param_default)
    print(sru_arks.url)
    dict_records = sru_arks.dict_records
    list_identifiers = sru_arks.list_identifiers
    return dict_records, list_identifiers


def ark2rdf_list(liste_ark):
    """
    En entrée, une liste d'ARK
    En sortie, un dictionnaire : clé = ARK
                                 valeur = triplets RDF
    """
    dict_rdf_resources = {}
    i = 0
    for ark in liste_ark:
        i += 1
        sparql_query = """
construct {<http://data.bnf.fr/""" + ark + """> ?prop ?val} where {
  {<https://data.bnf.fr/""" + ark + """> ?prop ?val.}
  UNION
  {<https://data.bnf.fr/""" + ark + """#about> ?prop ?val.}
  UNION
  {<http://data.bnf.fr/""" + ark + """> ?prop ?val.}
  UNION
  {<http://data.bnf.fr/""" + ark + """> ?prop ?val.}
}"""

        url = "".join(["https://data.bnf.fr/sparql?default-graph-uri=&query=",
                       parse.quote(sparql_query),
                       "&format=text%2Fplain&timeout=0&should-sponge=&debug=on"])
        print(i, "extraction RDF", ark)
        try:
            rdf_resource = request.urlopen(url).read().decode("utf-8")
            rdf_resource = rdf_resource.replace("# Empty NT", "").strip()
            dict_rdf_resources[ark] = rdf_resource
        except error.HTTPError:
            dict_rdf_resources[ark] = ""
    return dict_rdf_resources


def type2resources(type_record, aut_bib):
    index = "type"
    if (aut_bib == "bib"):
        index = "recordtype"
    query = f'{aut_bib}.{index} any "{type_record}"'
    dict_xml_records, liste_ark = sru2arks(query)
    dict_marc_records = {}
    for ark in dict_xml_records:
        # print(ark, dict_xml_records[ark])
        dict_marc_records[ark] = xml_record2dict(dict_xml_records[ark])
    dict_rdf_resources = ark2rdf_list(liste_ark)
    results_comparison = global_comparison_rdf_marc(dict_marc_records, dict_rdf_resources)
    return results_comparison



if __name__ == "__main__":
    type_record = input("Type de notices à comparer (RAM, PEP, MON, ...) : ")
    aut_bib = "aut"
    if (type_record == "MON"):
       aut_bib = "bib" 
    comparison = type2resources(type_record, aut_bib)
    ddprint(comparison)