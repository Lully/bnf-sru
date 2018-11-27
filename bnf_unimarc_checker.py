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


def file_rim2rim(rim_filename, recordtype="b"):
    """
    Constitution de la liste des zones autorisées
    Si pas de nom de fichier fourni --> aspiration du site documentation.abes.fr
    """
    rim_content = []
    if rim_filename:
        with open(rim_filename) as rim_file_content:
            for row in rim_file_content:
                rim_content.append(row.replace("\r", "").replace.("\n", ""))
    else:
        url_sommaire_abes = f"http://documentation.abes.fr/sudoc/formats/unm{recordtype}/index.htm"
    return rim_content

if __name__ == "__main__":
    recordtype = input("Type de notices : (B)iblio ou (A)utorité ? ").lower()
    if recordtype == "":
        recordtype = "b"
    rim_filename = input("Fichier contenant le RIM (liste de zones/sous-zones autorisées)\
\nSi vide, aspire le site documentation.abes.fr")
    rim_content = file_rim2rim(rim_filename, recordtype)
    