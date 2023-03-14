# -*- coding: utf-8 -*-
"""
Created on Thu Mar 29 12:03:35 2018

@author: Etienne Cavalié

Petit programme qui prend en entrée une liste d'ARK de notices Rameau sous la forme 
ark:/12148/cb123916837
ark:/12148/cb12391882f
ark:/12148/cb12392040j
ark:/12148/cb12392112k

et qui permet de récupérer un fichier SKOS (format NT)

"""

from lxml import etree
import urllib.parse
from urllib import request
import csv

ns = {"srw": "http://www.loc.gov/zing/srw/", "mxc": "info:lc/xmlns/marcxchange-v2",
      "m":"http://catalogue.bnf.fr/namespaces/InterXMarc","mn":"http://catalogue.bnf.fr/namespaces/motsnotices"}


mappingMarc2SKOS = {
        "prefLabel": ["161$a$x$g", "162$a$x$g", "163$a$x$g",
                      "164$a$x$g", "165$a$x$g", "166$a$x$g",
                      "167$a$x$g", "168$a$x$g", "169$a$x$g"],
        "altLabel": ["461$a$x$g", "462$a$x$g", "463$a$x$g",
                     "464$a$x$g", "465$a$x$g", "466$a$x$g",
                     "467$a$x$g", "468$a$x$g", "469$a$x$g"],
        "broader": ["502$3"],
        "narrower": ["302$3"],
        "note": ["600$a"],
        "scopeNote": ["202$a"],
        "editorialNote": ["610$a"]}



def ark2field(record, field, ark):
    f = field.split("$")[0]
    liste_subf = field.split("$")[1:]
    liste_values = []
    field_path = "*[@tag='" + f + "']"
    for field_occ in record.xpath(field_path):
        field_val = []
        for subf in liste_subf:
            path = "*[@code='" + subf + "']"
            for sub in field_occ.xpath(path):
                if (subf == "3"):
                    field_val.append(ark)
                else:
                    field_val.append('"' + sub.text.replace('"', '\"') + '"@fr')
        field_val = " -- ".join(field_val)
        liste_values.append(field_val)
    return liste_values


def ark2skos(ark):
    url = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query=aut.persistentid%20all%20%22" + urllib.parse.quote(ark) + "%22&recordSchema=intermarcxchange&maximumRecords=20&startRecord=1"
    print(ark)
    record = etree.parse(request.urlopen(url)).find("//mxc:record", namespaces=ns)
    if record is not None:
        for el in mappingMarc2SKOS:        
            for field in mappingMarc2SKOS[el]:
                values = ark2field(record, field, ark)
                if (values != []):
                    for value in values:
                        output_file.write('<http://data.bnf.fr/' + ark + '> <http://www.w3.org/2004/02/skos/core#' + el + '> ' + value + ".\n")
    else:
        print("Notice", ark, "non trouvée")


input_file_name = input("\n\nNom du fichier contenant la liste des ark : ")
output_file_name = input("\n\nNom du fichier en sortie : ")
if (output_file_name == ""):
    output_file_name = "export_skos.txt"
if (output_file_name[-4] != "."):
    output_file_name = output_file_name + ".txt"
output_file = open(output_file_name, "w",encoding="utf-8")

    
with open(input_file_name, newline='\n',encoding="utf-8") as csvfile:
        entry_file = csv.reader(csvfile, delimiter='\t')
        for row in entry_file:
            ark2skos(row[0])
        csvfile.close()

output_file.close()
    
