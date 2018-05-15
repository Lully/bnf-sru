# -*- coding: utf-8 -*-
"""
Created on Tue May 15 13:45:46 2018

@author: Lully
"""

from lxml import etree
import http.client
from urllib import request
import urllib.parse
from unidecode import unidecode
import urllib.error as error
from collections import defaultdict
import csv

ns = {"srw":"http://www.loc.gov/zing/srw/", "mxc":"info:lc/xmlns/marcxchange-v2", "m":"http://catalogue.bnf.fr/namespaces/InterXMarc","mn":"http://catalogue.bnf.fr/namespaces/motsnotices"}
sruroot = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query="

url_access_pbs = []
listeNNAdefault = ["33129956"]

report_headers = ["NNA","NNB","Cas","Zone 750 actuelle",
                  "Zone 245 actuelle","nouveau 750 ind2","Nouvelle 245",
                  "Présence d'un 245$r ?"]

def testURLetreeParse(url):
    test = True
    resultat = ""
    try:
        resultat = etree.parse(request.urlopen(url))
    except etree.XMLSyntaxError as err:
        print(url)
        print(err)
        url_access_pbs.append([url,"etree.XMLSyntaxError"])
        test = False
    except etree.ParseError as err:
        print(url)
        print(err)
        test = False
        url_access_pbs.append([url,"etree.ParseError"])
    except error.URLError as err:
        print(url)
        print(err)
        test = False
        url_access_pbs.append([url,"urllib.error.URLError"])
    except ConnectionResetError as err:
        print(url)
        print(err)
        test = False
        url_access_pbs.append([url,"ConnectionResetError"])
    except TimeoutError as err:
        print(url)
        print(err)
        test = False
        url_access_pbs.append([url,"TimeoutError"])
    except http.client.RemoteDisconnected as err:
        print(url)
        print(err)
        test = False
        url_access_pbs.append([url,"http.client.RemoteDisconnected"])
    except http.client.BadStatusLine as err:
        print(url)
        print(err)
        test = False
        url_access_pbs.append([url,"http.client.BadStatusLine"])
    except ConnectionAbortedError as err:
        print(url)
        print(err)
        test = False
        url_access_pbs.append([url,"ConnectionAbortedError"])
    return (test,resultat)

def url_requete_sru(query,recordSchema="intermarcxchange",maximumRecords="1000",startRecord="1"):
    url = sruroot + urllib.parse.quote(query) +"&recordSchema=" + recordSchema + "&maximumRecords=" + maximumRecords + "&startRecord=" + startRecord
    return url

def clean_string(string):
    """Nettoyage de tous les signes de ponctuation (sauf le point)"""
    ponctuation = [",",";",":","?","!","%","$","£","€","#","\\","\"","&","~","{","(","[","`","\\","_","@",")","]","}","=","+","*","\/","<",">",")","}"]
    #for signe in ponctuation:
    #    string = string.replace(signe,"")
    string = unidecode(string.lower())
    return string
        
def record2meta(record,field_subfield):
    val = []
    field = field_subfield("$")[0]
    subfield = field_subfield("$")[1]
    path = 'mxc:datafield[@tag="' + field + '"]/mxc:subfield[@code=' + subfield + '"]'
    for occ in record.xpath(path, namespaces=ns):
        val.append(occ.text)
    val = " ".join([c for c in val if c != ""])
    return val

def instanceOfInt(string):
    test = True
    try:
        isinstance(int(string),"int")
    except ValueError:
        test = False
    return test

def roman_to_int(n):
    numeral_map = tuple(zip(
    (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
    ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
    ))
    i = result = 0
    for integer, numeral in numeral_map:
        while n[i:i + len(numeral)] == numeral:
            result += integer
            i += len(numeral)
    test = True
    if (result == 0):
        test = False
    return test


def test_tomaison(string):
    """Vérifie si la chaîne de caractère qu'on lui envoie
    est un nombre en chiffres arabes ou romains"""
    test = instanceOfInt(string)
    if (test == False):
        test = roman_to_int(string)
    return False

def restructuration245i(f245a):
    return f245a

def analyse_cas1(f750,record,nna,outputfile,position750,nb_750_sansind2):
    """Cas des monographies en plusieurs volumes. Exemple : 32362406
    Cible : générer un 245$i
    Exemple avec plusieurs parties successives : 30977029 
    --> identifiables parce que le 750$a commence par un chiffre romain 
            -> sera à reprendre à la main"""
    test = False
    f750a = f750.find("mxc:subfield[@code='a']",namespaces=ns)
    f245a = record2meta(record,"245$a")
    f245r = record2meta(record,"245$r")
    f750a_clean = clean_string(f750a)
    f245a_clean = clean_string(f245a)
    if (f245a_clean.find(f750a_clean) > 4):
        #On cherche si le titre 750 est présent en 245$a
        #Si c'est le cas, on regarde si juste avant ce titre se trouve
        #un point, et juste avant ce point, un nombre en chiffres arabes ou romains
        #Si c'est le cas, on a un titre de partie en 245$a, repris en 750$a
        debut_245a = f245a_clean[0:f245a_clean.find(f750a_clean)].strip()
        last_car = debut_245a[-1]
        if (last_car == "."):
            debut_245a_decoupage = debut_245a[:-1].split(" ")
            test = test_tomaison(debut_245a_decoupage[-1])
    
    if (test):
        #Si le test est positif -> on génère une ligne "Cas 1" dans le rapport
        arkbib = record.get("id")
        cas = "1"
        nouveau_245 = restructuration245i(f245a)
        nouveau_750ind2 = "Supprimer"
        line = [nna,arkbib,cas,f750a,f245a,nouveau_750ind2,nouveau_245,f245r]
    return test

def analyse_cas2(f750,record,nna,outputfile,position750,nb_750_sansind2):
    """Quand la 750 $a est présente en $e (attention : il peut y avoir plusieurs $e : 34137837)
    Cible : 750 ind2 = 3"""
    test = False
    return test

def analyse_cas3(f750,record,nna,outputfile,position750,nb_750_sansind2):
    """Quand ORG. Cible : restructuration de la 245, suppression de la 750"""
    test = False
    return test

def analyse_cas4(f750,record,nna,outputfile,position750,nb_750_sansind2):
    """Quand la barre de classement est précédée d'une chaîne de caractères qu'on retrouve à l'identique en 750 (exemple : 31842412)"""
    test = False
    return test

def analyse_cas5(f750,record,nna,outputfile,position750,nb_750_sansind2):
    """titre forgé par l'éditeur
    Exemple : 39091229
    "L'ordre moral" présent en 245$i et 750$a
    Sortir à part les "oeuvres complètes"""
    test = False
    return test

def default_report(f750,record,nna,outputfile,position750,nb_750_sansind2):
    line = [nna,record.get("id")]
    outputfile("\t".join(line) + "\n")

def f750_analysis(f750,record,nna,outputfile,position750,nb_750_sansind2):
    """A partir d'une zone 750, analyse le cas auquel il correspond"""
    testcas1 = False
    testcas2 = False
    testcas3 = False
    testcas4 = False
    testcas5 = False
    testcas1 = analyse_cas1(f750,record,nna,outputfile,position750,nb_750_sansind2)
    if (testcas1 == False):
        testcas2 = analyse_cas2(f750,record,nna,outputfile,position750,nb_750_sansind2)
    if (testcas2 == False):
        testcas3 = analyse_cas3(f750,record,nna,outputfile,position750,nb_750_sansind2)
    if (testcas3 == False):
        testcas4 = analyse_cas4(f750,record,nna,outputfile,position750,nb_750_sansind2)
    if (testcas4 == False):
        testcas5 = analyse_cas5(f750,record,nna,outputfile,position750,nb_750_sansind2)
    if (testcas5 == False):
        default_report(f750,record,nna,outputfile,position750,nb_750_sansind2)

def record_to_750(record,nna,outputfile):
    nb_750 = 0
    for f750 in record.xpath("mxc:datafield[@tag='750']",namespaces=ns):
        if (f750.get("ind2") == " "):
            nb_750 += 1
    for f750 in record.xpath("mxc:datafield[@tag='750']",namespaces=ns):
        i = 1
        if (f750.get("ind2") == " "):
            f750_analysis(f750,record,nna,outputfile,i,nb_750)
        i += 1

def nna_to_750(nna,outputfile):
    (test,firstpage) = testURLetreeParse(url_requete_sru('bib.author2bib all "' + nna + '"'))
    if (test):
        nb_resultats = int(firstpage.find("//srw:numberOfRecords",namespaces=ns).text)
        for record in firstpage.xpath("//mxc:record",namespaces=ns):
            record_to_750(record,nna,outputfile)
        i = 1
        while ((i+999) < nb_resultats):
            (test,page) = testURLetreeParse(url_requete_sru('bib.author2bib all "' + nna + '"', startRecord=str(i+1000)))
            i += 1000
            if (test):
                for record in page.xpath.xpath("//mxc:record",namespaces=ns):
                    record_to_750(record,nna,outputfile)
            
def listeNna2750(filename):
    """En entrée : fichier contenant une liste de NNA.
    Pour chaque NNA, ouvre chaque notice comme auteur, et regarde si présence
    d'une zone 750.
    Si c'est le cas, identification d'un cas (pour chaque 750)"""
    output_filename = filename[:-4] + "-750.txt"
    ouptputfile = open(output_filename,"w",encoding="utf-8")
    ouptputfile.write("\t".join(report_headers) + "\n")
    if (filename != ""):
        with open(filename, newline='\n',encoding="utf-8") as csvfile:
            entry_file = csv.reader(csvfile, delimiter='\t')
            for nna in entry_file:
                nna_to_750(nna,ouptputfile)
    else:
        for NNA in listeNNAdefault:
            nna_to_750(nna,ouptputfile)
            

if __name__ == '__main__':
    input_filename = input("Fichier contenant la liste de NNA en entrée : ")

    listeNna2750(input_filename)
    