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
            row2alignment(row[0],outputfile,i)
            i += 1
            

def row2alignment(row,outputfile, i):
    dic_liste_fields = row2fields(row)
    liste_ark = []
    if (i != 0 and dic_liste_fields[0][0] == "1"):
        #print("alors alignement par ancien numéro de notices")
        liste_ark = oldnumber2ark(dic_liste_fields)
        libelle2methode[row] = "ancien numéro > SRU"
    if (i != 0 and liste_ark == []):
        liste_ark = accesspoint2ark(dic_liste_fields)
        libelle2methode[row] = "Point d'accès > Sparql/SRU"
    line = [row,str(len(liste_ark))," ".join(liste_ark), libelle2methode[row]]
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

def accesspoint2ark(dic_liste_fields):
    liste_ark = []
    dic_sans_id = []
    for el in dic_liste_fields:
            if (el[0] != "1"):
                dic_sans_id.append(el)
    liste_ark = accesspoint2sparql(dic_sans_id)
    if (liste_ark == []):
        query = liste_fields2query(dic_sans_id)
        url_sru = url_requete_sru(query,"intermarcxchange")
        (test,records) = testURLetreeParse(url_sru)
        if (test):
            for record in records.xpath("//mxc:record",namespaces=ns):
                ark = record.get("id")
                liste_ark.append(ark)
    return liste_ark
    

def row2fields(row):
    dico = []
    liste_row = [el for el in row.split("$") if el != ""]
    for el in liste_row:
        #el = el[0] + clean_string(el[2:])
        el = el[0] + el[2:]
        dico.append(el)
    return dico
  
def liste_fields2query(dic_liste_fields):
    query = []
    for el in dic_liste_fields:
        if (el[0] == "1"):
            query.append('aut.anywhere all "' + el[1:] + '*"')
        else:
            query.append('aut.accesspoint all "' + el[1:] + '"')
    query = " and ".join(query)
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

def accesspoint2sparql(dic_fields):
        accesspoint = " -- ".join(el[1:] for el in dic_fields if el != ["gFrance"])
        liste_uri = []
        
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
          UNION
          {
          ?concept foaf:name \"""" +  accesspoint + """\"@fr.
          } 
          UNION
          {
          ?concept skos:prefLabel \"""" +  accesspoint + """\".
          } 
          UNION {
          ?concept skos:altLabel \"""" +  accesspoint + """\".
          }
          UNION
          {
          ?concept foaf:name \"""" +  accesspoint + """\".
          } 

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
    
        
        return liste_uri

if __name__ == "__main__":
    filename = input("Nom du fichier à importer : ")
    if (filename == ""):
        filename = "LK7_619_liste_concepts.tsv"
    file2alignment(filename)