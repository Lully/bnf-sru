# -*- coding: utf-8 -*-
"""
Created on Fri Oct 13 18:30:30 2017

@author: Etienne Cavalié

Programme d'identification des ARK BnF à partir de numéros FRBNF

"""

from lxml import etree
from urllib import request
import urllib.parse
from unidecode import unidecode
import urllib.error 
import csv
import tkinter as tk
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt


ns = {"srw":"http://www.loc.gov/zing/srw/", "mxc":"info:lc/xmlns/marcxchange-v2", "m":"http://catalogue.bnf.fr/namespaces/InterXMarc","mn":"http://catalogue.bnf.fr/namespaces/motsnotices"}

#==============================================================================
# Rapport statistique final
#==============================================================================
nb_notices_nb_ARK = defaultdict(int)
report_file = open("rapport_stats_frbnf2ark.txt","w")
report_file.write("Nb ARK trouvés\tNb notices concernées\n")

#fonction de mise à jour de l'ARK s'il existe un ARK
def ark2ark(ark):
    url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.ark%20all%20%22" + urllib.parse.quote(ark) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1"
    page = etree.parse(url)
    nv_ark = ""
    if (page.find("//srw:recordIdentifier", namespaces=ns) is not None):
        nv_ark = page.find("//srw:recordIdentifier", namespaces=ns).text
    return nv_ark

#nettoyage des chaines de caractères (titres, auteurs, isbn) : suppression ponctuation, espaces (pour les titres et ISBN) et diacritiques
def nettoyage(string,remplacerEspaces=True):
    chercherremplacer = ["-",
            ".",
            ",",
            ";",
            ":",
            "?",
            "!",
            "%",
            "$",
            "£",
            "€",
            "#",
            "\\",
            "\"",
            "'",
            "&",
            "~",
            "{",
            "(",
            "[",
            "`",
            "\\",
            "_",
            "@",
            ")",
            "]",
            "}",
            "=",
            "+",
            "*",
            "\/",
            "<",
            ">",
            ")",
            "}"]
    string = unidecode(string.lower())
    for signe in chercherremplacer:
        string = string.replace(signe,"")
    if (remplacerEspaces == True):
        string = string.replace(" ","")
    return string

def nettoyageTitre(titre):
    titre = nettoyage(titre,True)
    return titre

def nettoyageIsbn(isbn):
    isbn = nettoyage(isbn)
    if (len(isbn) < 10):
        isbn = ""
    elif (isbn[0:3] == "978" or isbn[0:3] == "979"):
        isbn = isbn[3:12]
    else:
        isbn = isbn[0:10]
    return isbn

def nettoyageAuteur(auteur):
    listeMots = ["par","avec","by","Mr.","M.","Mme","Mrs"]
    listeChiffres = ["0","1","2","3","4","5","6","7","8","9"]
    for mot in listeMots:
        auteur = auteur.replace(mot,"")
    for chiffre in listeChiffres:
        auteur = auteur.replace(chiffre,"")
    auteur = nettoyage(auteur.lower(),False)
    auteur = auteur.split(" ")
    auteur = sorted(auteur,key=len,reverse=True)
    if (auteur is not None):
        auteur = auteur[0]
    else:
        auteur = ""
    return auteur

#Si la recherche NNB avec comporaison Mots du titre n'a rien donné, on recherche sur N° interne BnF + Auteur (en ne gardant que le mot le plus long du champ Auteur)
def relancerNNBAuteur(NumNot,systemid,isbn,titre,auteur):
    listeArk = []
    if (auteur != "" and auteur is not None):
        urlSRU = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.author%20all%20%22" + urllib.parse.quote(auteur) + "%22and%20bib.otherid%20all%20%22" + systemid + "%22&recordSchema=unimarcxchange&maximumRecords=1000&startRecord=1"
        pageSRU = etree.parse(urlSRU)
        for record in pageSRU.xpath("//srw:records/srw:record", namespaces=ns):
            ark = record.find("srw:recordIdentifier", namespaces=ns).text
            listeArk.append(ark)
    listeArk = ",".join(listeArk)
    return listeArk
        
    

#Quand on a trouvé l'ancien numéro système dans une notice BnF : 
#on compare l'ISBN de la notice de la Bibliothèque avec celui de la BnF pour voir si ça colle
#à défaut, on compare les titres (puis demi-titres)
def comparerBibBnf(NumNot,ark_current,systemid,isbn,titre,auteur):
    ark = ""
    recordBNF = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.ark%20all%20%22" + urllib.parse.quote(ark_current) + "%22&recordSchema=unimarcxchange&maximumRecords=20&startRecord=1")
    ark =  comparaisonIsbn(NumNot,ark_current,systemid,isbn,titre,auteur,recordBNF)
    if (ark == ""):
        ark = comparaisonTitres(NumNot,ark_current,systemid,isbn,titre,auteur,recordBNF)
    return ark

def comparaisonIsbn(NumNot,ark_current,systemid,isbn,titre,auteur,recordBNF):
    ark = ""
    isbnBNF = ""
    if (recordBNF.find("//mxc:datafield[@tag='010']/mxc:subfield[@code='a']", namespaces=ns) is not None):
        isbnBNF = nettoyage(recordBNF.find("//mxc:datafield[@tag='010']/mxc:subfield[@code='a']", namespaces=ns).text)
    if (isbn != "" and isbnBNF != ""):
        if (isbn in isbnBNF):
            ark = ark_current
    return ark

def comparaisonTitres(NumNot,ark_current,systemid,isbn,titre,auteur,recordBNF):
    ark = ""
    titreBNF = ""
    if (recordBNF.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='a']", namespaces=ns) is not None):
        if (recordBNF.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='a']", namespaces=ns).text is not None):
            titreBNF = nettoyage(recordBNF.find("//mxc:datafield[@tag='200']/mxc:subfield[@code='a']", namespaces=ns).text)
    if (titre != "" and titreBNF != ""):
        if (titre == titreBNF):
            ark = ark_current
            if (len(titre) < 5):
                ark += "[titre court]"
        elif(titre[0:round(len(titre)/2)] == titreBNF[0:round(len(titre)/2)]):
            ark = ark_current
            if (round(len(titre)/2)<10):
                ark += "[demi-titre" + "-" + str(round(len(titre)/2)) + "caractères]"
    return ark
            
    

#Recherche par n° système. Si le 3e paramètre est "False", c'est qu'on a pris uniquement le FRBNF initial, sans le tronquer. 
#Dans ce cas, et si 0 résultat pertinent, on relance la recherche avec info tronqué
def systemid2ark(NumNot,systemid,tronque,isbn,titre,auteur):
    url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.otherid%20all%20%22" + systemid + "%22&recordSchema=intermarcxchange&maximumRecords=1000&startRecord=1"
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
                            listeARK.append(comparerBibBnf(NumNot,ark_current,systemid,isbn,titre,auteur))
    listeARK = ",".join([ark1 for ark1 in listeARK if ark1 != ''])
    
#Si pas de réponse, on fait la recherche SystemID + Auteur
    if (listeARK == ""):
        listeARK = relancerNNBAuteur(NumNot,systemid,isbn,titre,auteur)
    listeARK = ",".join([ark1 for ark1 in listeARK.split(",") if ark1 != ''])
    
#Si à l'issue d'une première requête sur le numéro système dont on a conservé la clé ne donne rien -> on recherche sur le numéro tronqué comme numéro système
    if (listeARK == "" and tronque == False):
        systemid_tronque = systemid[0:len(systemid)-1]
        systemid2ark(NumNot,systemid_tronque, True,isbn,titre,auteur)   
    listeARK = ",".join([ark1 for ark1 in listeARK.split(",") if ark1 != ''])
    
    return listeARK

def rechercheNNB(NumNot,nnb,isbn,titre,auteur):
    ark = ""
    if (nnb.isdigit() is False):
        #pb_frbnf_source.write("\t".join[NumNot,nnb] + "\n")
        ark = "Pb FRBNF"
    elif (int(nnb) > 30000000 and int(nnb) < 50000000):
        url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.recordid%20any%20%22" + nnb + "%22&recordSchema=unimarcxchange&maximumRecords=1000&startRecord=1"
        page = etree.parse(url)
        for record in page.xpath("//srw:records/srw:record", namespaces=ns):
            ark_current = record.find("srw:recordIdentifier",namespaces=ns).text
            ark = comparerBibBnf(NumNot,ark_current,nnb,isbn,titre,auteur)
    return ark

#Si le FRBNF n'a pas été trouvé, on le recherche comme numéro système -> pour ça on extrait le n° système
def oldfrbnf2ark(NumNot,frbnf,isbn,titre,auteur):
    systemid = ""
    if (frbnf[0:5].upper() == "FRBNF"):
        systemid = frbnf[5:14]
    else:
        systemid = frbnf[4:13]
    ark = rechercheNNB(NumNot,systemid[0:8],isbn,titre,auteur)
    if (ark==""):
        ark = systemid2ark(NumNot,systemid,False,isbn,titre,auteur)
    return ark


#Rechercher le FRBNF avec le préfixe    
def frbnf2ark(NumNot,frbnf,isbn,titre,auteur):
    url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=bib.otherid%20all%20%22" + frbnf + "%22&recordSchema=unimarcxchange&maximumRecords=1000&startRecord=1"
    page = etree.parse(url)
    nb_resultats = int(page.find("//srw:numberOfRecords", namespaces=ns).text)
    ark = ""
    if (nb_resultats == 0):
        ark = oldfrbnf2ark(NumNot,frbnf,isbn,titre,auteur)
    elif (nb_resultats == 1):
        ark = page.find("//srw:recordIdentifier", namespaces=ns).text
    else:
        ark = ",".join(page.xpath("//srw:recordIdentifier", namespaces=ns))
    return ark

unique_file_results_frbnf2ark_name = "resultats_frbnf2ark.txt"
multiple_files_pbFRBNF_name = "resultats_Probleme_FRBNF.txt"
multiple_files_0_ark_name = "resultats_0_ark_trouve.txt"
multiple_files_1_ark_name = "resultats_1_ark_trouve.txt"
multiple_files_plusieurs_ark_name = "resultats_plusieurs_ark_trouves.txt"
      
        
def row2file(nb_fichiers_a_produire,nbARK,NumNot,frbnf,current_ark,ark,isbn,titre,auteur,unique_file_results_frbnf2ark):
    if (nb_fichiers_a_produire == 1):
        unique_file_results_frbnf2ark.write("\t".join([NumNot,str(nbARK),ark,frbnf,current_ark,isbn,titre,auteur]) + "\n")

def row2files(nb_fichiers_a_produire,nbARK,NumNot,frbnf,current_ark,ark,isbn,titre,auteur,multiple_files_pbFRBNF,multiple_files_0_ark,multiple_files_1_ark,multiple_files_plusieurs_ark):
    if (ark == "Pb FRBNF"):
        multiple_files_pbFRBNF.write("\t".join([NumNot,"",ark,frbnf,current_ark,isbn,titre,auteur]) + "\n")
    elif (nbARK == 0):
        multiple_files_0_ark.write("\t".join([NumNot,current_ark,isbn,titre,auteur]) + "\n")
    elif (nbARK == 1):
        multiple_files_1_ark.write("\t".join([NumNot,"1",ark,frbnf,current_ark,isbn,titre,auteur]) + "\n")
    else:
        multiple_files_plusieurs_ark.write("t".join([NumNot,str(nbARK),ark,frbnf,current_ark,isbn,titre,auteur]) + "\n")
        

def callback():
    nb_fichiers_a_produire = file_nb.get()
    #results2file(nb_fichiers_a_produire)
    entry_file = entry_filename.get()
    
    if (nb_fichiers_a_produire == 1):
        unique_file_results_frbnf2ark = open(unique_file_results_frbnf2ark_name,"w")
    elif (nb_fichiers_a_produire == 2):
        multiple_files_pbFRBNF = open(multiple_files_pbFRBNF_name,"w")
        multiple_files_0_ark = open(multiple_files_0_ark_name,"w")
        multiple_files_1_ark = open(multiple_files_1_ark_name,"w")
        multiple_files_plusieurs_ark = open(multiple_files_plusieurs_ark_name,"w")
    
    with open(entry_file, newline='\n',encoding="utf-8") as csvfile:
        entry_file = csv.reader(csvfile, delimiter='\t')
        next(entry_file)
        for row in entry_file:
            #print(row)
            NumNot = row[0]
            frbnf = row[1]
            current_ark = row[2]
            isbn = row[3]
            isbn_nett = nettoyageIsbn(isbn)
            titre = row[4]
            titre_nett= nettoyageTitre(titre)
            auteur = row[5]
            auteur_nett = nettoyageAuteur(auteur)
            
            if (current_ark != ""):
                ark = ark2ark(current_ark)
            else:
                ark = frbnf2ark(NumNot,frbnf,isbn_nett,titre_nett,auteur_nett)
            ark = ",".join([ark1 for ark1 in ark.split(",") if ark1 != ''])
            nbARK = len(ark.split(","))
            if (ark == ""):
                nbARK = 0   
            if (ark == "Pb FRBNF"):
                nb_notices_nb_ARK["Pb FRBNF"] += 1
            else:
                nb_notices_nb_ARK[nbARK] += 1
            if (nb_fichiers_a_produire ==  1):
                row2file(nb_fichiers_a_produire,nbARK,NumNot,frbnf,current_ark,ark,isbn_nett,titre_nett,auteur_nett,unique_file_results_frbnf2ark)
            elif(nb_fichiers_a_produire ==  2):
                row2files(nb_fichiers_a_produire,nbARK,NumNot,frbnf,current_ark,ark,isbn_nett,titre_nett,auteur_nett,multiple_files_pbFRBNF,multiple_files_0_ark,multiple_files_1_ark,multiple_files_plusieurs_ark)
        stats_extraction(nb_notices_nb_ARK)
        print("Programme terminé")
    
            
def stats_extraction(nb_notices_nb_ARK):
    for key in nb_notices_nb_ARK:
        report_file.write(str(key) + "\t" + str(nb_notices_nb_ARK[key]) + "\n")
    nb_notices_nb_ARK[-1] = nb_notices_nb_ARK.pop('Pb FRBNF')
    plt.bar(list(nb_notices_nb_ARK.keys()), nb_notices_nb_ARK.values(), color='skyblue')
    plt.show()
        

#==============================================================================
# Création de la boîte de dialogue
#==============================================================================

master = tk.Tk()
master.config(padx=30, pady=20)

#définition input URL (u)
tk.Label(master, text="\nFichier contenant les notices\nFormat : Num Not|FRBNF|ARK|ISBN|Titre|Auteur\nSéparateur TAB)", justify="left").pack(side="left")
entry_filename = tk.Entry(master, width=20, bd=2)
entry_filename.pack(side="left")
entry_filename.focus_set()

#Choix du format
tk.Label(master, text="\tEn sortie : ").pack(side="left")
file_nb = tk.IntVar()
tk.Radiobutton(master, text="1 fichier", variable=file_nb , value=1).pack(side="left")
tk.Radiobutton(master, text="Plusieurs fichiers \n(Pb / 0 / 1 / plusieurs ARK trouvés)", justify="left", variable=file_nb , value=2).pack(side="left")
file_nb.set(2)

#file_format.focus_set()
b = tk.Button(master, text = "OK", width = 20, command = callback, borderwidth=1)
b.pack()




tk.mainloop()

