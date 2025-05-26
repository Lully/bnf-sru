# coding: utf-8

explain = "Fourniture de notices ISBD à partir d'une liste d'ARKs"

import SRUextraction as sru
from lxml import etree

ns = {"m": "http://catalogue.bnf.fr/namespaces/InterXMarc"}

def convert_xml2isbd(xml_isbn_record, sep="\n", metas="all"):
    text_record = []
    if metas == "all":
        for node in xml_isbn_record.xpath("m:notice_isbd/*", namespaces=ns):
            node_text = []
            for subnode in node.xpath(".//*"):
                if subnode.text is not None:
                    node_text.append(subnode.text)
            node_text = "".join(node_text)
            text_record.append(node_text)
    else:
        nodes = [f"m:isbd_{el}" for el in metas.split(",")]
        for n in nodes:
            for node in xml_isbn_record.xpath(f"m:notice_isbd/{n}", namespaces=ns):
                node_text = []
                for subnode in node.xpath(".//*"):
                    if subnode.text is not None:
                        node_text.append(subnode.text)
                node_text = "".join(node_text)
                text_record.append(node_text)
    text_record = [el for el in text_record if el.strip()]
    if sep is not None:
        text_record = sep.join(text_record)
    return text_record



def list_ark2isbd(list_arks, metas="all"):
    dict_arks2isbd = {}
    for ark in list_arks:
        result = sru.SRU_result(f"idPerenne any \"{ark}\"", "http://noticesservices.bnf.fr/SRU", {"recordSchema": "ISBD"})
        if result.firstRecord is not None:
            text_isbn = convert_xml2isbd(result.firstRecord, metas=metas)
            dict_arks2isbd[ark] = text_isbn
    return dict_arks2isbd


if __name__ == "__main__":
    list_arks = input("Liste des ARKs à extraire sous forme de notices ISBD (sep : espace ou virgule): ")
    if " " in list_arks:
        list_arks = list_arks.split(" ")
    else:
        list_arks = list_arks.split(",")
    records = list_ark2isbd(list_arks)
    print(records)