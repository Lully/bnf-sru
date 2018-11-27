# coding: utf-8

"""
Fonctions de vérification de la conformité des notices Unimarc
avec un format de référence (Abes ou BnF)
Comme format de référence, on peut fournir un fichier en entrée
A défaut, aspiration des pages HTML du site documentation.abes.fr
"""

from collections import defaultdict
from lxml import etree
from lxml.html import parse

import SRUextraction as sru
from stdf import create_file, line2report


def file_rum2rum(rum_filename, recordtype="b"):
    """
    Constitution de la liste des zones autorisées
    Si pas de nom de fichier fourni --> aspiration du site documentation.abes.fr
    """
    rum_content = []
    if rum_filename:
        with open(rum_filename) as rum_file_content:
            for row in rum_file_content:
                rum_content.append(row.replace("\r", "").replace("\n", ""))
    else:
        rum_content = abes2rum(recordtype)
    return rum_content


def abes2rum(recordtype):
    # Ouvrir la page et récupérer tous les liens dont le href contient "zones/"
    # Si sous-zones (pas le cas des 00X)
    # <table> qui contient tbody/tr[@class='entete'] --> récupérer le 4e <td>
    rum_content = []
    url_sommaire_abes = f"http://documentation.abes.fr/sudoc/formats/unm{recordtype}/index.htm"
    liste_zones = extract_zones_from_page_abes(recordtype, url_sommaire_abes)
    rum_content = fields2subfields(recordtype, liste_zones)
    return rum_content

def extract_zones_from_page_abes(recordtype, url_sommaire_abes):
    liste_zones = []
    page = parse(url_sommaire_abes)
    for lien in page.xpath("//a"):
        url = lien.get("href")
        if (url and "zones/" in url):
            zone = url.split("/")[1].split(".")[0]
            liste_zones.append(zone)
    return liste_zones


def fields2subfields(recordtype, liste_zones):
    rum_content = []
    for zone in liste_zones:
        print("Zone", zone)
        url = f"http://documentation.abes.fr/sudoc/formats/unm{recordtype}/zones/{zone}.htm"
        liste_souszones = page2subfields(url)
        for subf in liste_souszones:
            rum_content.append(f"{zone}${subf}")
    return rum_content


def page2subfields(url):
    liste_subfields = []
    page = parse(url)
    for table in page.xpath("//table[tr[@class='entete']]"):
        #print(etree.tostring(table))
        for tr in table.xpath(".//tr"):     
            try:
                col4 = tr.xpath("td")[3]
                if (col4.find("a") is not None
                    and col4.find("a").text is not None):
                    col4 = col4.find("a").text.strip()
                elif (col4 is not None 
                      and col4.text is not None):
                    col4 = col4.text.strip()
                if (len(col4) == 1):
                    liste_subfields.append(col4)
            except IndexError:
                pass
    return liste_subfields

def launch(recordtype, rum_filename):
    """
    Exécution des différentes étapes du programme
    """
    print("Constitution du référentiel format")
    rum_content = file_rum2rum(rum_filename, recordtype)
    print("fin de la constitution du référentiel")


if __name__ == "__main__":
    recordtype = input("Type de notices : (B)iblio ou (A)utorité ? ").lower()
    if recordtype == "":
        recordtype = "b"
    rum_filename = input("Fichier contenant le rum (liste de zones/sous-zones autorisées)\
\nSi vide, aspire le site documentation.abes.fr\n")

    launch(recordtype, rum_filename)
