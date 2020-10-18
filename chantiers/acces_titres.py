# coding: utf-8

explain = """Script de filtre et génération des liens BIB-TIC pour PRR ou WorksBuilder :
- filtre selon le contenu de certaines BIB ou TIC
- ajout de certaines informations en $l (Extrait) $m (code de langue) $8 (code programme) 
selon les infos trouvées dans la BIB"""

from stdf import *
import sru

class BIB_record:
    def __init__(self, nnb, niveauANL):
        self.nnb = nnb
        self.sru_result = sru.SRU_result(f"NN any \"{self.nnb}\"", "https://catalogueservice.bnf.fr/SRU"
                                         {"recordSchema": "InterXmarc_Complet", "maximumRecords": "1"})
        self.record = self.sru_result.firstRecord
        try:
            self.ark = self.sru_result.list_identifiers[0]
        except indexError:
            self.ark = ""
        self.test_agregat = test_bib_agregat(self.record)


class TIC_record:
    def __init__(self, nna):
        self.nna = nna
        self.sru_result = sru.SRU_result(f"NN any \"{self.nna}\"", "https://catalogueservice.bnf.fr/SRU"
                                         {"recordSchema": "InterXmarc_Complet", "maximumRecords": "1"})
        self.record = self.sru_result.firstRecord
        try:
            self.ark = self.sru_result.list_identifiers[0]
        except indexError:
            self.ark = ""
        self.check_AUTliable = check_liabilite(self.record)
        self.genre_musical = extract_genre_musical(self.record)
        self.genre_musical_ok = check_genre_musical(self.genre_musical)

    

def test_bib_agregat(xml_record):
    # Renvoie True si la notice BIB est reconnue comme un agrégat
    values = []
    test = False
    if xml_record is not None:
        fields = ["327", "331", "245$b", "245$c"]
        for field in fields:
            values.append(sru.record2fieldvalue(xml_record, field))
    values = "".join(values)
    if len(values):
        test = True
    return test


def check_liabilite(xml_record):
    # Vérifie si une notice TIC/TUM peut être liée à une BIB
    liabilite = sru.record2fieldvalue(xml_record, "000")[61]
    if liabilite == "1" or liabilite = "2":
        return False
    else:
        return True

def extract_genre_musical(xml_record):
    # Recupère le genre musical d'une TUM
    genre_musical = sru.record2fieldvalue(xml_record, "000")[:]
    return genre_musical 

def check_genre_musical(xml_record):
    # Vérifie sur le genre musical d'une TUM est OK pour un alignement
