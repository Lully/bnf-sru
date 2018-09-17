# coding: utf-8

from pprint import pprint
from collections import defaultdict
import urllib.parse, urllib.request

from lxml.html import parse



url = "https://archivesetmanuscrits.bnf.fr/resultatRechercheSimple.html?TEXTE_LIBRE_INPUT=\
marcel+proust&DOC_NUMERISE_INPUT_RADIO=all_docs"

def words2url(searchwords):
    searchwords = urllib.parse.quote(searchwords.replace(" ", "+"))
    url = "".join(["https://archivesetmanuscrits.bnf.fr/resultatRechercheSimple.html?",
                    "TEXTE_LIBRE_INPUT=", 
                    searchwords, 
                    "&DOC_NUMERISE_INPUT_RADIO=all_docs",
                    "pageEnCours=1&nbResultParPage=100"])
    return url    

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
    doc_localisation = node2texvalue(IR, "h2")
    ir_title = node2texvalue(IR, "div[@class='naf ']")
    if not ir_title:
        ir_title = node2texvalue(IR, "div[@class='naf titreIrCliquable']//p/a")
    return doc_localisation, ir_title

def node2texvalue(node, path):
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
        c_title = node2texvalue(c, ".//a")
        c_link = node2attr(c, ".//a", "href")
        c_link = c_link.replace("./", "")
        liste_c[c_link] = c_title
    if not liste_c:
        c_link = node2attr(IR, ".//a", "href")
        c_link = c_link.replace("./", "")
        liste_c[c_link] = ""
    return liste_c


def url2parse(url, outputfile):
    page = parse(urllib.request.urlopen(url))
    nb_results = page2nb_results(page)
    liste_liens = page2links(page)
    # pprint(liste_liens)
    results2report(liste_liens, outputfile)


def page2nb_results(page):
    nb_results = node2textvalue(page, ".//div[@class='paginationBam hautPaginationBam']/div")
    if not nb_results:
        return 0
    else:
        nb_results = nb_results.split()[0].strip()
        return int(nb_results)


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
    url = words2url(searchwords)
    url2parse(url, outputfile)
    outputfile.close()