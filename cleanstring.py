import csv
from unidecode import unidecode
from collections import defaultdict


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
    ">", ")", "}", "'"
]


def clean_punctation(text):
    text = text.replace("\\'", "'")
    for char in ponctuation:
        text = text.replace(char, " ")
    return text


def clean_letters(text):
    text = funcs.unidecode_local(text.lower())
    for char in letters:
        text = text.replace(char, " ")
    return text


def clean_spaces(text):
    text = re.sub("\s\s+", " ", text).strip()
    return text

def nettoyage_edition(string):
    string = clean_punctation(string)
    string = string.replace("°", "").replace("-", " ")
    string = clean_letters(string)
    string = clean_spaces(string)

def unidecode_local(string):
    """personnalisation de la fonction unidecode, 
    qui modifie aussi certains caractères de manière problématique
    par exemple : 
    ° devient 'deg' 
    """
    corr_temp_dict = {
        '°': '#deg#'
    }

    reverse_corr_temp_dict = defaultdict(str)
    for key in corr_temp_dict:
        reverse_corr_temp_dict[corr_temp_dict[key]] = key

    for char in corr_temp_dict:
        string = string.replace(char, corr_temp_dict[char])

    string = unidecode(string)
    for char in reverse_corr_temp_dict:
        string = string.replace(char, reverse_corr_temp_dict[char])
    return string


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
    string = unidecode_local(string.lower())
    for signe in ponctuation:
        string = string.replace(signe, "")
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