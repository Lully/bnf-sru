# coding: utf-8

explain = "Stats sur les squelettes des ANL + pb des squelettes trop 'courts'"

from csv import reader
from collections import defaultdict
from stdf import *


def analyse_file(fname):
    report = input2outputfile(fname, "-stats.txt")
    pb_file = input2outputfile(fname, "-pb.txt")
    stats = defaultdict(int)
    with open(fname, encoding="utf-8") as file:
        content = reader(file, delimiter=="\t")
        next(content)
        for row in content:
            fields = sorted(list(set(row[-1].split("|")))) # liste dédoublonnée des zones
            if len(fields) < 2 or "".join(fields) == "":
                line2report(row, pb_file)
            fields = "|".join(fields)
            stats[fields] += 1
    for squelette in stats:
        line2report([squelette, stats[squelette]], report, display=False)


if __name__ == "__main__":
    fname = input("Nom du fichier en entrée (liste d'ANL) : ")
    analyse_file(fname)