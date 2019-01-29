# coding: utf-8

"""
Objectif : comparer un gros lot d'entités data.bnf.fr et de notices
sources pour générer la table de correspondance entre les
notices Intermarc source et les propriétés RDF
"""

import re
from collections import defaultdict
from lxml import etree

import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON

import SRUextraction as sru
from stdf import create_file, line2report

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
    rdf_resource.load(triplets, format="nt")
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
                        dict_record["splitted_values"][part.strip()].append(key)
    return dict_record


def comparison_rdf_marc(marc_record, rdf_resource):
    """
    En entrée une notice MARC au format dictionnaire (sortie de xml_record2dict())
    et une ressource RDF (sortie de rdf_resource2dict())
    En sortie : liste des sources candidates pour chaque propriété
    """
    comp_dict = defaultdict(list)
    marc_record_inversed = marc_inversion(marc_record)
    for prop in rdf_resource:
        for val in rdf_resource[prop]:
            if val in marc_record_inversed:
                print(marc_record_inversed[prop], rdf_resource[prop])
            elif val in marc_record_inversed["concat_values"]:
                print("concat", marc_record_inversed["concat_values"][prop], rdf_resource[prop])
    for prop in rdf_resource["splitted_values"]:
        if prop in marc_record_inversed:
            print(marc_record_inversed[prop], rdf_resource["splitted_values"][prop])
        elif prop in marc_record_inversed["concat_values"]:
            print("concat", marc_record_inversed["concat_values"][prop], rdf_resource["splitted_values"][prop])
    return comp_dict


def marc_inversion(marc_record):
    """
    A partir d'une notice (dictionnaire) dans le sens normal
    on intervertit les valeurs et les clés
    """
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
        inversed_dict["concat_values"][key] = value
    return inversed_dict

triple_example = "triplets.nt"
xml_record_example = "record.xml"

if __name__ == "__main__":
    rdf_record_dict = rdf_resource2dict(triple_example)
    xml_rec = open(xml_record_example, encoding="utf-8")
    xml_record = etree.parse(xml_rec)
    marc_record_dict = xml_record2dict(xml_record)
    comparison_rdf_marc(marc_record_dict, rdf_record_dict)
    