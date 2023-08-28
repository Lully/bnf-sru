# coding: utf-8

from lxml import etree
from stdf import *
import SRUextraction as sru

explain = "A partir d'un lot de NNB, génération d'une liste d'ISBD"


def extract_isbd_list(liste_nnb):
    dict_results = {}
    for nnb in liste_nnb:
        url = f"http://noticesservices.bnf.fr/SRU?version=1.2&operation=searchRetrieve&query=NN%20any%20%22{nnb}%22&recordSchema=ISBD"
        test, result = testURLetreeParse(url)
        if test:
            notice = result.find("//m:notice_isbd", namespaces=sru.ns_bnf)
            if notice is not None:
                pave_isbd = xml2isbd(notice)
                dict_results[nnb] = pave_isbd
    return dict_results

def xml2isbd(notice):
    full_isbd = []
    rejected_tags = "isbd_ved_resp_int,isbd_matiere,isbd_CDD,isbd_NumDL,isbd_NumNotBib,isbd_NumPubBgf,isbd_ark,isbd_015".split(",")
    rejected_tags = ["{http://catalogue.bnf.fr/namespaces/InterXMarc}"+el for el in rejected_tags]
    for node in notice.xpath("*"):
        if node.tag not in rejected_tags:
            subnodes = list(node.itertext())
            full_isbd.append("".join(subnodes))
    return "\n".join(full_isbd)


if __name__ == "__main__":
    filename = input("Nom du fichier contenant les numéros de notices : ")
    liste_nnb = file2list(filename)
    report_name = input("Nom du fichier rapport : ")
    report = create_file(report_name)
    dict_results = extract_isbd_list(liste_nnb)
    for nnb in dict_results:
        line2report([nnb], report)
        line2report([dict_results[nnb]], report)
        line2report([""], report)