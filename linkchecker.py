# coding: utf-8

"""
Vérificateur de liens
"""
from urllib import request, error
from lxml.html import parse

from stdf import *

def analyse_site(root, report):
    visited = []
    for url in root:
        if url not in visited:
            visited = analyse_url(url, visited, report)

def analyse_url(url, visited, report):
    if url not in visited:
        visited.append(url)
        alerte = ""
        try:
            content = request.urlopen(url)
            visited = analyse_content(url, content, visited, report)
        except error.URLError:
            alerte = "Erreur URL"
        except error.HTTPError:
            alerte = "Erreur HTTP"
    if alerte:
        line = [url, "", alerte]
        line2report(line, report)
    return visited

def analyse_content(url, content, visited, report):
    if url not in visited:
        visited.append(url)
        content = parse(content)
        title = get_html_element(content, "head/title")
        links = {}
        i = 0
        for link in content.xpath("//a"):
            text = get_html_element(link, ".")
            link = link.get("href")
            links[i] = {"text": text, "link": link}
            if link not in visited:
                visited = analyse_url(link, content, visited, report)
        for link in links:
            line = [url, title, link, links[link]["text"], links[link]["link"]]
            line2report(line, report)
    return visited

def get_html_element(content, path, occ="first"):
    value = ""
    if content.find(path) is not None
      and content.find(path).text is not None:
       value = content.find(path).text
    return value



if __name__ == "__main__":
    print("\nVérification des liens pour un site (internes et externes)\n")
    root = input("URL du site à vérifier (séparateur virgule) : ").split(",")
    report = input("Nom du fichier rapport : ")
    analyse_site(root, report)