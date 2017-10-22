# -*- coding: utf-8 -*-
"""
Created on Wed Apr  5 10:39:37 2017
Extraction de métadonnées catalogue BnF à partir de l'URL de requête WebCCA
---------------------
version 9 (29/09/2017)
Correction bug sur la récupération du nombre de notices liées (AUT) quand pas de lien dans la page

---------------------
version 8 (17/07/2017)
Prise en compte de l'existence de sous-zones vides

---------------------
version 7 (29/06/2017)
Amélioration : Dans la zone "Nom de fichier en entrée", on peut indiquer une liste de N° de NNB/NNA qui se suivent, plutôt que le nom d'un fichier
sous la forme : 42746636-42746741

---------------------
version 6 (26/06/2017)
Bug : prise en compte des listes de résultats AUT avec affinage Facette
---------------------
version 5 (19/05/2017)
Correction séparateur de zones quand on demande à récupérer une zone complète, répétable
---------------------
version 4 (16/05/2017)
Ajouter colonne NNA
Ajouter colonne Statut de notice (option)
Ajouter colonne Nb de notices bib liées (option)
---------------------
version 3 (15/05/2017)
Permet de récupérer 1 ligne par PEX
Alimente un fichier de rapport permettant de savoir ce qu'on a fait auparavant...
---------------------
version 2 (12/05/2017)
Récupère les informations répétables dans une seule colonne, avec séparateur "~"
Récupère toutes les infos de PEX si on coche la case prévue

Navigue dans les pages de résultats WebCCA en récupérant les liens quand la balise <a/> contient l'attribut title="Voir la notice"
Puis bascule sur le SRU pour récupérer les métadonnées derrière chaque ARK

@author: BNF0017855
"""

import tkinter as tk
import re
import csv
from tkinter import filedialog
from lxml.html import parse
from lxml import etree
from unidecode import unidecode
from time import gmtime, strftime

ns = {"srw":"http://www.loc.gov/zing/srw/", "m":"http://catalogue.bnf.fr/namespaces/InterXMarc","mn":"http://catalogue.bnf.fr/namespaces/motsnotices"}

resultats = []

report_file = open("extractionWebCCA_logs.txt","a")

master = tk.Tk()

master.config(padx=20, pady=20)

#définition input URL (u)
tk.Label(master, text="URL WebCCA : ").pack(side="left")
u = tk.Entry(master, width=30, bd=2)
u.pack(side="left")
u.focus_set()

#Ou fichier à uploader
#https://stackoverflow.com/questions/16798937/creating-a-browse-button-with-tkinter
tk.Label(master, text="OU Fichier (sép TAB) : ").pack(side="left")
l = tk.Entry(master, width=20, bd=2)
l.pack(side="left")
l.focus_set()


#définition nom fichier en sortie (f)
tk.Label(master, text="\tNom du fichier rapport : ").pack(side="left")
f = tk.Entry(master, width=30, bd=2)
f.pack(side="left")
f.focus_set()


#AUT : Nombre de notices liées
BIBliees = tk.IntVar()
b = tk.Checkbutton(master, text="[AUT] BIB liées ?", variable=BIBliees)
b.pack(side="left")
b.focus_set()

#Zones à récupérer
tk.Label(master, text="\tZones (séparateur : \";\") : ").pack(side="left")
z = tk.Entry(master, width=30, bd=2)
z.pack(side="left")
z.focus_set()

#Ajouter les données d'exemplaire ?
PEXvar = tk.IntVar()
c = tk.Checkbutton(master, text="[BIB] Colonne PEX ?", variable=PEXvar)
c.pack(side="left")
c.focus_set()

#Option une ligne par PEX
PEXligne = tk.IntVar()
c = tk.Checkbutton(master, text="[BIB] 1 ligne par PEX ?", variable=PEXligne)
c.pack(side="left")
c.focus_set()



attributsPEX = ['IdPex','NumNoticeBib','ConditionCommunication','ModeEntree','NumeroInventaire','NumeroDL','Destination','Usage','StatutAcquisition','LettrageMillesimeSupport','FinNumeroCote','CodeDroit','Permission','DateDebutDroit','DateFinDroit','Disponibilite','CodeSupportPhysique','CodeOriginal','DateCreation','ResponsableCreation','DateDerniereModif','ResponsableDerniereModif','Etablissement','SousCatalogue']

def ark2PEX(record):
    nbPEX = 0
    listeDept = []
    listePEX = []
    for PEX in record.xpath("//m:PEX", namespaces=ns):
        nbPEX = nbPEX + 1
        Dept = ""
        if (PEX.find("m:Attr[@Nom='Destination']", namespaces=ns) is not None):
            Dept = PEX.find("m:Attr[@Nom='Destination']", namespaces=ns).text
        if (Dept not in listeDept):
            listeDept.append(Dept)
        pex = []
        for el in attributsPEX:
            attrval = ""
            path = "m:Attr[@Nom='" + el + "']"
            if (PEX.find(path, namespaces=ns) is not None):
                attrval = PEX.find(path, namespaces=ns).text
            pex.append(attrval)
        pex = "~".join(pex)
        listePEX.append(pex)
    listePEX = "#".join(listePEX)
    listeDept = ",".join(listeDept)
    return (str(nbPEX), listeDept, listePEX)

def extract_meta(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = ""
    field = ""
    subfields = []
    if (zone.find("$") > 0):
        #si la zone contient une précision de sous-zone
        zone_ss_zones = zone.split("$")
        field = zone_ss_zones[0]
        fieldPath = ".//m:datafield[@tag='" + field + "']"
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
                subfieldpath = "m:subfield[@code='"+subfield+"']"
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
            path = ".//m:leader"
        else:
            path = ".//m:" + field_tag + "[@tag='" + field + "']"
        i = 0        
        for field in record.xpath(path,namespaces=ns):
            i = i+1
            j = 0
            if (field.find("m:subfield", namespaces=ns) is not None):
                sep = ""
                for subfield in field.xpath("m:subfield",namespaces=ns):
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

def ark2meta(recordId,IDtype,listezones,checkPEX, PEXligne,BIBliees):
    urlSRU = ""
    nn = ""
    ark = ""
    if (IDtype == "ark"):
        urlSRU = "http://noticesservices.bnf.fr/SRU?version=1.2&operation=searchRetrieve&query=idPerenne%20any%20%22" + recordId + "%22&recordSchema=InterXMarc_Complet"
        nn = recordId[13:21]
        ark = recordId
    else:
        urlSRU = "http://noticesservices.bnf.fr/SRU?version=1.2&operation=searchRetrieve&query=NN%20any%20" + recordId + "&recordSchema=InterXMarc_Complet"
        nn = recordId
        ark = ""
        if (etree.parse(urlSRU).find("//srw:recordIdentifier",namespaces=ns) is not None):
            ark = str(etree.parse(urlSRU).find("//srw:recordIdentifier",namespaces=ns).text)
    #print(urlSRU)
    
    record = etree.parse(urlSRU)
    typenotice = ""
    statutnotice = ""
    infosPEX = []
    if (checkPEX == 1 or PEXligne == 1):
        infosPEX = ark2PEX(record)
    metas = []
    if (record.find("//m:leader/m:Pos[@Code='06']", namespaces=ns) is not None):
        statutnotice = record.find("//m:leader/m:Pos[@Code='06']", namespaces=ns).text
    if (record.find("//m:leader/m:Pos[@Code='09']", namespaces=ns) is not None):
        typenotice = record.find("//m:leader/m:Pos[@Code='09']", namespaces=ns).get('Sens')
    else:
        if (record.find("//m:leader/m:Pos[@Code='08']", namespaces=ns) is not None):
            typenotice = record.find("//m:leader/m:Pos[@Code='08']", namespaces=ns).get('Sens')
        if (record.find("//m:leader/m:Pos[@Code='22']", namespaces=ns) is not None):
            typenotice = typenotice + ";" + record.find("//m:leader/m:Pos[@Code='22']", namespaces=ns).get('Sens')
    listeZones = listezones.split(";")
    colonnes_communes = [ark,nn,statutnotice,typenotice]
    for el in listeZones:
        metas.append(extract_meta(record,el))
    if (BIBliees == 1):
        nbBibliees = nna2bibliees(ark)
        colonnes_communes.append(nbBibliees)
    if (PEXligne == 1):
        nbPEX = infosPEX[0]
        listeDepts = infosPEX[1]
        listePEX = infosPEX[2]
        listePEX = listePEX.split("#")
        if (nbPEX == "0"):
            listeresultats = "\t".join(colonnes_communes) + "\t" + "\t".join(["\t".join(metas), "\t".join(infosPEX)])
        else:
            listeresultats_temp = []
            for PEX in listePEX:
                listeresultats_temp.append("\t".join(colonnes_communes) + "\t" + "\t".join(["\t".join(metas)]) + "\t" + nbPEX + "\t" + listeDepts + "\t" + PEX.replace("~","\t"))
            listeresultats = "\n".join(listeresultats_temp)
    else:
        listeresultats = "\t".join(colonnes_communes) + "\t" + "\t".join(["\t".join(metas), "\t".join(infosPEX)])
    return listeresultats

def catalogue2nn(url):
    #A partir de l'URL en entrée, naviguer dans les résultats pour récupérer les ARK
    hrefPath = ".//a[@id][@title='Voir la notice']/@href"
    url = url.replace("resultats-autorite-avancee.do","changerPageAdvAuto.do")
    url = url.replace("rechercher.do","changerPage.do")
    url = url.replace("search.do","changerPageAdv.do")
    url = url.replace("affinerAdvAuto.do","changerPageAdvAuto.do")
    url = url.replace("affiner.do","changerPage.do")
    url = url + "&pageEnCours="
    page = parse(url + "1")
    nbPage = ""
    if (page.xpath("//span[@id='nbPage']") is not None):
        nbPage = page.xpath("//span[@id='nbPage']")[0].text[8:-1]
        suppr = ["sur","\n"," ","\t","\r"]
        for el in suppr:
            nbPage=nbPage.replace(el,"")
    nbPage = int(nbPage)
    i = 1
    while (i <= nbPage):
        urlPageEnCours = url + str(i)
        PageEnCours = parse(urlPageEnCours)
        liste = PageEnCours.xpath(hrefPath)
        for ark in liste:
            ark = ark.replace("/ark","ark")
            listeresultats = ark2meta(ark,"ark",z.get(),PEXvar.get(), PEXligne.get(),BIBliees.get())
            resultats.append(listeresultats)
        i = i+1
    

#print(resultats)

def callback():
    #print e.get() # This is the text you may want to use later
    url = u.get()
    filename = f.get()
    #fichier en entrée ?
    entry_filename = l.get()
    #checkPEX()
    if (filename.find(".txt") < 0):
        filename = filename + ".txt"
    fileresults = open(filename, "w")
    listeentetescommuns = ["ARK","NNA/NNB","Statut notice","Type notice"]
    if (BIBliees.get() == 1):
        listeentetescommuns.append("Nb BIB liées")
    entete_colonnes = "\t".join(listeentetescommuns) + "\t" + "\t".join(z.get().split(";"))
    entetes_attributsPEX = ""
    if (PEXligne.get() == 0):
        entetes_attributsPEX  = "~".join(attributsPEX)
    else:
        entetes_attributsPEX = "\t".join(attributsPEX)
    if (PEXvar.get() == 1 or PEXligne.get() == 1):
        entete_colonnes = entete_colonnes + "\tNb PEX\tDepts\t" + entetes_attributsPEX
   
    if (entry_filename == ""):        
        entete_colonnes = entete_colonnes + "\n"
        fileresults.write(entete_colonnes)
        catalogue2nn(url)

    else:
        #On vérifie que le nom du fichier en entrée n'est pas une liste de NNB sous la forme 1er NNB-2e NNB
         if (re.fullmatch("\d\d\d\d\d\d\d\d-\d\d\d\d\d\d\d\d", entry_filename) is not None):
             entete_colonnes = entete_colonnes + "\n"
             fileresults.write(entete_colonnes)
             i = int(entry_filename.split("-")[0])
             j = int(entry_filename.split("-")[1])
             while (i <= j):
                 listeresultats = ark2meta(str(i),"NN",z.get(),PEXvar.get(), PEXligne.get(),BIBliees.get())
                 resultats.append(listeresultats)
                 i = i+1
         else:
             with open(entry_filename, newline='\n') as csvfile:
                 entry_file = csv.reader(csvfile, delimiter='\t')
                 entry_headers = csv.DictReader(csvfile).fieldnames
                 entete_colonnes = entete_colonnes + "\t" + "\t".join(entry_headers)
                 entete_colonnes = entete_colonnes + "\n"
                 fileresults.write(entete_colonnes)
                 #next(entry_file, None)
                 for row in entry_file:
                     ID = row[0]
                     IDtype = ""
                     if (ID.find("ark") != -1):
                         IDtype = "ark"
                     else:
                         IDtype = "NN"
                     listeresultats = ark2meta(ID,IDtype,z.get(),PEXvar.get(), PEXligne.get(),BIBliees.get()) + "\t".join(row)
                     resultats.append(listeresultats)
    for el in resultats:
        fileresults.write(el + "\n")
    report_file.write("Extraction : " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
    + "\nurl : " + url 
    + "\nFichier en sortie : " + filename 
    + "\nZones à extraire : " + z.get() 
    + "\nRécupérer les PEX ? : " + str(PEXvar.get())
    + "\n1 PEX par ligne ? : " + str(PEXligne.get())
    + "\n\n")            
        

b = tk.Button(master, text = "OK", width = 20, command = callback, borderwidth=1)
b.pack()

tk.mainloop()