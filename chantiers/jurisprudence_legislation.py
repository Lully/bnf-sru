# coding: utf-8

"""
Extraction Jurisprudence et Législation pour DPI 6 GF


Législation (13319331)
	* Si 008 pos.8-11 supérieur ou égal à 2009
      et si $y dans la chaîne d'indexation avant $x Législation --> GF
	* Ou si 008 pos. 8-11 < 2009
      et 245 contient "recueil" ou "texte" et ne contient pas commenta* --> GF

Jurisprudence (12029993)
	* si contient "recueil" ou "texte" et ne contient pas comment* --> GF

"""

from stdf import *
import SRUextraction as sru

param_default = {"recordSchema": "intermarcxchange"}
fields = ["600", "601", "602", "603", "604", "605",
          "606", "607", "608", "609", "610"]



def extract_bib(report, reject):
    extract_jurisprudence(report, reject)
    extract_legislation(report, reject)


def extract_jurisprudence(report, reject):
    query = "bib.subject2bib any 12029993 and bib.title any \"recueil* texte*\" not bib.title any \"comment*\""
    results = sru.SRU_result(query, parametres=param_default)
    for ark in results.dict_records:
        analyse_bib_juris(ark, results.dict_records[ark], report, reject)
    i = 1001
    while i < results.nb_results:
        param_default["startRecord"] = str(i)
        next_results = sru.SRU_result(query, parametres=param_default)
        for ark in next_results.dict_records:   
            analyse_bib_juris(ark, next_results.dict_records[ark], 
                              report, reject)



def extract_legislation(report, reject):
    query = "bib.subject2bib any 13319331"
    results = sru.SRU_result(query, parametres=param_default)
    for ark in results.dict_records:
        analyse_bib_legis(ark, results.dict_records[ark], report, reject)
    i = 1001
    while i < results.nb_results:
        param_default["startRecord"] = str(i)
        next_results = sru.SRU_result(query, parametres=param_default)
        for ark in next_results.dict_records:   
            analyse_bib_legis(ark, next_results.dict_records[ark], 
                              report, reject)


def analyse_bib_legis(ark, xml_record, report, reject):
    f245 = sru.record2fieldvalue(xml_record, "245$a$e$i$r$f$g")
    f245d = sru.record2fieldvalue(xml_record, "245$d")
    test = True
    f008_date = ""
    message = ""
    try:
        f008_date = sru.record2fieldvalue(xml_record, "008")[8:12]
    except IndexError:
        test = False
        message += "Pas de zone 008 pos.8-11"
    if test:
        try:
            f008_date = int(f008_date)
        except ValueError:
            test = False
            message += "pos.8-12 n'est pas une date"

    if test :
        if (f008_date > 2008):
            for field in fields:
                for field_occ in xml_record.xpath(f"*[@tag='{field}']"):
                    val = sru.field2value(field_occ)
                    if ("13319331 $x" in val):
                        split = val.split("13319331 $x")
                        if ("$y" in split[0] and "$x" not in split[1]
                            and "$7 DPIGenreForme" not in split[1]):
                            line = [ark, ark2nn(ark), f245d, "legislation", f245, str(f008_date), 
                                    field, val, split[0][:-4], "$3 13319331 $a Législation",
                                    "après 2009", message]
                            line2report(line, report)
                        elif ("$7 DPIGenreForme" not in split[1]):
                            line = [ark, ark2nn(ark), f245d, "legislation", 
                                    f245, str(f008_date), f"{message} Après 2009. Pas de $y | autre subdiv $x : {field} {val}"]
                            line2report(line, reject)
        elif(("texte" in f245.lower() or "recueil" in f245.lower())
             and "comment" not in f245.lower()):
            for field in fields:
                for field_occ in xml_record.xpath(f"*[@tag='{field}']"):
                    val = sru.field2value(field_occ)
                        if ("13319331 $x" in val):
                            split = val.split("13319331 $x")
                            if ("$x" not in split[1]
                                and "$7 DPIGenreForme" not in split[1]):
                                line = [ark, ark2nn(ark), f245d, "legislation", f245, str(f008_date), 
                                        field, val, split[0][:-4], "$3 13319331 $a Législation",
                                        "avant 2009", message]
                                line2report(line, report)
                            elif ("$7 DPIGenreForme" not in split[1]):
                                line = [ark, ark2nn(ark), f245d, "legislation", 
                                        f245, str(f008_date), f"{message} Avant 2009. Autre subdiv $x : {field} {val}"]
                                line2report(line, reject)
        else:
        # Avant 2009, pas de 245 telle que souhaitée
            line = [ark, ark2nn(ark), f245d, "legislation", 
                f245, str(f008_date), "Avant 2009. 245 non conforme aux filtres"]
            line2report(line, reject)
    else:
        line = [ark, ark2nn(ark), f245d, "legislation", 
                f245, str(f008_date), message]
        line2report(line, reject)


        

def analyse_bib_juris(ark, xml_record, report, reject):
    f245 = sru.record2fieldvalue(xml_record, "245$a$e$i$r$f$g")
    f245d = sru.record2fieldvalue(xml_record, "245$d")
    test = False
    message = ""
    if ("texte" in f245.lower() or "recueil" in f245.lower()):
        test = True
    if test :
        for field in fields:
            for field_occ in xml_record.xpath(f"*[@tag='{field}']"):
                val = sru.field2value(field_occ)
                if ("12029993 $x" in val):
                    split = val.split("12029993 $x")
                    if ("$x" not in split[1]
                        and "$7 DPIGenreForme" not in split[1]):
                        line = [ark, ark2nn(ark), f245d, "jurisprudence", f245, "", 
                                field, val, split[0][:-4], "$3 12029993 $a Jurisprudence"]
                        line2report(line, report)
                    elif ("$x" in split[1]
                          and "$7 DPIGenreForme" not in split[1]):
                        line = [ark, ark2nn(ark), f245d, "jurisprudence",
                                f245, "", f"Autre subdiv $x : {field} {val}"]
                        line2report(line, reject)
    else:
        line = [ark, ark2nn(ark), f245d, "jurisprudence", f245, "", 
                "Texte/Recueil absent de la 245"]
        line2report(line, reject)



if __name__ == "__main__":
    report = create_file("NNB_jurisprudence_extraction.txt",
                         ["ARK", "NNB", "245$d", "cas", "245", "008 pos.08-11", "zone",
                          "contenu actuel", "contenu cible", "nouvelle 608"])
    reject = create_file("NNB_jurisprudence_extraction_nontraites.txt",
                         ["ARK", "NNB", "245$d", "cas", "245", "008 pos.08-11", "zone",
                          "contenu actuel"])
    extract_bib(report, reject)
