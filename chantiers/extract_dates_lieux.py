# coding: utf-8

import SRUextraction as sru

from stdf import *

def extract_metas_from_file(filename, report):
    liste_ids = file2list(filename)
    for id_ in liste_ids:
        metas = extract_metas(id_)
        line = [id_]
        line.extend(metas)
        line2report(line, report)

def isni2record(isni):
    if ("/" in isni):
        isni = isni.split("/")[-1]
    url = f"http://isni.oclc.nl/sru/?query=pica.isn+%3D+%22{isni}%22&operation=searchRetrieve&recordSchema=isni-b"
    record = None
    return record


def extract_metas(id_):
    metas_isni = ["",""]
    metas_bnf = ["","","",""]
    """if "isni" in id_:
        xml_record = Record
        date_naissance = sru.record2fieldvalue(xml_record, "970$a")
        date_mort = sru.record2fieldvalue(xml_record, "970$b")
        if "¤" in date_naissance:
            date_naissance = date_naissance.split("¤")[0]
        if "¤" in date_mort:
            date_mort = date_mort.split("¤")[0]
        metas_isni.extend([date_naissance, date_mort])
    """
    if ("bnf" in id_):
        ark = id_
        ark = ark[ark.find("ark:"):]
        xml_record = sru.SRU_result(f"aut.persistentid any \"{ark}\" and aut.status any \"sparse validated\"", parametres={"recordSchema": "intermarcxchange"}).firstRecord
        f008 = sru.record2fieldvalue(xml_record, "008")
        date_naissance = ""
        date_mort = ""
        lieu_naissance = sru.record2fieldvalue(xml_record, "603$a")
        lieu_mort = sru.record2fieldvalue(xml_record, "603$b")
        if len(f008) > 45:
            date_naissance = f008[28:36]
            date_mort = f008[38:46]
        metas_bnf = [date_naissance, lieu_naissance, date_mort, lieu_mort]

    metas = metas_isni + metas_bnf
    return metas


if __name__ == "__main__":
    filename = "id_wp_test.txt"
    report = input2outputfile(filename, "metas")
    line2report("ID,Date naissance ISNI,Date mort ISNI,Date naissance BnF,Lieu naissance BnF,Date mort BnF,Lieu mort BnF".split(","), report)
    extract_metas_from_file(filename, report)
