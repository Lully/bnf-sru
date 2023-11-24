# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 09:22:21 2018

@author: Lully

Librairie de fonctions d'extraction de notices BnF ou Abes 
à partir d'un identifiant (PPN Sudoc, PPN IdRef, ARK BnF, NNB/NNA BnF)

Les PPN doivent être préfixés : "PPN", "https://www.idref.fr/", 
ou "https://www.sudoc.fr"

Les ARK BnF doivent être préfixés "ark:/12148" 
(mais "ark" peut être précédé d'un espace nommant : 
"http://catalogue.bnf.fr", etc.)

Les fonctions ci-dessous exploitent 
    - l'identifiant pour déterminer l'agence concernée, la plateforme
    - le format à utiliser (Dublin Core, Intermarc, Unimarc)
    - les zones (Marc) ou éléments d'information (Dublin Core) à extraire
pour générer, pour chaque ligne, une liste de métadonnées correspondant à
la combinaison des 3 informations ci-dessus

Si aucune URL n'est définie, c'est le SRU BnF qui est interrogé
Par défaut (paramètres non précisés)
    - format : Unimarc
    - 1000 premiers résultats rapatriés

Exemples de requêtes :
results = SRU_result(query="bib.title any 'france moyen age'")
results.list_identifiers : liste des identifiants (type list())
results.dict_records : clé = l'identifiant, valeur = dictionnaire 
        results.dict_records[clé] = notice en XML

"""

from lxml import etree
from lxml.html import parse
import urllib.parse
from urllib import request, error
import http.client
import requests
import ssl
import re
from collections import defaultdict
import re
from copy import deepcopy



ns_bnf = {"srw":"http://www.loc.gov/zing/srw/", 
          "m":"http://catalogue.bnf.fr/namespaces/InterXMarc",
          "mn":"http://catalogue.bnf.fr/namespaces/motsnotices",
          "mxc":"info:lc/xmlns/marcxchange-v2",
          "dc":"http://purl.org/dc/elements/1.1/",
          "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
          "ixm": "http://catalogue.bnf.fr/namespaces/InterXMarc"}

ns_abes = {
    "bibo" : "http://purl.org/ontology/bibo/",
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

srubnf_url = "http://catalogue.bnf.fr/api/SRU?"

aut_types = {"c": "collectivité (ORG)",
             "d": "indice Dewey (CDD)",
             "g": "marque (MAR)",
             "i": "incipit de manuscrit (INC)",
             "l": "nom géographique (GEO)",
             "m": "mot matière RAMEAU (RAM)",
             "n": "descripteur iconographique, liste du CRME (DIC)",
             "p": "personne physique (PEP)",
             "s": "titre conventionnel (TIC)",
             "t": "titre uniforme textuel (TUT)",
             "u": "titre uniforme musical (TUM)"}

class SRU_result:
    """"Resultat d'une requete SRU

    Les parametres sont sous forme de dictionnaire : nom: valeur
    Problème (ou pas ?) : l'instance de classe stocke tous les resultats
    de la requête. Il vaut mieux ne s'en servir que quand il y en a peu
    (processus d'alignement)"""

    def __init__(self, query, url_sru_root=srubnf_url,
                 parametres={}, get_all_records=False):  # Notre méthode constructeur
#==============================================================================
# Valeurs par défaut pour les paramètres de l'URL de requête SRU
#==============================================================================
        if (url_sru_root[-1] != "?"):
            url_sru_root += "?"
        if ("recordSchema" not in parametres):
            parametres["recordSchema"] = "unimarcxchange"
        if ("version" not in parametres):
            parametres["version"] = "1.2"
        if ("operation" not in parametres):
            parametres["operation"] = "searchRetrieve"
        if ("maximumRecords" not in parametres):
            parametres["maximumRecords"] = "1000"
        if ("startRecord" not in parametres):
            parametres["startRecord"] = "1"
        if ("namespaces" not in parametres):
            parametres["namespaces"] = ns_bnf
        self.parametres = parametres
        url_param = f"query={urllib.parse.quote(query)}&"
        url_param += "&".join([
                               "=".join([key, urllib.parse.quote(parametres[key])])
                               for key in parametres if key != "namespaces"
                              ])
        self.url = "".join([url_sru_root, url_param])
        #print(self.url)
        self.test, self.result_first = testURLetreeParse(self.url)
        self.result = [self.result_first]
        self.list_identifiers = []
        self.dict_records = defaultdict()
        self.nb_results = 0
        self.errors = ""
        self.multipages = False
        if (self.test):
#==============================================================================
#             Récupération des erreurs éventuelles dans la requête
#==============================================================================
            if (self.result[0].find("//srw:diagnostics",
                namespaces=parametres["namespaces"]) is not None):
                for err in self.result[0].xpath("//srw:diagnostics/srw:diagnostic",
                                                namespaces=parametres["namespaces"]):
                    for el in err.xpath(".", namespaces=parametres["namespaces"]):
                        self.errors += el.tag + " : " + el.text + "\n"
#==============================================================================
#           Récupération du nombre de résultats
#           S'il y a des résultats au-delà de la première page,
#           on active la pagination des résultats pour tout récupérer
#           Le résultat est stocké dans un dictionnaire
#           dont les clés sont les numéros de notices, 
#           et la valeur le contenu du srx:recordData/*
#==============================================================================
            self.nb_results = 0
            if (self.result[0].find("//srw:numberOfRecords", 
                                                namespaces=parametres["namespaces"]
                                                ) is not None):
                self.nb_results = int(self.result[0].find("//srw:numberOfRecords", 
                                                namespaces=parametres["namespaces"]
                                                ).text)
            self.multipages = self.nb_results > (int(parametres["startRecord"])+int(parametres["maximumRecords"])-1)
            if (get_all_records and self.multipages):
                j = int(parametres["startRecord"])
                while (j+int(parametres["maximumRecords"]) <= self.nb_results):
                    parametres["startRecords"] = str(int(parametres["startRecord"])+int(parametres["maximumRecords"]))
                    url_next_page = url_sru_root + "&".join([
                        "=".join([key, urllib.parse.quote(parametres[key])])
                         for key in parametres if key != "namespaces"
                        ])
                    (test_next, next_page) = testURLetreeParse(url_next_page)
                    if (test_next):
                        self.result.append(next_page)
                    j += int(parametres["maximumRecords"])
#==============================================================================
#           Après avoir agrégé toutes les pages de résultats dans self.result
#           on stocke dans le dict_records l'ensemble des résultats
#==============================================================================
            for page in self.result:
                for record in page.xpath("//srw:record", 
                                                    namespaces=parametres["namespaces"]):
                    identifier = ""
                    if (record.find("srw:recordIdentifier", 
                        namespaces=parametres["namespaces"]) is not None):
                        identifier = record.find("srw:recordIdentifier", 
                                                 namespaces=parametres["namespaces"]).text
                    elif (record.find(".//*[@tag='001']") is not None):
                        identifier = record.find(".//*[@tag='001']").text
                    full_record = record.find("srw:recordData/*",
                                              namespaces=parametres["namespaces"])
                    self.dict_records[identifier] = full_record
                    self.list_identifiers.append(identifier)
            self.firstRecord = None
            self.firstArk = ""
            if self.list_identifiers:
                self.firstArk = self.list_identifiers[0]
                self.firstRecord = self.dict_records[self.firstArk]
            

    def __str__(self):
        """Méthode permettant d'afficher plus joliment notre objet"""
        return "url: {}".format(self.url)
        return "nb_results: {}".format(self.nb_results)
        return "errors: {}".format(self.errors)


class SRU_result_serialized:
    """"Resultat d'une requete SRU

    Les parametres sont sous forme de dictionnaire : nom: valeur
    Problème (ou pas ?) : l'instance de classe stocke tous les resultats
    de la requête. Il vaut mieux ne s'en servir que quand il y en a peu
    (processus d'alignement)"""

    def __init__(self, query, url_sru_root=srubnf_url,
                 parametres={}, startRecord=1):  # Notre méthode constructeur
#==============================================================================
# Valeurs par défaut pour les paramètres de l'URL de requête SRU
#==============================================================================
        if (url_sru_root[-1] != "?"):
            url_sru_root += "?"
        if ("recordSchema" not in parametres):
            parametres["recordSchema"] = "unimarcxchange"
        if ("version" not in parametres):
            parametres["version"] = "1.2"
        if ("operation" not in parametres):
            parametres["operation"] = "searchRetrieve"
        if ("maximumRecords" not in parametres):
            parametres["maximumRecords"] = "1000"
        if ("namespaces" not in parametres):
            parametres["namespaces"] = ns_bnf
        parametres["startRecord"] = str(startRecord)
        self.parametres = parametres
        url_param = f"query={urllib.parse.quote(query)}&"
        url_param += "&".join([
                               "=".join([key, urllib.parse.quote(parametres[key])])
                               for key in parametres if key != "namespaces"
                              ])
        self.url = "".join([url_sru_root, url_param])
        # print(self.url)
        # print(self.url)
        self.test, result = testURLetreeParse(self.url)
        self.list_identifiers = []
        self.dict_records = defaultdict()
        self.nb_results = 0
        self.errors = ""
        self.multipages = False
        if (self.test):
#==============================================================================
#             Récupération des erreurs éventuelles dans la requête
#==============================================================================
            if (result.find("//srw:diagnostics",
                namespaces=parametres["namespaces"]) is not None):
                for err in result.xpath("//srw:diagnostics/srw:diagnostic",
                                                namespaces=parametres["namespaces"]):
                    for el in err.xpath(".", namespaces=parametres["namespaces"]):
                        self.errors += el.tag + " : " + el.text + "\n"
#==============================================================================
#           Récupération du nombre de résultats
#           S'il y a des résultats au-delà de la première page,
#           on active la pagination des résultats pour tout récupérer
#           Le résultat est stocké dans un dictionnaire
#           dont les clés sont les numéros de notices, 
#           et la valeur le contenu du srx:recordData/*
#==============================================================================
            self.nb_results = 0
            if (result.find("//srw:numberOfRecords", 
                                                namespaces=parametres["namespaces"]
                                                ) is not None):
                self.nb_results = int(result.find("//srw:numberOfRecords", 
                                                namespaces=parametres["namespaces"]
                                                ).text)
#==============================================================================
#           Après avoir agrégé toutes les pages de résultats dans self.result
#           on stocke dans le dict_records l'ensemble des résultats
#==============================================================================
        
            for record in result.xpath("//srw:record", 
                                                namespaces=parametres["namespaces"]):
                identifier = ""
                if (record.find("srw:recordIdentifier", 
                    namespaces=parametres["namespaces"]) is not None):
                    identifier = record.find("srw:recordIdentifier", 
                                                namespaces=parametres["namespaces"]).text
                elif (record.find(".//*[@tag='001']") is not None):
                    identifier = record.find(".//*[@tag='001']").text
                if record is not None:
                    full_record = record.find("srw:recordData/*",
                                             namespaces=parametres["namespaces"])
                    if full_record is not None:
                        full_record = etree.tostring(full_record, encoding='UTF-8')
                        self.dict_records[identifier] = full_record
                        self.list_identifiers.append(identifier)
            self.firstRecord = ""
            self.firstArk = ""
            if self.list_identifiers:
                self.firstArk = self.list_identifiers[0]
                self.firstRecord = self.dict_records[self.firstArk]
            


def nett_spaces_marc(value):
    # Fonction de nettoyage des espaces entre mentions de sous-zones
    # pour passer d'un affichage ADCAT-02 (plus lisible)
    # à un affichage tel que stocké en base
    # $a Titre $d Texte imprimé $e Complément du titre
    # devient
    # $aTitre$dTexte imprimé$eComplément du titre
    value = re.sub(r" \$(.) ", r"$\1", value)
    value = re.sub(r"^\$(.) ", r"$\1", value)
    return value


class Record2metas:
    """Métadonnées (à partir d'une notice et d'une liste de zones)
    renvoyées sous forme de tableau
    Il faut voir si la notice est une notice BnF ou Abes"""
    def __init__(self, identifier, XMLrecord, zones):  
        self.init = XMLrecord
        self.str = etree.tostring(XMLrecord, pretty_print=True)
        liste_zones = zones.split(";")
        self.format = "marc"
        if ("dc:" in zones):
            self.format = "dc"
        self.recordtype, self.doctype, self.entity_type = extract_docrecordtype(XMLrecord, self.format)
        self.docrecordtype = self.doctype + self.recordtype
        self.metas = []
        self.source = ""
        if ("ark:/12148" in identifier):
            self.source = "bnf"
        elif ("sudoc" in identifier 
              or "idref" in identifier
              or "ppn" in identifier.lower()):
            self.source = "abes"
        elif(re.fullmatch(r"\d\d\d\d\d\d\d\d", identifier) is not None):
            self.source = "bnf"
            
        if (self.source == "bnf" and self.format == "marc"):
            for zone in liste_zones:
                self.metas.append(extract_bnf_meta_marc(XMLrecord, 
                                                        zone))
        elif (self.source == "bnf" and self.format == "dc"):
            for zone in liste_zones:
                self.metas.append(extract_bnf_meta_dc(XMLrecord, 
                                                        zone))        
        elif (self.source == "abes" and self.format == "marc"):
            for zone in liste_zones:
                self.metas.append(extract_abes_meta_marc(XMLrecord, 
                                                        zone))
        elif (self.source == "abes" and self.format == "dc"):
            for zone in liste_zones:
                self.metas.append(extract_abes_meta_dc(XMLrecord, 
                                                        zone))

    def __str__(self):
        """Méthode permettant d'afficher plus joliment notre objet"""
        return "{}".format(self.metas)


class IndexField:
    """Chaîne d'indexation
    Peut récupérer l'information sous 2 formes :
    * 1 paramètre : ("600 .. $3 321654987 $a Mozart")
    * 2 paramètres : ("$3 321654987 $a Mozart", "600")

    Renvoie essentiellement :
        l'étiquette de zone
        le NNA
        l'étiquette de la première sous-zone
        la liste des sous-zones (si vedette construite) pour chaque NNA composant la chaîne d'indexation
    """
    def __init__(self, value, field=None):  
        self.init = value
        self._value_list = [el.strip() for el in value.split("$3") if el.strip()]
        self.field = field
        if (field is None
           and re.fullmatch(r"\d\d\d?+.", value) is not None):
            field = value[0:3]
            self._value_list = self._value_list[1:]
        self.list_subfields = [IndexSubfield(el) for el in self._value_list]

    def __str__(self):
        """Méthode permettant d'afficher plus joliment notre objet"""
        return self.init

class IndexSubfield:
    """
    Sous-zone d'indexation
    Récupère l'étiquette de sous-zone, le NNA
    et le libellé complet du report de forme
    IndexSubfield.code récupère le nom de la première sous-zone
    IndexSubfield.codes récupère tous les noms des sous-zones

    Type de valeur en entrée : "11932843 $x Portraits"
    """
    def __init__(self, value):
        self.init = value
        try:
            self.nna = value[0:8]
        except IndexError:
            self.nna = ""
        try:
            self.code = value[10]
        except IndexError:
            self.code = ""

        self.codes = " ".join([el[0] for el in value.split("$")[1:]])
    
    def __str__(self):
        """Méthode permettant d'afficher plus joliment notre objet"""
        return self.init



def sruquery2results(url, urlroot=srubnf_url):
    """
    Fonction utile pour les requêtes avec un grand nombre de résultats
    Permet de générer un SRU_result par page, 
    jusqu'à atteindre le nombre total de résultats
    """
    params = {}
    url_root, param_str = url.split("?")
    param_list = param_str.split("&")
    for el in param_list:
        params[el.split("=")[0]] = el.split("=")[1]
    query = urllib.parse.unquote(params.pop("query"))
    nb_results = SRU_result(query, url_root, parametres={"maximumRecords": "1"})
    i = 1
    while (i < nb_results):
        params_current = deepcopy(params)
        params_current["maximumRecords"] = "1000"
        params_current["startRecord"] = str(i)
        results = SRU_result(query, url_root, params_current)
     


def testURLetreeParse(url, print_error=True):
    """Essaie d'ouvrir l'URL et attend un résultat XML
    Renvoie 2 variable : résultat du test (True / False) et le fichier
    renvoyé par l'URL"""
    test = True
    resultat = ""
    try:
        resultat = etree.parse(request.urlopen(url))
    except etree.XMLSyntaxError as err:
        if (print_error):
            print(url)
            print(err)
        test = False

    except etree.ParseError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except error.URLError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except ConnectionResetError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except TimeoutError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except http.client.RemoteDisconnected as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except http.client.BadStatusLine as err:
        if (print_error):
            print(url)
            print(err)
        test = False
 
    except ConnectionAbortedError as err:
        if (print_error):
            print(url)
            print(err)
        test = False
    
    except http.client.IncompleteRead as err:
        if (print_error):
            print(url)
            print(err)
        test = False
    
    except ssl.CertificateError:
        try:
            resultat = requests.get(url, verify=False).content
            resultat = etree.fromstring(resultat)
        except requests.exceptions.ProxyError as err:
            if (print_error):
                print(url)
                print(err)
            test = False

    except OSError as err:
        if (print_error):
            print(url)
            print(err)
        test = False

    

    return (test,resultat)

def retrieveURL(url):
    page = etree.Element("default")
    try:
        page = etree.parse(url)
    except OSError:
        print("Page non ouverte, erreur Serveur")
    except etree.XMLSyntaxError:
        print("Erreur conformité XML")
    return page


#==============================================================================
#  Fonctions d'extraction des métadonnées
#==============================================================================

def extract_docrecordtype(XMLrecord, rec_format):
    """Fonction de récupération du type de notice et type de document
    rec_format peut prendre 2 valeurs: 'marc' et 'dc' """
    val_003 = ""
    leader = ""
    doctype = ""
    recordtype = ""
    entity_type = ""
    format_attribute = XMLrecord.get("format")
    if format_attribute is not None:
        format_attribute = format_attribute.lower()
    type_attribute = XMLrecord.get("type")
    if type_attribute:
        type_attribute = type_attribute.lower()
    if (rec_format == "marc"):
        for element in XMLrecord:
            if ("leader" in element.tag):
                leader = element.text
            if element.get("tag") == "003":
                val_003 = element.text
        if (val_003 != ""
            and format_attribute != "intermarc"):
            #Alors c'est de l'Unimarc
            if ("sudoc" in val_003):
            #Unimarc Bib
                doctype,recordtype = leader[6], leader[7]
                entity_type = "B"
            elif ("ark:/12148" in val_003 and int(val_003[-9:-1])>=3):
            #Unimarc Bib
                doctype,recordtype = leader[6], leader[7]
                entity_type = "B"
            elif ("idref" in val_003):
            #Unimarc AUT
                recordtype = leader[9]
                entity_type = "A"
            elif ("ark:/12148" in val_003 and int(val_003[-9:-1])<3):
            #Unimarc AUT
                recordtype = leader[9]
                entity_type = "A"
        elif type_attribute:
            #C'est de l'intermarc (BnF)
            entity_type = type_attribute[0].upper()
            if (entity_type == "B"
               and len(leader) > 8):
                #Intermarc BIB
                recordtype, doctype = leader[8], leader[22]
            elif (entity_type == "A"
                  and len(leader) > 8):
                recordtype = leader[8]
                doctype = leader[9]
                
    elif (rec_format == "dc"):
        entity_type = "B"
        
    return (doctype, recordtype, entity_type)




def field2listsubfields(field):
    """
    Récupère la liste des noms des sous-zones pour une zone donnée
    """
    if type(field) == str:
        if field.startswith("<"):
            field = etree.fromstring(field)
        else:
            field = seq2xml_field(field, result="xml")
    liste_subf = []
    for subf in field.xpath("*"):
        liste_subf.append(subf.get("code"))
    try:
        liste_subf = " ".join(liste_subf)
    except TypeError:
        liste_subf = ""
    return liste_subf



def field2subfield(field, subfield, nb_occ="all", sep="¤"):
    if type(field) == str:
        if field.startswith("<"):
            field = etree.fromstring(field)
        else:
            field = seq2xml_field(field, result="xml")
    path = "*[@code='" + subfield + "']"
    listeValues = []
    if (nb_occ == "first" or nb_occ == 1):
        if (field.find(path) is not None and
                field.find(path).text is not None):
            val = field.find(path).text
            listeValues.append(val)
    else:
        for occ in field.xpath(path):
            if (occ.text is not None):
                listeValues.append(occ.text)
    listeValues = sep.join(listeValues)
    return listeValues

def field2value(field):
    if type(field) == str:
        if field.startswith("<"):
            field = etree.fromstring(field)
        else:
            field = seq2xml_field(field, result="xml")
    try:
        if int(field.get("tag")) > 9:
            value = " ".join([" ".join(["$" + el.get("code"), el.text]) for el in field.xpath("*")])
        else:
            value = field.text
    except ValueError:
        value = ""
    except TypeError:
        value = ""
    return value


def extract_bnf_meta_marc(record, zone):
    """
    Ancien nom de la fonction, qui depuis a été généricisée
    """
    value = record2fieldvalue(record, zone)
    return value


def record2fieldvalue(record, zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule,
    # on applique le traitement ci-dessous
    if type(record) == str:
        if record.startswith("<"):
            record = etree.fromstring(record)
        else:
            record = seq2xml_record(record, result="xml")
    value = ""
    field = ""
    subfields = []
    if record is not None:
        if (zone.startswith("00") and zone != "000"):
            fields = []
            fieldPath = f"*[@tag='{zone}']"
            for field_occ in record.xpath(fieldPath):
                if field_occ.text is not None:
                    fields.append(field_occ.text)
            value = "¤".join(fields)
        elif ("$" in zone):
            #si la zone contient une précision de sous-zone
            zone_ss_zones = zone.split("$")
            field = zone_ss_zones[0]
            fieldPath = "*[@tag='" + field + "']"
            i = 0
            for field in record.xpath(fieldPath):
                i = i+1
                j = 0
                for subfield in zone_ss_zones[1:]:
                    sep = ""
                    if (i > 1 and j == 0):
                        sep = "¤"
                    j = j+1
                    subfields.append(subfield)
                    subfieldpath = "*[@code='" + subfield + "']"
                    if (field.find(subfieldpath) is not None):
                        if (field.find(subfieldpath).text != ""):
                            valtmp = "¤".join([get_subfield_value(subfieldocc) for subfieldocc in field.xpath(subfieldpath) if subfieldocc.text is not None])
                            #valtmp = field.find(subfieldpath).text
                            #valtmp = field.find(subfieldpath).text.encode("utf-8").decode("utf-8", "ignore")
                            prefixe = ""
                            if (len(zone_ss_zones) > 2):
                                prefixe = f" ${subfield} "
                            value = str(value) + str(sep) + str(prefixe) + str(valtmp)
        else:
            #si pas de sous-zone précisée
            field = zone
            path = ""
            if (field == "000"):
                path = "*[local-name()='leader']"
            else:
                path = "*[@tag='" + field + "']"
            i = 0        
            for field in record.xpath(path):
                i = i+1
                j = 0
                if ("leader" not in path
                   and field.find("*", namespaces=ns_bnf) is not None):
                    sep = ""
                    for subfield in field.xpath("*"):
                        sep = ""
                        if (i > 1 and j == 0):
                            sep = "¤"
                        #print (subfield.get("code") + " : " + str(j) + " // sep : " + sep)
                        j = j+1
                        valuesubfield = ""
                        if (subfield.text != ""):
                            valuesubfield = get_subfield_value(subfield)
                            if (valuesubfield == "None"):
                                valuesubfield = ""
                        value = value + sep + " $" + subfield.get("code") + " " + valuesubfield
                else:
                    value = field.find(".").text
        if (value != ""):
            if value is None:
                value = ""
            elif (value[0] == "¤"):
                value = value[1:]
    return value

def representsInt(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


def ark2nn(ark_catalogue):
    nn = ark_catalogue[ark_catalogue.find("ark:/")+13:-1]
    return nn


def get_subfield_value(subfield_node):
    # Récupérer la valeur d'une sous-zone,
    # en ajoutant la barre de classement si elle existe
    subfield_value = ""
    if subfield_node is not None and subfield_node.text is not None:
        try:
            barre = subfield_node.get("Barre")
            if representsInt(barre) and len(subfield_node.text) > int(barre):
                barre = int(barre)
                subfield_value = subfield_node.text[:barre] + "|" + subfield_node.text[barre:]
            else:
                subfield_value = subfield_node.text
        except TypeError:
            subfield_value = subfield_node.text
    return subfield_value


def extract_bnf_meta_dc(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = []
    for element in record.xpath(zone, namespaces=ns_bnf):
        value.append(element.text)
    value = "¤".join(value)
    return value.strip()


def extract_abes_meta_marc(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = ""
    field = ""
    subfields = []
    if (zone.find("$") > 0):
        #si la zone contient une précision de sous-zone
        zone_ss_zones = zone.split("$")
        field = zone_ss_zones[0]
        fieldPath = "datafield[@tag='" + field + "']"
        i = 0
        for field in record.xpath(fieldPath):
            i = i+1
            j = 0
            for subfield in zone_ss_zones[1:]:
                sep = ""
                if (i > 1 and j == 0):
                    sep = "¤"
                j = j+1
                subfields.append(subfield)
                subfieldpath = "subfield[@code='"+subfield+"']"
                if (field.find(subfieldpath) is not None):
                    if (field.find(subfieldpath).text != ""):
                        valtmp = field.find(subfieldpath).text
                        #valtmp = field.find(subfieldpath,namespaces=ns_bnf).text.encode("utf-8").decode("utf-8", "ignore")
                        prefixe = ""
                        if (len(zone_ss_zones) > 2):
                            prefixe = "$" + subfield + " "
                        value = str(value) + str(sep) + str(prefixe) + str(valtmp)
    else:
        #si pas de sous-zone précisée
        field = zone
        field_tag = ""
        if (field == "001" or field == "008" or field == "009"):
            field_tag="controlfield"
        else:
            field_tag = "datafield"
        path = ""
        if (field == "000"):
            path = "leader"
        else:
            path = field_tag + "[@tag='" + field + "']"
        i = 0        
        for field in record.xpath(path):
            i = i+1
            j = 0
            if (field.find("subfield") is not None):
                sep = ""
                for subfield in field.xpath("subfield"):
                    sep = ""
                    if (i > 1 and j == 0):
                        sep = "¤"
                    j = j+1
                    valuesubfield = ""
                    if (subfield.text != ""):
                        valuesubfield = str(subfield.text)
                        if (valuesubfield == "None"):
                            valuesubfield = ""
                    value = value + sep + " $" + subfield.get("code") + " " + valuesubfield
            else:
                value = field.find(".").text
    if (value != ""):
        if (value[0] == "¤"):
            value = value[1:]
    return value.strip()

def extract_abes_meta_dc(record,zone):
    #Pour chaque zone indiquée dans le formulaire, séparée par un point-virgule, on applique le traitement ci-dessous
    value = []
    zone = "//" + zone
    for element in record.xpath(zone, namespaces=ns_abes):
        value.append(element.text)
    value = "¤".join(value)
    return value.strip()


def nna2bibliees(ark):
    nbBIBliees = "0"
    url = "http://catalogue.bnf.fr/" + ark
    page = parse(url)
    hrefPath = "//a[@title='Voir toutes les notices liées']"
    if (page.xpath(hrefPath) is not None):
        if (len(page.xpath(hrefPath)) > 0):
            nbBIBliees = str(page.xpath(hrefPath)[0].text)
            nbBIBliees = nbBIBliees[31:].replace(")","")
        #print(url + " : " + nbBIBliees)
    return nbBIBliees


def abesrecord2meta(recordId, record, parametres):
    metas = []
    nn = recordId
    typenotice = ""
    if (record.find("leader") is not None):
        leader = record.find("leader").text
        if ("unimarc" in parametres["format_records"]):
            typenotice = leader[6] + leader[7] 
        elif ("intermarc" in parametres["format_records"]):
            typenotice = leader[22] + leader[8]
    listeZones = parametres["zones"].split(";")
    colonnes_communes = ["PPN"+recordId, nn, typenotice]
    for el in listeZones:
        if ("marc" in parametres["format_records"]):
            metas.append(extract_abes_meta_marc(record, el))
        else:
            metas.append(extract_abes_meta_dc(record, el))
    if (parametres["BIBliees"] == 1):
        nbBibliees = nna2bibliees(recordId)
        colonnes_communes.append(nbBibliees)
    line_resultats = "\t".join(colonnes_communes) + "\t" + "\t".join(metas)
    return line_resultats


def bnfrecord2meta(recordId, record, parametres):
    metas = []
    nn = recordId
    typenotice = ""
    if ("ark" in recordId):
        nn = recordId[recordId.find("ark")+13:-1]
    if (record.find("mxc:leader", namespaces=ns_bnf) is not None):
        leader = record.find("mxc:leader", namespaces=ns_bnf).text
        if ("unimarc" in parametres["format_records"]):
            typenotice = leader[6] + leader[7] 
        elif ("intermarc" in parametres["format_records"]):
            typenotice = leader[22] + leader[8]
    listeZones = parametres["zones"].split(";")
    colonnes_communes = [recordId,nn,typenotice]
    for el in listeZones:
        if ("marc" in parametres["format_records"]):
            metas.append(extract_bnf_meta_marc(record,el))
        else:
            metas.append(extract_bnf_meta_dc(record,el))
    if (parametres["BIBliees"] == 1):
        nbBibliees = nna2bibliees(recordId)
        colonnes_communes.append(nbBibliees)
    line_resultats = "\t".join(colonnes_communes) + "\t" + "\t".join(metas)
    return line_resultats

def ark2meta(recordId, IDtype, parametres):
    #TypeEntite= "B" pour notices Biblio, "A" pour notices d'autorité
    add_sparse_validated = ""
    if (parametres["typeEntite"] == "aut."):
        add_sparse_validated = urllib.parse.quote(' and aut.status any "sparse validated"')
    urlSRU = ""
    nn = recordId
    ark = recordId
    if (IDtype == "ark"):
        nn = recordId[13:21]
    line_resultats = ""
    query = parametres["typeEntite"] + "persistentid%20any%20%22" + recordId + "%22" + add_sparse_validated
    if (IDtype == "NN"):
        query = parametres["typeEntite"] + "recordId%20any%20%22" + nn + "%22" + add_sparse_validated 
    urlSRU = srubnf_url + query + "&recordSchema=" + parametres["format_records"]
    
    (test,page) = testURLetreeParse(urlSRU)    
    if (test):
        if (IDtype == "NN" and page.find("//srw:recordIdentifier",namespaces=ns_bnf) is not None):
            ark = page.find("//srw:recordIdentifier",namespaces=ns_bnf).text
        if (page.find("//srw:recordData/oai_dc:dc", namespaces=ns_bnf) is not None):
            record = page.xpath("//srw:recordData/oai_dc:dc",namespaces=ns_bnf)[0]
            line_resultats = bnfrecord2meta(ark,record,parametres)
        if (page.find("//srw:recordData/mxc:record", namespaces=ns_bnf) is not None):
            record = page.xpath("//srw:recordData/mxc:record",namespaces=ns_bnf)[0]
            line_resultats = bnfrecord2meta(ark,record,parametres)

    return line_resultats


def get_abes_record(ID, parametres):
    """A partir d'un identifiant PPN (IdRef / Sudoc), permet d'identifier si
    la notice est à récupérer sur IdRef ou sur le Sudoc"""
    platform = ""
    record = ""
    id_nett = ID.upper().split("/")[-1].replace("PPN","")

    if ("marc" in parametres["format_records"]):
        (test,record) = testURLetreeParse("https://www.sudoc.fr/" + id_nett + ".xml",False)
        if (test):
            platform = "https://www.sudoc.fr/"
        else:
            (test,record) = testURLetreeParse("https://www.idref.fr/" + id_nett + ".xml")
            if (test):
                platform = "https://www.idref.fr/"
    elif ("dublincore" in parametres["format_records"]):
        (test,record) = testURLetreeParse("https://www.sudoc.fr/" + id_nett + ".rdf",False)
        if (test):
            platform = "https://www.sudoc.fr/"
        else:
            (test,record) = testURLetreeParse("https://www.idref.fr/" + id_nett + ".rdf")
            if (test):
                platform = "https://www.idref.fr/"
    return (id_nett, test,record,platform)


def url2params(url):
    """
    Extrait les paramètres de requête du SRU à partir de l'URL
    Renvoie 
        - l'URL racine
        - la requête (query)
        - un dictionnaire des autres paramètres
    """
    url_root = url.split("?")[0]
    param = url.replace(url_root + "?", "")
    url_root += "?"
    param = param.split("&")
    param_list = [el.split("=") for el in param]
    param_dict = {}
    for el in param_list:
        param_dict[el[0]] = el[1]
    query = param_dict.pop("query", None)
    if query is not None:
        query = urllib.parse.unquote(query)
    return query, url_root, param_dict


def url2entity_type(url):
    entity_type = "bib."
    if ("aut." in url):
        entity_type= "aut."
    return entity_type
    
def extract_1_info_from_SRU(page,element,datatype = str):
    """Récupère le nombre de résultats"""
    val = ""
    if (datatype == int):
        val = 0
    path = ".//" + element
    if (page.find(path, namespaces=ns_bnf) is not None):
        val = page.find(path, namespaces=ns_bnf).text
        if (datatype == int):
            val = int(val)
    return val

def url2format_records(url):
    format_records = "unimarcxchange"
    if ("recordSchema=unimarcxchange-anl" in url):
        format_records = "unimarcxchange-anl"
    elif ("recordSchema=intermarcxchange" in url):
        format_records = "intermarcxchange"
    elif ("recordSchema=dublincore" in url):
        format_records = "dublincore"
    return format_records


def query2nbresults(url):
    if ("&maximumRecords" in url):
        url = re.sub(r"maximumRecords=(\d+)", "maximumRecords=1", url)
    else:
        url += "&maximumRecords=1"
    query, url_root, params = url2params(url)
    nb_results = SRU_result(query, url_root, params).nb_results
    return nb_results


def aut2bibliees(ark):
    """
    Pour une notice d'autorité, récupère le nombre de notices BIB liées 
    en ouvrant la notice AUT dans WebCCA (lien "Voir toutes les notices liées")
    """
    return nna2bibliees(ark)


def nnb2bibliees(ark):
    """
    Pour une notice d'autorité, récupère le nombre de notices BIB liées 
    en ouvrant la notice AUT dans WebCCA (lien "Voir toutes les notices liées")
    """
    return nna2bibliees(ark)


def xml2seq(xml_record, display_value=True, field_sep="\n", sort=False):
    """
    Pour une notice XML en entrée, renvoie un format "à plat" pour édition en TXT
    Si le parametre display_value est False, ne renvoie que les zones et sous-zones, sans leur contenu
    Le séparateur de zones peut prendre une autre valeur que le saut de ligne, 
    si on veut toute la notice sur une ligne (pour la copier-coller dans Excel par exemple)
    """
    record_content = []
    for field in xml_record.xpath("*[local-name()='leader']|*[local-name()='controlfield']|*[local-name()='datafield']"):
        subfields = []
        tag = field.get("tag")
        ind1 = field.get("ind1")
        ind2 = field.get("ind2")
        if ind1 == "":
            ind1 = " "
        if ind2 == "":
            ind2 = " "
        for subfield in field.xpath("*"):
            code = subfield.get("code")
            subfield_text = ""
            if subfield.text is not None:
                subfield_text = subfield.text
            if (display_value):
                value = subfield_text
            subfields.append(f"${code} {value}")
        field_content = f"{tag} {ind1}{ind2} {' '.join(subfields)}"
        if tag == "LDR":
            tag = None
        if tag is None or tag == "":
            field_text = ""
            if field.text is not None:
                field_text = field.text
            if (display_value):
                field_content = f"{field_sep}000    " + field_text
            else:
                field_content = f"{field_sep}000    "
        elif (int(tag) < 10):
            if (display_value):
                field_text = field.text
                field_content = f"{tag}    " + field_text
            else:
                field_content = f"{tag}    "
        record_content.append(field_content)
    record_content = field_sep.join(record_content)
    return record_content


def sort_xml_record(xml_record):
    # Retrier par ordre croissant les zones d'une notice XML
    rec = etree.Element("record")
    liste_values = []
    for attrib in xml_record.attrib:
        rec.set(attrib, xml_record.attrib[attrib])
    for leader in xml_record.xpath("*[local-name()='leader']"):
        rec.append(leader)
    for i in range(0,999):
        tag = str(i).zfill(3)
        for f_occ in xml_record.xpath(f"*[@tag='{tag}']"):
            full_val = f"{tag}{field2value(f_occ)}"
            if full_val not in liste_values:
                rec.append(f_occ)
                liste_values.append(full_val)
    return rec


def seq2xml_file(input_filename, ind_spaces=False, subfield_spaces=False, MarcEdit_format=False):
    # A partir d'un nom de fichier contenant du format MARC "à plat"
    # on renvoie du XML (en format string)
    # paramètre MarcEdit_format : si le fichier sort de MarcEdit, il y a un peu de remise en forme
    inputfile = open(input_filename, "r", encoding="utf-8")
    if MarcEdit_format:
        seq_collection = "".join(inputfile.readlines()).split("\r\n\r\n=LDR ")
        seq_collection[0] = seq_collection[0].replace("=LDR", "000")
        seq_collection = [convert_marc_edit_record(record) for record in seq_collection]
    else:
        seq_collection = "".join(inputfile.readlines()).split("\n000")
        seq_collection = [f"000{record}" for record in seq_collection]
    seq_collection[0] = seq_collection[0][3:]   # Eviter que la première notice  commence par 6 chiffres "0" au lieu de 3
    seq_collection = [el.replace("\r", "").split("\n") for el in seq_collection]
    xml_collection = seq2xml_collection(seq_collection, ind_spaces, subfield_spaces)
    inputfile.close()
    return xml_collection


def convert_marc_edit_record(record):
    record = f"000{record}"
    record = re.sub(r"\r\n=(\d\d\d) ", r"\n\1", record)
    record = re.sub(r"\n=(\d\d\d) ", r"\n\1", record)
    return record


def seq2xml_collection(records, ind_spaces=False, subfield_spaces=False, result="str"):
    # Conversion d'une liste de records (chaque record est une liste de zones)
    xml_collection = "<collection>"
    for record in records:
        xml_collection += seq2xml_record(record, ind_spaces, subfield_spaces)
    xml_collection += "</collection>"
    if result == "xml":
        xml_collection = etree.fromstring(xml_collection)
    return xml_collection


def seq2xml_record(record, ind_spaces=False, subfield_spaces=False, result="str"):
    # Convertit une notice "à plat" (une ligne par zone) en notice XML
    # En entrée, la notice est une liste d'éléments : 1 élément par ligne
    #
    #      * ind_spaces : indique si les indicateurs sont entourés d'espaces (par défaut : non)
    #      * subfield_spaces : indique si les sous-zones sont entourées d'espaces (par défaut : non)
    xml_record = "\n<record>"
    for field in record:
        xml_val = seq2xml_field(field, ind_spaces, subfield_spaces)
        xml_record += xml_val
    xml_record += "</record>\n"
    if result == "xml":
        xml_record = etree.fromstring(xml_record)
    return xml_record


def seq2xml_field(field, ind_spaces=False, subfield_spaces=False, result="str"):
    # conversion d'une zone séquentielle en élément XML (mais au format txt)
    xml_val = ""
    field = replace_xmlentities(field)
    if field.startswith("000"):
        xml_val = row2leader(field)
    elif ("$" in field) :
        xml_val = row2datafield(field, ind_spaces, subfield_spaces)
    elif field.strip():
        xml_val = row2controlfield(field)
    if result == "xml":
        xml_val = etree.fromstring(xml_val)
    return xml_val


def replace_xmlentities(field):
    # Remplacement de caractères par leurs entités en XML
    chars = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}
    for c in chars:
        field = field.replace(c, chars[c])
    return field


def row2datafield(row, ind_spaces=False, subfield_spaces=False):
    # Conversion format MARC séquentiel > MarcXM
    # voir fonction seq2xml_record
    field = row.split("$")
    if subfield_spaces:
        field = row.split(" $")
    tag = field[0][0:3]
    ind1 = field[0][3]
    ind2 = field[0][4]
    if ind_spaces:
        ind1 = field[0][5]
        ind2 = field[0][6]
    datafield = '  <datafield tag="' + tag + '" ind1="' + ind1 + '" ind2="' + ind2 + '">' + "\n"
    for subfield in field[1:]:
        code = subfield[0]
        #value = subfield[1:].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        value = subfield[1:]
        if (code != "w"):
            value = value.strip()
        elif subfield_spaces:
            value = subfield[2:]
        #print(code)
        datafield += '    <subfield code="' + code + '">' + value + "</subfield>\n"
    datafield += "  </datafield>\n"
    return datafield    
    
def row2leader(row):
    tag = row[0:3]
    value = row[3:]
    print("leader", tag, value, "//", row)
    while value.startswith(" "):
        value = value[1:]
    field = '<leader>' + value + "</leader>\n"
    return field    

def row2controlfield(row):
    tag = row[0:3]
    value = row[3:]
    while value.startswith(" "):
        value = value[1:]
    field = '<controlfield tag="' + tag + '">' + value + "</controlfield>\n"
    return field   


def clean_ark(messy_ark):
    # Nettoyage d'un ARK précédé d'une URL ou d'autres trucs divers
    ark = messy_ark[messy_ark.find("ark"):]
    ark = ark.split(".")[0].split("#")[0]
    return ark

def stats_marc_collection(liste_xml_records):
    # Pour une liste de notices MarcXML : statistiques des zones et sous-zones
    stats = defaultdict(int)
    for xml_record in liste_xml_records:
        stats = stats_marc_record(xml_record, stats)
    stats["Nb notices"] = len(liste_xml_records)
    return stats

def stats_marc_record(xml_record, stats=None):
    # Pour une notice MarcXML : statistiques des zones et sous-zones
    if stats is None:
        stats = defaultdict(int)
    for leader in xml_record.xpath("*[local-name()='leader']"):
        stats["000"] += 1
    for field in xml_record.xpath("*[@tag]"):
        tag = field.get("tag")
        stats[tag] += 1
        for subfield in field.xpath("*[@code]"):
            subf = subfield.get("code")
            stats[f"{tag}${subf}"] += 1
    return stats

def actualize_ark(ark):
    nn = ark2nn(ark)
    if nn and nn[0] in "123":
        rectype = "aut"
    else:
        rectype = "bib"
    query = f"{rectype}.persistentid any \"{ark}\""
    result = SRU_result(query)
    if result.list_identifiers:
        return result.list_identifiers[0]
    else:
        return ""