# coding: utf-8

from lxml import etree
import SRUextraction as sru

explain = """Conversion d'un fichier XML de notices BIB ou AUT en fichier séquentiel (à plat)"""


def convertXml2Txt(filename, report_name):
    xml_collection = etree.parse(filename)
    xml_records = xml_collection.xpath("./*[local-name()='record']")
    with open(report_name, "w", encoding="utf-8") as file:
        for xml_record in xml_records:
            txt_record = sru.xml2seq(xml_record)
            file.write(txt_record)
            file.write("\r\n")



if __name__ == "__main__":
    print(explain, "\n")
    filename = input("Nom du fichier XML en entrée : ")
    report_name = input("Nom du fichier TXT en sortie : ")
    if report_name[-4] != ".":
        report_name += ".txt"
    convertXml2Txt(filename, report_name)
