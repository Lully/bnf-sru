# coding: utf-8

import re
from stdf import *

def rewrite(inputfilename, report):
    with open(inputfilename, encoding="utf-8") as file:
        for row in file:
            line = re.sub("([^\t\r\n])\t([^\t\r\n])", r"\1\2", row)
            line = re.sub("([^\t\r\n])\t([^\t\r\n])", r"\1\2", line)
            report.write(line)


if __name__ == "__main__":
    inputfilename = input("Fichier en entrée : ")
    report = input2outputfile(inputfilename, "corr")
    rewrite(inputfilename, report)