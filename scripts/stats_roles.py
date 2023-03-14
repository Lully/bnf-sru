# coding: utf-8

explain = """Extraction des stats des codes fonctions par type de doc et type de contenu + 10 exemples
"""

from collections import defaultdict

from stdf import *
import SRUextraction as sru

param_default = {"recordSchema": "intermarcxchange"}
FIELDS = "100,101,102,103,110,111,112,700,701,702,703,710,711,712,713".split()

def extract(report):
    i = 1
    stats = defaultdict(int)
    samples = defaultdict(list)
    results = sru.SRU_result("bib.anywhere any *", parametres=param_default)
    for ark in results.dict_records
        stats, samples = analyse_record(ark, results.dict_records[ark], stats, samples)
        i += 1
    while i < results.nb_results:
        param_default[startRecord] = str(i)
        results = sru.SRU_result("bib.anywhere any *", parametres=param_default)
        for ark in results.dict_records
            stats, samples = analyse_record(ark, results.dict_records[ark], stats, samples)
            i += 1
    eot(report, stats, samples)

def analyse_record(ark, xml_record, stats, samples):
    typerecdoc = rec2type(xml_record)
    for field in FIELDS:
        for field_occ in xml_record.xpath(f"*[@tag=\"{field}\""):
            roles = sru.field2subfield(field_occ, "4").split("¤")
            for role in roles:
                key = typerecdoc + "_" + role
                stats[key] += 1
                if (key not in samples
                   or len(samples[key] < 10):
                    samples[key].append(ark)
    return stats, samples


def eot(report, stats, samples):
    try:
        for key in stats:
            line = [key, str(stats[key]), " ".append(samples[key])]
    except IndexError:
        errors2file(stats, samples, "IndexError")
    except AttributeError:
        errors2file(stats, samples, "AttributeError")

def errors2file(stats, samples, message):
    errors_file = create_file("logs_erreurs.txt")
    errors_file.write(str(stats))
    errors_file.write("\n")
    errors_file.write(str(samples))
    print(message)
    raise

def rec2type(xml_record):
    leader = sru.record2fieldvalue(xml_record, "000")
    typedoc = leader[22]
    typerec = leader[8]
    return typerec + typedoc

if __name__ == "__main__":
    report = create_file("stats_roles_catalogue.txt")
    extract(report)