# -*- coding: utf-8 -*-
"""
Created on Fri Nov  3 08:55:07 2017

@author: Etienne Cavalié
Fonction qui interroge une page en ligne (dictionnaire Python) et récupère le numéro de la dernière version compilée pour un programme donné
"""
import json
from urllib import request
import codecs

def check_last_compilation(programID):
    programID_last_compilation = 0
    url = "https://raw.githubusercontent.com/Lully/bnf-sru/master/last_compilations.json"
    last_compilations = request.urlopen(url)
    reader = codecs.getreader("utf-8")
    last_compilations = json.load(reader(last_compilations))["last_compilations"][0]
    if (programID in last_compilations):
        programID_last_compilation = last_compilations[programID]
    return programID_last_compilation 
