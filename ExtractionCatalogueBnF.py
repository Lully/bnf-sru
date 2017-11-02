# -*- coding: utf-8 -*-
"""
Created on Oct 27 10:39:37 2017
Last update : 30/10/2017

Extraction de métadonnées catalogue BnF à partir d'une URL de requête du SRU de la BnF
http://catalogue.bnf.fr/api

---------------------
A faire : réactiver la possibilité de mettre un fichier en entrée, dont la première colonne contient des identifiants
+ pouvoir préciser le format des notices dans lequel interroger le SRU
---------------------

@author: Etienne Cavalié (Lully)
http://bibliotheques.wordpress.com/
http://twitter.com/lully1804

---------------------
Relases notes

* version 0.2 - 30/10/2017
Ajout informations complémentaires en chapeau du terminal : version et mode d'emploi

"""

version = "0.2 - 30/10/2017"

textechapo = """\nExtractionCatalogueBnF - Etienne Cavalié
version : """ + version + """
Dernière version téléchargeable sur https://github.com/Lully/bnf-sru

Données en entrée : 
\t- URL d'une requête du SRU BnF http://catalogue.bnf.fr/api
\t- OU : fichier (1ère colonne = numéros de notices ou ARK BnF) 
\t       + préciser format SRU à exploiter (DC, Unimarc, Intermarc)
"""

print(textechapo)

import tkinter as tk
import re
import csv
from tkinter import filedialog
from lxml.html import parse
from lxml import etree
from unidecode import unidecode
from time import gmtime, strftime
import urllib.parse
import pathlib
import webbrowser

pathlib.Path('reports').mkdir(parents=True, exist_ok=True) 


ns = {"srw":"http://www.loc.gov/zing/srw/", 
      "m":"http://catalogue.bnf.fr/namespaces/InterXMarc",
      "mn":"http://catalogue.bnf.fr/namespaces/motsnotices",
       "mxc":"info:lc/xmlns/marcxchange-v2",
       "dc":"http://purl.org/dc/elements/1.1/"}

resultats = []

report_file = open("reports/" + "extractionWebCCA_logs.txt","a")


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
                        valtmp = unidecode(field.find(subfieldpath,namespaces=ns).text)
                        #valtmp = field.find(subfieldpath,namespaces=ns).text.encode("utf-8").decode("utf-8", "ignore")
                        prefixe = ""
                        if (len(zone_ss_zones) > 2):
                            prefixe = " $" + subfield + " "
                        value = value + sep + prefixe + valtmp
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
                        valuesubfield = unidecode(str(subfield.text))
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
        value.append(unidecode(element.text))
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
    
    urlSRU = ""
    nn = ""
    ark = ""
    if (IDtype == "ark"):
        nn = recordId[13:21]
        urlSRU = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=" + typeEntite + "recordId%20any%20%22" + nn + "%22&recordSchema=" + format_records
        ark = recordId
    else:
        urlSRU = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=" + typeEntite + "recordId%20any%20%22" + nn + "%22&recordSchema=" + format_records
        nn = recordId
        ark = ""
        if (etree.parse(urlSRU).find("//srw:recordIdentifier",namespaces=ns) is not None):
            ark = str(etree.parse(urlSRU).find("//srw:recordIdentifier",namespaces=ns).text)
    #print(urlSRU)
    
    record = etree.parse(urlSRU)
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

def sru2nn(url):
    #A partir de l'URL en entrée, naviguer dans les résultats pour récupérer les ARK
    if (url[0:4] != "http"):
        url = "http://" + urllib.parse.quote(url)
    page = etree.parse(url)
    typeEntite = "bib."
    if (url.find("aut.")>0):
        typeEntite = "aut."
    nbresultats = ""
    if (page.find("//srw:numberOfRecords", namespaces=ns) is not None):
        nbresultats = int(page.find("//srw:numberOfRecords", namespaces=ns).text)
    query = ""
    if (page.find("//srw:query", namespaces=ns) is not None):
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
    firstPageURL = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=" + urllib.parse.quote(query) + "&recordSchema=" + format_records + "&maximumRecords=10&startRecord="
    i = 1
    while (i <= nbresultats):
        findepage = i+9
        if (findepage >=  nbresultats):
            findepage = nbresultats
            findepage = " à " + str(findepage)
        else:
            findepage = " à " + str(findepage) + " sur " + str(nbresultats)
        print("Traitement des résultats " + str(i) + findepage)
        urlPageEnCours = firstPageURL + str(i)
        PageEnCours = etree.parse(urlPageEnCours)
        liste = []
        for record in PageEnCours.xpath("//srw:record", namespaces=ns):
            liste.append(record.find("srw:recordIdentifier", namespaces=ns).text)

        for ark in liste:
            listeresultats = ark2meta(ark,"ark",format_records,z.get(),BIBliees.get(),typeEntite)
            resultats.append(listeresultats)

        i = i+10
    print("L'extraction est terminée")
    print("Refermer le programme avant de relancer une nouvelle extraction")

    

#print(resultats)

def callback():
    #print e.get() # This is the text you may want to use later
    url = u.get()
    filename = f.get()
    if (filename.find(".")<0):
        filename = filename + ".tsv"
    #fichier en entrée ?
    entry_filename =  l.get().replace("\\","/")
    fileresults = open("reports/" + filename, "w")
    listeentetescommuns = ["ARK","Numéro notice","Type notice"]
    if (BIBliees.get() == 1):
        listeentetescommuns.append("Nb BIB liées")
    entete_colonnes = "\t".join(listeentetescommuns) + "\t" + "\t".join(z.get().split(";"))
   
    if (entry_filename == ""):        
        entete_colonnes = entete_colonnes + "\n"
        fileresults.write(entete_colonnes)
        #catalogue2nn(url)
        sru2nn(url)

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
                 listeresultats = ark2meta(str(i),"NN",format_records,z.get(),BIBliees.get(),typeEntite)
                 resultats.append(listeresultats)
                 i = i+1
         else:
             format_records = ""
             if (file_format.get() == 1):
                 format_records = "dublincore"
             elif (file_format.get() == 2):
                 format_records = "unimarcxchange"
             elif (file_format.get() == 3):
                 format_records = "intermarcxchange"
             else:
                 print("\n\n\n=================\nErreur : Format non précisé\n===============\n\n\n")
             typeEntite = ""
             with open(entry_filename, newline='\n') as csvfile:
                 entry_file = csv.reader(csvfile, delimiter='\t')
                 entry_headers = csv.DictReader(csvfile).fieldnames
                 entete_colonnes = entete_colonnes + "\t" + "\t".join(entry_headers)
                 entete_colonnes = entete_colonnes + "\n"
                 fileresults.write(entete_colonnes)
                 #next(entry_file, None)
                 

                 i = 1
                 for row in entry_file:
                     ID = row[0]
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
                     listeresultats = ark2meta(ID,IDtype,format_records,z.get(),BIBliees.get(),typeEntite) + "\t" + "\t".join(row)
                     
                     resultats.append(listeresultats)
    for el in resultats:
        fileresults.write(el + "\n")
    report_file.write("Extraction : " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
    + "\nurl : " + url 
    + "\nFichier en sortie : " + filename 
    + "\nZones à extraire : " + z.get() 
    + "\n\n")
    master.destroy()          
        
def call4help():
    url = "https://bibliotheques.wordpress.com/2017/10/30/extraire-des-donnees-du-catalogue-de-la-bnf-un-petit-logiciel/"
    webbrowser.open(url)
def open_sru():
    url = "http://catalogue.bnf.fr/api/"
    webbrowser.open(url)

#==============================================================================
# Formulaire
#==============================================================================
background_frame = "#ffffff"
background_validation =  "#348235"

master = tk.Tk()
master.title("ExtractionCatalogueBnF")
master.config(padx=20, pady=20, bg=background_frame)

frame_input = tk.Frame(master, bd=1, padx=10,pady=10, bg=background_frame, highlightbackground=background_validation, highlightthickness=2)
frame_input.pack(side="left")
tk.Label(frame_input, bg=background_frame, font="bold", text="En entrée                                                                             ", fg=background_validation).pack()


frame_input_url = tk.Frame(frame_input, bg=background_frame)
frame_input_url.pack()

frame_input_file = tk.Frame(frame_input, bg=background_frame)
frame_input_file.pack()
frame_input_file_name = tk.Frame(frame_input_file, bg=background_frame)
frame_input_file_name.pack()
frame_input_file_format = tk.Frame(frame_input_file, bg=background_frame)
frame_input_file_format.pack()

frame_inter = tk.Frame(master, bg=background_frame, padx=10)
frame_inter.pack(side="left")
tk.Label(frame_inter, text=" ", bg=background_frame).pack()

frame_output_validation = tk.Frame(master, bg=background_frame)
frame_output_validation.pack(side="left")
frame_output = tk.Frame(frame_output_validation, bd=1, padx=10,pady=10, bg=background_frame, highlightbackground=background_validation, highlightthickness=2)
frame_output.pack()
tk.Label(frame_output, bg=background_frame, font="bold", text="En sortie                                                                            ", fg=background_validation).pack()

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
open_sru_button = tk.Button(frame_input_url, text=">SRU", command=open_sru, padx=3)
open_sru_button.pack(side="left")

#Ou fichier à uploader
#https://stackoverflow.com/questions/16798937/creating-a-browse-button-with-tkinter
tk.Label(frame_input_file_name, text="", bg=background_frame).pack()
tk.Label(frame_input_file_name, text="OU Fichier (sép TAB) : ", bg=background_frame).pack(side="left")
l = tk.Entry(frame_input_file_name, width=36, bd=2, bg=background_frame)
l.pack(side="left")


#Choix du format
tk.Label(frame_input_file_format, bg=background_frame, text="+ format à utiliser pour l'extraction    :                           ").pack()
file_format = tk.IntVar()
tk.Radiobutton(frame_input_file_format, bg=background_frame, text="Dublin Core                              ", variable=file_format , value=1).pack()
tk.Radiobutton(frame_input_file_format, bg=background_frame, text="Unimarc                                    ", variable=file_format , value=2).pack()
tk.Radiobutton(frame_input_file_format, bg=background_frame, text="Intermarc                                   ", variable=file_format , value=3).pack()
file_format.set(1)

"""tk.Label(master, text="OU Fichier (sép TAB) : ").pack(side="left")
l = tk.Entry(master)
l.bbutton=tk.Button(master, text="Parcourir", command=filedialog.askopenfilename())
l.cbutton=tk.Button(master, text="OK")
l.focus_set()"""


#Zones à récupérer
tk.Label(frame_output_options_zones, bg=background_frame, text="Zones (sép. : \";\") : ").pack(side="left")
z = tk.Entry(frame_output_options_zones, bg=background_frame, width=37, bd=2)
z.pack(side="left")

#AUT : Nombre de notices liées
tk.Label(frame_output_options_bibliees, bg=background_frame, text="             ").pack(side="left")
BIBliees = tk.IntVar()
b = tk.Checkbutton(frame_output_options_bibliees, bg=background_frame, 
                   text="[Notices d'autorité] Récupérer le nombre \nde notices bibliographiques liées                ", 
                   variable=BIBliees)
b.pack()
tk.Label(frame_output_options_bibliees, bg=background_frame, text=" ").pack()
           
           
#définition nom fichier en sortie (f)
tk.Label(frame_output_file, bg=background_frame, text="Nom du rapport : ").pack(side="left")
f = tk.Entry(frame_output_file, bg=background_frame, width=35, bd=2)
f.pack(side="left")
tk.Label(frame_output_file, bg=background_frame, text=" ").pack()

b = tk.Button(frame_validation, text = "OK", width = 38, command = callback, borderwidth=1, fg="white",bg=background_validation, pady=5)
b.pack(side="left")

tk.Label(frame_validation, text=" ").pack(side="left")

help_button = tk.Button(frame_validation, text = "Besoin d'aide ?", width = 15, command = call4help, borderwidth=1,bg="white", pady=5)
help_button.pack(side="left")

tk.mainloop()
