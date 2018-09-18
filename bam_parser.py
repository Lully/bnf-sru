# coding: utf-8

from pprint import pprint
from collections import defaultdict
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from lxml import html
import requests

   # Set POST fields here


from lxml.html import parse


def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def words2url(searchwords):
    searchwords = quote(searchwords.replace(" ", "+"))
    return searchwords    


def page2links(page):
    """
    Extraction des liens à partir d'une page de résultats
    Regroupés par IR ?
    """
    ir_path = ".//div[@class='blocBlanc blocTypeItem']"
    results = defaultdict(dict)
    i = 0
    for IR in page.xpath(ir_path):
        doc_localisation, ir_title = meta_ir(IR)
        components = ir2c(IR)
        results[i]["title"] = ir_title
        results[i]["localisation"] = doc_localisation
        results[i]["components"] = components
        i += 1
    return results


def meta_ir(IR):
    """
    Pour un noeud HTML d'instrument de 
    recherche dans une liste de résultats, 
    on extrait les métas principales de l'IR :
    Bibliothèque, cote, titre
    """
    doc_localisation = node2textvalue(IR, "h2")
    ir_title = node2textvalue(IR, "div[@class='naf ']")
    if not ir_title:
        ir_title = node2textvalue(IR, "div[@class='naf titreIrCliquable']//p/a")
    return doc_localisation, ir_title


def node2textvalue(node, path):
    val = ""
    if node.find(path) is not None:
        val = node.find(path).text
    return val


def node2attr(node, path, attr):
    val = ""
    if node.find(path) is not None:
        el = node.find(path)
        val = el.get(attr)
    return val


def ir2c(IR):
    """
    Pour un noeud HTML d'instrument de 
    recherche dans une liste de résultats, 
    on extrait la liste des composants de l'IR
    correspondant à la recherche
    """
    liste_c = defaultdict(str)
    for c in IR.xpath(".//div[@class='occurrenceItem clearfix']"):
        c_title = node2textvalue(c, ".//a")
        c_link = node2attr(c, ".//a", "href")
        c_link = c_link.replace("./", "")
        liste_c[c_link] = c_title
    if not liste_c:
        c_link = node2attr(IR, ".//a", "href")
        c_link = c_link.replace("./", "")
        liste_c[c_link] = ""
    return liste_c


def url2parse(urlroot, searchwords, outputfile, params, no_page):
    if (no_page != 1):
        params = {'pageEnCours': str(no_page),
                  'nbResultParPage': '100'}
  
    request = requests.post(urlroot, data=params)
    page = html.fromstring(request.content)
    nb_pages = 1
    if (no_page == 1):
        nb_results = page2nb_results(page)
        if (nb_results > 100):
            nb_pages = int(str(nb_results)[:-2]) + 1

        print(nb_results, nb_pages)
        liste_liens = page2links(page)
        results2report(liste_liens, outputfile)
    if (page.find(".//li[@class='next']/a") is not None):
        li = page.find(".//li[@class='next']/a")
        url_next = li.get("href")
        url_next = "https://archivesetmanuscrits.bnf.fr/" + url_next
        pagesuivante(url_next, outputfile)

def pagesuivante(url, outputfile):
    print(url)
    page = html.parse(urlopen(url))
    liste_liens = page2links(page)
    results2report(liste_liens, outputfile)   
    if (page.find(".//li[@class='next']/a") is not None):
        li = page.find(".//li[@class='next']/a")
        url_next = li.get("href")
        url_next = "https://archivesetmanuscrits.bnf.fr/" + url_next
        pagesuivante(url_next, outputfile)


def page2nb_results(page):
    nb_results = node2textvalue(page, ".//div[@class='paginationBam hautPaginationBam']/div")
    if not nb_results:
        return 0
    else:
        nb_results = nb_results.split()[0].strip()
        if (RepresentsInt(nb_results)):
            return int(nb_results)
        else:
            return 0


def results2report(liste_liens, outputfile):
    headers = ["IR / Titre",
               "IR / localisation",
               "Composant / ARK",
               "Composant / Titre"]
    outputfile.write("\t".join(headers) + "\n")
    for IR in liste_liens:
        for component in liste_liens[IR]["components"]:
            line = [liste_liens[IR]["title"],
                    liste_liens[IR]["localisation"],
                    component,
                    liste_liens[IR]["components"][component]]
            print(line)
            outputfile.write("\t".join(line) + "\n")


if __name__ == "__main__":
    searchwords = input("Mots recherchés : ")
    outputfilename = input("Nom fichier rapport : ")
    if (outputfilename[-4] != "."):
        outputfilename += ".txt"
    outputfile = open(outputfilename, "w", encoding="utf-8")
    if not searchwords:
        searchwords = "marcel proust"
    searchwords = words2url(searchwords)
    post_fields = {'TEXTE_LIBRE_INPUT': searchwords,
        'DOC_NUMERISE_INPUT_RADIO': 'all_docs'}
    url_gen = 'https://archivesetmanuscrits.bnf.fr/resultatRechercheSimple.html'
    url2parse(url_gen, searchwords, outputfile, post_fields, 1)
    outputfile.close()