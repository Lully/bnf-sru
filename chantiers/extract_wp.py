# coding: utf-8

"""
Fonctions d'extraction d'informations venant de Wikipedia
"""
from urllib import request, parse
import json

from stdf import *

def extract_wp_from_file(filename, report):
    ids = file2list(filename)
    for row in ids:
        metas = extract_wp_id(row)
        line = [row]
        line.extend(metas)
        line2report(line, report)


def wpid2wdid(wp_id):
    # De l'identifiant WIkipedia à l'identifiant Wikidata
    wp_id = parse.unquote(wp_id.replace("_", " "))
    url = f"https://fr.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&ppprop=wikibase_item&redirects=1&titles={parse.quote(wp_id)}"
    page = request.urlopen(url)
    data = json.loads(page.read())
    wd_id = ""
    wp_pages = data["query"]["pages"]
    for wp_page in wp_pages:
        try:
            wd_id = wp_pages[wp_page]["pageprops"]["wikibase_item"]
        except KeyError:
            print(wp_pages)
    return wd_id

def extract_wp_id(wp_id):
    props = {"date of birth": "P569",
             "place of birth": "P19",
             "date of death": "P570",
             "place of death": "P20"}
    wd_id = wpid2wdid(wp_id)
    url = f"https://www.wikidata.org/w/api.php?format=json&action=wbgetclaims&entity={wd_id}"
    page = request.urlopen(url)
    data = json.loads(page.read())
    values = []
    for prop in props:
        # print(data["claims"][props[prop]])
        try:
            mainsnak = data["claims"][props[prop]][0]["mainsnak"]
            val =  mainsnak["datavalue"]["value"]
            if mainsnak["datatype"] == "time":
                val = mainsnak["datavalue"]["value"]["time"]
            elif mainsnak["datatype"] == "wikibase-item":
                val = mainsnak["datavalue"]["value"]["id"]
                val = wd_id2label(val)
        except KeyError:
            val = ""
        values.append(val)
    return values

def wd_id2label(wd_id):
    url = f"https://www.wikidata.org/w/api.php?format=json&action=wbgetclaims&entity={wd_id}&property=P1705"
    page = request.urlopen(url)
    data = json.loads(page.read())
    try:
        label = data["claims"]["P1705"][0]["mainsnak"]["datavalue"]["value"]["text"]
    except KeyError:
        url = f"https://www.wikidata.org/w/api.php?format=json&action=wbgetclaims&entity={wd_id}&property=P373"
        page = request.urlopen(url)
        data = json.loads(page.read())
        try:
            label = data["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"]
        except KeyError:
            label = wd_id
        except TypeError:
            print("data P373", data)
            label = wd_id
    except TypeError:
        print("data", data)
        label = wd_id
    return label


if __name__ == "__main__":
    filename = input("Nom du fichier contenant les identifiants : ")
    if filename == "":
        filename = "id_wp_test.txt"
    report = input2outputfile(filename, "metas")
    extract_wp_from_file(filename, report)