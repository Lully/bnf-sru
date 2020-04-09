# coding: utf-8

from joblib import Parallel, delayed
import datetime
import multiprocessing as m

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
    queue = JoinableQueue()
    process = Process(target=save2file, args=(queue, report.name,))
    processp.start()
    queue  = Parallel(n_jobs=num_parallel)(delayed(launch_1_query)(query, fields, startRecord, queue) for startRecord in startRecord_list)
    queue.put(None) # Poison pill
    process.join()   

def launch_one_query(query, fields, params, report, startRecord):
    params["startRecord"] = startRecord
    results = sru.SRU_result(query, parametres=params)
    for ark in results.dict_records:
        record = sru.Record2metas(ark, results.dict_records[ark], fields)
        line2report(record.metas, report)
 

def launch_1_query(query, fields, startRecord, queue):
    params = {"recordSchema": "intermarcxchange", "startRecord": startRecord, "maximumRecords": "10"}
    results = sru.SRU_result(query, parametres=params)
    list_results = []

    for ark in results.dict_records:
        record = sru.Record2metas(ark, results.dict_records[ark], fields)
        line = [ark, ark2nn(ark), record.docrecordtype] + record.metas
        list_results.append(line)
    queue.put(list_results)
    return queue


def save2file(q, outputfilename):
    with open(outputfilename, 'w') as out:
        while True:
            val = q.get()
            if val is None: break
            line2report(val, out)
        q.task_done()
        # Finish up
        q.task_done()


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