# coding: utf-8

from joblib import Parallel, delayed
import datetime
import multiprocessing

import SRUextraction as sru
from stdf import *

explain = """
Requêtes parallélisées sur un SRU
Exemple de script utilisant les fonctions de SRUextraction

"""


def launch_query(query, fields, params, report):
    # Exécution de la requête complète avec parallélisation
    num_parallel = 2
    nb_results = int(sru.SRU_result(query, parametres=params).nb_results)
    #startRecord_list = [str(i) for i in range(1, nb_results, 1000)]
    startRecord_list = [str(i) for i in range(1, 3500, 1000)]
    #results = Parallel(n_jobs=num_parallel)(delayed(launch_one_query)(query, fields, params, report, startRecord) for startRecord in startRecord_list)
    results = Parallel(n_jobs=num_parallel)(delayed(launch_1_query)(query, fields, startRecord) for startRecord in startRecord_list)
    print(type(results))
    print("results", results)    

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
    params = input("Paramètres de la requête : ")
    fields = input("Zones à récupérer : ")
    if params == "":
        params = {"recordSchema": "intermarcxchange"}
    else:
        params = eval(params)
    report = create_file(input("Nom du fichier rapport : "),
                         ["ARK", "NNB", "Type"] + fields.split(";"))
    report.close()
    launch_query(query, fields, params, report)