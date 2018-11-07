# coding: utf-8
"""
Extraction de l'indexation sujet d'un corpus de notices
pour évaluation statistique
L'objectif est de trouver des méthodes de comparaison
entre indexation automatisée et indexation manuelle
qui ne s'appuie pas sur une comparaison portant sur le même corpus
(sortir de l'évaluation par le rappel et la précision)
Pistes :
    - graphe des concepts (complexité, liens)
    - dispersion

Calculer :
- Distribution de zones par notices
- Distribution de concepts par notices
- Distribution de concepts par zone

Pour l'approche en graphe : 
- par notices identifiant randomisé sur les zones
- uniquement graphe de concepts : soit liés entre eux par des zones communes, 
soit liés par des notices communes

"""

from collections import defaultdict
from pprint import pprint
import matplotlib.pyplot as plt

from stdf import create_file, line2report, close_files
import SRUextraction as sru


def analyse(url, fields, max_records, output_filesid):
    output_files = {}
    output_files["results"] = create_file(output_filesid + "-results.txt")
    output_files["concepts_graph"] = create_file(output_filesid + "-concepts_graph.txt")
    nb_results = sru.query2nbresults(url)
    metas = defaultdict(list)
    if nb_results < max_records:
        max_records = nb_results
    i = 1
    print("Nombre total de résultats : ", nb_results)
    while i < max_records:
        metas = page_of_results(url, fields, i, max_records, metas)
        i += 100
    analyse_corpus(metas, output_files)
    EOT([output_files[key] for key in output_files])


def page_of_results(url, fields, i, max_records, metas):
    query, url_root, params = sru.url2params(url)
    params["maximumRecords"] = "100"
    if (max_records < int(params["maximumRecords"])):
        params["maximumRecords"] = str(max_records)
    params["startRecord"] = str(i)
    results = sru.SRU_result(query, url_root, params)
    for recordid in results.dict_records:
        if (i <= max_records):
            dict_metas_record = extract_metas(
                                    recordid,
                                    results.dict_records[recordid]["record"],
                                    fields)
            metas[recordid] = dict_metas_record
            print(i, recordid, str(dict_metas_record))
            i += 1
    return metas


def extract_metas(recordid, xml_record, fields):
    """
    Extraction des informations pour une notice
    Si une notice contient :
    600 .. $3 12032352 $a Stanislas $u 2 Auguste Poniatowski
           $h II Auguste Poniatowski $e roi de Pologne $d 1732-1798
    606 .. $3 11939093 $a Guerre mondiale $g 1914-1918
           $3 11934225 $x Historiographie
    607 .. $3 11957734 $a Varsovie $g Pologne
           $3 14533294 $z +* 1800......- 9900......+:1800-....:
    607 .. $3 11932826 $a Pologne $x Histoire
    607 .. $3 12033836 $a Pologne $x Relations extérieures
           $3 11934444 $x Histoire
    La liste en sortie sera :
    ['600':
        [
            ["12032352"]
        ],
     '606':
        [
            ["11939093", "11934225"]
        ],
     '607':
        [
            ["11957734", "14533294"],
            ["11932826"],
            ["12033836", "11934444"]
        ]

    """
    list_metas = {}
    for field in fields:
        field_values = extract_values(recordid, xml_record, field, list_metas)
        if field_values:
            list_metas[field] = field_values
    return list_metas


def extract_values(recordid, xml_record, fieldname, list_metas):
    """
    Doit renvoyer une liste de listes
    Par exemple
    [
            ["11957734", "14533294"],
            ["11932826"],
            ["12033836", "11934444"]
        ]
    """
    liste_values = []
    for field in xml_record.xpath(f"*[@tag='{fieldname}']"):
        field_val = []
        if field.find("*[@code='3']") is not None:
            for subf3 in field.xpath("*[@code='3']"):
                field_val.append(subf3.text)
        else:
            for subf in field.xpath("*"):
                code = subf.get("code")
                subf_list = "abcdefghijlmnopqrstuvwxyz"
                if code in subf_list:
                    field_val.append(subf.text)
        liste_values.append(field_val)
    return liste_values


def analyse_corpus(metas_dict, outputfiles):
    stats = defaultdict(int)
    stats = analyse_corpus_global(metas_dict, stats)
    print(stats)

    concepts_graph = corpus2concepts_graph(metas_dict)
    
    for pair in concepts_graph:
        outputfiles["concepts_graph"].write("\t".join(pair) + "\n")
    outputfiles["results"].write(str(metas_dict))
    graphique(stats)
    

def analyse_corpus_global(metas_dict, stats):
    stats["Nombre de notices avec au moins 1 zone"] = 0
    stats["Nombre total de notices"] = 0
    stats["Nb zones par notice"] = defaultdict(int)
    stats["Nb concepts par notice"] = defaultdict(int)
    stats["Nb concepts par zone"] = defaultdict(int)
    
    for record in metas_dict:
        nb_zones = 0
        nb_concepts = 0
        stats["Nombre total de notices"] += 1
        if metas_dict[record]:
            stats["Nombre de notices avec au moins 1 zone"] += 1
            for zone in metas_dict[record]:
                for zone_occ in metas_dict[record][zone]:
                    nb_concepts_par_zone = 0
                    nb_zones += 1
                    for concept in zone_occ:
                        nb_concepts_par_zone += 1
                        nb_concepts += 1
                    stats["Nb concepts par zone"][nb_concepts_par_zone] += 1
        stats["Nb zones par notice"][nb_zones] += 1
        stats["Nb concepts par notice"][nb_concepts] += 1
    return stats    


def corpus2concepts_graph(metas_dict):
    """
    A partir des métadonnées engrangées sous forme de dictionnaire
    on extrait des paires de concepts : on considère que deux concepts
    sont associés dès lors qu'ils sont présents dans une même notice
    """
    graphe_concepts = []
    for record in metas_dict:
        graphe_temp = set()
        if metas_dict[record]:
            for zone in metas_dict[record]:
                for zone_occ in metas_dict[record][zone]:
                    for concept in zone_occ:
                        graphe_temp.add(concept)
        i = 0
        graphe_temp = list(graphe_temp)
        if (graphe_temp):
            print(graphe_temp)
        for concept1 in graphe_temp[:-1]:
            if (i < len(graphe_temp)-1):
                for concept2 in graphe_temp[i+1:]:
                    graphe_concepts.append([concept1, concept2])
            i += 1
    return graphe_concepts


def graphique(stats):
    """
    Convertit en graphiques (histogrammes) certaines infos présentes
    dans le dictionnaire "stats"
    stats["Nb zones par notice"] = defaultdict(int)
    stats["Nb concepts par notice"] = defaultdict(int)
    stats["Nb concepts par zone"] = defaultdict(int)
    Chacun de ces 3 dictionnaires a pour valeur le nombre d'occurrences, et pour clé
    le décompte constaté
    """
    for stats_report in stats:
        if stats_report[0:2].lower() == "nb":
            hist(stats_report, stats[stats_report])


def hist(stats_report_name, stats_report):
    x = []
    y = []
    # plot = plt.plot(dict2axes(stats_report))
    hist = plt.hist(dict2axes(stats_report_name, stats_report)[1])
    plt.show()

def dict2axes(dic_title, dic):
    """
    Prend un dictionnaire de décomptes stats en entrée pour renvoyer
    un axe des abscisses (clés) et un axe des ordonnées (valeurs) 
    où les clés sont continues (pas de  numéro manquant)
    """
    x = []
    y = []
    i = 0
    maxy = 0
    maxx = max(dic)
    while i <= maxx:
        x.append(i)
        if (i in dic):
            y.extend([str(i)]*dic[i])
            if (dic[i]>maxy):
                maxy=dic[i]
        else:
            y.append(0)
        i += 1
    y = [int(el) for el in y]
    print(dic_title, x, y)
    axis = 0, max(dic), 0, maxy
    return x, y


def EOT(list_files):
    close_files(list_files)


if __name__ == "__main__":
    fields = input("List of fields to be analysed : ")
    url = input("full URL of the SRU to be searched (with query and parameters) : ")
    max_records = int(input("Max of results to be parsed : "))
    output_filesid = input("ID of output files : ")
    print("\n", "-"*20, "\n")
    fields = fields.split(";")
    if (len(fields) == 1):
        fields = fields[0].split(",")
    if url == "":
        url = "http://services.dnb.de/sru/dnb?operation=searchRetrieve&version=1.1&query=JHR%3D2017&recordSchema=MARC21-xml"
    analyse(url, fields, max_records, output_filesid)
