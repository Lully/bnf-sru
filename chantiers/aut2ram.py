# coding utf-8

from stdf import *
import csv

referentiel = file2list("nna_gf.txt")
fields = "301\t502\t302\t501\t401".split("\t")
report = create_file("AUT_liees_a_RAM_GF.txt", ["ARK", "NNA", "Zone", "Valeur"])

def filter_row(row):
    ark, nna, statut, typerec = row.pop(0), row.pop(0), row.pop(0), row.pop(0)
    i = 0
    for field in row:
        for val in field.split("¤"):
            nna_ram = val[4:11]
            if nna_ram in referentiel:
                line = [ark, nna, statut, typerec, fields[i], nna_ram, val]
                line2report(line, report)
        i += 1


with open("AUT_liees_a_1_RAM.txt", encoding="utf-8") as file:
    content = csv.reader(file, delimiter="\t")
    for row in content:
        filter_row(row)
