# coding: utf-8

import re
import datetime

from stdf import *

def rewrite_times(inputfilename, decalage, heure_debut_fin, outputfile):
    file = open(inputfilename, encoding="ansi")
    for line in file:
        line = line.replace("\n", "").replace("\r", "")
        if re.fullmatch(r"[:\d]+.+ --> ?[:\d]+.+", line) is not None:
            rewrite_line(line, decalage, heure_debut_fin, outputfile)
        else:
            outputfile.write(line + "\n")

def rewrite_line(line, decalage, heure_debut_fin, outputfile):
    time1_init = line[0:8]
    if (heure_debut_fin):
        decalage = recalc_decalage(heure_debut_fin, time1_init)
        print(decalage)
    time1 = convert_time(time1_init, decalage)
    time2_init = line[17:25]
    if (heure_debut_fin):
        decalage = recalc_decalage(heure_debut_fin, time2_init)
    time2 = convert_time(time2_init, decalage)
    line = time1 + line[8:16] + time2 + line[25:]
    # line[17:25] = time2
    # line = line.replace(time1_init, time1).replace(time2_init, time2)
    outputfile.write(line + "\n")

def recalc_decalage(heure_debut_fin, time1_init):
    # heure_debut_fin : 
    # ["00:01:51","00:02:27", "01:47:24", "01:54:28"]
    # converti en
    # [111, 157, 3824, 3927]
    heure_debut, nouv_heure_debut, heure_fin, nouv_heure_fin = heure_debut_fin
    time1_sec = convert_heure_in_sec(time1_init)
    ecart_debut = nouv_heure_debut-heure_debut
    ecart_fin = nouv_heure_fin-heure_fin
    decalage = (time1_sec-heure_debut)*ecart_fin/(heure_fin-heure_debut)
    decalage = round(decalage, 0)
    print(decalage)
    return decalage
    


def convert_time(time_init, decalage):
    """
    Fonction qui prend en entrée une indication d'horaire (sous la forme HH:MM:SS)
    auquel on ajoute ou retire un nombre de secondes (int, qui peut être négatif)
    """
    new_time = time_init.split(":")
    #new_time = datetime.time(int(new_time[0]), int(new_time[1]), int(new_time[2]))    
    new_time = datetime.time(*list(map(int, new_time)))
    new_time = datetime.datetime.combine(datetime.date.today(), 
                                         new_time) + datetime.timedelta(seconds=decalage)
    new_time = str(new_time.time())
    return new_time


def convert_heure_in_sec(hour):
    hour = [int(el) for el in hour.split(":")]
    seconds = hour[0]*3600 + hour[1]*60 + hour[2]
    return seconds

if __name__ == "__main__":
    text = """Programme d'ajustement dans la synchronisation des sous-titres
Le plus simple : il y a quelques secondes de décalage, même décalage sur toute la durée du film
--> on renseigne la zone "Decalage"
Une fois cela fait, si le décalage s'accroît au fil du film, il faut ajouter
les équivalences de début et de fin :
à quelle heure doit apparaître le premier sous-titre, et à quelle heure le dernier

"""
    print(text)
    inputfilename = input("Nom du fichier de sous-titres : ")
    decalage = input("Decalage (secondes) : ")
    if decalage:
        decalage = int(decalage)
    heure_debut_fin = input("Ou heure_debut=Nouvelle_heure_debut/heure_fin=Nouvelle_heure_fin\n\
Exemple : 00:01:51=00:02:27/01:47:24=01:54:28\n")
    if heure_debut_fin:
        heure_debut_fin = heure_debut_fin.split("/")[0].split("=") + heure_debut_fin.split("/")[1].split("=")
        heure_debut_fin = [convert_heure_in_sec(el) for el in heure_debut_fin]

    outputfile = input2outputfile(inputfilename, "corrige.sub")
    rewrite_times(inputfilename, decalage, heure_debut_fin, outputfile)