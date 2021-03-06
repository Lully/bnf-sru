# -*- coding: utf-8 -*-
"""
Created on Thu May 31 09:30:13 2018

@author: BNF0017855
"""
 
import csv
from unidecode import unidecode
from lxml import etree
import http.client
from urllib import request
import urllib.parse
import urllib.error as error
from collections import defaultdict
from SPARQLWrapper import SPARQLWrapper, JSON



ns = {"srw":"http://www.loc.gov/zing/srw/", "mxc":"info:lc/xmlns/marcxchange-v2", "m":"http://catalogue.bnf.fr/namespaces/InterXMarc","mn":"http://catalogue.bnf.fr/namespaces/motsnotices"}
urlSRUroot = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query="
sparql = SPARQLWrapper("http://data.bnf.fr/sparql")

chiffers = ["0","1","2","3","4","5","6","7","8","9"]
letters = ["a","b","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
punctuation = [".",",",";",":","?","!","%","$","£","€","#","\\","\"","&","~","{","(","[","`","\\","_","@",")","]","}","=","+","*","\/","<",">",")","}"]

libelle2methode = defaultdict(str)

def file2alignment(input_filename):
    outputfile = open(input_filename[:-4]+"-alignements.txt","w",encoding="utf-8")
    with open(input_filename, newline="\n", encoding='utf-8') as csvfile:
        file = csv.reader(csvfile, delimiter="\t")
        i = 0
        for row in file:
            row2alignment(row[0], outputfile, i)
            i += 1
            

def row2alignment(row, outputfile, i):
    liste_ark, methode = accesspoint2ark(row)
    if (liste_ark):
        libelle2methode[row] = methode
    line = [row, str(len(liste_ark)), " ".join(liste_ark), libelle2methode[row]]
    print(i, "-", row, liste_ark)
    outputfile.write("\t".join(line) + "\n")



def oldnumber2ark(dic_liste_fields):
    liste_ark = []
    query = liste_fields2query(dic_liste_fields)
    url_sru = url_requete_sru(query,"intermarcxchange")
    (test,records) = testURLetreeParse(url_sru)
    if (test):
        for record in records.xpath("//mxc:record",namespaces=ns):
            ark = record.get("id")
            liste_ark.append(ark)
    return liste_ark


def accesspoint2ark(accesspoint):
    liste_ark, methode = accesspoint2sparql(accesspoint)
    if (liste_ark == []):
        query = liste_fields2query(accesspoint)
        url_sru = url_requete_sru(query, "intermarcxchange")
        (test,records) = testURLetreeParse(url_sru)
        if (test):
            for record in records.xpath("//mxc:record", namespaces=ns):
                ark = record.get("id")
                liste_ark.append(ark)
        if liste_ark:
            methode = "Point d'accès > SRU"
    liste_ark = list(set(liste_ark))
    return liste_ark, methode


def row2fields(row):
    dico = []
    liste_row = [el for el in row.split("$") if el != ""]
    for el in liste_row:
        #el = el[0] + clean_string(el[2:])
        el = el[0] + el[2:]
        dico.append(el)
    return dico


def liste_fields2query(accesspoint):
    query = 'aut.accesspoint adj "' + accesspoint + '"'
    return query


# =============================================================================
# Ensemble de fonctions utilitaires
# =============================================================================

def testURLetreeParse(url):
    test = True
    resultat = ""
    try:
        resultat = etree.parse(request.urlopen(url))
    except etree.XMLSyntaxError as err:
        print(url)
        print(err)
        test = False
    except etree.ParseError as err:
        print(url)
        print(err)
        test = False
    except error.URLError as err:
        print(url)
        print(err)
        test = False
    except ConnectionResetError as err:
        print(url)
        print(err)
        test = False
    except TimeoutError as err:
        print(url)
        print(err)
        test = False
    except http.client.RemoteDisconnected as err:
        print(url)
        print(err)
        test = False
    except http.client.BadStatusLine as err:
        print(url)
        print(err)
        test = False
    except ConnectionAbortedError as err:
        print(url)
        print(err)
        test = False
    return (test,resultat)

def url_requete_sru(query,recordSchema="unimarcxchange",maximumRecords="1000",startRecord="1"):
    url = urlSRUroot + urllib.parse.quote(query) +"&recordSchema=" + recordSchema + "&maximumRecords=" + maximumRecords + "&startRecord=" + startRecord
    return url

def clean_string(string):
    for signe in punctuation:
        string = string.replace(signe," ")
    string = string.replace("  "," ")
    string = unidecode(string.lower())
    return string

def accesspoint2sparql(accesspoint):
    liste_uri = []
    methode = ""
    query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    select distinct ?concept where {
        {
        ?concept skos:prefLabel \"""" +  accesspoint + """\"@fr.
        } 
        UNION {
        ?concept skos:altLabel \"""" +  accesspoint + """\"@fr.
        }
    ?concept dcterms:isPartOf ?sous_ensemble_Rameau.
    }

    LIMIT 200
    """
    sparql.setQuery(query)
    try:
        sparql.setReturnFormat(JSON)
    except SPARQLWrapper.SPARQLExceptions.EndPointNotFound as err:
        print(err)
        print(query)
    try:
        results = sparql.query().convert()
        dataset = results["results"]["bindings"]

        for el in dataset:
            liste_uri.append(el.get("concept").get("value").replace("#about",""))
        liste_uri = list(set(liste_uri))
    except error.HTTPError as err:
        print(err)
        print(query)
    except SPARQLWrapper.SPARQLExceptions.EndPointNotFound as err:
        print(err)
        print(query)
    if (liste_uri):
        methode = "Point d'accès > SPARQL"
    return liste_uri, methode

if __name__ == "__main__":
    filename = input("Nom du fichier à importer : ")
    if (filename == ""):
        filename = "LK7_619_liste_concepts.tsv"
    file2alignment(filename)