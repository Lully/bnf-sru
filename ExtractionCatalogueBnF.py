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
Relases notes
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
version = 1.01
lastupdate = "06/02/2018"
programID = "ExtractionCatalogueBnF"

textechapo = programID + " - Etienne Cavalié\nversion : " + str(version)

print(textechapo)

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
import pathlib
import webbrowser
from collections import defaultdict
import json
import codecs

pathlib.Path('reports').mkdir(parents=True, exist_ok=True) 

errors = {
        "no_internet" : "Attention : Le programme n'a pas d'accès à Internet.\nSi votre navigateur y a accès, vérifiez les paramètres de votre proxy"
        }

ns = {"srw":"http://www.loc.gov/zing/srw/", 
      "m":"http://catalogue.bnf.fr/namespaces/InterXMarc",
      "mn":"http://catalogue.bnf.fr/namespaces/motsnotices",
       "mxc":"info:lc/xmlns/marcxchange-v2",
       "dc":"http://purl.org/dc/elements/1.1/"}

resultats = []

report_file = open("reports/" + "extractionWebCCA_logs.txt","a", encoding="utf-8")

url_last_updates = "https://github.com/Lully/bnf-sru/tree/master/bin"


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
	

def open_update_page():
    webbrowser.open(url_last_updates)


def extract_meta_marc(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = ""
    field = ""
    subfields = []
    if (zone.find("$") > 0):
        #si la zone contient une précision de sous-zone
        zone_ss_zones = zone.split("$")
        field = zone_ss_zones[0]
        fieldPath = ".//mxc:datafield[@tag='" + field + "']"
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
            path = ".//mxc:leader"
        else:
            path = ".//mxc:" + field_tag + "[@tag='" + field + "']"
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
    path = "//" + zone
    for element in record.xpath(path, namespaces=ns):
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


def ark2meta(recordId,IDtype,format_records,listezones,BIBliees,typeEntite):
    #TypeEntite= "B" pour notices Biblio, "A" pour notices d'autorité
    add_sparse_validated = ""
    if (typeEntite == "A"):
        add_sparse_validated = urllib.parse.quote(' and aut.status any "sparse validated"')
    urlSRU = ""
    nn = ""
    ark = ""
    listeresultats = []
    if (IDtype == "ark"):
        nn = recordId[13:21]
        urlSRU = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=" + typeEntite + "recordId%20any%20%22" + nn + "%22" + add_sparse_validated + "&recordSchema=" + format_records
        ark = recordId
    else:
        urlSRU = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=" + typeEntite + "recordId%20any%20%22" + nn + "%22" + add_sparse_validated + "&recordSchema=" + format_records
        nn = recordId
        ark = ""
        if (etree.parse(urlSRU).find("//srw:recordIdentifier",namespaces=ns) is not None):
            ark = str(etree.parse(urlSRU).find("//srw:recordIdentifier",namespaces=ns).text)
    #print(urlSRU)
    #print(urlSRU)
    try:
        record = etree.parse(request.urlopen(urlSRU))
    except etree.XMLSyntaxError:
        print ('Skipping invalid XML from URL ' + urlSRU)
    except urllib.error.HTTPError:
        print ('urllib.error.HTTPError :  ' + urlSRU)
    else:
        typenotice = ""
        statutnotice = ""
    
        metas = []
    
        if (record.find("//mxc:leader", namespaces=ns) is not None):
            typenotice = record.find("//mxc:leader", namespaces=ns).text[9]
        else:
            if (record.find("//mxc:leader", namespaces=ns) is not None):
                typenotice = record.find("//mxc:leader", namespaces=ns).text[8]
            if (record.find("//mxc:leader", namespaces=ns) is not None):
                typenotice = typenotice + ";" + record.find("//mxc:leader", namespaces=ns).text[22]
        listeZones = listezones.split(";")
        colonnes_communes = [ark,nn,typenotice]
        for el in listeZones:
            if (format_records.find("marc")>0):
                metas.append(extract_meta_marc(record,el))
            else:
                metas.append(extract_meta_dc(record,el))
        if (BIBliees == 1):
            nbBibliees = nna2bibliees(ark)
            colonnes_communes.append(nbBibliees)
        listeresultats = "\t".join(colonnes_communes) + "\t" + "\t".join(metas)
    return listeresultats

def sru2nn(url,zones,BIBliees,fileresults):
    #A partir de l'URL en entrée, naviguer dans les résultats pour récupérer les ARK
    if (url[0:4] != "http"):
        url = "http://" + urllib.parse.quote(url)
    page = retrieveURL(url)
    typeEntite = "bib."
    if (url.find("aut.")>0):
        typeEntite = "aut."
    nbresultats = 0
    if (page.find(".//srw:numberOfRecords", namespaces=ns) is not None):
        nbresultats = int(page.find("//srw:numberOfRecords", namespaces=ns).text)
    query = ""
    if (page.find(".//srw:query", namespaces=ns) is not None):
        query = page.find("//srw:query", namespaces=ns).text
    format_records = "unimarcxchange"
    if (url.find("recordSchema=unimarcxchange-anl")>0):
        format_records = "unimarcxchange-anl"
    elif (url.find("recordSchema=intermarcxchange")>0):
        format_records = "intermarcxchange"
    elif (url.find("recordSchema=dublincore")>0):
        format_records = "dublincore"
    print("recherche : " + query)
    print("format : " + format_records)
    print("Nombre de résultats : " + str(nbresultats))
    firstPageURL = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=" + urllib.parse.quote(query) + "&recordSchema=" + format_records + "&stylesheet=&maximumRecords=10&startRecord="
    i =  1
    while (i <= nbresultats):
        findepage = i+9
        if (findepage >=  nbresultats):
            findepage = nbresultats
            findepage = " à " + str(findepage)
        else:
            findepage = " à " + str(findepage) + " sur " + str(nbresultats)
        print("Traitement des résultats " + str(i) + findepage)
        urlPageEnCours = firstPageURL + str(i)
        PageEnCours = retrieveURL(urlPageEnCours)
        liste = []
        for record in PageEnCours.xpath("//srw:record", namespaces=ns):
            liste.append(record.find("srw:recordIdentifier", namespaces=ns).text)

        for ark in liste:
            print(ark)
            listeresultats = ark2meta(ark,"ark",format_records,zones,BIBliees,typeEntite)
            if (listeresultats != ""):
                fileresults.write(listeresultats + "\n")
                resultats.append(listeresultats)


        i = i+10
    print("L'extraction est terminée")

def retrieveURL(url):
    page = etree.Element("default")
    try:
        page = etree.parse(url)
    except OSError:
        print("Page non ouverte, erreur Serveur")
    except etree.XMLSyntaxError:
        print("Erreur conformité XML")
    return page


#print(resultats)

def callback(master, url,entry_filename,file_format,input_file_header,zones,BIBliees,filename):
    #print e.get() # This is the text you may want to use later
    controles_formulaire(zones,url)
    rapport_logs(filename,url, zones)

    if (filename.find(".")<0):
        filename = filename + ".tsv"
    #fichier en entrée ?
    entry_filename =  entry_filename.replace("\\","/")
    fileresults = open("reports/" + filename, "w", encoding="utf-8")
    listeentetescommuns = ["ARK","Numéro notice","Type notice"]
    if (BIBliees == 1):
        listeentetescommuns.append("Nb BIB liées")
    entete_colonnes = "\t".join(listeentetescommuns) + "\t" + "\t".join(zones.split(";"))
   
    if (entry_filename == ""):        
        entete_colonnes = entete_colonnes + "\n"
        fileresults.write(entete_colonnes)
        #catalogue2nn(url)
        sru2nn(url,zones,BIBliees,fileresults)

    else:
        #Pour pouvoir mettre un fichier en entrée, il faut pouvoir :
                #1.préciser le type de notices (AUT ou BIB)
                #2.préciser dans quel format on veut récupérer les noms des zones
        #On vérifie que le nom du fichier en entrée n'est pas une liste de NNB sous la forme 1er NNB-2e NNB
         if (re.fullmatch("\d\d\d\d\d\d\d\d-\d\d\d\d\d\d\d\d", entry_filename) is not None):
             entete_colonnes = entete_colonnes + "\n"
             fileresults.write(entete_colonnes)
             i = int(entry_filename.split("-")[0])
             j = int(entry_filename.split("-")[1])
             format_records = ""
             while (i <= j):
                 format_records = ""
                 typeEntite = ""
                 testTypeEntiteBib = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.recordId%20any%20%22" + str(i) + "%22&recordSchema=" + format_records)
                 if (testTypeEntiteBib.find("srw:numberOfRecords", namespaces=ns).text != "0"):
                     typeEntite = "bib."
                 else:
                     typeEntite = "aut."
                 listeresultats = ark2meta(str(i),"NN",format_records,zones,BIBliees,typeEntite)
                 fileresults.write(listeresultats + "\n")
                 resultats.append(listeresultats)
                 i = i+1
         else:
             format_records = ""
             if (file_format == 1):
                 format_records = "dublincore"
             elif (file_format == 2):
                 format_records = "unimarcxchange"
             elif (file_format == 3):
                 format_records = "intermarcxchange"
             else:
                 print("\n\n\n=================\nErreur : Format non précisé\n===============\n\n\n")
             typeEntite = ""
             with open(entry_filename, newline='\n', encoding="utf-8") as csvfile:
                 entry_file = csv.reader(csvfile, delimiter='\t')
                 entry_headers = []
                 if (input_file_header == 1):
                     entry_headers = csv.DictReader(csvfile).fieldnames
                 entete_colonnes = entete_colonnes + "\t" + "\t".join(entry_headers)
                 entete_colonnes = entete_colonnes + "\n"
                 fileresults.write(entete_colonnes)
                 #next(entry_file, None)
                 

                 i = 1
                 for row in entry_file:
                     ID = row[0]
                     if (ID == ""):
                         continue
                     IDtype = ""
                     if (ID.find("ark")>-1):
                         IDtype = "ark"
                         ID = ID[ID.find("ark"):]
                         nn = ID[13:21]
                         testTypeEntiteBib = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.recordId%20any%20%22" + nn + "%22&recordSchema=" + format_records)
                         if (testTypeEntiteBib.find("//srw:numberOfRecords", namespaces=ns).text != "0"):
                             typeEntite = "bib."
                         else:
                             typeEntite = "aut."
                     else:
                         IDtype = "NN"
                         testTypeEntiteBib = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.recordId%20any%20%22" + ID + "%22&recordSchema=" + format_records)
                         if (testTypeEntiteBib.find("//srw:numberOfRecords", namespaces=ns).text != "0"):
                             typeEntite = "bib."
                         else:
                             typeEntite = "aut."
                     print(str(i) + ". " + ID)
                     i = i+1
                     listeresultats = ark2meta(ID,IDtype,format_records,zones,BIBliees,typeEntite) + "\t" + "\t".join(row)
                     if (listeresultats != ""):
                           fileresults.write(listeresultats + "\n")
                           resultats.append(listeresultats)
    fin_traitements(master,filename, url)

def rapport_logs(filename,url, zones):
    report_file.write("Extraction : " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
    + "\nurl : " + url 
    + "\nFichier en sortie : " + filename 
    + "\nZones à extraire : " + zones 
    + "\n\n")


def fin_traitements(master,filename, url):
    master.destroy()          
        
def call4help():
    url = "https://bibliotheques.wordpress.com/2017/10/30/extraire-des-donnees-du-catalogue-de-la-bnf-un-petit-logiciel/"
    webbrowser.open(url)
def open_sru():
    url = "http://catalogue.bnf.fr/api/"
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
    frame_input_file_format = tk.Frame(frame_input_file)
    frame_input_file_format.pack(anchor="w", side="left")
    frame_input_file_header = tk.Frame(frame_input_file)
    frame_input_file_header.pack(anchor="se", side="left")
    
    
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
    open_sru_button = tk.Button(frame_input_url, text=">SRU", bg=background_frame, command=open_sru, padx=3)
    open_sru_button.pack(side="left")
    
    #Ou fichier à uploader
    #https://stackoverflow.com/questions/16798937/creating-a-browse-button-with-tkinter
    tk.Label(frame_input_file_name, text="OU Fichier (sép TAB) : ", pady=10).pack(side="left")
    l = tk.Entry(frame_input_file_name, width=36, bd=2)
    l.pack(side="left")
    
    
    #Choix du format
    tk.Label(frame_input_file_format, text="Format à utiliser pour l'extraction :").pack(anchor="w")
    file_format = tk.IntVar()
    tk.Radiobutton(frame_input_file_format, text="Dublin Core", variable=file_format , value=1).pack(anchor="w")
    tk.Radiobutton(frame_input_file_format, text="Unimarc", variable=file_format , value=2).pack(anchor="w")
    tk.Radiobutton(frame_input_file_format, text="Intermarc", variable=file_format , value=3).pack(anchor="w")
    file_format.set(1)
    
    
    input_file_header = tk.IntVar()
    input_file_header_button = tk.Checkbutton(frame_input_file_header, 
                       text="Mon fichier comporte\ndes en-têtes", 
                       variable=input_file_header, justify="left").pack(anchor="se")
    input_file_header.set(1)
    
    
    
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
    
    b = tk.Button(frame_validation, text = "OK", width = 38, command = lambda: callback(master,u.get(),l.get(),file_format.get(),input_file_header.get(),z.get(),BIBliees.get(),f.get()), borderwidth=1, fg="white",bg=background_validation, pady=5)
    b.pack(side="left")
    
    tk.Label(frame_validation, text=" ", bg=background_frame).pack(side="left")
    
    help_button = tk.Button(frame_validation, text = "Besoin d'aide ?", width = 15, command = call4help, borderwidth=1,bg="white", pady=5)
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

def check_access_to_network():
    access_to_network = True
    try:
        request.urlopen("http://www.bnf.fr")
    except urllib.error.URLError:
        print("Pas de réseau internet")
        access_to_network = False
    return access_to_network

if __name__ == '__main__':
    access_to_network = check_access_to_network()
    last_version = [0, False]
    if(access_to_network is True):
        last_version = check_last_compilation(programID)
    formulaire(access_to_network, last_version)
    #formulaire_marc2tables(access_to_network,last_version)

