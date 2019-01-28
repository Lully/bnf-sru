# coding: utf-8

"""
Récupération des coordonnées géographiques des monuments 
fournies par Wikidata, grâce aux alignements BnF 
déclarés dans Wikidata
"""

from collections import defaultdict
from urllib import error 
from lxml import etree

from SPARQLWrapper import SPARQLWrapper, JSON

from stdf import create_file, line2report
import SRUextraction as sru


def sparql2dict(endpoint, sparql_query, liste_el):
    sparql = SPARQLWrapper(endpoint)
    """
    En entrée, une requête Sparql et la liste des variables
    à récupérer. La première de ces variables est la clé dans le dictionnaire
    Les autres correspondent à des listes (plusieurs valeurs possibles)
    """
    dict_results = {}
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        dataset = results["results"]["bindings"]
        
        for el in dataset:
            key_name = liste_el[0]
            key_value= el.get(key_name).get("value")
            dict_results[key_value] = defaultdict(list)
            for el_ in liste_el[1:]:
                dict_results[key_value][el_].append(el.get(el_).get("value"))
    except error.HTTPError as err:
        print(err)
        print(query)
    return dict_results


def launch(sparql_query, report):
    """
    Lancement de la requête Sparql et récupération
    des résultats dans un dictionnaire
    """
    results = sparql2dict("https://query.wikidata.org/sparql",
                          sparql_query, 
                          ["ressource", "idBnF", 
                           "nom", "coordonnees_geo"])
    analyse_results(results, report)


def analyse_results(results, report):
    """
    Analyse des résultats des alignements
    """
    i = 1
    for el in results:
        analyse_1result(el, results[el], report)
        print(i, el)
        i += 1

def analyse_1result(el, result, report):
    if (len(result["idBnF"]) == 1):
        BnF_ID = "ark:/12148/cb" + result["idBnF"][0]
        geoID = None
        type_bnf = ark2type(BnF_ID)
        if type_bnf == "RAM":
            geoID = convert_ram2geo(BnF_ID)
            if geoID is not None:
                line = [el, geoID, result["nom"][0],
                        result["coordonnees_geo"][0],
                        "conversion RAM > GEO",
                        BnF_ID, type_bnf
                        ]
                line2report(line, report)
        elif (type_bnf == "GEO"):
            line = [el, BnF_ID, result["nom"][0],
                    result["coordonnees_geo"][0],
                    "", "", type_bnf]
            line2report(line, report)
        else:
            line = [el, BnF_ID, result["nom"][0],
                    result["coordonnees_geo"][0],
                    "", "", type_bnf]
            line2report(line, report)

    else:
        BnF_IDs = result["idBnF"]
        i = 0
        for BnF_ID in BnF_IDs:
            BnF_ID = "ark:/12148/cb" + BnF_ID
            type_bnf = ark2type(BnF_ID)
            if (type_bnf == "GEO"):
                line = [el, BnF_ID, result["nom"][i],
                    result["coordonnees_geo"][i]]
                line2report(line, report)
            else:
                geoID = convert_ram2geo(BnF_ID)
                if geoID:
                    line = [el, geoID, result["nom"][i],
                            result["coordonnees_geo"][i],
                            "conversion RAM > GEO",
                            BnF_ID]
                    line2report(line, report)
            i += 1

def ark2type(bnf_id):
    query = f'aut.persistentid any "{bnf_id}"'
    param_default = {"recordSchema": "intermarcxchange"}
    result = sru.SRU_result(query, parametres = param_default)
    record_type = ""
    dic_type = {"c" : "ORG",
                "g" : "MAR", 
                "l" : "GEO",
                "m" : "RAM", 
                "p" : "PEP",
                "s" : "TIC",
                "t" : "TUT",
                "u" : "TUM"}
    for rec in result.dict_records:
        xml_record = result.dict_records[rec]
        label = xml_record.find("mxc:leader", namespaces=sru.ns_bnf).text
        #print(bnf_id, label, "|", label[4])
        record_type = dic_type[label[9]]
        if (record_type == "GEO"):
            if (xml_record.find("mxc:datafield[@tag='167']",
                               namespaces=sru.ns_bnf) is not None):
                print("geo > ram")
                record_type = "RAM"
    return record_type

def convert_ram2geo(bnf_id):
    geo_id = ""
    sparql_query = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
select distinct ?uri_GEO ?type_GEO where {
  {<https://data.bnf.fr/""" + bnf_id + """> skos:closeMatch ?uri_GEO.
?uri_GEO a ?type_GEO.}
  UNION 
  {<http://data.bnf.fr/""" + bnf_id + """> skos:closeMatch ?uri_GEO.
?uri_GEO a ?type_GEO.}
  FILTER (?type_GEO = <http://www.w3.org/2004/02/skos/core#Concept>)
  FILTER CONTAINS(str(?uri_GEO), "data.bnf.fr")
}
    """
    results = sparql2dict("https://data.bnf.fr/sparql",
                          sparql_query, ["uri_GEO", "type_GEO"])
    
    for el in results:
        ark = el[el.find("ark"):]
        type_align = ark2type(ark)
        if type_align == "GEO":
            geo_id = ark
    if geo_id == "":
        geo_id = None
    return geo_id


identifiant = input("Identifiant (nom du fichier) : ")
sparql_query = """
select * where {
  ?ressource wdt:P268 ?idBnF;
             rdfs:label ?nom;
             wdt:P625 ?coordonnees_geo;
             wdt:P31 ?type_construction.
  ?type_construction wdt:P279+ wd:Q811979.
             
FILTER (langMatches(lang(?nom), "FR"))
             }
    """
report = create_file(identifiant + ".txt")
headers = ["ID Wikidata", "ARK", "Nom",
               "Coordonnées geo", "Conversion RAM > Geo ?",
               "ARK Rameau initial dans Wikidata"]
line2report(headers, report)
launch(sparql_query, report)
