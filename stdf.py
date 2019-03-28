# coding: utf-8

"""
Ensemble de fonctions standard pour la génération de rapports
la manipulation de fichiers, etc.
"""
import csv
from urllib import request, error
from pprint import pprint

from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions

import SRUextraction as sru

def create_file(filename, mode="w", headers=[], display=True):
    """
    Crée un fichier à partir d'un nom. 
    Renvoie le fichier en objet
    """
    file = open(filename, mode, encoding="utf-8")
    if headers:
        if display:
            print(headers)
        file.write("\t".join(headers) + "\n")
    return file

def file2dict(inputfilename, col_key=0, col_val=-1):
    """
    Convertit un fichier en dictionnaire : prend la 1ère colonne comme clé
    et la colonne 'col' comme valeur
    """
    dict = {}
    with open(inputfilename, encoding="utf-8") as  csvfile:
        entry_file = csv.reader(csvfile, delimiter='\t')
        for row in entry_file:
            dict[row[col_key]] = row[col_val]
    return dict


def close_files(files_list):
    for file in files_list:
        file.close()


def nn2ark(nna_nnb):
    """
    Convertit un NNB ou un NNA en ARK
    En entrée, le NNB ou NNA, nettoyé, de type str
    """
    type = "bib"
    if (nna_nnb.startswith("1") or nna_nnb.startswith("2")):
        type = "aut"
    query = f'{type}.recordid any "{nna_nnb}"'
    if (type == "aut"):
        query += ' and aut.status any "sparse validated"'
    results = sru.SRU_result(query)
    return results.list_identifiers


def input2outputfile(inputfilename, suffix):
    """
    A partir d'un nom de fichier (TXT ou CSV en général) en entrée,
    génération d'un fichier d'écriture en sortie, avec ajout d'un suffixe
    """
    outputfilename = inputfilename[:-4] + "-" + suffix + ".txt"
    outputfile = create_file(outputfilename)
    return outputfile


def line2report(line, report, i=0, display=True):
    """
    Envoie une line (liste) dans un fichier.
    Sauf demande contraire, affiche la ligne
    dans le terminal avec un compteur
    """
    if display:
        if i:
            print(i, line)
        else:
            print(line)
    report.write("\t".join(line) + "\n")


def ddprint(defaultdict):
    """
    Formation d'impression de defaultdict (pprint ne le prévoit pas)
    """
    tempdict = dict(defaultdict)
    pprint(tempdict)
    return tempdict


def file2list(filename):
    liste = []
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for row in content:
            liste.append(row[0])
    return liste


def sparql2dict(endpoint, sparql_query, liste_el):
    sparql = SPARQLWrapper(endpoint)
    """
    En entrée, une requête Sparql et la liste des variables
    à récupérer. La première de ces variables est la clé dans le dictionnaire
    Les autres correspondent à des listes (plusieurs valeurs possibles)
    {"ark:///": {
                 "id_wikidata": ["Q6321654", "QS321"]   
                 "coordonnees_geo": ["48.54656, 12.354684", "45.156165, 27.5165165"]
                 }
    }
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

def ark2nn(ark_catalogue):
    nn = ark_catalogue[ark_catalogue.find("ark:/")+13:-2]
    return nn

def uri2label(uri, prop="skos:prefLabel", sparql_endpoint="https://data.bnf.fr/sparql"):
    """
    A partir d'une URI, récupère 1 propriété (le label)
    """
    ns = {"bibo" : "http://purl.org/ontology/bibo/",
          "bio" : "http://purl.org/vocab/bio/0.1/",
          "bnf-onto" : "http://data.bnf.fr/ontology/bnf-onto/",
          "dbpedia-owl" : "http://dbpedia.org/ontology/",
          "dbpprop" : "http://dbpedia.org/property/",
          "dc" : "http://purl.org/dc/elements/1.1/",
          "dcterms" : "http://purl.org/dc/terms/",
          "dctype" : "http://purl.org/dc/dcmitype/",
          "fb" : "http://rdf.freebase.com/ns/",
          "foaf" : "http://xmlns.com/foaf/0.1/",
          "frbr" : "http://purl.org/vocab/frbr/core#",
          "gr" : "http://purl.org/goodrelations/v1#",
          "isbd" : "http://iflastandards.info/ns/isbd/elements/",
          "isni" : "http://isni.org/ontology#",
          "marcrel" : "http://id.loc.gov/vocabulary/relators/",
          "owl" : "http://www.w3.org/2002/07/owl#",
          "rdac" : "http://rdaregistry.info/Elements/c/",
          "rdae" : "http://rdaregistry.info/Elements/e/",
          "rdaelements" : "http://rdvocab.info/Elements/",
          "rdafrbr1" : "http://rdvocab.info/RDARelationshipsWEMI/",
          "rdafrbr2" : "http://RDVocab.info/uri/schema/FRBRentitiesRDA/",
          "rdai" : "http://rdaregistry.info/Elements/i/",
          "rdam" : "http://rdaregistry.info/Elements/m/",
          "rdau" : "http://rdaregistry.info/Elements/u/",
          "rdaw" : "http://rdaregistry.info/Elements/w/",
          "rdf" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
          "rdfs" : "http://www.w3.org/2000/01/rdf-schema#",
          "skos" : "http://www.w3.org/2004/02/skos/core#"
          }
    prefix_prop = prop.split(":")[0]
    query_ns = f"PREFIX {prefix_prop}: <{ns[prefix_prop]}>\n"
    query = query_ns + """
select ?value where {
    <""" + uri + """> """ + prop + """ ?value.
}
""" 
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    label = ""
    try:
        results = sparql.query().convert()
        dataset = results["results"]["bindings"]
        for el in dataset:
            label = el["value"]["value"]
    except error.HTTPError as err:
        print(err)
        print(query)
    except SPARQLExceptions.EndPointNotFound as err:
        print(err)
        print(query)
    return label


def proxy_opener():
    """
    Utilisation du proxy pour les requêtes HTTP/HTTPS
    """
    proxies = {"http":"fw_in.bnf.fr:8080",
               "https": "fw_in.bnf.fr:8080"}
      
    proxy_handler = request.ProxyHandler(proxies)
    # construct a new opener using your proxy settings
    opener = request.build_opener(proxy_handler)
    # install the opener on the module-level
    request.install_opener(opener)
