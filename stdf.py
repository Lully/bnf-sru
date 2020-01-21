# coding: utf-8

"""
Ensemble de fonctions standard pour la génération de rapports
la manipulation de fichiers, etc.
"""

import io
from lxml import etree
import http.client
import csv
import re
import string
import json
from urllib import request, error, parse
from pprint import pprint
from collections import defaultdict

from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions

import SRUextraction as sru


def create_file(filename, headers=[], mode="w", display=True):
    """
    Crée un fichier à partir d'un nom. 
    Renvoie le fichier en objet
    """
    file = open(filename, mode, encoding="utf-8")
    if headers:
        if display:
            print(headers)
        file.write("\t".join(headers) + "\n")
    return file

def file2dict(inputfilename, col_key=0, col_val=-1, all_values=False):
    """
    Convertit un fichier en dictionnaire : prend la 1ère colonne comme clé
    et la colonne 'col_val' comme valeur
    """
    dict = {}
    with open(inputfilename, encoding="utf-8") as  csvfile:
        entry_file = csv.reader(csvfile, delimiter='\t')
        if all_values:
            headers = next(entry_file)
            headers.pop(col_key)
            for row in entry_file:
                identifier = row[col_key]
                dict[identifier] = {}
                row.pop(col_key)
                i = 0
                for col in row:
                    dict[identifier][headers[i]] = col
                    i += 1

        else:
            for row in entry_file:
                dict[row[col_key]] = row[col_val]
    return dict


def input2default(value, default):
    if value == "":
        return default
    elif type(default) == int:
        try:
            value = int(value)
        except TypeError:
            print("Erreur des données en entrée : int attendu")
            raise
    elif type(default) == bool:
        value = bool(value)
    return value


def close_files(files_list):
    for file in files_list:
        file.close()

def bib_record2date(xml_record):
    """
    Pour une notice BIB, extrait la date en 008
    ou, à défaut, en 260$d nettoyée
    """
    date = ""
    f008 = sru.record2fieldvalue(xml_record, "008")[8:12]
    if (re.fullmatch(".*\d+.*", f008) is not None):
        date = f008
    else:
        f260d = sru.record2fieldvalue(xml_record, "260$d")
        f260d_nett = clean_date(f260d)
        if f260d_nett:
            date = f260d_nett
        else:
            date = f260d
    return date

def clean_date(date):
    date_clean = "".join([el for el in date if udecode(el.lower()) not in string.ascii_lowercase])
    ponctuation = [
                    ".", ",", ";", ":", "?", "!", "%", "$", "£", "€", "#", "\\", "\"", "&", "~",
                    "{", "(", "[", "`", "\\", "_", "@", ")", "]", "}", "=", "+", "*", "\/", "<",
                    ">", ")", "}", "̊"
                    ]
    for char in ponctuation:
        date_clean = date_clean.replace(char, "")
    return date_clean

def nn2ark(nna_nnb):
    """
    Convertit un NNB ou un NNA en ARK
    En entrée, le NNB ou NNA, nettoyé, de type str
    """
    type = "bib"
    if (nna_nnb.startswith("1") or nna_nnb.startswith("2")):
        type = "aut"
    query = f'{type}.recordid any "{nna_nnb}"'
    if (type == "aut"):
        query += ' and aut.status any "sparse validated"'
    results = sru.SRU_result(query, parametres={'recordSchema': 'intermarcxchange'})
    return results.list_identifiers


def input2outputfile(inputfilename, suffix):
    """
    A partir d'un nom de fichier (TXT ou CSV en général) en entrée,
    génération d'un fichier d'écriture en sortie, avec ajout d'un suffixe
    """
    outputfilename = inputfilename[:-4] + "-" + suffix + ".txt"
    try:
        if (suffix[-4] == "."):
            outputfilename = outputfilename[:-4]
    except IndexError:
        pass
    outputfile = create_file(outputfilename)
    return outputfile


def line2report(line, report, i=0, display=True):
    """
    Envoie une line (liste) dans un fichier.
    Sauf demande contraire, affiche la ligne
    dans le terminal avec un compteur
    """
    if display:
        if i:
            print(i, line)
        else:
            print(line)
    try:
        report.write("\t".join(line) + "\n")
    except TypeError:
        report.write("\t".join([str(el) for el in line]) + "\n")


def ddprint(defaultdict):
    """
    Formation d'impression de defaultdict (pprint ne le prévoit pas)
    """
    tempdict = dict(defaultdict)
    pprint(tempdict)
    return tempdict

def compare2lists(liste1, liste2):
    liste_commune = []
    in_liste1_only = []
    in_liste2_only = []
    i = 1
    len_liste1 = len(liste1)
    len_liste2 = len(liste2)
    for ark in liste1:
        if ark in liste2:
            liste_commune.append(ark)
        else:
            in_liste1_only.append(ark)
        if (i % 1000 == 0):
            print("liste1", i, "/", len_liste1)
        i += 1
    i = 1
    for ark in liste2:
        if ark in liste1:
            liste_commune.append(ark)
        else:
            in_liste2_only.append(ark)
        if (i % 1000 == 0):
            print("liste2", i, "/", len_liste2)
        i += 1
    liste_commune = list(set(liste_commune))
    in_liste1_only = list(set(in_liste1_only))
    in_liste2_only = list(set(in_liste2_only))
    return liste_commune, in_liste1_only, in_liste2_only


def file2list(filename, all_cols=False):
    liste = []
    if filename.startswith("http"):
        file = request.urlopen(filename)
        for line in file:
            liste.append(line.decode(encoding="utf-8").replace("\n", "").replace("\r", ""))
    else:
        try:
            file = open(filename, encoding="utf-8")
            content = csv.reader(file, delimiter="\t")
            for row in content:
                if row:
                    if all_cols:
                        liste.append(row)
                    else:
                        liste.append(row[0])
            file.close()
        except FileNotFoundError:
            pass
    return liste


def list2file(liste, file, sep="\n"):
    for el in liste:
        file.write(f"{el}{sep}")


def sparql2dict(endpoint, sparql_query, liste_el):
    sparql = SPARQLWrapper(endpoint)
    """
    En entrée, une requête Sparql et la liste des variables
    à récupérer. La première de ces variables est la clé dans le dictionnaire
    Les autres correspondent à des listes (plusieurs valeurs possibles)
    {"ark:///": {
                 "id_wikidata": ["Q6321654", "QS321"]   
                 "coordonnees_geo": ["48.54656, 12.354684", "45.156165, 27.5165165"]
                 }
    }
    """
    dict_results = {}
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        dataset = results["results"]["bindings"]
        for el in dataset:
            key_name = liste_el[0]
            key_value = el.get(key_name).get("value")
            dict_results[key_value] = defaultdict(list)
            for el_ in liste_el[1:]:
                dict_results[key_value][el_].append(el.get(el_).get("value"))
    except error.HTTPError as err:
        print(err)
        print(sparql_query)
    return dict_results

def ark2nn(ark_catalogue):
    nn = ark_catalogue[ark_catalogue.find("ark:/")+13:-1]
    return nn


def ark2autrecord(ark):
    ns = {"srw": "http://www.loc.gov/zing/srw/",
      "mxc": "info:lc/xmlns/marcxchange-v2",
      "m": "http://catalogue.bnf.fr/namespaces/InterXMarc",
      "mn": "http://catalogue.bnf.fr/namespaces/motsnotices",
      "srw": "http://www.loc.gov/zing/srw/"
      }
    url_sru = url_requete_sru('aut.persistentid any "' + ark + '" and aut.status any "sparse validated"', "intermarcxchange")
    record = etree.Element("root")
    (test,records) = testURLetreeParse(url_sru)
    if (test):
        for rec in records.xpath("//mxc:record", namespaces=ns):
            record = rec
    return record


def url_requete_sru(query, recordSchema="unimarcxchange",
                    maximumRecords="1000", startRecord="1"):
    urlSRUroot = "http://catalogue.bnf.fr/api/SRU?version=1.2&operation=searchRetrieve&query="
    url = urlSRUroot + parse.quote(query) +"&recordSchema=" + recordSchema + "&maximumRecords=" + maximumRecords + "&startRecord=" + startRecord
    #print(url)
    return url


def testURLetreeParse(url):
    test = True
    resultat = ""
    try:
        resultat = etree.parse(request.urlopen(url))
    except etree.XMLSyntaxError as err:
        print(url)
        print(err)
        test = False
    except etree.ParseError as err:
        print(url)
        print(err)
        test = False
    except error.URLError as err:
        print(url)
        print(err)
        test = False
    except ConnectionResetError as err:
        print(url)
        print(err)
        test = False
    except TimeoutError as err:
        print(url)
        print(err)
        test = False
    except http.client.RemoteDisconnected as err:
        print(url)
        print(err)
        test = False
    except http.client.BadStatusLine as err:
        print(url)
        print(err)
        test = False
    except ConnectionAbortedError as err:
        print(url)
        print(err)
        test = False
    return (test, resultat)


def ark2label(ark, record):
    ns = {"srw": "http://www.loc.gov/zing/srw/",
          "mxc": "info:lc/xmlns/marcxchange-v2",
          "m": "http://catalogue.bnf.fr/namespaces/InterXMarc",
          "mn": "http://catalogue.bnf.fr/namespaces/motsnotices",
          "srw": "http://www.loc.gov/zing/srw/"
         }
    marc_label = []
    full_label = []
    label_sans_dept = []
    short_label = []
    test_compl_label = False
    tag_label = ""
    for datafield in record.xpath("mxc:datafield", namespaces=ns):
        tag = datafield.get("tag")
        if (tag[0] == "1"):
            tag_label = tag
            for subfield in datafield.xpath("mxc:subfield", namespaces=ns):
                code = subfield.get("code")
                if (code != "w"):
                    marc_label.append("$"+code)
                    marc_label.append(subfield.text)
                    full_label.append(subfield.text)
                    if (code == "a"):
                        short_label.append(subfield.text)
                if (code != "w" and code != "a"):
                    test_compl_label = True
    marc_label = " ".join(marc_label)
    full_label = " ".join(full_label)
    short_label = " ".join(short_label)
    label_sans_dept = " ".join(label_sans_dept)
    return tag_label, marc_label, full_label, short_label, test_compl_label



def uri2label(uri, prop="skos:prefLabel", sparql_endpoint="https://data.bnf.fr/sparql"):
    """
    A partir d'une URI, récupère 1 propriété (le label)
    """
    ns = {"bibo" : "http://purl.org/ontology/bibo/",
          "bio" : "http://purl.org/vocab/bio/0.1/",
          "bnf-onto" : "http://data.bnf.fr/ontology/bnf-onto/",
          "dbpedia-owl" : "http://dbpedia.org/ontology/",
          "dbpprop" : "http://dbpedia.org/property/",
          "dc" : "http://purl.org/dc/elements/1.1/",
          "dcterms" : "http://purl.org/dc/terms/",
          "dctype" : "http://purl.org/dc/dcmitype/",
          "fb" : "http://rdf.freebase.com/ns/",
          "foaf" : "http://xmlns.com/foaf/0.1/",
          "frbr" : "http://purl.org/vocab/frbr/core#",
          "gr" : "http://purl.org/goodrelations/v1#",
          "isbd" : "http://iflastandards.info/ns/isbd/elements/",
          "isni" : "http://isni.org/ontology#",
          "marcrel" : "http://id.loc.gov/vocabulary/relators/",
          "owl" : "http://www.w3.org/2002/07/owl#",
          "rdac" : "http://rdaregistry.info/Elements/c/",
          "rdae" : "http://rdaregistry.info/Elements/e/",
          "rdaelements" : "http://rdvocab.info/Elements/",
          "rdafrbr1" : "http://rdvocab.info/RDARelationshipsWEMI/",
          "rdafrbr2" : "http://RDVocab.info/uri/schema/FRBRentitiesRDA/",
          "rdai" : "http://rdaregistry.info/Elements/i/",
          "rdam" : "http://rdaregistry.info/Elements/m/",
          "rdau" : "http://rdaregistry.info/Elements/u/",
          "rdaw" : "http://rdaregistry.info/Elements/w/",
          "rdf" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
          "rdfs" : "http://www.w3.org/2000/01/rdf-schema#",
          "skos" : "http://www.w3.org/2004/02/skos/core#"
          }
    prefix_prop = prop.split(":")[0]
    query_ns = f"PREFIX {prefix_prop}: <{ns[prefix_prop]}>\n"
    query = query_ns + """
select ?value where {
    <""" + uri + """> """ + prop + """ ?value.
}
""" 
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    label = ""
    try:
        results = sparql.query().convert()
        dataset = results["results"]["bindings"]
        for el in dataset:
            label = el["value"]["value"]
    except error.HTTPError as err:
        print(err)
        print(query)
    except SPARQLExceptions.EndPointNotFound as err:
        print(err)
        print(query)
    return label


def proxy_opener():
    """
    Utilisation du proxy pour les requêtes HTTP/HTTPS
    """
    proxies = {"http":"fw_in.bnf.fr:8080",
               "https": "fw_in.bnf.fr:8080"}
      
    proxy_handler = request.ProxyHandler(proxies)
    # construct a new opener using your proxy settings
    opener = request.build_opener(proxy_handler)
    # install the opener on the module-level
    request.install_opener(opener)


def json2file(json_data, filename):
    """
    Envoi du contenu d'un dictionnaire dans un fichier JSON
    """
    if type(filename) is str:
        with open(filename, 'w', encoding="utf-8") as outfile:  
            json.dump(json_data, outfile, indent=4)    
    elif type(filename) is io.TextIOWrapper:
        json.dump(json_data, filename)


def udecode(string):
    convert_diacritics = [
        ['ª', 'Á', 'á', 'À', 'à', 'Ă', 'ă', 'Ắ', 'ắ', 'Ằ', 'ằ',
        'Ẵ', 'ẵ', 'Ẳ', 'ẳ', 'Â', 'â', 'Ấ', 'ấ', 'Ầ', 'ầ', 'Ẫ',
        'ẫ', 'Ẩ', 'ẩ', 'Ǎ', 'ǎ', 'Å', 'å', 'Ǻ', 'ǻ', 'Ä', 'ä',
        'Ã', 'ã', 'Ą', 'ą', 'Ā', 'ā', 'Ả', 'ả', 'Ȁ', 'ȁ', 'Ȃ',
        'ȃ', 'Ạ', 'ạ', 'Ặ', 'ặ', 'Ậ', 'ậ', 'Ḁ', 'ḁ', 'Æ', 'æ',
        'Ǽ', 'ǽ', 'ẚ', 'Ⱥ', 'Ḃ', 'ḃ', 'Ḅ', 'ḅ', 'Ḇ', 'ḇ', 'Ć',
        'ć', 'Ĉ', 'ĉ', 'Č', 'č', 'Ċ', 'ċ', 'Ç', 'ç', 'Ḉ', 'ḉ',
        'Ȼ', 'ȼ', 'Ď', 'ď', 'Ḋ', 'ḋ', 'Ḑ', 'ḑ', 'Ḍ', 'ḍ', 'Ḓ',
        'ḓ', 'Ḏ', 'ḏ', 'Đ', 'đ', 'Ð', 'ð', 'Ǳ', 'ǲ', 'ǳ', 'Ǆ',
        'ǅ', 'ǆ', 'É', 'é', 'È', 'è', 'Ĕ', 'ĕ', 'Ê', 'ê', 'Ế',
        'ế', 'Ề', 'ề', 'Ễ', 'ễ', 'Ể', 'ể', 'Ě', 'ě', 'Ë', 'ë',
        'Ẽ', 'ẽ', 'Ė', 'ė', 'Ȩ', 'ȩ', 'Ḝ', 'ḝ', 'Ę', 'ę', 'Ē',
        'ē', 'Ḗ', 'ḗ', 'Ḕ', 'ḕ', 'Ẻ', 'ẻ', 'Ȅ', 'ȅ', 'Ȇ', 'ȇ',
        'Ẹ', 'ẹ', 'Ệ', 'ệ', 'Ḙ', 'ḙ', 'Ḛ', 'ḛ', 'Ḟ', 'ḟ', 'ƒ',
        'Ǵ', 'ǵ', 'Ğ', 'ğ', 'Ĝ', 'ĝ', 'Ġ', 'ġ', 'Ģ', 'ģ', 'Ḡ',
        'ḡ', 'Ĥ', 'ĥ', 'Ḧ', 'ḧ', 'Ḣ', 'ḣ', 'Ḩ', 'ḩ', 'Ḥ', 'ḥ',
        'Ḫ', 'ḫ', 'ẖ', 'Ħ', 'ħ', 'Í', 'í', 'Ì', 'ì', 'Ĭ', 'ĭ',
        'Î', 'î', 'Ǐ', 'ǐ', 'Ï', 'ï', 'Ḯ', 'ḯ', 'Ĩ', 'ĩ', 'İ',
        'Į', 'į', 'Ī', 'ī', 'Ỉ', 'ỉ', 'Ȉ', 'ȉ', 'Ȋ', 'ȋ', 'Ị',
        'ị', 'Ḭ', 'ḭ', 'Ĳ', 'ĳ', 'ı', 'Ĵ', 'ĵ', 'Ḱ', 'ḱ', 'Ķ',
        'ķ', 'Ḳ', 'ḳ', 'Ḵ', 'ḵ', 'Ĺ', 'ĺ', 'Ľ', 'ľ', 'Ļ', 'ļ',
        'Ḷ', 'ḷ', 'Ḹ', 'ḹ', 'Ḽ', 'ḽ', 'Ḻ', 'ḻ', 'Ł', 'ł', 'Ŀ',
        'ŀ', 'Ǉ', 'ǈ', 'ǉ', 'Ƚ', 'Ḿ', 'ḿ', 'Ṁ', 'ṁ', 'Ṃ', 'ṃ',
        'Ń', 'ń', 'Ǹ', 'ǹ', 'Ň', 'ň', 'Ñ', 'ñ', 'Ṅ', 'ṅ', 'Ņ',
        'ņ', 'Ṇ', 'ṇ', 'Ṋ', 'ṋ', 'Ṉ', 'ṉ', 'Ǌ', 'ǋ', 'ǌ', 'º',
        'Ó', 'ó', 'Ò', 'ò', 'Ŏ', 'ŏ', 'Ô', 'ô', 'Ố', 'ố', 'Ồ',
        'ồ', 'Ỗ', 'ỗ', 'Ổ', 'ổ', 'Ǒ', 'ǒ', 'Ö', 'ö', 'Ȫ', 'ȫ',
        'Ő', 'ő', 'Õ', 'õ', 'Ṍ', 'ṍ', 'Ṏ', 'ṏ', 'Ȭ', 'ȭ', 'Ȯ',
        'ȯ', 'Ȱ', 'ȱ', 'Ø', 'ø', 'Ǿ', 'ǿ', 'Ō', 'ō', 'Ṓ', 'ṓ',
        'Ṑ', 'ṑ', 'Ỏ', 'ỏ', 'Ȍ', 'ȍ', 'Ȏ', 'ȏ', 'Ơ', 'ơ', 'Ớ',
        'ớ', 'Ờ', 'ờ', 'Ỡ', 'ỡ', 'Ở', 'ở', 'Ợ', 'ợ', 'Ọ', 'ọ',
        'Ộ', 'ộ', 'Œ', 'œ', 'Ṕ', 'ṕ', 'Ṗ', 'ṗ', 'Ŕ', 'ŕ', 'Ř',
        'ř', 'Ṙ', 'ṙ', 'Ŗ', 'ŗ', 'Ȑ', 'ȑ', 'Ȓ', 'ȓ', 'Ṛ', 'ṛ',
        'Ṝ', 'ṝ', 'Ṟ', 'ṟ', 'Ś', 'ś', 'Ṥ', 'ṥ', 'Ŝ', 'ŝ', 'Š',
        'š', 'Ṧ', 'ṧ', 'Ṡ', 'ṡ', 'Ş', 'ş', 'Ṣ', 'ṣ', 'Ṩ', 'ṩ',
        'Ș', 'ș', 'ſ', 'ẛ', 'ß', 'ẞ', 'ȿ', 'Ť', 'ť', 'ẗ', 'Ṫ',
        'ṫ', 'Ţ', 'ţ', 'Ṭ', 'ṭ', 'Ț', 'ț', 'Ṱ', 'ṱ', 'Ṯ', 'ṯ',
        'Ŧ', 'ŧ', 'Ⱦ', 'Ú', 'ú', 'Ù', 'ù', 'Ŭ', 'ŭ', 'Û', 'û',
        'Ǔ', 'ǔ', 'Ů', 'ů', 'Ü', 'ü', 'Ǘ', 'ǘ', 'Ǜ', 'ǜ', 'Ǚ',
        'ǚ', 'Ǖ', 'ǖ', 'Ű', 'ű', 'Ũ', 'ũ', 'Ṹ', 'ṹ', 'Ų', 'ų',
        'Ū', 'ū', 'Ṻ', 'ṻ', 'Ủ', 'ủ', 'Ȕ', 'ȕ', 'Ȗ', 'ȗ', 'Ư',
        'ư', 'Ứ', 'ứ', 'Ừ', 'ừ', 'Ữ', 'ữ', 'Ử', 'ử', 'Ự', 'ự',
        'Ụ', 'ụ', 'Ṳ', 'ṳ', 'Ṷ', 'ṷ', 'Ṵ', 'ṵ', 'Ṽ', 'ṽ', 'Ṿ',
        'ṿ', 'Ẃ', 'ẃ', 'Ẁ', 'ẁ', 'Ŵ', 'ŵ', 'ẘ', 'Ẅ', 'ẅ', 'Ẇ',
        'ẇ', 'Ẉ', 'ẉ', 'Ẍ', 'ẍ', 'Ẋ', 'ẋ', 'Ý', 'ý', 'Ỳ', 'ỳ',
        'Ŷ', 'ŷ', 'ẙ', 'ÿ', 'Ÿ', 'Ỹ', 'ỹ', 'Ẏ', 'ẏ', 'Ȳ', 'ȳ',
        'Ỷ', 'ỷ', 'Ỵ', 'ỵ', 'Ź', 'ź', 'Ẑ', 'ẑ', 'Ž', 'ž', 'Ż',
        'ż', 'Ẓ', 'ẓ', 'Ẕ', 'ẕ', 'ɀ', 'Þ', 'þ'],
        ['a', 'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a',
        'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A',
        'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a',
        'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A',
        'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A', 'a', 'A', 'e',
        'a', 'e', 'A', 'e', 'a', 'e', 'a', 'A', 'B', 'b', 'B',
        'b', 'B', 'b', 'C', 'c', 'C', 'c', 'C', 'c', 'C', 'c',
        'C', 'c', 'C', 'c', 'C', 'c', 'D', 'd', 'D', 'd', 'D',
        'd', 'D', 'd', 'D', 'd', 'D', 'd', 'DZ', 'Dz', 'dz', 'DZ',
        'DZ', 'dz', 'E', 'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E',
        'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E',
        'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E',
        'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E', 'e', 'E',
        'e', 'E', 'e', 'E', 'e', 'F', 'f', 'f', 'G', 'g', 'G', 'g',
        'G', 'g', 'G', 'g', 'G', 'g', 'G', 'g', 'H', 'h', 'H', 'h',
        'H', 'h', 'H', 'h', 'H', 'h', 'H', 'h', 'h', 'H', 'h', 'I',
        'i', 'I', 'i', 'I', 'i', 'I', 'i', 'I', 'i', 'I', 'i', 'I',
        'i', 'I', 'i', 'I', 'I', 'i', 'I', 'i', 'I', 'i', 'I', 'i',
        'I', 'i', 'I', 'i', 'I', 'i', 'IJ', 'ij', 'i', 'J', 'j', 'K',
        'k', 'K', 'k', 'K', 'k', 'K', 'k', 'L', 'l', 'L', 'l', 'L',
        'l', 'L', 'l', 'L', 'l', 'L', 'l', 'L', 'l', 'L', 'l', 'L',
        'l', 'LJ', 'Lj', 'lj', 'L', 'M', 'm', 'M', 'm', 'M', 'm', 'N',
        'n', 'N', 'n', 'N', 'n', 'N', 'n', 'N', 'n', 'N', 'n', 'N',
        'n', 'N', 'n', 'N', 'n', 'NJ', 'Nj', 'nj', 'o', 'O', 'o', 'O',
        'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O',
        'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O',
        'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O',
        'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O',
        'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O', 'o', 'O',
        'o', 'O', 'o', 'O', 'o', 'OE', 'oe', 'P', 'p', 'P', 'p', 'R',
        'r', 'R', 'r', 'R', 'r', 'R', 'r', 'R', 'r', 'R', 'r', 'R',
        'r', 'R', 'r', 'R', 'r', 'S', 's', 'S', 's', 'S', 's', 'S',
        's', 'S', 's', 'S', 's', 'S', 's', 'S', 's', 'S', 's', 'S',
        's', 's', 's', 'ss', 'Ss', 's', 'T', 't', 't', 'T', 't', 'T',
        't', 'T', 't', 'T', 't', 'T', 't', 'T', 't', 'T', 't', 'T',
        'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u',
        'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u',
        'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u',
        'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u',
        'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u', 'U', 'u',
        'V', 'v', 'V', 'v', 'W', 'w', 'W', 'w', 'W', 'w', 'w', 'W',
        'w', 'W', 'w', 'W', 'w', 'X', 'x', 'X', 'x', 'Y', 'y', 'Y',
        'y', 'Y', 'y', 'y', 'y', 'Y', 'Y', 'y', 'Y', 'y', 'Y', 'y',
        'Y', 'y', 'Y', 'y', 'Z', 'z', 'Z', 'z', 'Z', 'z', 'Z', 'z',
        'Z', 'z', 'Z', 'z', 'z', 'Th', 'th']
    ]
    for el in string:
        try:
            i = convert_diacritics[0].index(el)
            string = string.replace(el, convert_diacritics[1][i])
        except ValueError:
            pass
    return string