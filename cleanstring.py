# coding: utf-8

import os
from stdf import file2list
import csv
import re
from collections import defaultdict

from udecode import udecode

# Quelques listes de signes à nettoyer
listeChiffres = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
lettres = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o",
    "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"
]
lettres_sauf_x = [
    "a", "c", "b", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o",
    "p", "q", "r", "s", "t", "u", "v", "w", "y", "z"
]
ponctuation = [
    ".", ",", ";", ":", "?", "!", "%", "$", "£", "€", "#", "\\", "\"", "&", "~",
    "{", "(", "[", "`", "\\", "_", "@", ")", "]", "}", "=", "+", "*", "\/", "<",
    ">", ")", "}", "'", "/", "|"
]

stopWords = file2list(f"{os.path.dirname(os.path.realpath(__file__))}\stopWords.txt")
skipKeywords = file2list(f"{os.path.dirname(os.path.realpath(__file__))}\skipKeywords.txt")
punctuation = "!\"#$%&'()*+,./:;<=>?@[\\]^_`{|}~"


def clean_punctation(text):
    text = text.replace("\\'", "'")
    for char in ponctuation:
        text = text.replace(char, " ")
    return text


def clean_letters(text):
    text = udecode(text.lower())
    for char in lettres:
        text = text.replace(char, " ")
    return text


def clean_spaces(text):
    text = re.sub("\s\s+", " ", text).strip()
    return text


def clean_dollars(text):
    text = re.sub(r" ?\$. ", " ", text)
    return text



def clean_like_rd(titre):
    # Nettoyage façon RobotDonnées
    for skip in skipKeywords:
        if skip in titre:
            titre = titre.split(skip)[0]
    titre = udecode(titre.lower())
    for skip in skipKeywords:
        if skip in titre:
            titre = titre.split(skip)[0]
    titre = " ".join([el for el in titre.split(" ") if el and el not in stopWords])
    for sign in punctuation:
        titre = titre.replace(sign, " ")
    titre = " ".join([el for el in titre.split(" ") if el])
    return titre

def nettoyage_edition(string):
    string = clean_punctation(string)
    string = string.replace("°", "").replace("-", " ")
    string = clean_letters(string)
    string = clean_spaces(string)


def nettoyageTitrePourControle(string):
    string = clean_string(string, True)
    return string


def nettoyageTitrePourRecherche(string):
    string = clean_string(string, False)
    string = string.split(" ")
    string = [mot for mot in string if len(mot) > 1]
    string = " ".join(string)
    return string

def clean_string(string, remplacerEspaces=True, remplacerTirets=True):
    """nettoyage des chaines de caractères (titres, auteurs, isbn)

    suppression ponctuation, espaces (pour les titres et ISBN) et diacritiques"""
    string = udecode(string.lower())
    for signe in ponctuation:
        string = string.replace(signe, " ")
    # string = string.replace("'", " ")
    string = " ".join([el for el in string.split(" ") if el != ""])
    if remplacerTirets:
        string = string.replace("-", " ")
    if remplacerEspaces:
        string = string.replace(" ", "")
    string = string.strip()
    return string

class Titre:
    """Zone de titre"""

    def __init__(self, string):  # Notre méthode constructeur
        self.init = string
        self.controles = nettoyageTitrePourControle(self.init)
        self.recherche = nettoyageTitrePourRecherche(self.init)

    def __str__(self):
        """Méthode permettant d'afficher plus joliment notre objet"""
        return "{}".format(self.init)


if __name__ == "__main__":
    entry_filename = input("Fichier en entrée  : ")
    output_file = open(entry_filename[:-4]+"-nett.txt", "w", encoding="utf-8")
    with open(entry_filename, newline="\n", encoding="utf-8") as csvfile:
        entry_file = csv.reader(csvfile, delimiter="\t")
        for row in entry_file:
            texte = ""
            if row:
                texte = row[0].replace("$a", "").replace("$e", "").replace("$f", "").replace("$h", "").replace("$i", "")
            texte_nett = Titre(texte)
            print(texte_nett.init, texte_nett.controles)
            output_file.write(texte_nett.controles + "\n")