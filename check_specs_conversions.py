# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 10:45:57 2017

@author: Lully

Programme de contrôle de conformité sur un ensemble de notices, dans le cadre de la conversion Unimarc
En entrée, un fichier de spécifications
Pour chaque règle, le programme essaie de trouver des exemples en parcourant le catalogue.
Au fur et à mesure où il rencontre un cas de notice correspondant à la règle, il vérifie si la règle est correctement vérifiée ou non.
Quand toutes les règles ont été vérifiées, le programme s'arrête

"""

from lxml import etree
import csv
from collections import defaultdict

ns = {"srw":"http://www.loc.gov/zing/srw/", "mxc":"info:lc/xmlns/marcxchange-v2", "m":"http://catalogue.bnf.fr/namespaces/InterXMarc","mn":"http://catalogue.bnf.fr/namespaces/motsnotices"}


def count_lines(file):
    i = 0
    for line in file:
        i += 1
    return i

def url2query(url):
    query = url[url.find("query=")+6:]
    query = query[:query.find("&")]
    return query

def check_specs(spec_file_name,URLreqSRU,format_source,format_target):
#☺Dictionnaire qui incrémente la liste des résultats
    specifications = defaultdict(dict)
    with open(spec_file_name, newline='\n',encoding="utf-8") as csvfile:
        spec_file = csv.reader(csvfile, delimiter='\t')
        next(spec_file)
        for row in spec_file:
            ID = row[0]
            source_field = row[1]
            source_value = row[2]
            target_field = row[3]
            target_value = row[4]
            specifications[ID]["source_field"] = source_field
            specifications[ID]["source_value"] = source_value
            specifications[ID]["target_field"] = target_field
            specifications[ID]["target_value"] = target_value
    nb_specs = len(specifications)
    nb_checks = 0
    SRUquery = url2query(URLreqSRU)
    launch_test(specifications,nb_specs,nb_checks,SRUquery,format_source,format_target)

def field2path(field):
#field contient un $ ? = sous-zone
    if (field.find("$")>0):
    
#field désigne un indicateur
    elif (field.find("ind")>0):

#field contient des crochets = zone codée
    elif (field.find("["])>0):
        if (int(field[0:field.find("[")])]) < 10):
            path = "//mxc:controlfield[@code='" field[0:field.find("[")]) + "']"]
    

def check_regle(IDregle,regle,notice_source,notice_target):
#==============================================================================
# La règle est un dictionnaire : 
# Clés = source_field, source_value, target_field, target_value
#==============================================================================
    path_source = field2path(source_field)


def launch_test(specifications,nb_specs,nb_checks,SRUquery):
    i = 1
    while (nb_specs > nb_checks):
        notice_source = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=" + SRUquery + "&recordSchema=" + format_source + "&maximumRecords=1&startRecord=" + str(i))
        notice_target = etree.parse("http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=" + SRUquery + "&recordSchema=" + format_target + "&maximumRecords=1&startRecord=" + str(i))
        for regle in specifications:
            (test_realise,valeur_attendue_test) = check_regle(regle, specifications[regle],notice_source,notice_target)
            nb_checks += test_realise
    

if __name__ == '__main__':
    #spec_file_name = input("Nom du fichier de spécifications (sép : tabulations) : ")
    spec_file_name = "specs_sample.txt"
    URLreqSRU = input("URL SRU des notices à parcourir pour vérifier les specs : ")
    format_source = "intermarcxchange"
    format_target = "unimarcxchange"
    check_specs(spec_file_name,URLreqSRU,format_source,format_target)
