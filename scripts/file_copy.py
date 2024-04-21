# coding: utf-8

explain = "Copie d'une succession de fichiers et sous-dossiers vers une destination pour sauvegarde"

import re
import os

def clean_fname(string):
    rootname = ".".join(string.split(".")[:-1])
    rootname_nett = rootname.lower()
    extension = string.split(".")[-1]
    chars = ".()"
    for c in chars:
        rootname_nett = rootname_nett.replace(c, " ")
    rootname_nett = rootname_nett.strip()
    return rootname, rootname_nett,extension


class Filename:
    def __init__(self, init_name, dirname):
        self.init = init_name
        self.dirname = dirname
        self.rootname, self.rootname_nett, self.extension = clean_fname(self.init)


def explore_directory(dirname, dict_dir):
    for f in os.listdir(dirname):
        if os.isfile(f):
            filename = Filename(f, dirname)
            
            dict_dir[filename.rootname_nett] = filename
        else:
            for subf in os.listdir(os.path.join(dirname, f)):
                if os.isfile(subf):
                    filename = Filename(subf, dirname)
                    dict_dir[filename.rootname_nett] = filename



def file_copy(source, target):
    dict_source = {}
    dict_target = {}
    explore_directory(source, dict_source)
    explore_directory(target, dict_target)



if __name__ == "__main__":
    source = input("Dossier d'origine (à sauvegarder) : ")
    target = input("Dossier de destination : ")
    file_copy(source, target)