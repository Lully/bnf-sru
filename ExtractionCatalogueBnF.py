# -*- coding: utf-8 -*-
"""
Created on Oct 27 10:39:37 2017
Last update : 30/10/2017

Extraction de métadonnées catalogue BnF à partir d'une URL de requête du SRU de la BnF
http://catalogue.bnf.fr/api

---------------------
---------------------

@author: Etienne Cavalié (Lully)
http://bibliotheques.wordpress.com/
http://twitter.com/lully1804

---------------------
Releases notes
*version 1.04 [juin 2018]
Injection des PPN comme fichier en entrée
Réécriture pour simplification de certains processus (parametres, etc.)
Constitution d'une classe SRU_result : "résultat d'une requête SRU"
et d'une classe "Recordid2metas" : "liste des métadonnées pour une notice en XML"

*version 1.03 - [18/05/2018]
- Correction bug quand fichier en entrée

*version 1.02 - [08/05/2018]
- Prise en charge nouveau type d'erreur quand on essaie d'ouvrir une URL SRU

*version 1.01 - 06/02/2018
- Meilleur traitement de certains types d'erreurs en ouvrant les URL du SRU BnF

*version 1.0 - 25/01/2018
- Génération du formulaire mise sous forme de fonction

*version 0.9 - 15/01/2018
- Correction d'un bug idiot : il était impossible d'extraire du Dublin Core à partir d'un fichier en entrée

*version 0.8 - 18/12/2017
- Le fichier en entrée peut contenir tous types de caractères UTF-8

*version 0.7 - 26/11/2017
- le rapport de logs est alimenté au début (et non à la fin, comme ça il est document si le programme plante au milieu=
- restauration des en-têtes de colonne si URL en entrée (mis en commentaire je ne sais pas quand)

* version 0.6 - 12/11/2017
Possibilité d'indiquer que le fichier en entrée ne comporte pas d'en-têtes (option cochée "oui" par défaut)
Controle cohérence entre URL format en entrée et zones en sortie (éviter URL Unimarc et balises DC). Fonction d'alerte par popup

* version 0.5 - 10/11/2017
Correction quand fichier en entrée : les résultats n'étaient pas écrits dans le rapport final

* version 0.4 - 03/11/2017
- restitution des signes diacritiques
- intégration d'un bouton Télécharger la dernière version (reste à interroger correctement le fichier JSON)
- écriture du fichier résultat au fur et à mesure du processus
- fonction fin_traitement() pour la génération des logs

* version 0.3 - 02/11/2017
Refonte du formulaire 
fermeture automatique du formulaire à la fin du traitement

* version 0.2 - 30/10/2017
Ajout informations complémentaires en chapeau du terminal : version et mode d'emploi

"""
version = 1.04
lastupdate = "23/06/2018"
programID = "ExtractionCatalogueBnF"

textechapo = programID + " - Etienne Cavalié\nversion : " + str(version)


import tkinter as tk
import re
import csv
#from tkinter import filedialog
from lxml.html import parse
from lxml import etree
#from unidecode import unidecode
from time import gmtime, strftime
import urllib.parse
from urllib import request
import urllib.error as error
import pathlib
import webbrowser
import json
import codecs
import http.client
from recordid2metas import SRU_result, Record2metas

pathlib.Path('reports').mkdir(parents=True, exist_ok=True) 

errors = {
        "no_internet" : "Attention : Le programme n'a pas d'accès à Internet.\nSi votre navigateur y a accès, vérifiez les paramètres de votre proxy"
        }

ns = {"srw":"http://www.loc.gov/zing/srw/", 
      "m":"http://catalogue.bnf.fr/namespaces/InterXMarc",
      "mn":"http://catalogue.bnf.fr/namespaces/motsnotices",
       "mxc":"info:lc/xmlns/marcxchange-v2",
       "dc":"http://purl.org/dc/elements/1.1/",
       "oai_dc":"http://www.openarchives.org/OAI/2.0/oai_dc/"}

ns_abes = {
    "bibo" : "http://purl.org/ontology/bibo/",
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

srubnf_url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query="

resultats = []

report_file = open("reports/" + "extractionWebCCA_logs.txt","a", encoding="utf-8")

url_last_updates = "https://github.com/Lully/bnf-sru/tree/master/bin"

#==============================================================================
#  Fonctions utilitaires du logiciel
#==============================================================================

def testURLetreeParse(url, print_error = True):
    test = True
    resultat = ""
    try:
        resultat = etree.parse(request.urlopen(url))
    except etree.XMLSyntaxError as err:
        if (print_error):
            print(url)
            print(err)
 
        test = False
    except etree.ParseError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except error.URLError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except ConnectionResetError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except TimeoutError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except http.client.RemoteDisconnected as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except http.client.BadStatusLine as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except ConnectionAbortedError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    return (test,resultat)

def retrieveURL(url):
    page = etree.Element("default")
    try:
        page = etree.parse(url)
    except OSError:
        print("Page non ouverte, erreur Serveur")
    except etree.XMLSyntaxError:
        print("Erreur conformité XML")
    return page


def check_last_compilation(programID):
    programID_last_compilation = 0
    display_update_button = False
    url = "https://raw.githubusercontent.com/Lully/bnf-sru/master/last_compilations.json"
    last_compilations = request.urlopen(url)
    reader = codecs.getreader("utf-8")
    last_compilations = json.load(reader(last_compilations))["last_compilations"][0]
    if (programID in last_compilations):
        programID_last_compilation = last_compilations[programID]
    if (programID_last_compilation > version):
        display_update_button = True
    return [programID_last_compilation,display_update_button]
	
def check_access_to_network():
    access_to_network = True
    try:
        request.urlopen("http://www.bnf.fr")
    except urllib.error.URLError:
        print("Pas de réseau internet")
        access_to_network = False
    return access_to_network

def open_update_page():
    webbrowser.open(url_last_updates)


def rapport_logs(filename,url, zones):
    report_file.write("Extraction : " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
    + "\nurl : " + url 
    + "\nFichier en sortie : " + filename 
    + "\nZones à extraire : " + zones 
    + "\n\n")


def fin_traitements(master,filename, url, parametres):
    print("L'extraction est terminée")
    master.destroy()          
    parametres["output_file"].close()
        
def openpage(url):
    webbrowser.open(url)

def controles_formulaire(zones,url):
    if (zones.find("dc:")>-1 and url.find("dublin")==-1 and url != ""):
        message = """Attention : vous avez indiqué des éléments d'information Dublin Core
        alors que votre requête dans le SRU est dans un format MARC"""
        popup_alert(message)

def popup_alert(message):
    popup = tk.Tk()
    popup.title("Attention")
    popup.config(padx=20,pady=20, bg="white")
    tk.Label(popup,text=message,fg="red",bg="white", padx=10, pady=10).pack()
    tk.Button(popup,text="Fermer", command=lambda:close_popup(popup)).pack()
    tk.mainloop()

def close_popup(popup):
    popup.destroy()
    

#==============================================================================
#  Fonctions d'extraction des métadonnées
#==============================================================================

def extract_meta_marc(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = ""
    field = ""
    subfields = []
    if (zone.find("$") > 0):
        #si la zone contient une précision de sous-zone
        zone_ss_zones = zone.split("$")
        field = zone_ss_zones[0]
        fieldPath = "mxc:datafield[@tag='" + field + "']"
        i = 0
        for field in record.xpath(fieldPath, namespaces=ns):
            i = i+1
            j = 0
            for subfield in zone_ss_zones[1:]:
                sep = ""
                if (i > 1 and j == 0):
                    sep = "~"
                j = j+1
                subfields.append(subfield)
                subfieldpath = "mxc:subfield[@code='"+subfield+"']"
                if (field.find(subfieldpath,namespaces=ns) is not None):
                    if (field.find(subfieldpath,namespaces=ns).text != ""):
                        valtmp = field.find(subfieldpath,namespaces=ns).text
                        #valtmp = field.find(subfieldpath,namespaces=ns).text.encode("utf-8").decode("utf-8", "ignore")
                        prefixe = ""
                        if (len(zone_ss_zones) > 2):
                            prefixe = " $" + subfield + " "
                        value = str(value) + str(sep) + str(prefixe) + str(valtmp)
    else:
        #si pas de sous-zone précisée
        field = zone
        field_tag = ""
        if (field == "001" or field == "008" or field == "009"):
            field_tag="controlfield"
        else:
            field_tag = "datafield"
        path = ""
        if (field == "000"):
            path = "mxc:leader"
        else:
            path = "mxc:" + field_tag + "[@tag='" + field + "']"
        i = 0        
        for field in record.xpath(path,namespaces=ns):
            i = i+1
            j = 0
            if (field.find("mxc:subfield", namespaces=ns) is not None):
                sep = ""
                for subfield in field.xpath("mxc:subfield",namespaces=ns):
                    sep = ""
                    if (i > 1 and j == 0):
                        sep = "~"
                    #print (subfield.get("code") + " : " + str(j) + " // sep : " + sep)
                    j = j+1
                    valuesubfield = ""
                    if (subfield.text != ""):
                        valuesubfield = str(subfield.text)
                        if (valuesubfield == "None"):
                            valuesubfield = ""
                    value = value + sep + " $" + subfield.get("code") + " " + valuesubfield
            else:
                value = field.find(".").text
    if (value != ""):
        if (value[0] == "~"):
            value = value[1:]
    return value.strip()

def extract_meta_dc(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = []
    for element in record.xpath(zone, namespaces=ns):
        value.append(element.text)
    value = "~".join(value)
    return value.strip()



def extract_abes_meta_marc(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = ""
    field = ""
    subfields = []
    if (zone.find("$") > 0):
        #si la zone contient une précision de sous-zone
        zone_ss_zones = zone.split("$")
        field = zone_ss_zones[0]
        fieldPath = "datafield[@tag='" + field + "']"
        i = 0
        for field in record.xpath(fieldPath):
            i = i+1
            j = 0
            for subfield in zone_ss_zones[1:]:
                sep = ""
                if (i > 1 and j == 0):
                    sep = "~"
                j = j+1
                subfields.append(subfield)
                subfieldpath = "subfield[@code='"+subfield+"']"
                if (field.find(subfieldpath) is not None):
                    if (field.find(subfieldpath).text != ""):
                        valtmp = field.find(subfieldpath).text
                        #valtmp = field.find(subfieldpath,namespaces=ns).text.encode("utf-8").decode("utf-8", "ignore")
                        prefixe = ""
                        if (len(zone_ss_zones) > 2):
                            prefixe = " $" + subfield + " "
                        value = str(value) + str(sep) + str(prefixe) + str(valtmp)
    else:
        #si pas de sous-zone précisée
        field = zone
        field_tag = ""
        if (field == "001" or field == "008" or field == "009"):
            field_tag="controlfield"
        else:
            field_tag = "datafield"
        path = ""
        if (field == "000"):
            path = "leader"
        else:
            path = field_tag + "[@tag='" + field + "']"
        i = 0        
        for field in record.xpath(path):
            i = i+1
            j = 0
            if (field.find("subfield") is not None):
                sep = ""
                for subfield in field.xpath("subfield"):
                    sep = ""
                    if (i > 1 and j == 0):
                        sep = "~"
                    j = j+1
                    valuesubfield = ""
                    if (subfield.text != ""):
                        valuesubfield = str(subfield.text)
                        if (valuesubfield == "None"):
                            valuesubfield = ""
                    value = value + sep + " $" + subfield.get("code") + " " + valuesubfield
            else:
                value = field.find(".").text
    if (value != ""):
        if (value[0] == "~"):
            value = value[1:]
    return value.strip()

def extract_abes_meta_dc(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = []
    zone = "//" + zone
    for element in record.xpath(zone, namespaces=ns_abes):
        value.append(element.text)
    value = "~".join(value)
    return value.strip()


def nna2bibliees(ark):
    nbBIBliees = "0"
    url = "http://catalogue.bnf.fr/" + ark
    page = parse(url)
    hrefPath = "//a[@title='Voir toutes les notices liées']"
    if (page.xpath(hrefPath) is not None):
        if (len(page.xpath(hrefPath)) > 0):
            nbBIBliees = str(page.xpath(hrefPath)[0].text)
            nbBIBliees = nbBIBliees[31:].replace(")","")
        #print(url + " : " + nbBIBliees)
    return nbBIBliees


def abesrecord2meta(recordId, record, parametres):
    metas = []
    nn = recordId
    typenotice = ""
    if (record.find("leader") is not None):
        leader = record.find("leader").text
        if ("unimarc" in parametres["format_records"]):
            typenotice = leader[6] + leader[7] 
        elif ("intermarc" in parametres["format_records"]):
            typenotice = leader[22] + leader[8]
    listeZones = parametres["zones"].split(";")
    colonnes_communes = ["PPN"+recordId, nn, typenotice]
    for el in listeZones:
        if ("marc" in parametres["format_records"]):
            metas.append(extract_abes_meta_marc(record, el))
        else:
            metas.append(extract_abes_meta_dc(record, el))
    if (parametres["BIBliees"] == 1):
        nbBibliees = nna2bibliees(recordId)
        colonnes_communes.append(nbBibliees)
    line_resultats = "\t".join(colonnes_communes) + "\t" + "\t".join(metas)
    return line_resultats


def bnfrecord2meta(recordId, record, parametres):
    metas = []
    nn = recordId
    typenotice = ""
    if ("ark" in recordId):
        nn = recordId[recordId.find("ark")+13:-1]
    if (record.find("mxc:leader", namespaces=ns) is not None):
        leader = record.find("mxc:leader", namespaces=ns).text
        if ("unimarc" in parametres["format_records"]):
            typenotice = leader[6] + leader[7] 
        elif ("intermarc" in parametres["format_records"]):
            typenotice = leader[22] + leader[8]
    listeZones = parametres["zones"].split(";")
    colonnes_communes = [recordId,nn,typenotice]
    for el in listeZones:
        if ("marc" in parametres["format_records"]):
            metas.append(extract_meta_marc(record,el))
        else:
            metas.append(extract_meta_dc(record,el))
    if (parametres["BIBliees"] == 1):
        nbBibliees = nna2bibliees(recordId)
        colonnes_communes.append(nbBibliees)
    line_resultats = "\t".join(colonnes_communes) + "\t" + "\t".join(metas)
    return line_resultats

def ark2meta(recordId,IDtype,parametres):
    #TypeEntite= "B" pour notices Biblio, "A" pour notices d'autorité
    add_sparse_validated = ""
    if (parametres["typeEntite"] == "aut."):
        add_sparse_validated = urllib.parse.quote(' and aut.status any "sparse validated"')
    urlSRU = ""
    nn = recordId
    ark = recordId
    if (IDtype == "ark"):
        nn = recordId[13:21]
    line_resultats = ""
    query = parametres["typeEntite"] + "persistentid%20any%20%22" + recordId + "%22" + add_sparse_validated
    if (IDtype == "NN"):
        query = parametres["typeEntite"] + "recordId%20any%20%22" + nn + "%22" + add_sparse_validated 
    urlSRU = srubnf_url + query + "&recordSchema=" + parametres["format_records"]
    
    (test,page) = testURLetreeParse(urlSRU)    
    if (test):
        if (IDtype == "NN" and page.find("//srw:recordIdentifier",namespaces=ns) is not None):
            ark = page.find("//srw:recordIdentifier",namespaces=ns).text
        if (page.find("//srw:recordData/oai_dc:dc", namespaces=ns) is not None):
            record = page.xpath("//srw:recordData/oai_dc:dc",namespaces=ns)[0]
            line_resultats = bnfrecord2meta(ark,record,parametres)
        if (page.find("//srw:recordData/mxc:record", namespaces=ns) is not None):
            record = page.xpath("//srw:recordData/mxc:record",namespaces=ns)[0]
            line_resultats = bnfrecord2meta(ark,record,parametres)

    return line_resultats


def get_abes_record(ID, parametres):
    """A partir d'un identifiant PPN (IdRef / Sudoc), permet d'identifier si
    la notice est à récupérer sur IdRef ou sur le Sudoc"""
    platform = ""
    record = ""
    id_nett = ID.upper().split("/")[-1].replace("PPN","")

    if ("marc" in parametres["format_records"]):
        (test,record) = testURLetreeParse("https://www.sudoc.fr/" + id_nett + ".xml",False)
        if (test):
            platform = "https://www.sudoc.fr/"
        else:
            (test,record) = testURLetreeParse("https://www.idref.fr/" + id_nett + ".xml")
            if (test):
                platform = "https://www.idref.fr/"
    elif ("dublincore" in parametres["format_records"]):
        (test,record) = testURLetreeParse("https://www.sudoc.fr/" + id_nett + ".rdf",False)
        if (test):
            platform = "https://www.sudoc.fr/"
        else:
            (test,record) = testURLetreeParse("https://www.idref.fr/" + id_nett + ".rdf")
            if (test):
                platform = "https://www.idref.fr/"
    return (id_nett, test,record,platform)



def url2entity_type(url):
    entity_type = "bib."
    if ("aut." in url):
        entity_type= "aut."
    return entity_type
    
def extract_1_info_from_SRU(page,element,datatype = str):
    """Récupère le nombre de résultats"""
    val = ""
    if (datatype == int):
        val = 0
    path = ".//" + element
    if (page.find(path, namespaces=ns) is not None):
        val = page.find(path, namespaces=ns).text
        if (datatype == int):
            val = int(val)
    return val

def url2format_records(url):
    format_records = "unimarcxchange"
    if ("recordSchema=unimarcxchange-anl" in url):
        format_records = "unimarcxchange-anl"
    elif ("recordSchema=intermarcxchange" in url):
        format_records = "intermarcxchange"
    elif ("recordSchema=dublincore" in url):
        format_records = "dublincore"
    return format_records

def results2file(sru_result, parametres):
    for recordid in sru_result.dict_records:
        print(sru_result.dict_records[recordid]["position"], ".", recordid)
        metas = Record2metas(recordid, sru_result.dict_records[recordid]["record"], parametres["zones"]).metas
        line = recordid + "\t" + "\t".join(metas)
        parametres["output_file"].write(line + "\n")

def sru2records(url, parametres):
    #Extraction des métadonnées à partir de la bibliothèque recordid2metas
    try:
        assert "?" in url
    except AssertionError as err:
        print("URL mal saisie")
    if (url[0:4] != "http"):
        url = "http://" + url
    #Extraction des paramètres de requête à partir de l'URL
    url_root = url.split("?")[0]+"?"
    url_param = url.split("?")[1].split("&")
    sru_param = {}
    for param in url_param:
        key, value = param.split("=")[0], param.split("=")[1]
        sru_param[key] = value
    first_page = SRU_result(url_root, sru_param)
    results2file(first_page, parametres)
    if (first_page.multipages):
        j = int(first_page.parametres["startRecord"])
        while (j < first_page.nb_results):
            sru_param["startRecord"] = str(
                                            int(sru_param["startRecord"]) 
                                            + int(sru_param["maximumRecords"])
                                            )
            next_page = SRU_result(url_root, sru_param)
            results2file(next_page, parametres)
            j += int(sru_param["maximumRecords"])

def sru2nn(url, parametres):
    #A partir de l'URL en entrée, naviguer dans les résultats pour récupérer les ARK
    if (url[0:4] != "http"):
        url = "http://" + urllib.parse.quote(url)
    (test,page) = testURLetreeParse(url)
    if (test):
        parametres["typeEntite"] = url2entity_type(url)
        parametres["format_records"] = url2format_records(url)
        nbresultats = extract_1_info_from_SRU(page, "srw:numberOfRecords", int)
        query = extract_1_info_from_SRU(page,"srw:query", str)
        
        print("recherche : " + query)
        print("format : " + parametres["format_records"])
        print("Nombre de résultats : ", nbresultats)
        firstPageURL = "".join([
                                srubnf_url,
                                urllib.parse.quote(query),
                                "&recordSchema=",
                                parametres["format_records"],
                                "&stylesheet=&maximumRecords=100&startRecord="
                                ])
        
        i =  1
        while (i <= nbresultats):
            findepage = i+99
            if (findepage >=  nbresultats):
                findepage = nbresultats
                findepage = " à " + str(findepage)
            else:
                findepage = " à " + str(findepage) + " sur " + str(nbresultats)
            print("Traitement des résultats " + str(i) + findepage)
            urlPageEnCours = firstPageURL + str(i)
            PageEnCours = retrieveURL(urlPageEnCours)

            for rec in PageEnCours.xpath("//srw:record", namespaces=ns):
                ark = rec.find("srw:recordIdentifier", namespaces=ns).text
                record = rec.xpath("srw:recordData/mxc:record|srw:recordData/oai_dc:dc",
                                                 namespaces=ns)[0]
                print(ark)
                line = bnfrecord2meta(record,record,parametres)
                parametres["output_file"].write(line + "\n")
            i = i+100


def file2results(entry_filename, parametres, entete_colonnes):
    """Exploitation d'un fichier listant des numéros de notice en entrée"""
    #Option 1 : indication d'une tranche de numéros de notices (NNA ou NNB)
    if (re.fullmatch("\d\d\d\d\d\d\d\d-\d\d\d\d\d\d\d\d", entry_filename) is not None):
        entete_colonnes = entete_colonnes + "\n"
        parametres["output_file"].write(entete_colonnes)
        i = int(entry_filename.split("-")[0])
        j = int(entry_filename.split("-")[1])
        typeEntite = "aut."
        if (i > 29999999):
            typeEntite = "bib."
        parametres["typeEntite"] = typeEntite
        while (i <= j):
            line_resultats = ark2meta(str(i),"NN",parametres)
            print(i)
            parametres["ouptput_file"].write(line_resultats + "\n")

            i = i+1
    #Option 2 : c'est bien un nom de fichier
    else:
        typeEntite = ""
        with open(entry_filename, newline='\n', encoding="utf-8") as csvfile:
            entry_file = csv.reader(csvfile, delimiter='\t')
            entry_headers = []
            if (parametres["input_file_header"] == 1):
                entry_headers = csv.DictReader(csvfile).fieldnames
            entete_colonnes = entete_colonnes + "\t" + "\t".join(entry_headers)
            entete_colonnes = entete_colonnes + "\n"
            parametres["output_file"].write(entete_colonnes)
            #next(entry_file, None)
            
   
            i = 1
            for row in entry_file:
                row2metas(row,i,parametres)
                i += 1

def row2metas(row,i,parametres):
    ID = row[0]
    if (ID == ""):
        pass
    if ("ppn" in ID.lower() or "sudoc.fr" in ID.lower() or "idref.fr" in ID.lower()):
        ppn2metas(ID, row, i, parametres)
    else:
        bnf2metas(ID, row, i, parametres)

def ppn2metas(ID, row, i, parametres):
    (ID, test, record, platform) = get_abes_record(ID, parametres)
    print(str(i) + ". PPN" + ID + "  (" + platform + ")")
    line = abesrecord2meta(ID, record, parametres)
    parametres["output_file"].write(line + "\n")

def bnf2metas(ID, row, i, parametres):
    IDtype = "NN"
    nn = ID
    if ("ark" in ID):
        IDtype = "ark"
        ID = ID[ID.find("ark"):]
        nn = ID[13:21]
    print(str(i) + ". " + ID)
    typeEntite = "bib."
    if (int(nn) < 30000000):
       typeEntite = "aut."
    parametres["typeEntite"] = typeEntite
    line = ark2meta(
                    ID, IDtype, parametres
                    ) + "\t" + "\t".join(row)

    parametres["output_file"].write(line + "\n")
    



#print(resultats)

def callback(master, url,entry_filename,file_format,input_file_header,zones,BIBliees,filename):
    #print e.get() # This is the text you may want to use later
    controles_formulaire(zones,url)
    rapport_logs(filename,url, zones)

    if ("." not in filename):
        filename = filename + ".tsv"
    #fichier en entrée ?
    entry_filename =  entry_filename.replace("\\","/")
    output_file = open("reports/" + filename, "w", encoding="utf-8")
    common_headers = ["ARK","Numéro notice","Type notice"]
    if (BIBliees == 1):
        common_headers.append("Nb BIB liées")
    headers = "\t".join(common_headers) + "\t" + "\t".join(zones.split(";"))

    parametres = {
            "input_file_header": input_file_header,
            "zones" : zones,
            "BIBliees" : BIBliees,
            "file_format": file_format,
            "output_file":output_file
            }

    #Si pas de nom de fichier en entrée -> URL du SRU
    if (entry_filename == ""):        
        headers = headers + "\n"
        output_file.write(headers)
        #catalogue2nn(url)
        sru2records(url,parametres)

    #Sinon : fichier en entrée dont la 1ère colonne est un identifiant
    else:
        mapping_formats = {
                1 : "dublincore",
                2 : "unimarcxchange",
                3 : "intermarcxchange"}
        parametres["format_records"] = mapping_formats[file_format]
        file2results(entry_filename, parametres, headers)
        
    #Fermeture du formulaire et du fichier rapport
    fin_traitements(master,filename, url, parametres)


#==============================================================================
# Formulaire
#==============================================================================
 
def formulaire(access_to_network, last_version):


    background_frame = "#ffffff"
    background_validation =  "#348235"
    
    master = tk.Tk()
    master.title("ExtractionCatalogueBnF")
    master.config(padx=20, pady=20, bg=background_frame)
    
    frame_form = tk.Frame(master, bg=background_frame)
    frame_form.pack()
    frame_commentaires = tk.Frame(master, pady=10, bg=background_frame)
    frame_commentaires.pack()
    
    frame_input = tk.Frame(frame_form, bd=1, padx=10,pady=10, bg=background_frame, highlightbackground=background_validation, highlightthickness=2)
    frame_input.pack(side="left")
    tk.Label(frame_input, bg=background_frame, font="bold", text="En entrée", fg=background_validation).pack(anchor="w")
    
    
    frame_input_url = tk.Frame(frame_input, bg=background_frame, pady=10)
    frame_input_url.pack(anchor="w")
    
    frame_input_file = tk.Frame(frame_input, padx=5, pady=5)
    frame_input_file.pack()
    frame_input_file_name = tk.Frame(frame_input_file)
    frame_input_file_name.pack()
    frame_input_file_header = tk.Frame(frame_input_file)
    frame_input_file_header.pack(anchor="se")

    frame_input_file_format = tk.Frame(frame_input_file)
    frame_input_file_format.pack(anchor="w")
    
    
    frame_inter = tk.Frame(frame_form, bg=background_frame, padx=10)
    frame_inter.pack(side="left")
    tk.Label(frame_inter, text=" ", bg=background_frame).pack()
    
    frame_output_validation = tk.Frame(frame_form, bg=background_frame)
    frame_output_validation.pack(side="left")
    frame_output = tk.Frame(frame_output_validation, bd=1, padx=10,pady=10, bg=background_frame, highlightbackground=background_validation, highlightthickness=2)
    frame_output.pack()
    tk.Label(frame_output, bg=background_frame, font="bold", text="En sortie", fg=background_validation).pack(anchor="w")
    
    frame_output_options = tk.Frame(frame_output, bg=background_frame)
    frame_output_options.pack()
    frame_output_options_zones = tk.Frame(frame_output_options, bg=background_frame)
    frame_output_options_zones.pack()
    frame_output_options_bibliees = tk.Frame(frame_output_options, bg=background_frame)
    frame_output_options_bibliees.pack()
    frame_output_file = tk.Frame(frame_output, bg=background_frame)
    frame_output_file.pack()
    
    frame_validation = tk.Frame(frame_output_validation, border=0, padx=10,pady=10, bg=background_frame)
    frame_validation.pack()
    
    
    #définition input URL (u)
    tk.Label(frame_input_url, text="URL de requête du SRU : ", bg=background_frame).pack(side="left")
    u = tk.Entry(frame_input_url, width=25, bd=2, bg=background_frame)
    u.pack(side="left")
    u.focus_set()
    tk.Label(frame_input_url, text=" ", bg=background_frame).pack(side="left")
    open_sru_button = tk.Button(frame_input_url, text=">SRU", bg=background_frame, command=lambda:openpage("http://catalogue.bnf.fr/api/"), padx=3)
    open_sru_button.pack(side="left")
    
    #Ou fichier à uploader
    #https://stackoverflow.com/questions/16798937/creating-a-browse-button-with-tkinter
    tk.Label(frame_input_file_name, text="OU Fichier (sép TAB) : ", 
             font="Arial 9 bold", pady=10).pack(side="left")
    l = tk.Entry(frame_input_file_name, width=36, bd=2)
    l.pack(side="left")
    
    #Option : Fichier avec en-tête
    input_file_header = tk.IntVar()
    tk.Checkbutton(frame_input_file_header, 
                       text="Fichier avec en-têtes", 
                       variable=input_file_header, justify="left").pack(anchor="ne")
    input_file_header.set(1)
    
        
    
    #Choix du format
    tk.Label(frame_input_file_format, text="Format à utiliser pour l'extraction :",
             font="Arial 9 bold").pack(anchor="w")
    file_format = tk.IntVar()
    tk.Radiobutton(frame_input_file_format, text="Unimarc         (ARK BnF ou PPN Abes)", variable=file_format , value=2).pack(anchor="w")
    tk.Radiobutton(frame_input_file_format, text="Intermarc       (ARK BnF uniquement)", variable=file_format , value=3).pack(anchor="w")
    tk.Radiobutton(frame_input_file_format, text="Dublin Core   (BIB uniquement - BnF ou Abes)", variable=file_format , value=1).pack(anchor="w")

    file_format.set(1)
    

    
    #Zones à récupérer
    tk.Label(frame_output_options_zones, bg=background_frame, text="Zones (sép. : \";\") : ").pack(side="left")
    z = tk.Entry(frame_output_options_zones, bg=background_frame, width=37, bd=2)
    z.pack(side="left")
    
    #AUT : Nombre de notices liées
    tk.Label(frame_output_options_bibliees, bg=background_frame, text=" ").pack(side="left")
    BIBliees = tk.IntVar()
    b = tk.Checkbutton(frame_output_options_bibliees, bg=background_frame, 
                       text="[Notices d'autorité] Récupérer le nombre \nde notices bibliographiques liées                ", 
                       variable=BIBliees)
    b.pack(anchor="w")
    tk.Label(frame_output_options_bibliees, bg=background_frame, text=" ").pack()
               
               
    #définition nom fichier en sortie (f)
    tk.Label(frame_output_file, bg=background_frame, text="Nom du rapport : ").pack(side="left")
    f = tk.Entry(frame_output_file, bg=background_frame, width=35, bd=2)
    f.pack(side="left")
    tk.Label(frame_output_file, bg=background_frame, text=" ").pack()
    
    b = tk.Button(frame_validation, text = "OK", width = 38, 
                  command = lambda: callback(master,u.get(),l.get(),file_format.get(),input_file_header.get(),z.get(),BIBliees.get(),f.get()), 
                  borderwidth=1, fg="white",bg=background_validation, pady=5)
    b.pack(side="left")
    
    tk.Label(frame_validation, text=" ", bg=background_frame).pack(side="left")
    
    help_button = tk.Button(frame_validation, text = "Besoin d'aide ?", width = 15, 
                            command = lambda: openpage("https://bibliotheques.wordpress.com/2017/10/30/extraire-des-donnees-du-catalogue-de-la-bnf-un-petit-logiciel/"), 
                            borderwidth=1,bg="white", pady=5)
    help_button.pack(side="left")
    
    textAbout = tk.Label(frame_commentaires, text=textechapo, bg=background_frame)
    textAbout.pack()
    
    if (access_to_network == False):
        tk.Label(frame_commentaires, text=errors["no_internet"], 
             bg=background_frame,  fg="red").pack()

    tk.Label(frame_commentaires, text = "Version " + str(version) + " - " + lastupdate, bg=background_frame).pack()


    if (last_version[1] == True):
        button_updates = tk.Button(frame_commentaires, padx=10, text="Version " + str(last_version[0]) + " disponible", command=open_update_page)
        button_updates.pack()
    
    
    tk.mainloop()



if __name__ == '__main__':
    print(textechapo)
    access_to_network = check_access_to_network()
    last_version = [0, False]
    if(access_to_network is True):
        last_version = check_last_compilation(programID)
    formulaire(access_to_network, last_version)
    #formulaire_marc2tables(access_to_network,last_version)

