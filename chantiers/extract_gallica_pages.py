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
from udecode import udecode

import re

from aut2id_concepts import accesspoint2sru
import SRUextraction as sru
from stdf import *

headers = "URL page,URL lien,Texte,Nb résultats,URL SRU Gallica,Requête initiale,A modifier ?,motif,Nouvelle requête GF,\
Nouvelle URL GF,Nouvelle requête Lieu,Nouvelle URL Lieu".split(",")
referentielGF_libelles = file2list("referentiel_gf.txt")
referentielGF_libelles = [udecode(el.lower()) for el in referentielGF_libelles]
subdiv_lieu = file2list("subdiv_lieux.txt")
subdiv_lieu = [udecode(el.lower()) for el in subdiv_lieu]
query_done = {}
entitesLieu = {}


class Query:
    def __init__(self, url, text=""):
        self.url = url
        self.text = text
        self.params = url.split("?")[1].split("&")
        self.params = extract_params(self.params)
        self.query = urllib.parse.unquote(self.params["query"])
        self.nb_results, self.sru_url = query2results(self.query)
        [self.gf_query, self.loc_query,
         self.hist_crit_query, self.alertes] = extract_subjects(self.query)
        self.gf_url = query2url(self.gf_query, self.params)
        self.loc_url = query2url(self.loc_query, self.params)
        self.hist_crit_url = query2url(self.hist_crit_query, self.params)
        self.alertes = ",".join(list(set(self.alertes)))
        if ("Genre" not in self.alertes):
            [self.gf_query, self.gf_url]= ["", ""]
        if ("lieu" not in self.alertes):
            [self.loc_query, self.loc_url]= ["", ""]
        if ("critique" not in self.alertes):
            [self.hist_crit_query, self.hist_crit_url]= ["", ""]


def extract_params(params):
    dict_params = {}
    for el in params:
        el = el.split("=")
        if len(el) == 2:
            critere = el[0]
            value = el[1]
            dict_params[critere] = value
        elif len(el) > 2:
            critere = el[0]
            value = "=".join(el[1:])
            dict_params[critere] = value
    dict_params["query"] = udecode(dict_params["query"].lower())
    return dict_params


def query2url(query, params):
    url = "https://gallica.bnf.fr/services/engine/search/sru?"
    url += f"query=({urllib.parse.quote(query)})"
    for entry in params:
        if entry != "query":
            url += f"&{entry}={params[entry]}"
    if query == "":
        url = ""
    return url

def query2results(query):
    query = query.split("/sort")[0].split(" sortby")[0]
    url_root = "https://gallica.bnf.fr/SRU?"
    results = sru.SRU_result(query, url_root, {"recordSchema": "dublincore"})
    nb_results = str(results.nb_results)
    return nb_results, results.url

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
    hist_crit_query, alertes = analyse_hist_crit_in_query(list_req2, alertes)
    return gf_query, loc_query, hist_crit_query, alertes


def analyse_hist_crit_in_query(query_elements, alertes):
    list_elements = []
    for el in query_elements:
        if "histoire et critique" in el:
            list_elements.append(el.lower().replace("--histoire et critique", "").replace("-- histoire et critique", ""))
            alertes.append("Histoire et critique")
        else:
            list_elements.append(el)
    list_elements = " ".join(list_elements)
    return list_elements, alertes

def analyse_GF_in_query(query_elements, alertes):
    list_elements = []
    for el in query_elements:
        if "dc.subject" in el:
            alert = searchGFinQuery(el)
            if alert:
                alertes.append("Genre-forme")
            list_subjects = []
            list_gf = []
            try:
                critere, elements, fin = el.split('"')
            except ValueError:
                critere, elements = el.split('"')[0], el.split('"')[1]
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


def searchGFinQuery(query_element):
    test = False
    split_criteres = [" -- ", "--", '"', " or ", " and ", " any ",
                      " all ", " adj ", " notice ", " dc.type "]
    for el in split_criteres:
        query_element = query_element.replace(el, "¤")
    query_element = [el.strip() for el in query_element.split("¤") if el.strip()]
    for el in query_element:
        el = udecode(el).lower()
        if el in referentielGF_libelles:
            test = True
    if test is False:
        for el_gf in referentielGF_libelles:
            for el in query_element:
                el = udecode(el).lower()
                if el_gf in el:
                    test = True
    print(test)
    return test



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
            alert = searchLOCinQuery(el)
            if alert:
                alertes.append("Nom de lieu (?) + subdiv")
            list_subjects = []
            try:
                critere, elements, fin = el.split('"')
            except ValueError:
                critere, elements = el.split('"')[0], el.split('"')[1]
                if len(el.split('"')) > 2:
                    fin = '"'.join(el.split('"')[2:])
                else:
                    fin = ""
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


def searchLOCinQuery(query_element):
    test = False
    split_criteres = [" -- ", "--", '"', " or ", " and ", " all ", " adj ", " any ",
                      " notice ", " dc.type "]
    for el in split_criteres:    
        query_element = query_element.replace(el, "¤")
    query_element = [el.strip() for el in query_element.split("¤") if el.strip()]
    for el in query_element:
        if el.lower in subdiv_lieu:
            test = True
    query_element = udecode(" ".join(query_element).lower())
    if test is False:
        for el in subdiv_lieu:
            if el in query_element:
                test = True
    return test


def analyse_file(filename, report, errors_report):
    """
    Analyse d'un fichier contenant une URL par ligne
    Il faut ouvrir chaque page et y regarder les URL présentes
    Si pertinent, réécrire les URL selon réforme Rameau
    """
    liste_pages = file2list(filename)
    url_pages_done = []
    for page in liste_pages:
        if page not in url_pages_done:
            url_pages_done.append(page)
            print("\n"*10, url_pages_done)
            url_pages_done = analyse_page(page, report, url_pages_done, errors_report)
            


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


def analyse_page(url_page, report, url_pages_done, errors_report):
    #parser = etree.HTMLParser()
    #content = url2strcontent(url_page)
    content = fromstring(url2strcontent(url_page, errors_report))
    url_supp = set()
    if content is not None:
        for link in content.xpath("//a"):
            text = ""
            if link.text is not None:
                text = link.text.strip()
            elif link.find("img") is not None and link.find("img").get("alt") is not None:
                text = "Image / " + link.find("img").get("alt").strip()
            link = link.get("href")
            if (link is not None 
               and "gallica.bnf.fr/services/engine/search/sru?" in link):
                analyse_link(link, text, url_page, report)
            elif(link is not None
                 and "gallica.bnf.fr/html/und" in link
                 and link not in url_pages_done):
                url_supp.add(link)
             
    for url_page in url_supp:
        if url_page not in url_pages_done:
            url_pages_done.append(url_page)
            url_pages_done = analyse_page(url_page, report, url_pages_done, errors_report)

    return url_pages_done
                
                


def analyse_link(link, text, url_page, report):
    """
    Identifier si un lien mérite d'être réécrit
    """
    if link not in query_done:
        query = Query(link, text)
        query_done[link] = query
    else:
        query = query_done[link]
    message = "non"
    if query.alertes:
        message = "oui"
    # URL page,URL lien,A modifier ?,motif,nouvelle URL
    line = [url_page, link,
            query.text, query.nb_results,
            query.sru_url,
            query.query, message,
            query.alertes, 
            query.gf_query, query.gf_url,
            query.loc_query, query.loc_url,
            query.hist_crit_query, query.hist_crit_url]
    line2report(line, report)



if __name__ == "__main__":
    filename = input("Fichier contenant les URL des pages à inspecter (une URL par ligne) :\n")
    if filename == "":
        filename = "url_gallica.txt"
    report = input2outputfile(filename, "analyse_url")
    errors_report = input2outputfile(filename, "erreurs")
    line2report(headers, report)
    analyse_file(filename, report, errors_report)