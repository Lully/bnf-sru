# coding: utf-8

"""
Script pour extraire des métadonnées à partir d'une interrogation massive
du catalogue BnF (parser tous les imprimés, ou toutes les PEP, par exemple)
"""

import SRUextraction as sru


param_default = {"recordSchema": "intermarcxchange",
                 "maximumRecords": "1000"}


def query2nbresults(query):
    param = param_default
    param["maximumRecords"] = "1"
    result = sru.SRU_result(query, parametres=param)
    nb_results = result.nb_results
    try:
        nb_results = int(nb_results)
    except ValueError:
        nb_results = 0
    return nb_results


def create_file(filename, type="w"):
    file = open(filename, type, encoding="utf-8")
    return file


def query2results(query, zones, not_null, output_file):
    nb_results = query2nbresults(query)
    i = 1
    while (i < nb_results+1):
        query2pageresults(query, zones, not_null, output_file, i)
        i += 1000


def query2pageresults(query, zones, not_null, output_file, i):
    param = param_default
    param["startRecord"] = str(i)
    param["maximumRecords"] = "1000"
    results = sru.SRU_result(query, parametres=param)
    print(results.url)
    for ark in results.dict_records:
        extract_metas(ark, results.dict_records[ark]["record"],
                      zones, not_null, i, output_file)
        i += 1

def extract_docrecordtype(xml_record, ark):
    leader, recordtype, doctype, entity_type = ["", "", "", ""]
    for element in xml_record:
        if ("leader" in element.tag):
            leader = element.text
    if (int(ark[-9:-8]) >= 3):
        #Intermarc BIB
        recordtype, doctype = leader[8], leader[22]
        entity_type = "B"
    else:
        recordtype = leader[8]
        entity_type = "A"
    return recordtype, doctype, entity_type


def extract_metas(ark, xml_record, zones, not_null, i, output_file):
    metas = []
    for zone in zones.split(";"):
        value = sru.extract_bnf_meta_marc(xml_record, zone)
        metas.append(value)
    doctype, recordtype, entity_type = extract_docrecordtype(xml_record, ark)
    init_metas = [ark, ark[13:21], entity_type, doctype, recordtype]
    if (not_null[0] == "o"):
        check_metas = "".join([el for el in metas if el])
        if check_metas:
            line = init_metas
            line.extend(metas)
            line2report(line, output_file, i)
    else:
        line = init_metas
        line.extend(metas)
        line2report(line, output_file, i)


def line2report(line, file, i):
    print(i, line)
    file.write("\t".join(line) + "\n")


def EOT(files_list):
    for file in files_list:
        file.close()


if __name__ == "__main__":
    query = input("requête SRU : ")
    output_filename = input("Nom du fichier en sortie : ")
    zones = input("Zones à extraire : ")
    not_null = input("Filtrer si valeur vide (oui/non) ? ").lower()
    output_file = create_file(output_filename)

    query2results(query, zones, not_null, output_file)

    EOT([output_file])
