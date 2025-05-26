from pymarc import MARCReader
from collections import defaultdict
from string import ascii_letters

fields = [i for i in range(1000)]
fields = [str(i).zfill(3) for i in fields]
subfields = ascii_letters + "0123456789"

def file2stats(filename):
    stats_zones = defaultdict(int)
    i = 0
    with open(filename, "rb") as collection:
        reader = MARCReader(collection, force_utf8=True)
        for record in reader:
            i += 1
            if i%1000 == 0:
                break
            for f in fields:
                for f_occ in record.get_fields(f):
                    stats_zones[f] += 1
                    if not(f.startswith("00")):
                        for subf in subfields:
                            for subf_occ in f_occ.get_subfields(subf):
                                stats_zones[f"{f}${subf}"] += 1
    return stats_zones

if __name__ == "__main__":
    filename = input("Nom du fichier à analyser (statistiques des zones) [fichier iso2709] : ")
    stats = file2stats(filename)
    print(stats)