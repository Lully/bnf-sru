# coding: utf-8

explain = """
Extraction du modèle de données de data.bnf.fr, par type d'entités

"""

import urllib.parse
from pprint import pprint

from stdf import *
from SPARQLWrapper import SPARQLWrapper, JSON

SPARQLEndpoint = "https://data.bnf.fr/sparql"
ns = {"http://purl.org/ontology/bibo/": "bibo",
    "http://vocab.org/bio/0.1/": "bio",
    "http://data.bnf.fr/ontology/bnf-onto/": "bnf-onto",
    "http://data.bnf.fr/vocabulary/roles/": "bnfroles",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://dublincore.org/documents/dcmi-box/": "dcmi-box",
    "http://purl.org/dc/dcmitype/": "dcmitype",
    "http://purl.org/dc/terms/": "dcterms",
    "http://xmlns.com/foaf/0.1/": "foaf",
    "http://rdvocab.info/uri/schema/FRBRentitiesRDA/": "frbr-rda",
    "http://data.bnf.fr/vocabulary/musical-genre/": "genremus",
    "http://www.w3.org/2003/01/geo/wgs84_pos#": "geo",
    "http://www.geonames.org/ontology#": "geonames",
    "http://data.ign.fr/ontology/topo.owl#": "ign",
    "http://rdf.insee.fr/geo/": "insee",
    "http://isni.org/ontology#": "isni",
    "http://id.loc.gov/vocabulary/relators/": "marcrel",
    "http://purl.org/ontology/mo/": "mo",
    "http://www.openarchives.org/ore/terms/": "ore",
    "http://www.w3.org/2002/07/owl#": "owl",
    "http://rdvocab.info/Elements/": "rdagroup1elements",
    "http://rdvocab.info/ElementsGr2/": "rdagroup2elements",
    "http://rdvocab.info/RDARelationshipsWEMI/": "rdarelationships",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://schema.org/": "schemaorg",
    "http://www.w3.org/2004/02/skos/core#": "skos"}


def extract_data(report):
    classes = extract_classes()
    dict_data_model = {}
    for classe in classes:
        print("Extraction classe ", classe)
        dict_data_model[classe] = analyse_classe(classe)
    pprint(dict_data_model)
    report.write(str(dict_data_model))

def extract_classes():
    query = """select distinct ?class where {
  ?thing a ?class
}"""
    classes_temp = sparql2list(SPARQLEndpoint, query)
    classes = [el[0] for el in classes_temp]
    return classes


def analyse_classe(classe):
    # Pour une classe d'objet donnée, on analyse les propriétés et sous-domaines
    dict_class = {"prop": []}
    nb_instances = count_occ(classe)
    dict_class["nb_instances"] = nb_instances
    if nb_instances:
        prop_subdomains = extract_subdomains(classe)
        for el in prop_subdomains:
            prop = el[0]
            for n in ns:
                prop = prop.replace(n, f"{ns[n]}:")
            dict_class["prop"].append([prop, int(el[1])])
    return dict_class


def count_occ(classe):
    query = """select count(?thing) where {
  ?thing a <""" + classe + """>.
}"""
    nb_instances = int(sparql2list(SPARQLEndpoint, query)[0][0])
    return nb_instances

def extract_subdomains(classe):
    # Pour une classe donnée : on extrait la liste de ses propriétés
    # et les types d'objets qui sont en sous-domaines
    query = """select ?prop (count(?subdomain) as ?occ_subdomains) where {
  ?thing a <""" + classe + """>.
  ?thing ?prop ?val.
  ?val a ?subdomain.
}"""
    results = sparql2list(SPARQLEndpoint, query)
    return results


def sparql2list(endpoint, sparql_query):
    sparql = SPARQLWrapper(endpoint)
    """
    En entrée, une requête Sparql
    En sortie, les résultats sous forme de dataset
    """
    url = f"{SPARQLEndpoint}?default-graph-uri=&query={urllib.parse.quote(sparql_query)}\
&format=text%2Ftab-separated-values&timeout=0&should-sponge=&debug=on"
    list_results = file2list(url, True)
    list_results.pop(0)
    j = 0
    for row in list_results:
        if type(row) == list:
            i = 0
            for el in row:
                if el[0] == '"':
                    el = el[1:]
                if el[-1] == '"':
                    el = el[:-1]
                row[i] = el
                i += 1
        else:
            if row[0] == '"':
                row = row[1:]
            if row[-1] == '"':
                row = row[:-1]
            list_results[j] = row
            j += 1
    return list_results


if __name__ == "__main__":
    print(explain)
    report = create_file(input("Nom du fichier de résultats : "))
    extract_data(report)