# coding: utf-8

"""
Extraction de notices Rameau (Unimarc, Intermarc, libellé) préconstruites
avec une subdivision de lieu
Utile pour fournir des exemples dans le cadre de la réforme Rameau > retournement
au lieu
"""
from stdf import create_file, line2report, uri2label
import SRUextraction as sru


def query2reports(query, report_lieu_sujet, report_sujet_lieu):
    first_page = sru.SRU_result(query, parametres={"recordSchema": "intermarcxchange"})
    # print(first_page.url)
    for ark in first_page.dict_records:
        test_record(ark, first_page.dict_records[ark],
                    report_lieu_sujet, report_sujet_lieu)
    i = 1001
"""    while i < first_page.nb_results:
        next_page = sru.SRU_result(query, parametres={"recordSchema": "intermarcxchange",
                                                       "startRecord": str(i)})
        for ark in next_page.dict_records:
            test_record(ark, next_page.dict_records[ark],
                        report_lieu_sujet, report_sujet_lieu)
            i += 1
"""

def test_record(ark, xml_record, report_lieu_sujet, report_sujet_lieu):
    test166 = sru.record2fieldvalue(xml_record, "166$y")
    test167 = sru.record2fieldvalue(xml_record, "167$x")
    print(ark, test166, test167)
    if (test166):
        # print(ark, "166 avec subdivision lieu")
        line = [ark]
        line.extend(extract_labels(ark, xml_record, "166"))
        line2report(line, report_sujet_lieu)
    elif(test167):
        # print(ark, "167 avec subdivision sujet")
        line = [ark]
        line.extend(extract_labels(ark, xml_record, "167"))
        line2report(line, report_lieu_sujet)

def extract_labels(ark, xml_record, tag):
    intermarc2unimarc = {"166": "250", "167": "215"}
    intermarc_label = sru.record2fieldvalue(xml_record, tag)
    unimarc_record = sru.SRU_result(f'aut.persistentid any "{ark}"').dict_records[ark]
    unimarc_label = sru.record2fieldvalue(unimarc_record, intermarc2unimarc[tag])
    uri = "http://data.bnf.fr/" + ark
    label = uri2label(uri)
    return [intermarc_label, unimarc_label, label]


if __name__ == "__main__":
    query = "aut.type any RAM"
    report_lieu_sujet = create_file("Notices_Lieu_Sujet_a_retourner.txt")
    report_sujet_lieu = create_file("Notices_Sujet_Lieu_a_conserver.txt")
    query2reports(query, report_lieu_sujet, report_sujet_lieu)