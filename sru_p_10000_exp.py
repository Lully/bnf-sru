# coding: utf-8

from joblib import Parallel, delayed
import datetime
import multiprocessing
from pprint import pprint

import SRUextraction as sru
from stdf import *


explain = """
Requêtes parallélisées sur un SRU
Exemple de script utilisant les fonctions de SRUextraction
"""

scores = {"parallele": {},
          "seriel": {}}

def launch_query(query, fields, params, report):
    # Exécution de la requête complète avec parallélisation
    num_parallel = 10
    nb_results = int(sru.SRU_result(query, parametres=params).nb_results)
    #startRecord_list = [str(i) for i in range(1, nb_results, 1000)]
    startRecord_list = [str(i) for i in range(1, nb_results, 1000)]
    for sublist in chunks(startRecord_list, num_parallel):
        debut = datetime.datetime.utcnow()
        #results = Parallel(n_jobs=num_parallel)(delayed(launch_one_query)(query, fields, params, report, startRecord) for startRecord in startRecord_list)
        results = Parallel(n_jobs=num_parallel)(delayed(launch_1_query)(query, fields, startRecord) for startRecord in startRecord_list)
        for query_results in results:
            for record in query_results:
                line2report(record, report)
        scores["parallele"][sublist[0]] = datetime.datetime.utcnow() - debut
    i = 1
    debut_seriel = datetime.datetime.utcnow()
    scores["seriel"][str(i)] = debut_seriel
    while i < nb_results:
        params["startRecord"] = str(i)
        results = sru.SRU_result(query, parametres=params)
        for ark in results.dict_records:
            record = sru.Record2metas(ark, results.dict_records[ark], fields)
            metas = [ark, ark2nn(ark), record.docrecordtype] + record.metas
            line2report(metas, report)
            i += 1
        scores["seriel"][str(i)] = datetime.datetime.utcnow() -debut_seriel
    pprint(scores)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst.
    Permet de découper les requêtes dans le SRU par 10.000 (donc de paralléliser 
    10 requêtes de 1000"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def launch_one_query(query, fields, params, report, startRecord):
    params["startRecord"] = startRecord
    results = sru.SRU_result(query, parametres=params)
    for ark in results.dict_records:
        record = sru.Record2metas(ark, results.dict_records[ark], fields)
        line2report(record.metas, report)
 

def launch_1_query(query, fields, startRecord):
    params = {"recordSchema": "intermarcxchange", "startRecord": startRecord, "maximumRecords": "10"}
    results = sru.SRU_result(query, parametres=params)
    list_results = []

    for ark in results.dict_records:
        record = sru.Record2metas(ark, results.dict_records[ark], fields)
        line = [ark, ark2nn(ark), record.docrecordtype] + record.metas
        list_results.append(line)
    
    return list_results



if __name__ == "__main__":
    query = input("Requête SRU : ")
    format_marc = input("Format ([intermarcxchange]/unimarcxchange) : ")
    fields = input("Zones à récupérer : ")
    if format_marc == "":
        params = {"recordSchema": "intermarcxchange"}
    else:
        params = {"recordSchema": format_marc}
    report = create_file(input("Nom du fichier rapport : "),
                         ["ARK", "NNB", "Type"] + fields.split(";"))
    launch_query(query, fields, params, report)