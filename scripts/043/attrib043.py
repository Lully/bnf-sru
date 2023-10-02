# coding: utf-8

explain = "implémentation de la 043 selon les spécifications de la DPI"

from lxml import etree
import re
from copy import deepcopy
import pandas as pd
from collections import Counter

from stdf import *
import SRUextraction as sru
from string import ascii_lowercase

# Liste des zones non répétables
rules_repetabilite = {"060": "*", "062": "a", "063": "*", "064": "bc", "065": "*"}


class Record:
    def __init__(self, ark, xmlrecord):
        self.ark = ark
        self.xml_init = xmlrecord
        self.type = get_recordtype(self.xml_init)  # ["TIC", "TUT", "TUM"]
        self.fields = Metas_init(self.xml_init)
        self.f043error = None
        self.new043 = generate_043(self)
        self.new06X, self.new630, self.new631 = generate_06X(self)
        self.new06X = dedub_06X(self.new06X)
        self.f600a2061 = get600a(self.xml_init)  # dict listant les zones 600$a et indiquant si converties en 061
        self.new_xml = generate_xml_record(self)
        self.new630 = get_new63X(self, "630")
        self.new631 = get_new63X(self, "631")
        self.metas_tab = generate_metas_tab(self)


class Metas_init:
    def __init__(self, xmlrecord):
        # Récupération d'un ensemble de métadonnées de la notice initiale
        self.leader = sru.record2fieldvalue(xmlrecord, "000")
        self.leader9 = sru.record2fieldvalue(xmlrecord, "000")[9]
        self.f043 = sru.record2fieldvalue(xmlrecord, "043")
        self.f043a = sru.record2fieldvalue(xmlrecord, "043$a")
        self.f043b = sru.record2fieldvalue(xmlrecord, "043$b")
        self.f043o = sru.record2fieldvalue(xmlrecord, "043$o")
        self.f600a_3mots = sru.record2fieldvalue(xmlrecord, "600$a").split(" ")
        if len(self.f600a_3mots) > 2:
            self.f600a_3mots = self.f600a_3mots[0:3]
        self.f600a_3mots = " ".join(self.f600a_3mots)
        self.f600a_5mots = sru.record2fieldvalue(xmlrecord, "600$a").split(" ")
        if len(self.f600a_5mots) > 4:
            self.f600a_5mots = self.f600a_5mots[0:5]
        self.f600a_5mots = " ".join(self.f600a_5mots)
        self.f624a = sru.record2fieldvalue(xmlrecord, "624$a")
        self.f145a = sru.record2fieldvalue(xmlrecord, "145$a")
        self.f145e = sru.record2fieldvalue(xmlrecord, "145$e")
        self.f145f = sru.record2fieldvalue(xmlrecord, "145$f")
        self.f445a = sru.record2fieldvalue(xmlrecord, "445$a")
        if self.f145a == "":
            self.f145a = sru.record2fieldvalue(xmlrecord, "141$a")
            self.f145e = sru.record2fieldvalue(xmlrecord, "141$e")
            self.f145f = sru.record2fieldvalue(xmlrecord, "141$f")
            self.f445a = sru.record2fieldvalue(xmlrecord, "441$a")
        self.f145a_sans_article = drop_article(self.f145a)
        self.f445a_sans_article = drop_article(self.f445a)
        self.f145a_3mots = self.f145a.split(" ")
        if len(self.f145a_3mots) > 2:
            self.f145a_3mots = self.f145a_3mots[0:3]
        self.f145a_3mots = " ".join(self.f145a_3mots)
        self.f445a_3mots = self.f445a.split(" ")
        if len(self.f445a_3mots) > 2:
            self.f445a_3mots = self.f445a_3mots[0:3]
        self.f445a_3mots = " ".join(self.f445a_3mots)
        self.f600a = sru.record2fieldvalue(xmlrecord, "600$a")
        self.f624a = sru.record2fieldvalue(xmlrecord, "624$a")
        self.f060 = sru.record2fieldvalue(xmlrecord, "060")
        self.f061 = sru.record2fieldvalue(xmlrecord, "061")
        self.f062 = sru.record2fieldvalue(xmlrecord, "062")
        self.f063 = sru.record2fieldvalue(xmlrecord, "063")
        self.f064 = sru.record2fieldvalue(xmlrecord, "064")
        self.f065 = sru.record2fieldvalue(xmlrecord, "065")


def get_new63X(record, zone):
    old_zone = sru.record2fieldvalue(record.xml_init, zone)
    new_zone = sru.record2fieldvalue(record.new_xml, zone)
    if old_zone != new_zone:
        return new_zone
    else:
        return ""


def get600a(xml_init):
    # Pour une notice, renvoie la liste des valeurs 600$a sous forme de dictionnaire
    # avec valeur = False. Quand une de ces valeurs sera reconnue pour générer une zone 061
    # on supprimera l'intégralité de la 600
    dict600 = {}
    f600a = sru.record2fieldvalue(xml_init, "600$a").split("¤")
    for el in f600a:
        dict600[el] = False
    return dict600
    

def drop_article(string):
    # récupération du 2e mot s'il existe
    articles = ["Le ", "La ", "Les ", "Un ", "Une ", "Des ", "L'"]
    articles = articles + [el.lower() for el in articles]
    articles = "(" + "|".join(articles) + ")"
    new_string = []
    for substring in string.split("¤"):
        if re.match(articles, substring) is not None:
            article_trouve = re.match(articles, substring).group(0)
            len_article = len(article_trouve)
            substring_sans_article = substring[len_article:]
            substring = substring_sans_article
        new_string.append(substring)
    return "¤".join(new_string)


def get_recordtype(xml_init):
    rectype = ""
    dict_types = {"s": "TIC", "t": "TUT", "u": "TUM"}
    try:
        leader9 = sru.record2fieldvalue(xml_init, "000")[9]
        if leader9 in dict_types:
            rectype = dict_types[leader9]
    except IndexError:
        print(etree.tostring(xml_init))
        raise
    return rectype


def generate_043(record: Record) -> str:
    # Implémentation des règles d'application de la 043

    new_f043 = ""
    if re.search("($a Bande dessinée|$a Série de bandes dessinées|$a Séries de bandes dessinées|$a Trilogie de bandes dessinées)", sru.record2fieldvalue(record.xml_init, "600")) is not None and ("$a te" in record.fields.f043 or "$o te" in record.fields.f043):
        new_f043 = "$o mi"
    elif record.fields.f043o == "" and record.fields.f043b == "" and record.fields.f043a != "" and record.type in ["TIC", "TUT"]:
        rules = {"ca": "ca", "ch": "ch", "ci": "au", "cs": "au", "ic": "ic",
                 "lo": "lo", "mi": "mi", "pl": "ba", "rt": "au", "te": "te"}

        if record.fields.f043a in rules:
            new_f043 = f"$o {rules[record.fields.f043a]}"
        else:
            new_f043 = f"valeur de la 043$a non trouvée : {record.fields.f043a}"
    elif sru.record2fieldvalue(record.xml_init, "141$a"):  # Si présence d'une 141 --> 043$o te
        new_f043 = "$o te"
    
    elif record.fields.f043b:
        rules043b = {"bd": "mi", "de": "ic", "er": "au", "es": "ic", "et": "au",
                     "jv": "lo", "pe": "ba", "ph": "ic", "sc": "ba", "sr": "au",
                     "st": "au", "tf": "au", "ws": "au"}
        if record.fields.f043b in rules043b:
            new_f043 = f"$o {rules043b[record.fields.f043b]} $b {record.fields.f043b}"
        else:
            new_f043 = f"valeur de la 043$b non trouvée : {record.fields.f043b}"
    if record.fields.f043o:
        new_f043 = f"Déjà renseigné : {record.fields.f043o}"
        if record.fields.f043o == "te":
            check_043 = verif_043_deja_presente(record)
            if check_043:
                new_f043 += f" - Proposition script : {check_043}"
    return new_f043


def verif_043_deja_presente(record):
    # si une 043$o te est déjà présente, on vérifie que le programme est d'accord avec
    temp_record = record
    temp_record.f043o = "mi"
    temp_record.new043 = "$o mi"
    f065_value = generate_065(record)
    if f065_value:
        return f"si 043 $o mi -> 065 {' '.join(f065_value)}"
    else:
        return ""



def generate_06X(record: Record):
    f06X_tag = ""
    f06X_value = ""
    f06X_label = ""
    new630, new631 = [], []

    if record.new043 == "$o te" or record.fields.f043o == "te":
        f06X_tag = "060"
        f06X_value = generate_060(record)
        if record.fields.f060:
            f06X_value = merge_06X(record.ark, "060", f06X_value, record.fields.f060)
    elif record.new043 == "$o au" or record.fields.f043o == "au":
        f06X_tag = "061"
        f06X_value = generate_061(record)
        if record.fields.f061:
            f06X_value = merge_06X(record.ark,"061", f06X_value, record.fields.f061)
    elif record.new043 == "$o lo"  or record.fields.f043o == "lo":
        f06X_tag = "062"
        f06X_value, new630, new631 = generate_062(record)
        if record.fields.f062:
            f06X_value = merge_06X(record.ark,"062", f06X_value, record.fields.f062)
    elif record.new043 == "$o ba" or record.fields.f043o == "ba":
        f06X_tag = "063"
        f06X_value = generate_063(record)
        if record.fields.f063:        
            f06X_value = merge_06X(record.ark,"063", f06X_value, record.fields.f063)
    elif record.new043 == "$o ic" or record.fields.f043o == "ic":
        f06X_tag = "064"
        f06X_value = generate_064(record)
        if record.fields.f064:
            f06X_value = merge_06X(record.ark,"064", f06X_value, record.fields.f061)
    elif record.new043 == "$o mi" and record.type in "TIC,TUT" or record.fields.f043o == "mi":
        f06X_tag = "065"
        f06X_value = generate_065(record)
        if record.fields.f065:
            f06X_value = merge_06X(record.ark,"065", f06X_value, record.fields.f065)
    return {"tag": f06X_tag, "value": f06X_value, "label": f06X_label}, new630, new631


def dedub_06X(field06X):
    # Dédoublonne les valeurs de la 06X, en gardant l'ordre d'injection
    liste_dedub = []
    for el in field06X["value"]:
        if el not in liste_dedub:
            liste_dedub.append(el)
    field06X["value"] = liste_dedub
    return field06X

def merge_06X(ark, zone, new_val, old_val):
    # Fusion des sous-zones de la nouvelle valeur (calculée par l'algo)
    # et de l'ancienne
    merged = []
    new_val = [el[1:] for el in new_val]
    old_val = [el.strip() for el in old_val.split("$") if el.strip()]
    print(217, ark, new_val, "<-->", old_val)
    temp = []
    for char in ascii_lowercase:        # On alimente "temp" par ordre alphabétique,
        for el in old_val:              # avec les éléments old_val avant ceux new_val
            if el[0] == char:
                temp.append(el)
        for el in new_val:
            if el[0] == char:
                temp.append(el)
    subfields_passed = []
    for el in temp:
        sub = el[0]
        if el not in subfields_passed:
            merged.append(el)
            subfields_passed.append(sub)
        elif rules_repetabilite[zone] != "*" and sub not in rules_repetabilite[zone]:
            merged.append(el)
    merged = [f"${el.replace('_nouveau', '')}" for el in merged]
    
    print(236, ark, zone, new_val, " + ", old_val, "-->", merged)
    return merged



def generate_060(record: Record):
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f060 = []
    if record.fields.f624a == "100":
        f060.append("$a philo")
    expressions2values = [["(anthologie|anthologies)", "$b antho", "145,445,600"],
                            ["(catéchisme|catéchismes)", "$b catec", "145,445,600"],
                            ["(correspondance|correspondances)", "$b corre", "145,445,600"],
                            ["(dictionnaire biographique|dictionnaires biographiques)", "$b dicbi", "600"],
                            ["(dictionnaire étymologique|dictionnaire d'étymologie|dictionnaire d'etymologie)", "$b dicet", "600"],
                            ["(dictionnaire|dictionnaires)", "$b dicti", "145,445,600"],
                            ["(livret|livrets)", "$b livre", "600"],
                            ["(chanson de geste|chansons de geste)", "$c chans", "TUT141"],
                            ["(comédie|comédies)", "$c comed", "600"],
                            ["(conte|contes)", "$c conte", "600"],
                            ["(dialogue|dialogues)", "$c dialo", "600"],
                            ["(épopée|épopées)", "$c epope", "600"],
                            ["(épopée|épopées)", "$c epope", "145,445"],
                            ["(fable|fables)", "$c fable", "600"],
                            ["(fabliau|fabliaus)", "$c fabli", "600"],
                            ["(farce|farces)", "$c farce", "600"],
                            ["jeu de carnaval", "$c jeuca", "600"],
                            ["journal intime", "$c jouin", "600"],
                            ["lai", "$c laiss", "600"],
                            ["maximes", "$c maxim", "600"],
                            ["(miracle|miracles)", "$c mirac", "600"],
                            ["(mystère|mystères)", "$c myste", "600"],
                            ["(nouvelle|nouvelles)", "$c nouve", "600"],
                            ["(oraison funèbre|oraisons funèbres)", "$c orais", "600"],
                            ["(pamphlet|pamphlets)", "$c pamph", "600"],
                            ["(panégyrique|panégyriques)", "$c paneg", "600"],
                            ["(pièce en un acte|pièce de théâtre en un acte)", "$c piact", "600"],  # ALERT Aberration : condition de 6 mots -> ajout d'une condition : si la 600$a commence par
                            ["(poésie|poésies|poème|poèmes)", "$c poesi", "600"],
                            ["proverbes", "$c prove", "600"],
                            ["récit de voyage", "$c recvo", "600"],
                            ["roman d'aventures", "$c roave", "600"],
                            ["roman de chevalerie", "$c roche", "600"],
                            ["roman courtois", "$c rocou", "600"],
                            ["(roman|romans)", "$c roman", "600"],
                            ["roman policier", "$c ropol", "600"],
                            ["(satire|satires)", "$c satir", "600"],
                            ["science-fiction", "$c scifi", "600"],
                            ["(sonnet|sonnets)", "$c sonne", "600"],
                            ["(théâtre|théâtres|drame|drames)", "$c theat", "3mots6"],
                            ["(tragédie|tragédies)", "$c trage", "600"],
                            ["(vaudeville|vaudevilles)", "$c vaude", "600"],
                            ["(charte|chartes)", "$e chart", "145,445,600"],
                            ["(concordat|concordats)", "$e conco", "600"],
                            ["(constitution|constitutions)", "$e const", "145,445,600", '(apostolique|dogmatique|pastorale|du concile|église catholique)'],
                            ["(coutumier|coutumiers)", "$e coutm", "600"],
                            ["340", "$e traite", "624"],
                            ["(commentaire biblique|commentaires bibliques)", "$f combi", "600"],
                            ["(commentaire exégétique|commentaires exégétiques)", "$f comex", "600"],
                            ["(constitution apostolique|constitutions apostoliques)", "$f const", "600"], 
                            ["(encyclique|encycliques)", "$f encyc", "600"],
                            ["(exhortation apostolique|exhortations apostoliques)", "$f exhor", "600"],
                            ["(texte funéraire|textes funéraires)", "$f funer", "600"],
                            ["(lettre apostolique|lettres apostoliques|motu proprio)", "$f letap", "600"],
                            ["(livre liturgique|livres liturgiques)", "$f livli", "600"],
                            ["(ouvrage de mystique|ouvrages de mystique)", "$f mysti", "600"],
                            ["(ouvrage de piété|ouvrages de piété)", "$f piete", "600"],
                            ["(sermon|sermons|homélie|homélies)", "$f sermo", "600"],
                            ["(ouvrage de spiritualité|ouvrages de spiritualité)", "$f spiri", "600"],
                            ["(testament spirituel|testaments spirituels)", "$f tessp", "600"],
                            ["130", "$a philo", "624"],
                            ["150,300,304,360,391,401", "$a scihu", "624"],
                            [",".join([str(i) for i in range(500,591)]), "$a scipu", "624"],
                            [",".join([str(i) for i in range(600,691)]), "$a techn", "624"],
                            ["bibliographie", "$b bibli", "145,445,600"],
                            ["encyclopédie", "$b encyc", "145,445"],
                            ["enquête", "$b enque", "600"],
                            ["glossaire", "$b glole", "600"],
                            ["exégèse biblique", "$f combi", "600"],
                            ["264.015", "$g cator", "628"],
                            ["264.02", "$g catho", "628"],
                            [["294.382", "bouddh*"], "$g boudd", "bouddbrahmluth"],
                            [["294.382", "brahm*"], "$g brahm", "bouddbrahmluth"],
                            ["294.4", "$g jaini", "628"],
                            ["294.592", "$g hindo", "628"],
                            ["294.592", "$g hindo", "628"],
                            ["294.6", "$g sikhi", "628"],
                            ["295", "$g zoroa", "628"],
                            ["296.45", "$g judai", "628"],
                            ["296.1", "$g judai", "628"],
                            ["296.12", "$g judai", "628"],
                            ["297.38", "$g islam", "628"],
                            ["299.31", "$g relan", "628"],
                            ["264.017 2", "$g copto", "628"],
                            ["264.019", "$g ortho", "628"],
                            ["264.09", "$g chreti", "628"],
                            ["296.155", "$g judai", "628"],
                            ["296.16", "$g judai", "628"],
                            [["264.04", "luther*"], "$g luthe", "bouddbrahmluth"],
                            ["(ouvrage de théologie|ouvrages de théologie)", "$f theol", "600"],
                            ]
    for expr in expressions2values:
        if len(expr) == 3:
            expr.append("")
        test = searchfor060(record, expr[0], expr[1], expr[2], expr[3], f060)
        """if test:
            break"""    # ALERT : appliquer cette règle si la 060 $xxx n'est pas répétable (pas clair)
    return f060


def searchfor060(record, expression, valeur060, conditions, exceptions, f060):
    test = False
    if "145" in conditions and (re.match(expression, record.fields.f145a.lower()) is not None or re.match(expression, record.fields.f145a_sans_article.lower()) is not None or re.search(expression, record.fields.f145a_3mots.lower()) is not None):
        if exceptions:
            if re.match(exceptions, record.fields.f145a.lower()) is None and "11869156" not in sru.record2fieldvalue(record.xml_init, "100$3"):
                f060.append(valeur060)
                test = True
        else:
            f060.append(valeur060)
            test = True
    if "445" in conditions:
        liste_445a = record.fields.f445a.lower().split("¤") + record.fields.f445a_sans_article.lower().split("¤")
        for f445a_occ in liste_445a:
            f445a_occ_3mots = f445a_occ.split(" ")
            if len(f445a_occ_3mots) > 2:
                f445a_occ_3mots = " ".join(f445a_occ_3mots[0:3])
            else:
                f445a_occ_3mots = " ".join(f445a_occ_3mots)
            if (re.match(expression, f445a_occ) is not None or re.match(expression, f445a_occ) is not None  or re.search(expression, f445a_occ_3mots) is not None):
                if exceptions:
                    if re.match(exceptions, record.fields.f445a.lower()) is None and "11869156" not in sru.record2fieldvalue(record.xml_init, "100$3"):
                        f060.append(valeur060)
                        test = True                  
                else:
                    f060.append(valeur060)
                    test = True
    if "600" in conditions and (re.search(expression, record.fields.f600a_5mots.lower()) is not None or re.match(expression, record.fields.f600a.lower()) is not None):
        if exceptions:
            if re.match(exceptions, record.fields.f600a_5mots.lower()) is None:
                f060.append(valeur060)
                test = True
        else:
            f060.append(valeur060)
            test = True
    if "TUT141" in conditions and record.type == "TUT" and re.search(expression, record.fields.f600a_5mots.lower()) is not None:
        f060.append(valeur060)
        test = True
    if "3mots6" in conditions and re.search(expression, record.fields.f600a_3mots.lower()) is not None:
        f060.append(valeur060)
        test = True
    if "624" in conditions and record.fields.f624a:
        for val in expression.split(","):
            if val in record.fields.f624a:
                f060.append(valeur060)
                test = True
    if "628" in conditions and sru.record2fieldvalue(record.xml_init, "628$a") == expression:
        f060.append(valeur060)
        test = True
    if "bouddbrahmluth" in conditions:
        if sru.record2fieldvalue(record.xml_init, "628$a") == expression[0] and re.search(expression[1], "600$a") is not None:
            f060.append(valeur060)
            test = True
    return test


def generate_061(record: Record):
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f061 = []

    if ("$o au" in record.new043 or "$o au" in record.fields.f043) and re.search("(art vidéo|art video)", record.fields.f600a.lower()) is not None:
        f061.append("$a av")
    if "$b er" in record.new043 or "$b er" in record.fields.f043:
        f061.append("$a er")
    if "$b et" in record.new043 or "$b et" in record.fields.f043:
        f061.append("$a et")
    if "émission télévisée" in record.fields.f145e.lower():
        f061.append("$a et")
    if "film" in record.fields.f145e.lower():
        f061.append("$a fi")
    if "$b sr" in record.new043 or "$b sr" in record.fields.f043:
        f061.append("$a sr")
    if "série télévisée" in record.fields.f145e.lower():
        f061.append("$a et")
    if("$o au" in record.new043 or "$o au" in record.fields.f043) and re.search("série télévisée", record.fields.f600a_5mots.lower()) is not None:
        f061.append("$a st")
    if "$b st" in record.new043 or "$b st" in record.fields.f043:
        f061.append("$a st")
    if re.search("(téléfilm|télé-film)", record.fields.f600a_5mots.lower()) is not None:
        f061.append("$a tf")
    if "téléfilm" in record.fields.f145e.lower():
        f061.append("$a tf")
    if "$b tf" in record.new043:
        f061.append("$a tf")   
    if "web-série" in record.fields.f145e.lower():
        f061.append("$a ws")
    if "web-documentaire" in record.fields.f145e.lower():
        f061.append("$a wd")  
    if "$a fi" in f061 and ("$a documentaire" in sru.record2fieldvalue(record.xml_init, "600").lower() or "film documentaire" in sru.record2fieldvalue(record.xml_init, "600").lower()):
        f061.append("$b fd")
    if "$a fi" in f061 and ("$a fiction" in sru.record2fieldvalue(record.xml_init, "600").lower() or "film de fiction" in sru.record2fieldvalue(record.xml_init, "600").lower()):
        f061.append("$b ff")
    if "$a fi" in f061 and "film biographique" in sru.record2fieldvalue(record.xml_init, "600").lower():
        f061.append("$c ffbi")
    if "$a fi" in f061 and (re.search("(film burlesque|comédie)", record.fields.f600a.lower()) is not None):
        f061.append("$c ffco")
    if "$a fi" in f061 and (re.search("film catastrophe", record.fields.f600a.lower()) is not None):
        f061.append("$c ffca")
    if "$a fi" in f061 and (re.search("film d'arts martiaux", record.fields.f600a.lower()) is not None):
        f061.append("$c ffam")
    if "$a fi" in f061 and (re.search("film d'aventures et d’action", record.fields.f600a.lower()) is not None):
        f061.append("$c ffaa")
    if "$a fi" in f061 and (re.search("film d'horreur", record.fields.f600a.lower()) is not None):
        f061.append("$c ffho")
    if "$a fi" in f061 and (re.search("film de danse", record.fields.f600a.lower()) is not None):
        f061.append("$c ffda")
    if "$a fi" in f061 and (re.search("film de guerre", record.fields.f600a.lower()) is not None):
        f061.append("$c ffgu")
    if "$a fi" in f061 and (re.search("film de science-fiction", record.fields.f600a.lower()) is not None):
        f061.append("$c ffsf")
    if "$a fi" in f061 and (re.search("film dramatique", record.fields.f600a.lower()) is not None):
        f061.append("$c ffdr")
    if "$a fi" in f061 and (re.search("film érotique", record.fields.f600a.lower()) is not None):
        f061.append("$c ffer")
    if "$a fi" in f061 and (re.search("film fantastique", record.fields.f600a.lower()) is not None):
        f061.append("$c fffa")
    if "$a fi" in f061 and (re.search("film historique", record.fields.f600a.lower()) is not None):
        f061.append("$c ffhi")
    if "$a fi" in f061 and (re.search("film musical", record.fields.f600a.lower()) is not None):
        f061.append("$c ffmu")
    if "$a fi" in f061 and (re.search("(film policier|thriller|espionnage)", record.fields.f600a.lower()) is not None):
        f061.append("$c ffpo")
    if "$a fi" in f061 and (re.search("film pornographique", record.fields.f600a.lower()) is not None):
        f061.append("$c ffpr")
    if "$a fi" in f061 and (re.search("western", record.fields.f600a.lower()) is not None):
        f061.append("$c ffwe")
    if "$a et" in f061 and (re.search("émission télév?i?s?é?e? de divertissement", record.fields.f600a.lower()) is not None):
        f061.append("$e etdi")
    if "$a st" in f061 and (re.search("série télév?i?s?é?e? documentaire", record.fields.f600a.lower()) is not None):
        f061.append("$f std")
    if "$a st" in f061 and (re.search("série télév?i?s?é?e? d’aventures et d’action", record.fields.f600a.lower()) is not None):
        f061.append("$g staa")
    if "$a st" in f061 and (re.search("série télév?i?s?é?e? de comédie", record.fields.f600a.lower()) is not None):
        f061.append("$g stco")
    if "$a st" in f061 and (re.search("série télév?i?s?é?e? de science-fiction", record.fields.f600a.lower()) is not None):
        f061.append("$g stsf")
    if "$a st" in f061 and (re.search("série télév?i?s?é?e? d’horreur", record.fields.f600a.lower()) is not None):
        f061.append("$g stho")
    if "$a st" in f061 and (re.search("série télév?i?s?é?e? fantastique", record.fields.f600a.lower()) is not None):
        f061.append("$g stfa")
    if "$a st" in f061 and (re.search("(série télév?i?s?é?e? policière|série télév?i?s?é?e? policière|série télév?i?s?é?e? judiciaire)", record.fields.f600a.lower()) is not None):
        f061.append("$g stpj")
    if ("$o au" in record.new043 or "$o au" in record.fields.f043) and (re.search("court métrage", record.fields.f600a.lower()) is not None):
        f061.append("$k mc")
    if ("$o au" in record.new043 or "$o au" in record.fields.f043) and (re.search("long métrage", record.fields.f600a.lower()) is not None):
        f061.append("$k ml")
    if ("$o au" in record.new043 or "$o au" in record.fields.f043) and (re.search("moyen métrage", record.fields.f600a.lower()) is not None): 
        f061.append("$k mm")
    if ("$a st" in f061 or "$a fi" in f061) and (re.search("film d'animation", record.fields.f600a.lower()) is not None):
        f061.append("$l ani")
    if ("$a st" in f061 or "$a fi" in f061) and (re.search("dessin animé", record.fields.f600a.lower()) is not None):
        f061.append("$l dea")
    return f061


def generate_062(record: Record):
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f062 = []
    if "$b jv" in record.new043:
        f062.append("$a jv")
    if "logiciel" in record.fields.f145f.lower():
        f062.append("$a lo")
    if "système d'exploitation des ordinateurs" in record.fields.f145f.lower():
        f062.append("$a lo")
    if "$a jv" in f062 and test2e600(record, "jeu d'action"):
        f062.append("$b jvac")
    if "$a jv" in f062 and test2e600(record, "jeu d'arcade"):
        f062.append("$b jvar")
    if "$a jv" in f062 and test2e600(record, "jeu d’aventure"):
        f062.append("$b jvav")
    if "$a jv" in f062 and test2e600(record, "jeu de rôle"):
        f062.append("$b jvro")
    if "$a jv" in f062 and test2e600(record, "jeu de stratégie"):
        f062.append("$b jvst")
    if "$a jv" in f062 and test2e600(record, "jeu de gestion"):
        f062.append("$b jvge")
    if "$a jv" in f062 and test2e600(record, "jeu de réflexion"):
        f062.append("$b jvre")
    if "$a jv" in f062 and test2e600(record, "jeu éducatif"):
        f062.append("$b jved")
    if "$a jv" in f062 and test2e600(record, "jeu de simulation de vie"):
        f062.append("$b jvsv")
    if "$a jv" in f062 and test2e600(record, "jeu de simulation sportive"):
        f062.append("$b jvsp")
    if "$a jv" in f062 and test2e600(record, "jeu de développement personnel"):
        f062.append("$b jvdp")
    if "$a jv" in f062 and test2e600(record, "jeu de pilotage"):
        f062.append("$b jvpi")
    if "$a jv" in f062 and test2e600(record, "jeu de rythme"):
        f062.append("$b jvry")

    # ALERT : ensemble de consignes incomplètes
    # Si 062$a = lo (généré un peu plus haut) et si
    new630 = []
    new631 = []
    reg = "(série de jeux vidéo|jeu d’action|jeu d’arcade|jeu d’aventure|jeu de rôle|jeu de stratégie|jeu de gestion|jeu de réflexion|jeu éducatif|jeu de simulation de vie|jeu de simulation sportive|jeu de développement personnel|jeu de pilotage|jeu de rythme)"
    if "$a jv" in f062:
        for f600 in sru.record2fieldvalue(record.xml_init, "600").split("¤"):
            if re.search(reg, f600.lower()) is None and re.search("série de jeux vidéo", f600.lower()) is None:  # ALERT : ajout de la seconde condition, pour être cohérent avec la suite
                new630.append(f600)
            elif re.search(reg, f600.lower()) is None and re.search("série de jeux vidéo", f600.lower()) is not None:
                new631.append(f600)
    # ALERT : nécessairement, l'ensemble des 600$a aura été soit converti en code 062, soit déplacé en 630 ou 631, 
    # et donc chaque 600$a peut disparaître, non ?
    return f062, new630, new631


def test2e600(record, string):
    # Vérifier si au moins 2 600$a, et que la première contient une chaîne de caractères
    f600 = sru.record2fieldvalue(record.xml_init, "600$a").split("¤")
    if len(f600) > 1 and string in f600[0].lower():
        return True
    else:
        return False


def generate_063(record: Record):
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f063 = []
    if re.match("(mosaique|mosaiques|mosaïque|mosaïques)", record.fields.f145e.lower()) is not None:
        f063.append("$a bamo")
    if re.search("(mosaique|mosaiques|mosaïque|mosaïques)", record.fields.f600a_5mots.lower()) is not None:
        f063.append("$a bamo")
    if re.search("(peinture|peintures)", record.fields.f600a_5mots.lower()) is not None:
        f063.append("$a bape")
    if re.search("peinture", record.fields.f145f.lower()) is not None:
        f063.append("$a bape")
    if re.search("peinture", record.fields.f145e.lower()) is not None:
        f063.append("$a bape")
    if "$b pe" in record.new043:
        f063.append("$a bape")
    if re.search("sculpture", record.fields.f600a_5mots.lower()) is not None:
        f063.append("$a basc")
    if re.search("sculpture", record.fields.f145f.lower()) is not None:
        f063.append("$a basc")
    if re.search("sculpture", record.fields.f145e.lower()) is not None:
        f063.append("$a basc")
    if "$b sc" in record.new043:
        f063.append("$a basc")
    if re.search("tapisserie", record.fields.f145f.lower()) is not None:
        f063.append("$a bata")
    if re.search("tapisserie", record.fields.f145e.lower()) is not None:
        f063.append("$a bata")
    if re.search("tapisserie", record.fields.f600a_5mots.lower()) is not None:
        f063.append("$a bata")
    if re.search("(vitraux|vitraux)", record.fields.f145f.lower()) is not None:
        f063.append("$a bavi")
    if re.search("(vitraux|vitraux)", record.fields.f145e.lower()) is not None:
        f063.append("$a bavi")
    if re.search("(vitraux|vitraux)", record.fields.f600a_5mots.lower()) is not None:
        f063.append("$a bavi")
    return f063


def generate_064(record: Record):
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f064 = []
    if "$b de" in record.new043:
        f064.append("$a icde")
    if "$b es" in record.new043:
        f064.append("$a ices")
    if "$b ph" in record.new043:
        f064.append("$a icph")
    return f064


def generate_065(record: Record):
    # Si l'information est répétée, on génère plusieurs sous-zones au sein d'une même zone
    f065 = []
    if "$b bd" in record.new043:
        f065.append("$a bddes")
    rules065 = [["bande dessinée érotique", "bdero"],
                ["(bandes dessinées d'aventures|bande dessinée d'aventure)", "bdave"],
                ["(bandes dessinées de science-fiction|bande dessinée de science-fiction)", "bdsfi"],
                ["(bande dessinée de western|bandes dessinées de western)", "bdwes"],
                ["bande dessinée historique", "bdhis"],
                ["bande dessinée humoristique", "bdhum"],
                ["(comic|comics)", "comic"],
                ["(manga|mangas)", "manga"],
                ["(roman graphique|romans graphiques)", "rogra"],
                ["shônen", "shone"],
                ["(bandes dessinées|bande dessinée|série de bandes dessinées|séries de bandes dessinées)", "bddes"]
                ]
    for rule in rules065:
        if re.search(rule[0], record.fields.f600a_5mots.lower()) is not None:
            f065.append(f"$a {rule[1]}")
        else:
            rule_serie = rule[0].replace("(", "(séries? de ").replace("|", "|séries? de ")  # Ajout d'une règle pour les séries : la séquence de mots est trop longue et dépasse les 5 mots
            if re.search(rule_serie, record.fields.f600a.lower()) is not None:
                f065.append(f"$a {rule[1]}")
    return f065


def generate_xml_record(record: Record):
    # A partir d'un objet Record, renvoie d'un objet XML
    # constituant la nouvelle notice
    # intégrant la 043, la 06X et le transfert des 600 en 630 
    # (et d'autres trucs éventuels)
    tags = "043,060,061,062,063,064,065,600,630".split(",")
    new_xml_record = etree.Element("record")
    test043 = False
    test06X = False
    test630 = False
    for node in record.xml_init.xpath("*"):
        if "leader" in node.tag:
            new_xml_record.append(deepcopy(node))
        else:
            # print(record.ark, etree.tostring(node))
            tag = node.get("tag")
            if int(tag) < 43:
                new_xml_record.append(deepcopy(node))
            elif tag == "043":
                test043 = True
                if record.new043.startswith("$"):
                    new_node = f'<datafield tag="043" ind1=" " ind2=" "><subfield code="{record.new043[1]}">{record.new043[3:]}</subfield></datafield>'
                    new_node = etree.fromstring(new_node)
                    new_xml_record.append(new_node)
                else:
                    new_xml_record.append(deepcopy(node))
            elif int(tag) > 43 and test043 is False and int(tag) < 60:
                test043 = True
                if record.new043.startswith("$"):
                    new_node = f'<datafield tag="043" ind1=" " ind2=" "><subfield code="{record.new043[1]}">{record.new043[3:]}</subfield></datafield>'
                    new_node = etree.fromstring(new_node)
                    new_xml_record.append(new_node)
                new_xml_record.append(deepcopy(node))
            elif int(tag) > 60 and test043 is False and test06X is False:
                test043 = True
                test06X = True
                if record.new043.startswith("$"):
                    new_node = f'<datafield tag="043" ind1=" " ind2=" "><subfield code="{record.new043[1]}">{record.new043[3:]}</subfield></datafield>'
                    new_node = etree.fromstring(new_node)
                    new_xml_record.append(new_node)
                if record.new06X["value"]:
                    new_tag = record.new06X["tag"]
                    new_value = record.new06X["value"]
                    new_node = f'<datafield tag="{new_tag}" ind1=" " ind2=" ">'
                    for val in new_value:
                        subf = f'<subfield code="{val[1]}">{val[3:]}</subfield>'
                        new_node += subf
                    new_node += "</datafield>"
                    new_node = etree.fromstring(new_node)
                    new_xml_record.append(new_node)
                new_xml_record.append(deepcopy(node))
            elif int(tag) > 43 and test043 and int(tag) < 60:
                new_xml_record.append(deepcopy(node))
            elif tag in "060,061,062,063,064,065".split(",") and test06X is False:
                test06X = True
                if record.new06X:
                    new_tag = record.new06X["tag"]
                    new_value = record.new06X["value"]
                    if new_value:
                        new_node = f'<datafield tag="{new_tag}" ind1=" " ind2=" ">'
                        for val in new_value:
                            subf = f'<subfield code="{val[1]}">{val[3:]}</subfield>'
                            new_node += subf
                        new_node += "</datafield>"
                        new_node = etree.fromstring(new_node)
                        new_xml_record.append(new_node)
                    else:
                        new_xml_record.append(deepcopy(node)) 
                else:
                   new_xml_record.append(deepcopy(node))
            elif int(tag) > 65 and test06X is False:
                test06X = True
                if record.new06X["value"]:
                    new_tag = record.new06X["tag"]
                    new_value = record.new06X["value"]
                    new_node = f'<datafield tag="{new_tag}" ind1=" " ind2=" ">'
                    for val in new_value:
                        subf = f'<subfield code="{val[1]}">{val[3:]}</subfield>'
                        new_node += subf
                    new_node += "</datafield>"
                    new_node = etree.fromstring(new_node)
                    new_xml_record.append(new_node)
                new_xml_record.append(deepcopy(node))
            elif int(tag) > 65 and test06X and int(tag) < 600:
                new_xml_record.append(deepcopy(node))
            elif tag == "600":
                # ICI, contrôler les 600 à supprimer
                check_preserver600 = True
                """check_preserver600 = False
                for f600a in sru.field2subfield(node, "a").split("¤"):
                    value = f"$a {f600a}"
                    if value not in record.new630 + record.new631:
                        check_preserver600 = True"""
                if check_preserver600:
                    new_node = '<datafield tag="600" ind1=" " ind2=" ">'
                    for f600a in sru.field2subfield(node, "a").split("¤"):
                        value = f"$a {f600a}"
                        if value not in record.new630 + record.new631:
                            subf = f'<subfield code="a">{replace_xml_entities(f600a)}</subfield>'
                            new_node += subf
                    new_node += "</datafield>"
                    new_node = etree.fromstring(new_node)
                    new_xml_record.append(new_node)

            elif int(tag) > 600 and int(tag) < 630:
                new_xml_record.append(deepcopy(node))
            elif int(tag) > 630 and test630 is False:
                test630 = True
                if record.new630:
                    new_node = '<datafield tag="630" ind1=" " ind2=" ">'
                    for subf in record.new630:
                        new_node += f'<subfield code="a">{subf}</subfield>'
                    new_node += "</datafield>"
                    new_node = etree.fromstring(new_node)
                    new_xml_record.append(new_node)
                if record.new631:
                    new_node = '<datafield tag="631" ind1=" " ind2=" ">'
                    for subf in record.new631:
                        new_node += f'<subfield code="a">{subf}</subfield>'
                    new_node += "</datafield>"
                    new_node = etree.fromstring(new_node)
                    new_xml_record.append(new_node)
                new_xml_record.append(deepcopy(node))
            elif int(tag) > 630 and test630:
                new_xml_record.append(deepcopy(node))
    if record.new043 or record.new06X["value"]:
        new_node = '<datafield tag="909" ind1=" " ind2=" "><subfield code="a">Notice modifiée automatiquement : injection de zone 043 et 06X</subfield></datafield>'
        new_node = etree.fromstring(new_node)
        new_xml_record.append(new_node)
    # A désactiver quand tout est débuggué :
    # new_xml_record = record.xml_init

    return new_xml_record


def replace_xml_entities(string):
    chars = {"&": "&amp;",
             ">": "&gt;",
             "<": "&lt;"}
    for char in chars:
        string = string.replace(char, chars[char])
    return string

def generate_metas_tab(record: Record):
    # Génération d'une ligne de tableau contenant:
    # ark, type notice, nouvelle 043, étiquette 6XX, valeur 6XX, autres modifs, ancienne notice, nouvelle notice
    tag06X = record.new06X["tag"]
    if len(record.new06X["value"]) == 0:
        tag06X = ""
        record.new06X["value"] = ""
    seq_init = sru.xml2seq(record.xml_init, field_sep="\n").replace("\n000", "000").replace('"', '""')
    seq_init = f'"{seq_init}"'
    seq_final = sru.xml2seq(record.new_xml, field_sep="\n").replace("\n000", "000").replace('"', '""')
    seq_final = f'"{seq_final}"'
    return [record.ark, record.type, record.new043, tag06X, str(record.new06X["value"]),
            record.new630, record.new631,
            "", seq_init, seq_final] 


def extract_load(query, reports_prefix):
    params = {"recordSchema": "intermarcxchange", "maximumRecords":"500"}
    dict_svm = get_video_table()
    report_tab = create_file(f"{reports_prefix}.tsv", "ark,type notice,nouvelle 043,étiquette 06X,valeur 06X,nouvelle 630, nouvelle 631,autres modifs,ancienne notice,nouvelle notice".split(","))
    report_xml = create_file(f"{reports_prefix}.xml")
    report_pb_043te = create_file(f"{reports_prefix}_pb043te.txt")
    debut_fichier_xml(report_xml)
    results = sru.SRU_result(query, parametres=params)
    for ark in results.dict_records:
        if ark2nn(ark)[0] in dict_svm:
            metas = [ark, "BXD/SVM", dict_svm[nn2ark(ark)]["043"], dict_svm[nn2ark(ark)]["06X"][0:3], dict_svm[nn2ark(ark)]["06X"][3:].strip()]
            line2report(metas, report_tab, display=False)
        else:
            record = Record(ark, results.dict_records[ark])
            if record.f043error is not None:
                line2report(record.metas_tab, report_pb_043te, display=False)
            else:
                line2report(record.metas_tab, report_tab, display=False)
    i = 501
    while i < results.nb_results:
        params["startRecord"] = str(i)
        results = sru.SRU_result(query, parametres=params)
        for ark in results.dict_records:
            if results.dict_records[ark] is not None:
                record = Record(ark, results.dict_records[ark])
                line2report(record.metas_tab, report_tab, display=False)
            else:
                print(i, ark, results.dict_records[ark])
            i += 1
    fin_fichier_xml(report_xml)


def get_video_table():
    fname = "table_OR.xlsx"
    df = pd.read_excel(fname, sheet_name="Bilan")
    df = df.fillna("")
    df = df.astype(str)
    dict_svm = {}
    for i, row in df.iterrows():
        nna = row["nna"]
        f043 = row["new 043o"]
        f06X = row["new 06X"]
        if f06X.startswith("061") or f06X.startswith("062"):
            dict_svm[nna] = {"043": f043, "06X": f06X}
    return dict_svm


def check_repetabilite_zone(zone, valeur):
    """060 : toutes zones sont non répétables
        061 : zones non répétables = "ceghi"
        062 : zones non répétables = "a"
        063 : toutes zones sont non répétables
        064 : zones non répétables = "bc"
        065 : toutes zones sont non répétables"""
    subfields = [el.strip() for el in valeur.split("$") if el.strip()]
    controlled_val = []
    passed_subfields = []
    for sub in subfields:
        subfield = sub[0]
        if subfield not in passed_subfields:
            controlled_val.append(sub)
            passed_subfields.append(subfield)
        else:
            if subfield not in rules_repetabilite[zone] and rules_repetabilite[zone] != "*":
                controlled_val.append(sub)
    controlled_val = "$" + " $".join(controlled_val)
    print(776, zone, valeur, "-->", controlled_val)
    if (valeur != controlled_val):
        raise
    return controlled_val





def extract_load_file(arks):
    collection = etree.parse("castest-aut.xml")
    for xmlrecord in collection.xpath("//record"):
        ark = sru.clean_ark(sru.record2fieldvalue(xmlrecord, "003"))
        if ark in arks:
            record = Record(ark, xmlrecord)
            print(ark)
            print(sru.xml2seq(xmlrecord))
            print("----")
            print(record.new043)
            print(record.new06X)
            print(sru.xml2seq(record.new_xml))
            print("\n"*3)


def debut_fichier_xml(report_xml):
    line2report(['<?xml version="1.0" encoding="utf-8"?>'], report_xml, display=False)
    line2report(['<collection>'], report_xml, display=False)


def fin_fichier_xml(report_xml):
    line2report(['</collection>'], report_xml, display=False)


if __name__ == "__main__":
    test = input2default(input("Test ? o/[n] : "), "n")
    if test == "n":
        query = "aut.type any \"TIC TUT\" and aut.status any \"sparse validated\""
        # query = "aut.status any \"sparse validated\" and aut.persistentid any \"ark:/12148/cb14571449q ark:/12148/cb12533159k ark:/12148/cb162377504 ark:/12148/cb15020434p ark:/12148/cb12488688m ark:/12148/cb17740615v ark:/12148/cb16676218j ark:/12148/cb12331718t ark:/12148/cb136049153 ark:/12148/cb119683941 ark:/12148/cb135629866 ark:/12148/cb122410821 ark:/12148/cb120427987 ark:/12148/cb12252079k ark:/12148/cb125711488 ark:/12148/cb14437938w ark:/12148/cb120920719 ark:/12148/cb14559947x ark:/12148/cb145425488 ark:/12148/cb16710800m ark:/12148/cb121308593 ark:/12148/cb15121868h ark:/12148/cb157554530 ark:/12148/cb11985856j ark:/12148/cb12001150h ark:/12148/cb123460514 ark:/12148/cb14400550b ark:/12148/cb121784154 ark:/12148/cb12201676x ark:/12148/cb170172802 ark:/12148/cb121965458 ark:/12148/cb12199919j ark:/12148/cb12073812t ark:/12148/cb123209047 ark:/12148/cb15011576x ark:/12148/cb14616948w ark:/12148/cb15593148k ark:/12148/cb14489389n ark:/12148/cb15015591s ark:/12148/cb12502056d ark:/12148/cb16549408q ark:/12148/cb121098856 ark:/12148/cb17705195b ark:/12148/cb15972431q ark:/12148/cb14580209w ark:/12148/cb12167664f ark:/12148/cb165311318 ark:/12148/cb123420290 ark:/12148/cb123213980 ark:/12148/cb13328347x ark:/12148/cb17160391h ark:/12148/cb166624198 ark:/12148/cb15704760t ark:/12148/cb15059918m ark:/12148/cb159744405 ark:/12148/cb12565673m ark:/12148/cb170258646 ark:/12148/cb15112596z ark:/12148/cb135615020 ark:/12148/cb15535769f ark:/12148/cb150512898 ark:/12148/cb158017383 ark:/12148/cb16135383b ark:/12148/cb119656704 ark:/12148/cb17061860p ark:/12148/cb16629061t ark:/12148/cb16182927t ark:/12148/cb12565676n ark:/12148/cb170921838 ark:/12148/cb177776751 ark:/12148/cb15585057j ark:/12148/cb135360982 ark:/12148/cb162491803 ark:/12148/cb13197343d ark:/12148/cb169041583 ark:/12148/cb135177426 ark:/12148/cb177766137 ark:/12148/cb12128811t ark:/12148/cb15598560r ark:/12148/cb12485013b ark:/12148/cb13517616c ark:/12148/cb160615794 ark:/12148/cb14422307j ark:/12148/cb15608565s ark:/12148/cb162056246 ark:/12148/cb14531112q ark:/12148/cb14480164k ark:/12148/cb157338985 ark:/12148/cb12099201c ark:/12148/cb151187948 ark:/12148/cb136027330 ark:/12148/cb15079578s ark:/12148/cb16545320b ark:/12148/cb156653919 ark:/12148/cb14583901s ark:/12148/cb17750808b ark:/12148/cb12008332t ark:/12148/cb12237793v ark:/12148/cb157451309 ark:/12148/cb155530234 ark:/12148/cb14503046m ark:/12148/cb12081720w ark:/12148/cb12085494k ark:/12148/cb157276495 ark:/12148/cb16635559w ark:/12148/cb17048733s ark:/12148/cb11973390n ark:/12148/cb162347465 ark:/12148/cb177770741 ark:/12148/cb17026841s ark:/12148/cb124663568 ark:/12148/cb15502406c ark:/12148/cb165995724 ark:/12148/cb124663599 ark:/12148/cb14291244b ark:/12148/cb14291743c ark:/12148/cb14293147k ark:/12148/cb17060034p ark:/12148/cb17762378t ark:/12148/cb171335241 ark:/12148/cb17766840g ark:/12148/cb17084012r ark:/12148/cb170157981 ark:/12148/cb164587237 ark:/12148/cb137505931 ark:/12148/cb14444145f ark:/12148/cb14438888d ark:/12148/cb17133547p ark:/12148/cb12435995z ark:/12148/cb144388694 ark:/12148/cb12483109w ark:/12148/cb17044039z ark:/12148/cb12504867r ark:/12148/cb146619899 ark:/12148/cb14591035b ark:/12148/cb14662649g ark:/12148/cb164750668 ark:/12148/cb17702056f ark:/12148/cb13325370q ark:/12148/cb14596321p ark:/12148/cb17770547t ark:/12148/cb17717080q ark:/12148/cb170693669 ark:/12148/cb16555483q ark:/12148/cb17770547t ark:/12148/cb17099895w ark:/12148/cb14291810p ark:/12148/cb17063964t ark:/12148/cb170289092 ark:/12148/cb146622768 ark:/12148/cb13750598r ark:/12148/cb17049503j ark:/12148/cb124464800 ark:/12148/cb155322022 ark:/12148/cb166054292 ark:/12148/cb17165394r ark:/12148/cb17148669p ark:/12148/cb167585027 ark:/12148/cb171128126 ark:/12148/cb16595998z ark:/12148/cb166048513 ark:/12148/cb17136594x ark:/12148/cb166105191 ark:/12148/cb16569899c ark:/12148/cb165993074 ark:/12148/cb166042356 ark:/12148/cb170772495 ark:/12148/cb16145371j ark:/12148/cb161255365 ark:/12148/cb123670199 ark:/12148/cb144429753 ark:/12148/cb13331369r ark:/12148/cb12155900b ark:/12148/cb14408737m ark:/12148/cb161712728 ark:/12148/cb16601166g ark:/12148/cb17732613f ark:/12148/cb17731265b ark:/12148/cb177002090 ark:/12148/cb171317154 ark:/12148/cb14578636m ark:/12148/cb170939753 ark:/12148/cb14548849w ark:/12148/cb16705145n ark:/12148/cb135175012 ark:/12148/cb171600894 ark:/12148/cb16729657d ark:/12148/cb145673428 ark:/12148/cb177145555 ark:/12148/cb144447453 ark:/12148/cb171557652 ark:/12148/cb12046925j ark:/12148/cb12016336x ark:/12148/cb120773352 ark:/12148/cb120433673 ark:/12148/cb122197483 ark:/12148/cb13194727j ark:/12148/cb125545778 ark:/12148/cb120232991 ark:/12148/cb161358157 ark:/12148/cb146117484 ark:/12148/cb12228167p ark:/12148/cb17711111q ark:/12148/cb123487281 ark:/12148/cb17761027v ark:/12148/cb16548857s ark:/12148/cb120271882 ark:/12148/cb177272589 ark:/12148/cb12071178b ark:/12148/cb14557486z ark:/12148/cb14293147k\""
        # query = "aut.status any \"sparse validated\" and aut.persistentid any \"ark:/12148/cb14578636m"
        report_name = input("Préfixe des fichiers (XML et tab) en sortie : ")
        extract_load(query, report_name)
    else:
        liste_arks = input("Liste des ARK (sep : ',') : ")
        extract_load_file(liste_arks.split(","))

