# coding: utf-8

explain = """Extraction d'homonymes "flous" : à partir d'une liste de notices de personnes BnF (ARK),
on récupère les homonymes qui ont même nom de famille, et même prénom ou initiale compatible.
Par exemple :
    - Si la PEP s'appelle "Lafon, Alexandre", le script récupère
        - Lafon, A.
        - Lafon, Alexandre
        - Lafon, Alex
        - Lafon, Alex.
        mais pas "Lafon, Alexandra" ni "Lafon, Albert"
    - Si la PEP s'appelle "Lafon, A.", le script récupère
        - Lafon, A.
        - Lafon, Albert
        - Lafon, Alexandre
        - etc.
"""

from stdf import *
from cleanstring import clean_string, udecode
import SRUextraction as sru

class PEP:
    def __init__(self, ark, xml_record):
        self.ark = ark
        self.nna = ark2nn(self.ark)
        self.record = xml_record
        self.f100 = sru.record2fieldvalue(xml_record, "100")
        self.f100a = sru.record2fieldvalue(xml_record, "100$a")
        self.f100m = sru.record2fieldvalue(xml_record, "100$m")
        self.f100a_nett = clean_string(self.f100a, False, True)
        self.f100m_nett = clean_string(self.f100m, False, True)
        self.len_f100m_nett = len(self.f100m_nett)
        self.cas_prenom = check_cas_prenom(self.f100m)
        self.initiales = extract_initiales(self.f100m)
        self.cas_homonymie = ""


    def __str__(self):
        return " | ".join([self.ark, self.f100a, self.f100m])


class Comparaison:
    def __init__(self, pep1, pep2):
        self.check_nom = comparaison_noms(pep1, pep2)
        self.check_prenom, self.cas = comparaison_prenoms(pep1, pep2)
        self.comparaison_full = False
        if self.check_nom and self.check_prenom and pep1.ark != pep2.ark:
            self.comparaison_full = True
            

def comparaison_noms(pep1, pep2):
    nom_nett1 = clean_string(pep1.f100a)
    nom_nett2 = clean_string(pep2.f100a)
    if nom_nett1 == nom_nett2:
        return True
    else:
        return False


def comparaison_prenoms(pep1, pep2):
    # On compare le prénom le plus court (par défaut : pep1) avec le prénom le plus long
    pep_a = pep1  
    pep_b = pep2
    
    if pep_a.len_f100m_nett > pep_b.len_f100m_nett:
        pep_a = pep2
        pep_b = pep1
    # print(pep_b.f100m_nett)
    reg_prenom = prenom2regex(pep_b.f100m_nett)
    test = check_prenoms(reg_prenom, pep_a.f100m_nett)
    cas = " - ".join([pep1.cas_prenom, pep2.cas_prenom])
    return test, cas    


def check_prenoms(regex_prenom, prenomcourt):
    test = False
    if re.fullmatch(regex_prenom, prenomcourt) is not  None:
        test = True
    return test


def prenom2regex(prenom):
    # on cherche une chaîne de caractères composée de la même initiale, suivie d'un point ou d'une des autres lettres (chacune facultative) du prénom complet
    reg_prenom = []
    while "  " in prenom:
        prenom = prenom.replace("  ", " ")
    prenom = prenom.strip()
    if prenom:
        for mot in prenom.split(" "):
            initiale = mot[0]
            autreslettres = "?".join([el for el in mot[1:] if el != "."])
            if autreslettres:
                autreslettres += "?"
            else:
                autreslettres += ".*"
            reg_prenom.append(f"{initiale}\.?{autreslettres}")  
    reg_prenom = " ".join([el for el in reg_prenom if el])
    return reg_prenom


def nett_prenom(prenom):
    prenom = udecode(prenom).lower()
    prenom = prenom.replace("-", " ").strip()
    while "  " in prenom:
        prenom = prenom.replace("  ", " ")
    return prenom


def check_cas_prenom(f100m):
    # On regarde si la 100$m contient des initiales ou des prénoms complets
    f100m_nett = nett_prenom(f100m)
    cas = set()
    if f100m_nett == "":
        cas.add("100$m vide")
    else:
        for mot in f100m_nett.split(" "):
            if mot.endswith("."):
                cas.add("initiale")
            else:
                cas.add("Prénom")
    cas = sorted(list(cas))
    return "-".join(cas)


def extract_initiales(f100m):
    f100m_nett = nett_prenom(f100m)
    initiales = []
    if f100m_nett:
        for mot in f100m_nett.split(" "):
            initiales.append(mot[0])
    initiales = " ".join([f"{el}*" for el in initiales if el])
    return initiales


def file2extract(input_filename):
    report = input2outputfile(input_filename, "homonymes_flous.txt")
    line2report("ARK,NNA,100,100$a,100$m,H1 cas,H1 ARK,H1 NNA,H1 100,H1 100$a,H1 100$m".split(","), report)
    liste_ark = file2list(input_filename)
    for ark in liste_ark:
        if "ark" in ark:
            record = sru.SRU_result(f"aut.persistentid any \"{ark}\"", "http://noticesservices.bnf.fr/SRU", parametres={"recordSchema": "InterXMarc_Complet"}).firstRecord
            arkpep = PEP(ark, record)
            liste_homonymes = extract_homonymes_1PEP(ark, arkpep)
            liste_homonymes_validated = validate_homonymes(arkpep, liste_homonymes)
            line = [arkpep.ark, arkpep.nna, arkpep.f100, arkpep.f100a, arkpep.f100m]
            for pep in liste_homonymes_validated:
                line.extend([pep.cas_homonymie, pep.ark, pep.nna, pep.f100, pep.f100a, pep.f100m])
                line2report(line, report)


def validate_homonymes(pep_init, liste_homonymes_extraite):
    liste_homonymes_validated = []
    for pep in liste_homonymes_extraite:
        comparaison = Comparaison(pep_init, pep)
        if comparaison.comparaison_full:
            pep.cas_homonymie = comparaison.cas
            liste_homonymes_validated.append(pep)
    return liste_homonymes_validated



def extract_homonymes_1PEP(ark, arkpep):
    liste_homonymes = []
    query = f"aut.accesspoint all \"{arkpep.f100a_nett} {arkpep.initiales}\" and aut.type all \"PEP\" and aut.status any \"sparse validated\""
    params = {"recordSchema": "intermarcxchange", "maximumRecords": "500"}
    results = sru.SRU_result(query, parametres=params)
    print(query, results.nb_results, "résultats")
    if results.nb_results < 2000:
        for ark in results.dict_records:
            pep = PEP(ark, results.dict_records[ark])
            liste_homonymes.append(pep)
        i = 501
        while i < results.nb_results:
            params["startRecord"] = str(i)
            results = sru.SRU_result(query, parametres=params)
            for ark in results.dict_records:
                pep = PEP(ark, results.dict_records[ark])
                liste_homonymes.append(pep)
            i += 500
    return liste_homonymes


if __name__ == "__main__":
    input_filename = input("Fichier contenant la liste des ARK : ")
    if "ark:/" in input_filename:
        record = sru.SRU_result(f"IdPerenne any \"{input_filename}\"", "http://noticesservices.bnf.fr/SRU", parametres={"recordSchema": "InterXMarc_Complet"}).firstRecord
        arkpep = PEP(input_filename, record)
        liste_homonymes = extract_homonymes_1PEP(input_filename, arkpep)
        for pep in liste_homonymes:
            comparaison = Comparaison(arkpep, pep)
            if comparaison.comparaison_full:
                print(comparaison.cas, arkpep, "//", pep)
    else:
        file2extract(input_filename)