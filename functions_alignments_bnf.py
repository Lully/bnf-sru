# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 05:38:21 2017

@author: Lully

Fonctions communes aux programmes d'alignement avec les données de la BnF
"""

from lxml import etree
from urllib import request
import urllib.parse
from unidecode import unidecode
import urllib.error as error
import csv
import tkinter as tk
from collections import defaultdict
import re

#Quelques listes de signes à nettoyer
listeChiffres = ["0","1","2","3","4","5","6","7","8","9"]
lettres = ["a","b","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
ponctuation = [".",",",";",":","?","!","%","$","£","€","#","\\","\"","&","~","{","(","[","`","\\","_","@",")","]","}","=","+","*","\/","<",">",")","}"]

ns = {"srw":"http://www.loc.gov/zing/srw/", "mxc":"info:lc/xmlns/marcxchange-v2", "m":"http://catalogue.bnf.fr/namespaces/InterXMarc","mn":"http://catalogue.bnf.fr/namespaces/motsnotices"}
nsOCLC = {"xisbn": "http://worldcat.org/xid/isbn/"}
nsSudoc = {"rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#", "bibo":"http://purl.org/ontology/bibo/", "dc":"http://purl.org/dc/elements/1.1/", "dcterms":"http://purl.org/dc/terms/", "rdafrbr1":"http://rdvocab.info/RDARelationshipsWEMI/", "marcrel":"http://id.loc.gov/vocabulary/relators/", "foaf":"http://xmlns.com/foaf/0.1/", "gr":"http://purl.org/goodrelations/v1#", "owl":"http://www.w3.org/2002/07/owl#", "isbd":"http://iflastandards.info/ns/isbd/elements/", "skos":"http://www.w3.org/2004/02/skos/core#", "rdafrbr2":"http://RDVocab.info/uri/schema/FRBRentitiesRDA/", "rdaelements":"http://rdvocab.info/Elements/", "rdac":"http://rdaregistry.info/Elements/c/", "rdau":"http://rdaregistry.info/Elements/u/", "rdaw":"http://rdaregistry.info/Elements/w/", "rdae":"http://rdaregistry.info/Elements/e/", "rdam":"http://rdaregistry.info/Elements/m/", "rdai":"http://rdaregistry.info/Elements/i/", "sudoc":"http://www.sudoc.fr/ns/", "bnf-onto":"http://data.bnf.fr/ontology/bnf-onto/"}


#fonction de mise à jour de l'ARK s'il existe un ARK
def ark2ark(NumNot,ark):
    url = url_requete_sru("bib.ark%20all%20%22" + urllib.parse.quote(ark) + "%22", 
                          "unimarcxchange", 
                          "20", 
                          "1")
    page = etree.parse(url)
    nv_ark = ""
    if (page.find("//srw:recordIdentifier", namespaces=ns) is not None):
        nv_ark = page.find("//srw:recordIdentifier", namespaces=ns).text
    return nv_ark

#nettoyage des chaines de caractères (titres, auteurs, isbn) : suppression ponctuation, espaces (pour les titres et ISBN) et diacritiques
def nettoyage(string,remplacerEspaces=True,remplacerTirets=True):
    string = unidecode(string.lower())
    for signe in ponctuation:
        string = string.replace(signe,"")
    string = string.replace("'"," ")
    if (remplacerEspaces == True):
        string = string.replace(" ","")
    if (remplacerTirets == True):
        string = string.replace("-","")
    return string

def nettoyageTitrePourControle(titre):
    titre = nettoyage(titre,True)
    return titre
    
def nettoyageTitrePourRecherche(titre):
    titre = nettoyage(titre,False)
    titre = nettoyageAuteur(titre,False)
    return titre
    

def nettoyageIsbnPourControle(isbn):
    isbn = nettoyage(isbn)
    if (len(isbn) < 10):
        isbn = ""
    elif (isbn[0:3] == "978" or isbn[0:3] == "979"):
        isbn = isbn[3:12]
    else:
        isbn = isbn[0:10]
    return isbn

def nettoyageAuteur(auteur,justeunmot=True):
    listeMots = ["par","avec","by","Mr.","M.","Mme","Mrs"]
    for mot in listeMots:
        auteur = auteur.replace(mot,"")
    for chiffre in listeChiffres:
        auteur = auteur.replace(chiffre,"")
    auteur = nettoyage(auteur.lower(),False)
    auteur = auteur.split(" ")
    auteur = sorted(auteur,key=len,reverse=True)
    auteur = [auteur1 for auteur1 in auteur if len(auteur1) > 1]
    if (auteur is not None and auteur != []):
        if (justeunmot==True):
            auteur = auteur[0]
        else:
            auteur = " ".join(auteur)
    else:
        auteur = ""
    return auteur

def nettoyageDate(date):
    date = unidecode(date.lower())
    for lettre in lettres:
        date.replace(lettre,"")
    for signe in ponctuation:
        date = date.split(signe)
        date = " ".join(annee for annee in date if annee != "")
    return date
    
    

#Si la recherche NNB avec comporaison Mots du titre n'a rien donné, on recherche sur N° interne BnF + Auteur (en ne gardant que le mot le plus long du champ Auteur)
def relancerNNBAuteur(NumNot,systemid,isbn,titre,auteur,date):
    listeArk = []
    if (auteur != "" and auteur is not None):
        urlSRU = url_requete_sru('bib.author all "' + auteur + '" and bib.otherid all "' + systemid + '"',
                                 "unimarcxchange",
                                 "1000",
                                 "1")
        pageSRU = etree.parse(urlSRU)
        for record in pageSRU.xpath("//srw:records/srw:record", namespaces=ns):
            ark = record.find("srw:recordIdentifier", namespaces=ns).text
            listeArk.append(ark)
    listeArk = ",".join(listeArk)
    return listeArk
        
    

#Quand on a trouvé l'ancien numéro système dans une notice BnF : 
#on compare l'ISBN de la notice de la Bibliothèque avec celui de la BnF pour voir si ça colle
#à défaut, on compare les titres (puis demi-titres)
def comparerBibBnf(NumNot,ark_current,systemid,isbn,titre,auteur,date):
    ark = ""
    recordBNF = etree.parse(url_requete_sru('bib.ark all "' + ark_current + '"',
                                            "unimarcxchange",
                                            "20",
                                            "1"))
    ark =  comparaisonIsbn(NumNot,ark_current,systemid,isbn,titre,auteur,date,recordBNF)
    if (ark == ""):
        ark = comparaisonTitres(NumNot,ark_current,systemid,isbn,titre,auteur,date,recordBNF)
    return ark

def comparaisonIsbn(NumNot,ark_current,systemid,isbn,titre,auteur,date,recordBNF):
    ark = ""
    isbnBNF = extract_meta(recordBNF,"010$a","first")
    if (recordBNF.find("//mxc:datafield[@tag='010']/mxc:subfield[@code='a']", namespaces=ns) is not None):
        isbnBNF = nettoyage(recordBNF.find("//mxc:datafield[@tag='010']/mxc:subfield[@code='a']", namespaces=ns).text)
    if (isbn != "" and isbnBNF != ""):
        if (isbn in isbnBNF):
            ark = ark_current
    return ark

def comparaisonTitres(NumNot,ark_current,systemid,isbn,titre,auteur,date,recordBNF):
    ark = ""
    titreBNF = nettoyage(recordBNF,"200$a","first")
    """if (recordBNF.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='a']", namespaces=ns) is not None):
        if (recordBNF.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='a']", namespaces=ns).text is not None):
            titreBNF = nettoyage(recordBNF.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='a']", namespaces=ns).text)"""
    if (titre != "" and titreBNF != ""):
        if (titre == titreBNF):
            ark = ark_current
            if (len(titre) < 5):
                ark += "[titre court]"
        elif(titre[0:round(len(titre)/2)] == titreBNF[0:round(len(titre)/2)]):
            ark = ark_current
            if (round(len(titre)/2)<10):
                ark += "[demi-titre" + "-" + str(round(len(titre)/2)) + "caractères]"
        elif(titre.find(titreBNF) > -1):
            ark = ark_current
        elif (titreBNF.find(titre) > -1):
            ark = ark_current
    return ark
            
def extract_meta(recordBNF,field_subfield,occ="all",anl=False):
    assert field_subfield.find("$") == 3
    assert len(field_subfield) == 5
    field = field_subfield.split("$")[0]
    subfield = field_subfield.split("$")[1]
    value = []
    path = "//srw:recordData/mxc:record/mxc:datafield[@tag='" + field + "']/mxc:subfield[@code='"+ subfield + "']"
    for elem in recordBNF.xpath(path,namespaces = ns):
        if (elem.text is not None):
            value.append(elem.text)
    if (occ == "first"):
        value = value[0]
    elif (occ == "all"):
        value = " ".join(value)
    return value

def url_requete_sru(query,recordSchema,maximumRecords,startRecord):
    url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query="
    + urllib.parse.quote(query) 
    + "&recordSchema=" + recordSchema 
    + "&maximumRecords=" + maximumRecords
    + "&startRecord=" + startRecord
    return url

#Recherche par n° système. Si le 3e paramètre est "False", c'est qu'on a pris uniquement le FRBNF initial, sans le tronquer. 
#Dans ce cas, et si 0 résultat pertinent, on relance la recherche avec info tronqué
def systemid2ark(NumNot,systemid,tronque,isbn,titre,auteur,date):
    query = 'bib.otherid all "' + systemid + '"'    
    url = url_requete_sru(query,"intermarcxchange","1000","1")
    #url = "http://catalogueservice.bnf.fr/SRU?version=1.2&operation=searchRetrieve&query=NumNotice%20any%20%22" + systemid + "%22&recordSchema=InterXMarc_Complet&maximumRecords=1000&startRecord=1"
    page = etree.parse(url)
    listeARK = []
    for record in page.xpath("//srw:records/srw:record", namespaces=ns):
        ark_current = record.find("srw:recordIdentifier",namespaces=ns).text
        for zone9XX in record.xpath("srw:recordData/mxc:record/mxc:datafield", namespaces=ns):
            #print(ark_current)
            tag = zone9XX.get("tag")
            if (tag[0:1] =="9"):
                if (zone9XX.find("mxc:subfield[@code='a']", namespaces=ns) is not None):
                    if (zone9XX.find("mxc:subfield[@code='a']", namespaces=ns).text is not None):
                        if (zone9XX.find("mxc:subfield[@code='a']", namespaces=ns).text == systemid):
                            #print(zone9XX.get("tag"))
                            listeARK.append(comparerBibBnf(NumNot,ark_current,systemid,isbn,titre,auteur,date))
    listeARK = ",".join([ark1 for ark1 in listeARK if ark1 != ''])
    
#Si pas de réponse, on fait la recherche SystemID + Auteur
    if (listeARK == ""):
        listeARK = relancerNNBAuteur(NumNot,systemid,isbn,titre,auteur,date)
    listeARK = ",".join([ark1 for ark1 in listeARK.split(",") if ark1 != ''])
    
#Si à l'issue d'une première requête sur le numéro système dont on a conservé la clé ne donne rien -> on recherche sur le numéro tronqué comme numéro système
    if (listeARK == "" and tronque == False):
        systemid_tronque = systemid[0:len(systemid)-1]
        systemid2ark(NumNot,systemid_tronque, True,isbn,titre,auteur,date)   
    listeARK = ",".join([ark1 for ark1 in listeARK.split(",") if ark1 != ''])
    
    return listeARK

def rechercheNNB(NumNot,nnb,isbn,titre,auteur,date):
    ark = ""
    if (nnb.isdigit() is False):
        #pb_frbnf_source.write("\t".join[NumNot,nnb] + "\n")
        ark = "Pb FRBNF"
    elif (int(nnb) > 30000000 and int(nnb) < 50000000):
        url = url_requete_sru("bib.recordid%20any%20%22" + nnb + "%22","unimarcxchange","1000","1")
        page = etree.parse(url)
        for record in page.xpath("//srw:records/srw:record", namespaces=ns):
            ark_current = record.find("srw:recordIdentifier",namespaces=ns).text
            ark = comparerBibBnf(NumNot,ark_current,nnb,isbn,titre,auteur,date)
    return ark

#Si le FRBNF n'a pas été trouvé, on le recherche comme numéro système -> pour ça on extrait le n° système
def oldfrbnf2ark(NumNot,frbnf,isbn,titre,auteur,date):
    systemid = ""
    if (frbnf[0:5].upper() == "FRBNF"):
        systemid = frbnf[5:14]
    else:
        systemid = frbnf[4:13]
    ark = rechercheNNB(NumNot,systemid[0:8],isbn,titre,auteur,date)
    if (ark==""):
        ark = systemid2ark(NumNot,systemid,False,isbn,titre,auteur,date)
    return ark


#Rechercher le FRBNF avec le préfixe    
def frbnf2ark(NumNot,frbnf,isbn,titre,auteur,date):
    url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.otherid%20all%20%22" + frbnf + "%22&recordSchema=unimarcxchange&maximumRecords=1000&startRecord=1"
    page = etree.parse(url)
    nb_resultats = int(page.find("//srw:numberOfRecords", namespaces=ns).text)
    ark = ""
    if (nb_resultats == 0):
        ark = oldfrbnf2ark(NumNot,frbnf,isbn,titre,auteur,date)
    elif (nb_resultats == 1):
        ark = page.find("//srw:recordIdentifier", namespaces=ns).text
    else:
        ark = ",".join(page.xpath("//srw:recordIdentifier", namespaces=ns))
    return ark

        
def row2file(nb_fichiers_a_produire,nbARK,NumNot,frbnf,current_ark,ark,isbn,titre,auteur,date,unique_file_results_frbnf_isbn2ark):
    if (nb_fichiers_a_produire == 1):
        unique_file_results_frbnf_isbn2ark.write("\t".join([NumNot,str(nbARK),ark,frbnf,current_ark,isbn,titre,auteur,date]) + "\n")

def row2files(nb_fichiers_a_produire,nbARK,NumNot,frbnf,current_ark,ark,isbn,titre,auteur,date,multiple_files_pbFRBNF_ISBN,multiple_files_0_ark,multiple_files_1_ark,multiple_files_plusieurs_ark):
    if (ark == "Pb FRBNF"):
        multiple_files_pbFRBNF_ISBN.write("\t".join([NumNot,"",ark,frbnf,current_ark,isbn,titre,auteur,date]) + "\n")
    elif (nbARK == 0):
        multiple_files_0_ark.write("\t".join([NumNot,current_ark,isbn,titre,auteur,date]) + "\n")
    elif (nbARK == 1):
        multiple_files_1_ark.write("\t".join([NumNot,"1",ark,frbnf,current_ark,isbn,titre,auteur,date]) + "\n")
    else:
        multiple_files_plusieurs_ark.write("t".join([NumNot,str(nbARK),ark,frbnf,current_ark,isbn,titre,auteur,date]) + "\n")
        
def nettoyage_isbn(isbn):
    isbn_nett = isbn.split(";")[0].split(",")[0]
    isbn_nett = isbn_nett.replace("-","").replace(" ","")
    return isbn_nett
    
def conversionIsbn(isbn):
    longueur = len(isbn)
    isbnConverti = ""
    if (longueur == 10):
        isbnConverti == conversionIsbn1013(isbn)
    elif (longueur == 13):
        isbnConverti == conversionIsbn1310(isbn)    
    return isbnConverti

#conversion isbn13 en isbn10
def conversionIsbn1310(isbn):
    if (isbn[0:3] == "978"):
        prefix = isbn[3:-1]
        check = check_digit_10(prefix)
        return prefix + check
    else:
        return ""

#conversion isbn10 en isbn13
def conversionIsbn1013(isbn):
    prefix = '978' + isbn[:-1]
    check = check_digit_13(prefix)
    return prefix + check
    
def check_digit_10(isbn):
    assert len(isbn) == 9
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        w = i + 1
        sum += w * c
    r = sum % 11
    if (r == 10):
        return 'X'
    else: 
        return str(r)

def check_digit_13(isbn):
    assert len(isbn) == 12
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        if (i % 2):
            w = 3
        else: 
            w = 1
        sum += w * c
    r = 10 - (sum % 10)
    if (r == 10):
        return '0'
    else:
        return str(r)

def isbn2sru(NumNot,isbn,titre,auteur,date):
    urlSRU = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.isbn%20all%20%22" + isbn + "%22"
    resultats = etree.parse(urlSRU)
    listeARK = []
    for record in resultats.xpath("//srw:record", namespaces=ns):
        ark_current = record.find("srw:recordIdentifier", namespaces=ns).text
        recordBNF = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.ark%20all%20%22" + urllib.parse.quote(ark_current) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1")
        ark = comparaisonTitres(NumNot,ark_current,"",isbn,titre,auteur,date,recordBNF)
        listeARK.append(ark)
    listeARK = ",".join(listeARK)
    return listeARK

def isbn2sudoc(NumNot,isbn,isbnConverti,titre,auteur):
    url = "https://www.sudoc.fr/services/isbn2ppn/" + isbn
    Listeppn = []

    #page = etree.parse(url)
    isbnTrouve = True
    ark = ""
    try:
        request.urlretrieve(url)
    except error.HTTPError as err:
        isbnTrouve = False
    if (isbnTrouve == True):
        resultats = etree.parse(request.urlopen(url))
        for ppn in resultats.xpath("//ppn"):
            ppn_val = resultats.find("//ppn").text
            Listeppn.append("PPN" + ppn_val)
            ark = ppn2ark(NumNot,ppn_val,isbn,titre,auteur)
        if (ark == ""):
            url = "https://www.sudoc.fr/services/isbn2ppn/" + isbnConverti
            try:
                request.urlretrieve(url)
            except error.HTTPError as err:
                isbnTrouve = False
            if (isbnTrouve == True):
                resultats = etree.parse(request.urlopen(url))
                for ppn in resultats.xpath("//ppn"):
                    ppn_val = resultats.find("//ppn").text
                    Listeppn.append("PPN" + ppn_val)
                    ark = ppn2ark(NumNot,ppn_val,isbnConverti,titre,auteur)
    #Si on trouve un PPN, on ouvre la notice pour voir s'il n'y a pas un ARK déclaré comme équivalent --> dans ce cas on récupère l'ARK
    Listeppn = ",".join(Listeppn)
    if (ark != ""):
        return ark
    else:
        return Listeppn

def ppn2ark(NumNot,ppn,isbn,titre,auteur):
    record = etree.parse(request.urlopen("http://www.sudoc.fr/" + ppn + ".rdf" ))
    ark = ""
    for sameAs in record.xpath("//owl:sameAs",namespaces=nsSudoc):
        resource = sameAs.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource")
        if (resource.find("ark:/12148/")>0):
            ark = resource[24:46]
    if (ark == ""):
        for frbnf in record.xpath("//bnf-onto:FRBNF",namespaces=nsSudoc):
            frbnf_val = frbnf.text
            ark = frbnf2ark(NumNot,frbnf_val,isbn,titre,auteur)
    return ark
  

def isbn2ark(NumNot,isbn,titre,auteur,date):
    #Requête sur l'ISBN dans le SRU, avec contrôle sur Titre ou auteur
    resultatsIsbn2ARK = isbn2sru(NumNot,isbn,titre,auteur,date)

    isbnConverti = conversionIsbn(isbn)
#Si pas de résultats : on convertit l'ISBN en 10 ou 13 et on relance une recherche dans le catalogue BnF
    if (resultatsIsbn2ARK == ""):
        resultatsIsbn2ARK = isbn2sru(NumNot,isbnConverti,titre,auteur,date)
        
#Si pas de résultats : on relance une recherche dans le Sudoc    
    if (resultatsIsbn2ARK == ""):
        resultatsIsbn2ARK = isbn2sudoc(NumNot,isbn,isbnConverti,titre,auteur)
    return resultatsIsbn2ARK

def ark2metas(ark):
    record = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.ark%20any%20%22" + urllib.parse.quote(ark) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1")
    titre = ""
    premierauteurPrenom = ""
    premierauteurNom = ""
    tousauteurs = ""
    if (record.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='a']", namespaces=ns) is not None):
        titre = unidecode(record.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='a']", namespaces=ns).text)
    if (record.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='e']", namespaces=ns) is not None):
        titre = titre + ", " + unidecode(record.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='e']", namespaces=ns).text)
    if (record.find("//mxc:datafield[@tag='700']/mxc:subfield[@code='a']", namespaces=ns) is not None):
        premierauteurNom = unidecode(record.find("//mxc:datafield[@tag='700']/mxc:subfield[@code='a']", namespaces=ns).text)
    if (record.find("//mxc:datafield[@tag='700']/mxc:subfield[@code='m']", namespaces=ns) is not None):
        premierauteurPrenom = unidecode(record.find("//mxc:datafield[@tag='700']/mxc:subfield[@code='m']", namespaces=ns).text)
    if (premierauteurNom  == ""):
        if (record.find("//mxc:datafield[@tag='710']/mxc:subfield[@code='a']", namespaces=ns) is not None):
            premierauteurNom = unidecode(record.find("//mxc:datafield[@tag='700']/mxc:subfield[@code='a']", namespaces=ns).text)
    if (record.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='f']", namespaces=ns) is not None):
        tousauteurs = unidecode(record.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='f']", namespaces=ns).text)

    return [titre,premierauteurPrenom,premierauteurNom,tousauteurs]
    
def ppn2metas(ppn):
    record = etree.parse(request.urlopen("https://www.sudoc.fr/" + ppn + ".rdf"))
    titre = ""
    premierauteurPrenom = ""
    premierauteurNom = ""
    tousauteurs = ""
    if (record.find("//dc:title",namespaces=nsSudoc) is not None):
        titre = unidecode(record.find("//dc:title",namespaces=nsSudoc).text).split("[")[0].split("/")[0]
        tousauteurs = unidecode(record.find("//dc:title",namespaces=nsSudoc).text).split("/")[1]
        if (titre[0:5] == tousauteurs[0:5]):
            tousauteurs = ""
    if (record.find("//marcrel:aut/foaf:Person/foaf:name",namespaces=nsSudoc) is not None):
        premierauteurNom = unidecode(record.find("//marcrel:aut/foaf:Person/foaf:name",namespaces=nsSudoc).text).split(",")[0]
        if (record.find("//marcrel:aut/foaf:Person/foaf:name",namespaces=nsSudoc).text.find(",") > 0):
            premierauteurPrenom = unidecode(record.find("//marcrel:aut/foaf:Person/foaf:name",namespaces=nsSudoc).text).split(",")[1]
        if (premierauteurPrenom.find("(") > 0):
            premierauteurPrenom = premierauteurPrenom.split("(")[0]
    return [titre,premierauteurPrenom,premierauteurNom,tousauteurs]
  
def tad2ark(NumNot,titre,auteur,auteur_nett,date_nett,anywhere=False):
#En entrée : le numéro de notice, le titre (qu'il faut nettoyer pour la recherche)
#L'auteur = zone auteur initiale, ou à défaut auteur_nett
#date_nett
    ark = []
    titre_propre = nettoyageTitrePourRecherche(titre)
    #print("titre propre : " + titre_propre)
    if (titre_propre != ""):
        if (auteur == ""):
            auteur = "-"
        if (date_nett == ""):
            date_nett = "-"
        if (auteur_nett == ""):
            auteur_nett = "-"
        url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.title%20all%20%22" + urllib.parse.quote(titre_propre) + "%22%20and%20bib.author%20all%20%22" + urllib.parse.quote(auteur) + "%22%20and%20bib.date%20all%20%22" + urllib.parse.quote(date_nett) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1"
        if (anywhere == True):
            url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.anywhere%20all%20%22" + urllib.parse.quote(titre_propre) + "%20" + urllib.parse.quote(auteur) + "%20" + urllib.parse.quote(date_nett) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1"
        #print(url)
        results = etree.parse(url)
        if (results.find("//srw:numberOfRecords", namespaces=ns) == "0"):
            url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.title%20all%20%22" + urllib.parse.quote(titre_propre) + "%22%20and%20bib.author%20all%20%22" + urllib.parse.quote(auteur_nett) + "%22%20and%20bib.date%20all%20%22" + urllib.parse.quote(date_nett) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1"
            if (anywhere == True):
                url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.anywhere%20all%20%22" + urllib.parse.quote(titre_propre) + "%20" + urllib.parse.quote(auteur_nett) + "%20" + urllib.parse.quote(date_nett) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1"
            results = etree.parse(url)
        for record in results.xpath("//srw:recordIdentifier",namespaces=ns):
            ark_current = record.text
            #print(NumNot + " : " + ark_current)
            recordBNF = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.ark%20all%20%22" + urllib.parse.quote(ark_current) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1")
            ark.append(comparaisonTitres(NumNot,ark_current,"","",nettoyageTitrePourControle(titre),auteur,date_nett,recordBNF))
            methode = "Titre-Auteur-Date"
            if (auteur == "-" and date_nett == "-"):
                methode = "Titre"
            elif (auteur == "-"):
                methode = "Titre-Date"
            elif (date_nett == "-"):
                methode = "Titre-Auteur"
    ark = ",".join([ark1 for ark1 in ark if ark1 != ""])
    return ark

