# coding: utf-8

import re
import datetime

from stdf import *

def rewrite_times(inputfilename, decalage, outputfile):
    file = open(inputfilename, encoding="ansi")
    for line in file:
        line = line.replace("\n", "").replace("\r", "")
        if re.fullmatch(r"[:\d]+.+ --> [:\d]+.+", line) is not None:
            rewrite_line(line, decalage, outputfile)
        else:
            outputfile.write(line + "\n")

def rewrite_line(line, decalage, outputfile):
    time1_init = line[0:8]
    time1 = convert_time(time1_init, decalage)
    time2_init = line[17:25]
    time2 = convert_time(time2_init, decalage)
    line = line.replace(time1_init, time1).replace(time2_init, time2)
    outputfile.write(line + "\n")


def convert_time(time_init, decalage):
    new_time = time_init.split(":")
    new_time = datetime.time(int(new_time[0]), int(new_time[1]), int(new_time[2]))    
    new_time = datetime.datetime.combine(datetime.date.today(), 
                                         new_time) + datetime.timedelta(seconds=decalage)
    new_time = str(new_time.time())
    return new_time


if __name__ == "__main__":
    inputfilename = input("Nom du fichier de sous-titres : ")
    decalage = int(input("Decalage (secondes) : "))
    outputfile = input2outputfile(inputfilename, "corrige.sub")
    rewrite_times(inputfilename, decalage, outputfile)