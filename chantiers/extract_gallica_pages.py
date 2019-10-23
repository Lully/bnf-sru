# coding: utf-8

"""
Extraire les URL de requêtes profondes des pages de médiation Gallica
pour sortir celles qui sont concernées par la réforme Rameau :
- chaine d'indexation Lieu + Sujet
- genre-forme
- Histoire et critique
- "Histoire" (!= discipline)
"""

from lxml import etree
from lxml.html import fromstring
from urllib import request
import urllib.parse
import urllib.error

import re

from aut2id_concepts import accesspoint2sru
import SRUextraction as sru
from stdf import *

headers = "URL page,URL lien,Requête initiale,A modifier ?,motif,Nouvelle requête GF,\
Nouvelle URL GF,Nouvelle requête Lieu,Nouvelle URL Lieu".split(",")
referentielGF_libelles = file2list("referentiel_gf.txt")
referentielGF_libelles = [el.lower() for el in referentielGF_libelles]
subdiv_lieu = file2list("subdiv_lieux.txt")
subdiv_lieu = [el.lower() for el in subdiv_lieu]
entitesLieu = {}
url_pages_done = []

class Query:
    def __init__(self, url):
        self.url = url
        self.params = {el.split("=")[0]: el.split("=")[1] for el in url.split("?")[1].split("&")}
        self.query = urllib.parse.unquote(self.params["query"])
        self.gf_query, self.loc_query, self.alertes = extract_subjects(self.query)
        self.gf_url = query2url(self.gf_query, self.params)
        self.loc_url = query2url(self.loc_query, self.params)
        self.alertes = ",".join(list(set(self.alertes)))
        if ("Genre" not in self.alertes):
            [self.gf_query, self.gf_url]= ["", ""]
        if ("lieu" not in self.alertes):
            [self.loc_query, self.loc_url]= ["", ""]


def query2url(query, params):
    url = "https://gallica.bnf.fr/services/engine/search/sru?"
    url += f"query=({urllib.parse.quote(query)})"
    for entry in params:
        if entry != "query":
            url += f"&{entry}={params[entry]}"
    if query == "":
        url = ""
    return url

def extract_subjects(sru_query):
    sru_query = sru_query.replace("(", "").replace(")", "")
    list_req = [el.replace("(", "").replace(")", "").strip() for el in sru_query.split(" and ")] 
    list_req = [el for el in list_req if el]
    list_req = [f"and {el}" for el in list_req]
    list_req[0] = list_req[0].replace("and ", "")
    list_req2 = []
    for el in list_req:
        if " or " in el:
            first = el.split(" or ")[0]
            foll = el.split(" or ")[1:]
            list_req2.append(first)
            list_req2.extend([f" or {el}" for el in foll])
        else:
            list_req2.append(el)
    alertes = []
    gf_query, alertes = analyse_GF_in_query(list_req2, alertes)
    loc_query, alertes = analyse_location_in_query(list_req2, alertes)
    return gf_query, loc_query, alertes

def analyse_GF_in_query(query_elements, alertes):
    list_elements = []
    for el in query_elements:
        if "dc.subject" in el:
            list_subjects = []
            list_gf = []
            try:
                critere, elements, fin = el.split('"')
            except ValueError:
                criteres, elements = el.split('"')[0], el.split('"')[1]
                if len(el.split('"')) > 2:
                    fin = '"'.join(el.split('"')[2:])
                else:
                    fin = ""
            elements = elements.split("--")
            for element in elements:
                libelle = element.strip().lower()
                if libelle in referentielGF_libelles:
                    alertes.append("Genre-forme")
                    list_gf.append(libelle)
                else:
                    list_subjects.append(libelle)
            if list_subjects:
                list_elements.append(f"{critere} \"{' -- '.join(list_subjects)}\"")
            if list_gf:
                list_elements.append(f"and dc.description all \"{' '.join(list_gf)}\"")
        else:
            list_elements.append(el)
    list_elements = " ".join(list_elements)
    return list_elements, alertes

def analyse_location_in_query(list_req, alertes):
    """
    Vérifier s'il y a un lieu suivi d'une subdivision au lieu
    En ce cas, il faut inverser l'ordre de la chaîne de caractères
    """
    list_elements = []
    pos_loc = 0
    pos_subdiv = 0
    for el in list_req:
        if "dc.subject" in el:
            list_subjects = []
            critere, elements, fin = el.split('"')
            elements = elements.split("--")
            i = 0
            for element in elements:
                libelle = element.strip()
                if (len(elements) > i+1
                   and elements[i+1].strip().lower() in subdiv_lieu):
                    arks, methode = accesspoint2sru(libelle)
                    if arks:
                        ark = arks.split(",")[0]
                        aut_record = ark2autrecord(ark)
                        if aut_record.find("*[@tag='167']") is not None:
                            alertes.append("Nom de lieu + subdiv")
                        pos_loc = i
                        pos_subdiv = i+1
                list_subjects.append(el)
                i += 1
            list_subjects[pos_loc], list_subjects[pos_subdiv] = list_subjects[pos_subdiv], list_subjects[pos_loc]
            list_elements.append(f"{critere} \"{' -- '.join(list_subjects)}\"")
        else:
            list_elements.append(el)
    list_elements = " ".join(list_elements)
    return list_elements, alertes


def analyse_file(filename, report, errors_report):
    """
    Analyse d'un fichier contenant une URL par ligne
    Il faut ouvrir chaque page et y regarder les URL présentes
    Si pertinent, réécrire les URL selon réforme Rameau
    """
    liste_pages = file2list(filename)
    for page in liste_pages:
        analyse_page(page, report, errors_report)
        url_pages_done.append(page)


def url2strcontent(url, errors_report):
    content = "<html><head><title></title><body><p> </p></body></html>"
    try:
        content = request.urlopen(url)
        content_list = []
        for row in content:
            content_list.append(row.decode("utf-8"))
        content = "\n".join(content_list)
    except urllib.error.HTTPError as err:
        content = "<html><head><title></title><body><p> </p></body></html>"
        errors_report.write(url + "\n")
        errors_report.write(str(err))
    except UnicodeDecodeError as err:
        content = "<html><head><title></title><body><p> </p></body></html>"
        errors_report.write(url + "\n")
        errors_report.write(str(err))
    except TypeError as err:
        content = "<html><head><title></title><body><p> </p></body></html>"
        errors_report.write(url + "\n")
        errors_report.write(str(err))
    return content


def analyse_page(url_page, report, errors_report):
    #parser = etree.HTMLParser()
    #content = url2strcontent(url_page)
    content = fromstring(url2strcontent(url_page, errors_report))
    if content is not None:
        for link in content.xpath("//a"):
            link = link.get("href")
            if (link is not None 
               and "gallica.bnf.fr/services/engine/search/sru?" in link):
                analyse_link(link, url_page, report)
            elif(link is not None
                 and "gallica.bnf.fr/html/und" in link
                 and link not in url_pages_done):
                analyse_page(link, report, errors_report)
                url_pages_done.append(link)


def analyse_link(link, url_page, report):
    """
    Identifier si un lien mérite d'être réécrit
    """
    query = Query(link)
    message = "non"
    if query.alertes:
        message = "oui"
    # URL page,URL lien,A modifier ?,motif,nouvelle URL
    line = [url_page, link, query.query, message, query.alertes, 
            query.gf_query, query.gf_url,
            query.loc_query, query.loc_url]
    line2report(line, report)



if __name__ == "__main__":
    filename = input("Fichier contenant les URL des pages à inspecter (une URL par ligne) :\n")
    if filename == "":
        filename = "url_gallica.txt"
    report = input2outputfile(filename, "analyse_url")
    errors_report = input2outputfile(filename, "erreurs")
    line2report(headers, report)
    analyse_file(filename, report, errors_report)