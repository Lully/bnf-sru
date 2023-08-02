# coding: utf-8

explain = "implémentation de la 043 selon les spécifications de la DPI"

from lxml import etree
import re

from stdf import *
import SRUextraction as sru


class Record:
    def __init__(self, ark, xmlrecord):
        self.ark = ark
        self.xml_init = xmlrecord
        self.type = get_recordtype(self.xml_init)  # ["TIC", "TUT", "TUM"]
        self.fields = Metas_init(self.xml_init)
        self.new043o = generate_043(self)
        self.new06X = generate_06X(self)
        self.new06X = dedub_06X(self.new06X)
        self.new_xml = generate_xml_record(self)
        self.metas_tab = generate_metas_tab(self)


class Metas_init:
    def __init__(self, xmlrecord):
        # Récupération d'un ensemble de métadonnées de la notice initiale
        self.leader = sru.record2fieldvalue(self.xml_init, "000")
        self.leader9 = sru.record2fieldvalue(self.xml_init, "000")[9]
        self.f043 = sru.record2fieldvalue(self.xml_init, "043")
        self.f043a = sru.record2fieldvalue(self.xml_init, "043$a")
        self.f043b = sru.record2fieldvalue(self.xml_init, "043$b")
        self.f043o = sru.record2fieldvalue(self.xml_init, "043$o")
        self.f600a_3mots = sru.record2fieldvalue(self.xml_init, "600$a").split(" ")
        if len(self.f600a_3mots) > 2:
            self.f600a_3mots = self.f600a_3mots[0:3]
        self.f600a_5mots = sru.record2fieldvalue(self.xml_init, "600$a").split(" ")
        if len(self.f600a_5mots) > 4:
            self.f600a_5mots = self.f600a_5mots[0:5]
        self.f624a = sru.record2fieldvalue(self.xml_init, "624$a")
        self.f145a = sru.record2fieldvalue(self.xml_init, "145$a")
        self.f445a = sru.record2fieldvalue(self.xml_init, "445$a")
        self.f600a = sru.record2fieldvalue(xmlrecord, "600$a")


def get_recordtype(xml_init):
    rectype = ""
    dict_types = {"s": "TIC", "t": "TUT", "u": "TUM"}
    leader9 = sru.record2fieldvalue(xml_init, "000")[9]
    if leader9 in dict_types:
        rectype = dict_types[leader9]
    return rectype


def generate_043(record: Record) -> dict:
    # Implémentation des règles d'application de la 043

    new_f043o = ""
    if record.fields.f043o == "" and record.fields.f043b == "" and record.fields.f043a != "" and record.type in ["TIC", "TUT"]:
        rules = {"ca": "ca", "ch": "ch", "ci": "au", "cs": "au", "ic": "ic",
                 "lo": "lo", "mi": "mi", "pl": "ba", "rt": "au", "te": "te"}
        
        if record.fields.f043a in rules:
            new_f043o = rules[record.fields.f043a]
        else:
            new_f043o = f"valeur de la 043$a non trouvée : {record.fields.f043a}"
    elif sru.record2fieldvalue(record.xml_init, "141$a"):  # Si présence d'une 141 --> 043$o te
        new_f043o = "te"
    elif re.match(sru.record2fieldvalue(record.xml_init, "600$a"), "(Bande dessinée|Série de bandes dessinées|Séries de bandes dessinées|Trilogie de bandes dessinées)") is not None and ("$a te" in f043_init or "$o te" in f043_init):
        new_f043o = "te"
    elif record.fields.f043b:
        rules043b = {"bd": "mi", "de": "ic", "er": "au", "es": "ic", "et": "au",
                     "jv": "lo", "pe": "ba", "ph": "ic", "sc": "ba", "sr": "au",
                     "st": "au", "tf": "au", "ws": "au"}
        if record.fields.f043b in rules043b:
            new_f043o = rules043b[record.fields.f043b]
        else:
            new_f043o = f"valeur de la 043$b non trouvée : {record.fields.f043b}"
    return new_f043o


def generate_06X(record: Record) -> dict:
    f06X_tag = ""
    f06X_value = ""
    f06X_label = ""

    if record.new043o == "te":
        f06X_tag = "060"
        f06X_value = generate_060(record)

    return {"tag": f06X_tag, "value": f06X_value, "label": f06X_label}


def dedub_06X(liste_06X):
    # Dédoublonne les valeurs de la 06X, en gardant l'ordre d'injection
    liste_dedub = []
    for el in liste_06X:
        if el not in liste_dedub:
            liste_dedub.append(el)
    return liste_dedub


def generate_060(record: Record) --> list:
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f060 = []
    if record.fields.f624a == "100":
        f060.append("philo")
    else:
        expressions2values = [["(anthologie|anthologies)", "antho", "145,445,600"],
                              ["(catéchisme|catéchismes)", "catec", "145,445,600"],
                              ["(correspondance|correspondances)", "corre", "145,445,600"],
                              ["(dictionnaire biographique|dictionnaires biographiques)", "dicbi", "600"],
                              ["(dictionnaire étymologique|dictionnaire d'étymologie)", "dicet", "600"],
                              ["(dictionnaire|dictionnaires)", "dicti", "145,445,600"],
                              ["(livret|livrets)", "livre", "600"],
                              ["(chanson de geste|chansons de geste)", "chans", "TUT141"],
                              ["(comédie|comédies)", "comed", "600"],
                              ["(conte|contes)", "conte", "600"],
                              ["(dialogue|dialogues)", "dialo", "600"],
                              ["(épopée|épopées)", "epope", "600"],
                              ["(épopée|épopées)", "epope", "145,445"],
                              ["(fable|fables)", "fable", "600"],
                              ["(fabliau|fabliaus)", "fabli", "600"],
                              ["(farce|farces)", "farce", "600"],
                              ["jeu de carnaval", "jeuca", "600"],
                              ["journal intime", "jouin", "600"],
                              ["lai", "laiss", "600"],
                              ["maximes", "maxim", "600"],
                              ["(miracle|miracles)", "mirac", "600"],
                              ["(mystère|mystères)", "myste", "600"],
                              ["(nouvelle|nouvelles)", "nouve", "600"],
                              ["(oraison funèbre|oraisons funèbres)", "orais", "600"],
                              ["(pamphlet|pamphlets)", "pamph", "600"],
                              ["(panégyrique|panégyriques)", "paneg", "600"],
                              ["(pièce en un acte|pièce de théâtre en un acte)", "piact", "600"],  # Aberration : condition de 6 mots
                              ["(poésie|poésies|poème|poèmes)", "poesi", "600"],
                              ["proverbes", "prove", "600"],
                              ["récit de voyage", "recvo", "600"],
                              ["roman d'aventures", "roave", "600"],
                              ["roman de chevalerie", "roche", "600"],
                              ["roman courtois", "rocou", "600"],
                              ["(roman|romans)", "roman", "600"],
                              ["roman policier", "ropol", "600"],
                              ["(satire|satires)", "satir", "600"],
                              ["science-fiction", "scifi", "600"],
                              ["(sonnet|sonnets)", "sonne", "600"],
                              ["(théâtre|théâtres|drame|drames)", "theat", "3mots6"],
                              ["(tragédie|tragédies)", "trage", "600"],
                              ["(vaudeville|vaudevilles)", "sonne", "600"],
                              ["(charte|chartes)", "chart", "145,445,600"],
                              ["(concordat|concordats)", "conco", "600"],
                              ["(charte|chartes)", "chart", "145,445,600"],
                              ["(constitution|constitutions)", "const", "145,445,600", '(apostolique|dogmatique|pastorale|du concile|église catholique)'],
                    # Reprendre à la ligne
                    # Si 600 $a contient dans les 5 premiers mots "coutumier", "coutumiers"
                             ]
        for expr in expressions2values:
            if len(expr) == 3:
                expr.append("")
            test = searchfor060(record, expr[0], expr[1], expr[2], expr[3], f060)
            if test:
                break
        

    return f060


def searchfor060(record, expression, valeur060, conditions, exceptions, f060):
    test = False
    if "145" in conditions and re.match(expression, record.fields.f145a.lower()):
        if exceptions:
            if re.match(exceptions, record.fields.f145a.lower()) is None and "11869156" not in sru.field2value(record.xml_init, "100$3"):
                f060.append(valeur060)
                test = True
        else:
            f060.append(valeur060)
            test = True
    elif "445" in conditions and re.match(expression, record.fields.f445a.lower()):
        if exceptions:
            if re.match(exceptions, record.fields.f445a.lower()) is None and "11869156" not in sru.field2value(record.xml_init, "100$3"):
        else:
            f060.append(valeur060)
            test = True
    elif "600" in conditions and re.search(expression, " ".join(record.fields.f600a_5mots).lower()) is not None:
        if exceptions:
            if re.match(exceptions, " ".join(record.fields.f600a_5mots).lower()) is None:
                f060.append(valeur060)
                test = True
        else:
            f060.append(valeur060)
            test = True
    elif "TUT141" in conditions and record.type == "TUT" and  "600" in conditions and re.search(expression, " ".join(record.fields.f600a_5mots).lower()) is not None:
        f060.append(valeur060)
        test = True
    elif "3mots6" in conditions and  "600" in conditions and re.search(expression, " ".join(record.fields.f600a_3mots).lower()) is not None:
        f060.append(valeur060)
        test = True
    return test


def generate_061(record: Record) --> list:
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f061 = []
    return f061


def generate_062(record: Record) --> list:
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f062 = []
    return f062


def generate_063(record: Record) --> list:
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f063 = []
    return f063


def generate_064(record: Record) --> list:
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f064 = []
    return f064


def generate_065(record: Record) --> list:
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f065 = []
    return f065


def generate_xml_record(record: Record):
    # A partir d'un objet Record, renvoie d'un objet XML
    # constituant la nouvelle notice
    # intégrant la 043, la 06X et le transfert des 600 en 630 
    # (et d'autres trucs éventuels)
    new_xml_record = record.xml_init
    return new_xml_record


def generate_metas_tab(record: Record):
    # Génération d'une ligne de tableau contenant:
    # ark, type notice, nouvelle 043, étiquette 6XX, valeur 6XX, autres modifs, ancienne notice, nouvelle notice
    return [record.ark, record.type, record.new043o, record.new06X["tag"], record.new06X["value"],
            "", sru.xml2seq(record.xml_init, field_sep="¤"), sru.xml2seq(record.new_xml, field_sep="¤")] 

def extract_load(query, reports_prefix):
    params = {"recordSchema": "intermarcxchange"}
    report_tab = create_file(f"{prefix}.tsv", "ark,type notice,nouvelle 043,étiquette 06X,valeur 06X,autres modifs,ancienne notice,nouvelle notice".split(","))
    report_xml = create_file(f"{prefix}.tsv")
    debut_fichier_xml(report_xml)
    results = sru.SRU_result(query, parametres=params)
    for ark in results.dict_records:
        record = Record(ark, results.dict_records[ark])

    fin_fichier_xml(report_xml)


def debut_fichier_xml(report_xml):
    line2report(['<?xml version="1.0" encoding="utf-8"?>'], report_xml)
    line2report(['<collection>'], report_xml)


def fin_fichier_xml(report_xml):
    line2report(['</collection>'], report_xml)


if __name__ == "__main__":
    query = "aut.type any \"TIC TUT\" and aut.status any \"sparse validated\""
    report_name = input("Préfixe des fichiers (XML et tab) en sortie : ")
    extract_load(query, report_name)

