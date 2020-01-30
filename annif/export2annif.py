# coding: utf-8

explain ="""
Convertit un export catalogue BnF (output ExtraCat) en fichier de métadonnées
exploitable par Annif pour entraîner la machine
"""

from collections import defaultdict
import csv

import SRUextraction as sru
from stdf import *

rameau_dict = {}
dewey_dict = {}


class Record:
    def __init__(self, row, cols_metas, cols_rameau, cols_dewey):
        self.init = row
        self.id = row[0]
        self.metas = [""]
        for col in cols_metas:
            self.metas.append(clean_marc(row[col]))
        self.metas = " ".join([el.strip() for el in self.metas if el.strip()])
        self.rameau = {}
        self.dewey = {}
        for col in cols_rameau:
            if row[col]:
                for occ_field in row[col].split("¤"):
                    entryid, libelle = field2entry(occ_field, "rameau")
                    self.rameau[entryid] = libelle
        for col in cols_dewey:
            if row[col]:
                for occ_field in row[col].split("¤"):
                    entryid, libelle = field2entry(occ_field, "dewey")
                    self.dewey[entryid] = libelle
        self.rameau_ids = ";".join(self.rameau)
        self.rameau_libelles = ";".join([self.rameau[el] for el in self.rameau])
        self.dewey_ids = ";".join(self.dewey)
        self.dewey_libelles = ";".join([self.dewey[el] for el in self.dewey])


class Rameau_record:
    def __init__(self, record):
        self.record = record
        self.label_tag = ""
        convert = {"166": "subject", "167": "location",
                   "168": "date", "160": "person",
                   "161": "organization", "163": "serials",
                   "165": "work"}
        self.type = ""
        self.label = [""]
        if record is not None:
            for field in record.xpath("*[@tag]"):
                tag = field.get("tag")
                if tag.startswith("16"):
                    self.label_tag = tag
                    self.type = convert[tag]
                    for subf in field.xpath("*"):
                        if subf.get("code") != "w":
                            self.label.append(subf.text)
        self.label = " -- ".join([el for el in self.label if el])

class Dewey_record:
    def __init__(self, record):
        self.record = record
        self.label = [""]
        if record is not None:
            self.indice = sru.record2fieldvalue(record, "186$i")
            for field in record.xpath("*[@tag='186']"):
                for subf in field.xpath("*"):
                    code = subf.get("code")
                    no_label = ["w", "i", "v"]
                    if code not in no_label:
                        self.label.append(subf.text)
        self.label = " -- ".join([el for el in self.label if el])



def field2entry(occfield, record_type="rameau"):
    subfs = [el.strip() for el in occfield.split("$3 ") if el.strip()]
    entryid = ""
    entrylibelle = []
    if record_type == "rameau":
        for subf in subfs:
            nna = subf[0:8]
            entryid += nna
            entrylibelle.append(nna2label(nna, record_type))
        entrylibelle = " -- ".join(entrylibelle)
    else:
        subfs = [el.strip() for el in subfs[0].split("$")]
        entryid = subfs[0]
        for el in subfs[1:]:
            if el[0] == "i":
                entrylibelle = el[2:]
    return  entryid, entrylibelle


def nna2label(nna, record_type):
    libelle = ""
    if record_type == "rameau":
        if nna in rameau_dict:
            libelle = rameau_dict[nna]
        else:
            try:
                record = sru.SRU_result(f"aut.recordid any {nna}", parametres={"recordSchema": "intermarcxchange"}).firstRecord
                libelle = Rameau_record(record).label
                rameau_dict[nna] = libelle
            except AttributeError:
                pass
    elif record_type == "dewey":
        if nna in dewey_dict:
            libelle = dewey_dict[nna]
        else:
            try:
                record = sru.SRU_result(f"NN any {nna}", "http://noticesservices.bnf.fr/").firstRecord
                record = Dewey_record(record)
                libelle = record.indice
                dewey_dict[nna] = {"label": record.label,
                                   "indice": record.indice}
            except AttributeError:
                pass
            
    return libelle



def clean_marc(marc_val, sep=None):
    if "$" in marc_val:
        marc_val = marc_val.split("$")
        marc_val = [el[1:].strip() for el in marc_val if el[1:].strip()]
        if sep is not None:
            marc_val = sep.join(marc_val)    
        else:
            marc_val = " ".join(marc_val)
    marc_val = marc_val.replace("¤", " ")
    return marc_val


def analyse_file(filename, reports):
    """ filename : nom du fichier en entrée
     reports : {"train_rameau": file_trainingNOIDRameau,
                "train_dewey": file_trainingNOIDDewey,
                "train_archive": file_trainingID,
                "test_rameau": file_testNOIDRameau,
                "test_dewey": file_testNOIDDewey,
                "test_archive": file_testID,
                "corpus": file_corpusID}) """
    errors_file = input2outputfile(filename, "erreurs")
    i = 0
    initialize_ref(rameau_dict, reports["referentielRameau"])
    initialize_ref(dewey_dict, reports["referentielDewey"])
    compteur = defaultdict(int)
    with open(filename, encoding="utf-8") as file:
        # content = csv.reader(file, delimiter="\t", doublequote=False)
        header = next(file)
        cols_metas, cols_rameau, cols_dewey = analyse_header(header)
        i = 0
        for row in file:
            row = row.replace("\r", "").replace("\n", "").split("\t")
            try:
                analyse_row(row, i, cols_metas, cols_rameau,
                            cols_dewey, reports, compteur)
                compteur["Nombre de notices"] += 1
                i += 1
                if i == 5:
                    i = 0
            except IndexError:
                print("\n\nErreur de structuration d'une ligne\n")
                line2report(row, errors_file)
    print("\n"*4, "-"*30, "\n"*2)
    for el in compteur:
        print(el, compteur[el])

def initialize_ref(referentiel, file):
    for entry in referentiel:
        line2report([f"<{nna2uri(entry)}>", referentiel[entry]], 
                    file, display=False)


def nna2uri(nna):
    if (nna[0] == " "):
        raise
    return f"http://data.bnf.fr/{nna}"


def isInt(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


def analyse_header(header):
    header = header.replace("\n", "").replace("\r", "").split("\t")
    # Analyse les noms des colonnes pour 
    # identifier les numéros de colonnes pour cettes contenant
    # des métadonnées et celles contenant des numéros de notice sujet
    cols_metas = []
    cols_rameau = []
    cols_dewey = []
    i = 0
    for col in header:
        if isInt(col[0:3]):
            if col.startswith("676"):
                cols_dewey.append(i)
            elif col.startswith("6"):
                cols_rameau.append(i)
            else:
                cols_metas.append(i)
        i += 1
    return cols_metas, cols_rameau, cols_dewey


def analyse_row(row, i, cols_metas, cols_rameau, cols_dewey, reports, compteur):
    # Tous les 5 notices indexées, on en passe 1 dans le jeu de test (donc 20%)
    # 
    train_or_test = "Pour entraînement"
    if i == 0:
        outputRameau = reports["test_rameau"]
        outputDewey = reports["test_dewey"]
        outputArchive = reports["test_archive"]
        train_or_test = "Pour tests"
    else:
        outputRameau = reports["train_rameau"]
        outputDewey = reports["train_dewey"]
        outputArchive = reports["train_archive"]
    record = Record(row, cols_metas, cols_rameau, cols_dewey)
    if record.rameau or record.dewey:
        line2report([record.id, record.metas,
                     record.rameau_ids,
                     record.rameau_libelles,
                     record.dewey_ids,
                     record.dewey_libelles], outputArchive)
        compteur["Rameau ou Dewey"] += 1
        compteur[train_or_test] += 1
        if record.rameau:
            line2report([record.metas,
                         " ".join([f"<{nna2uri(el)}>" for el in record.rameau])],
                        outputRameau)
            compteur["Rameau"] += 1
            for ram in record.rameau:
                if ram not in rameau_dict:
                    rameau_dict[ram] = record.rameau[ram]
                    line2report([f"<{nna2uri(ram)}>",
                                 record.rameau[ram]],
                                reports["referentielRameau"])
        if record.dewey:
            line2report([record.metas, " ".join([f"<{nna2uri(el)}>" for el in record.dewey])], outputDewey)
            compteur["Dewey"] += 1
            for nna in record.dewey:
                if nna not in dewey_dict:
                    dewey_dict[nna] = record.dewey[nna]
                    line2report([f"<{nna2uri(nna)}>", record.dewey[nna]], reports["referentielDewey"])
    else:
        line2report([record.id, record.metas], reports["corpus"])
        compteur["A indexer"] += 1


def file_ref2dict(filename):
    temp_dict = {}
    liste = file2list(filename, True)
    for el in liste:
        nna = ark2nn(el[0])
        label = el[1]
        temp_dict[nna] = label
    return temp_dict


if __name__ == "__main__":
    print(explain)
    filename = input("Nom du fichier en entrée : ")
    try:
        rameau_dict = file_ref2dict("D:/BNF0017855/Documents/Catalogue_ADCAT/Chantiers_corrections/annif/vocabularies/rameau20191119.tsv")
    except FileNotFoundError:
        rameau_dict = file_ref2dict("C:/Users/Lully/Documents/testsPython/annif/vocabularies/rameau20191119.tsv")
        
    try:
        dewey_dict = file_ref2dict("D:/BNF0017855/Documents/Catalogue_ADCAT/Chantiers_corrections/annif/vocabularies/dewey202001.tsv")
    except FileNotFoundError:
        dewey_dict = {}
    file_referentielRameau = input2outputfile(filename, "referentielRameau.tsv")
    file_referentielDewey = input2outputfile(filename, "referentielDewey.tsv")
    file_trainingNOIDRameau = input2outputfile(filename, "metas-entrainementRameau-sansID.tsv")
    file_trainingNOIDDewey = input2outputfile(filename, "metas-entrainementDewey-sansID.tsv")
    file_trainingID = input2outputfile(filename, "metas-entrainement-avecID.tsv")
    file_testNOIDRameau = input2outputfile(filename, "metas-testRameau-sansID.tsv")
    file_testNOIDDewey = input2outputfile(filename, "metas-testDewey-sansID.tsv")
    file_testID = input2outputfile(filename, "metas-test-avecID.tsv")
    file_corpusID = input2outputfile(filename, "metas-a_indexer.tsv")
    analyse_file(filename, {"train_rameau": file_trainingNOIDRameau,
                            "train_dewey": file_trainingNOIDDewey,
                            "train_archive": file_trainingID,
                            "test_rameau": file_testNOIDRameau,
                            "test_dewey": file_testNOIDDewey,
                            "test_archive": file_testID,
                            "referentielRameau": file_referentielRameau,
                            "referentielDewey": file_referentielDewey,
                            "corpus": file_corpusID})