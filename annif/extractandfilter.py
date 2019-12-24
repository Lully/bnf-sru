# coding: utf-8

"""
Filtrage sur un corpus, selon la richesse des métadonnées
"""

import re

from stdf import *
import SRUextraction as sru
from cleanstring import clean_string, clean_dollars
from udecode import udecode

stopwords = ["Notes bibliogr.", "resume",
             "bibliographie", "bibliogr.", "webographie", "webliogr.", "annexes", "tome", "volume",
             "preface", "pref.", "la couv. porte en plus", "la couverture", "sur la couverture", "couv.",
             "index", "glossaire", "presentation", "postface", "post-face", "introduction",
             "avec", "references", "ill.", "glossaire", "en 2e de couv."]
stop_regex = [" p\. \d+-\d+", " p\. \d+", " \d+ p\."]
skip_resp = [", par ", ", trad"]
skipwords = [", avec une "]

def extract_corpus(corpus_init, type_corpus, report, rejected_file):
    if type_corpus == "sru":
        sru2corpus(corpus_init, report, rejected_file)
    else:
        file2corpus(corpus_init, report, rejected_file)

def sru2corpus(sru_query, report):
    param_default = {"recordSchema": "intermarcxchange"}
    results = sru.SRU_result(sru_query, parametres=param_default)
    for ark in results.dict_records:
        analyse_record(ark, results.dict_records[ark], report, rejected_file)
    i = 1001
    while i < results.nb_results:
        param_default["startRecord"] = str(i)
        next_results = sru.SRU_result(sru_query, parametres=param_default)
        for ark in next_results.dict_records:
            analyse_record(ark, next_results.dict_records[ark], report, rejected_file)


def file2corpus(corpus_init, report, rejected_file):
    liste_ark = file2list(corpus_init)
    param_default = {"recordSchema": "intermarcxchange"}
    for ark in liste_ark:
        record = None
        try:
            record = sru.SRU_result(f"bib.persistentid any \"{ark}\"", 
                                    parametres=param_default).firstRecord
        except AttributeError:
            pass
        if record is not None:
            analyse_record(ark, record, report, rejected_file)        

def analyse_record(ark, xml_record, report, rejected_file):
    title_fields = ["245$a$e$i$b$c$r", "142$a$e", "247$a$e$i$b$c", "750$a", "751$a", "749$a", "748$a"]
    content_fields = ["300$a", "327$a", "331$a", "829$a", "830$a", "833$a"]
    index_fields = ["600", "601", "602", "603", "605", "606", "607", "608", "610"]
    language = sru.record2fieldvalue(xml_record, "008")[31:34]
    indexation = " ".join([sru.record2fieldvalue(xml_record, el) for el in index_fields])
    if language == "fre" and inexation == "":
        titles = [clean_title_field(sru.record2fieldvalue(xml_record, field)) for el in title_fields]
        contents = [clean_content_field(sru.record2fieldvalue(xml_record, field)) for el in content_fields if el]
        titles = " ".join([el for el in titles if el])
        contents = " ".join([el for el in contents if el])
        if (len(titles) > 40
           or len(contents) > 40):
            line2report([ark, title_fields, content_fields], report)
        else:
            line2report([ark, title_fields, content_fields], rejected_file)

def clean_title_field(field):
    field = udecode(clean_dollars(field)).lower()
    for el in skipwords:
        if el in field:
            field = field[:field.find(el)]
    for el in skipwords:
        if el in field:
            field = field[:field.find(el)]
    field = clean_stopwords(field)
    field = " ".join([el for el in field.split(" ") if el])
    return field


def clean_content_field(field):
    field = udecode(field).lower()
    field = clean_dollars(field)
    field = clean_stopwords(field)
    return field


def clean_stopwords(field):
    for el in stopwords:
        el += " "
        if field.startswith(el):
            field = field[len(el):]
        el = " " + el
        field = field.replace(el, " ")
        el = el[:-1]
        if field.endswith(el):
            field = field[:-len(el)]
    for regex in stop_regex:
        field = re.sub(regex, " ", field)
    field = " ".join([el for el in field.split(" ") if el])
    return field

if __name__ == "__main__":
    corpus_init = input("Requête SRU ou fichier d'ARK : ")
    type_corpus = "file"
    if corpus_init.startswith("bib."):
        type_corpus = "sru"
    outputfilename = input("fichier en sortie (défaut : 'extract2annif.tsv') : ")
    if outputfilename == "":
        outputfilename = "extract2annif.tsv"
    elif len(outputfilename) < 5:
        outputfilename += ".tsv"
    elif (len(outputfilename) >=5 and outputfilename[-4] != "."):
        outputfilename += ".tsv"
    report = create_file(outputfilename)
    rejected_file = create_file(f"{outputfilename[-4]}-rejected.csv")
    extract_corpus(corpus_init, type_corpus, report, rejected_file)