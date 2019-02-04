# coding: utf-8

"""
Extraction des indexations liées aux concepts Genre-forme 
avec implémentation des règles décrites dans les spécifications de ce projet
afin de pouvoir distinguer les usages comme Sujet de ceux comme Genre-forme

Fichiers nécessaire en entrée :
- Liste des ARK des notices Rameau du référentiel Genre-forme (fichier texte, 1 colonne).
  Le nom est du fichier est demandé à l'exécution
- 1 fichier nommé "nna_combines_regles.txt" à 4 colonnes :
            - NNA
            - Libellé
            - Statut par défaut du concept qui précède ("GF" ou "Sujet") 
              s'il fait partie du référentiel GF
            - Exceptions à ce statut par défaut. 1 exception par ligne
- 1 fichier nommé "subdiv_sujets_ou_forme.txt" : 
            - NNA
            - choix par défaut (sujet ou forme)
            - types de documents qui sont des exceptions au comportement par défaut
            par exemple "Autoportraits" sera par défaut du Sujet
            sauf pour les types de document iconographiques. 
            Le fichier comportera alors la ligne :
            11930999    GF  i
"""

from collections import defaultdict
import re
import csv

import SRUextraction as sru
from stdf import create_file, line2report, input2outputfile, nn2ark

# Récupération de la liste des NNB traités
ark_bib_traites = set()

""" Pour chaque RAM, on identifie si :
libelle
zone_202 : True/False
histoire_et_critique : True/False
vedette_de_forme : True/False
sous_cette_vedette = True_False
etudes_sur = True/False
gf_combine_default = ""
gf_combine_exceptions = []
"""
dict_ram = defaultdict(dict)

# Dictionnaire des subdivisions autorisées comme sujet ou forme
# sans qu'on sache a priori de quoi il s'agit
dict_subdiv_sujets_formes = {}

def file2ark(input_filename, nna_combines_dict, outputfile):
    """
    Extraction des ARK du fichier en entrée
    """
    with open(input_filename) as file:
        for row in file:
            nna_ram = row.replace("\r", "").replace("\n", "")
            print(nna_ram)
            ram_still_exists = ram2metas(nna_ram, nna_combines_dict)
            if ram_still_exists:
                ram2bib(nna_ram, outputfile)


def nnacombines2rules(nna_combines_filename):
    ram_combinees_dict = defaultdict(dict)
    with open(nna_combines_filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for row in content:
            nna = row[0]
            ram_combinees_dict[nna]["libelle"] = row[1]
            ram_combinees_dict[nna]["default"] = row[2]
            if (len(row) == 4):
                exception = row[3]
                if ("exceptions" in ram_combinees_dict[nna]):
                    ram_combinees_dict[nna].exceptions.append(exception)
                else:
                    ram_combinees_dict[nna].exceptions = [exception]
    return ram_combinees_dict


def ram2metas(nna_ram, nna_combines_dict):
    """
    On peuple au fur et à mesure le dictionnaire des RAM
    """
    ark_ram = nn2ark(nna_ram)
    if ark_ram == "":
        dict_ram[nna] = {
            "ark_ram": "",
            "libelle": "",
            "zone_202": "",
            "histoire_et_critique": "",
            "vedette_de_forme": "",
            "sous_cette_vedette": "",
            "etudes_sur": "",
            "gf_combine_default": "",
            "gf_combine_exceptions": []
        }
    else:
        ram_record = sru.SRU_result(f'aut.ark any {ark_ram}',
                                    parametres={"recordSchema": "intermarcxchange"}).dict_records[ark_ram]
        dict_ram[nna] = {
                         "ark_ram": ark_ram,
                         "libelle": sru.record2fieldvalue(ram_record, "166"),
                         "zone_202": ram202(ram_record),
                         "gf_combine_default": nna_combines_dict[nna]["default"],
                         "gf_combine_exceptions": nna_combines_dict[nna]["exceptions"]
                        }
        if (dict_ram[nna]["zone_202"]):
            f202 = dict_ram[nna]["zone_202"]
            dict_ram[nna] = {
                             "histoire_et_critique": ram2histcritique(ram_record, f202),
                             "vedette_de_forme": ram2vedette_de_forme(ram_record, f202),
                             "sous_cette_vedette": ram2sous_cette_vedette(ram_record, f202),
                             "etudes_sur": ram2etudes_sur(ram_record, f202)
                            }
    if ark_ram:
        return True
    else:
        return False


def ram202(ram_record):
    # Notice RAM avec une zone 202 ? -> True/False
    f202 = record2fieldvalue(ram_record, "202")
    return f202


def ram2histcritique(ram_record, f202):
    # Notice RAM A-202 contient "Histoire et critique" -> True/False
    test = False
    if ("histoire et critique" in f202.lower()):
        test = True
    return test


def ram2vedette_de_forme(ram_record, f202):
    # Notice RAM A-202 commence par : "Sous cette vedette de forme" -> True/False
    test = False
    if (f202.startswith("$a Sous cette vedette de forme")):
        test = True
    return test


def ram2sous_cette_vedette(ram_record, f202):
    # Notice RAM A-202 commence par : "Sous cette vedette, on trouve" -> True/False
    test = False
    if (f202.startswith("$a Sous cette vedette, on trouve")):
        test = True
    return test


def ram2etudes_sur(ram_record, f202):
    # Notice RAM A-202 contient ".+(études|documents)[^\.]* sur .+" -> True/False
    test = False
    regex = ".+(études|documents)[^\.]* sur .+\..*"
    if (re.fullmatch(regex, f202)):
        test = True
    return test


def ram2bib(nna_ram, outputfile):
    """
    Pour chaque ARK Rameau, identification des BIB liées
    """
    query = f'bib.subject2bib any "{nna_ram}"'
    param_default = {"recordSchema": "intermarcxchange"}
    first_page = sru.SRU_result(query, parametres=param_default)
    # print(first_page.url)
    for ark_bib in first_page.dict_records:
        analyse_bib(nna_ram, ark_bib,
                    first_page.dict_records[ark_bib], outputfile)
    i = 1001
    while i < first_page.nb_results:
        param_default["startRecord"] = str(i)
        page = sru.SRU_result(query, parametres=param_default)
        for ark_bib in page.dict_records:
            analyse_bib(nna_ram, ark_bib,
                        page.dict_records[ark_bib], outputfile)
        i += 1000


def analyse_bib(nna_ram, ark_bib, xml_record, outputfile):
    """
    Pour chaque notice bib, on analyse si la notice correspond
    à un des cas des règles d'utilisation
    """
    fields_6XX = ["600", "601", "602", "603", "604", "605", "606", "607",
                  "608", "609", "610", "615", "616", "617"]
    for field in fields_6XX:
        fields_values = sru.record2fieldvalue(xml_record, field).split("~")
        for value in fields_values:
            value = value.strip()
            if (f"$3 {nna_ram} " in value):
                analyse_field(nna_ram, ark_bib,
                              xml_record, field, value,
                              outputfile)


def analyse_field(nna_ram, ark_bib, xml_record, field, value, outputfile):
    """
    Analyse d'une zone de la notice BIB dès lors qu'elle contient le NNA du GF
    On ne conserve la zone que si la RAM recherchée est la dernière $x de la zone,
    ou est une $a non suivie d'une $x
    """
    end_value = value[value.find(f"$3 {nna_ram} ") + len(f"$3 {nna_ram} "):]
    if (field != "606"
        and "$x" not in end_value[2:]):
        field6XXx(nna_ram, ark_bib, xml_record, field, value, outputfile)
    elif (end_value[1] == "a"
          and "$x" not in end_value[2:]):
        field606a(nna_ram, ark_bib, xml_record, field, value, outputfile)
    elif (end_value[1] == "x"
          and "$x" not in end_value[2:]):
        field606x(nna_ram, ark_bib, xml_record, field, value, outputfile)


def field6XXx(nna_ram, ark_bib, xml_record, field, value, outputfile):
    """
    Cas où le GF apparaît ailleurs qu'en 606
    = c'est du genre-forme. Reste à voir si c'est du GF combiné,
    ça si la RAM est précédée d'un autre GF
    """
    end_value = value[value.find(f"$3 {nna_ram} ") + len(f"$3 {nna_ram} "):]
    begin_value = value[:value.find(f"$3 {nna_ram} ")]
    if ("$x" not in begin_value):
        new_f6XX = begin_value.strip()
        new_f608 = f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
        line = [ark_bib, nna_ram, field, end_value[1],
                 value, new_f6XX, new_f608]
        line2report(line, outputfile)
    else:
        prec_subdiv = begin_value.split(" $3 ")][-1].strip()
        if (prec_subdiv[0:8] in ram_dict
            and prec_subdiv[10] == "x"):
            antepenultieme_subdiv = begin_value.split(" $3 ")][-2].strip()
            if (antepenultieme_subdiv[0:8] in ram_dict
                and antepenultieme_subdiv[10] == "x"):
                trois_genres_formes(nna_ram, ark_bib, 
                                    xml_record, field,
                                    value, 
                                    prec_subdiv,
                                    antepenultieme_subdiv,
                                    outputfile)
            else:
                deux_genres_formes(nna_ram, ark_bib, 
                                    xml_record, field,
                                    value, 
                                    prec_subdiv,
                                    outputfile)
 


        
def trois_genres_formes(nna_ram, ark_bib, xml_record, field, value, 
                        prec_subdiv, antepenultieme_subdiv, outputfile):
    """
    Cas où on a 3 genres-formes qui se suivent
    """
    end_value = value[value.find(f"$3 {nna_ram} ") + len(f"$3 {nna_ram} "):]
    new_f6XX = ""
    new_f608 = ""
    # Cas 1 : le concept du milieu est "Bibliographie"
    if (prec_subdiv == "13318324 $x Bibliographie"):
        new_f6XX = value[:value.find(f" $3 {prec_subdiv[0:8]}")]
        new_f608 = "¤".join([
                             f"$3 {prec_subdiv[0:8]} $a {prec_subdiv[12:]}",
                             f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
                            ])
    # Cas 2 : le concept du milieu est sujet
    # parce que le dernier concept est toujours précédé de sujet 
    # ou que celui du milieu fait partie des exceptions du dernier concept
    elif (
          (prec_subdiv[12:] in dict_ram[nna_ram]["gf_combine_exceptions"]
           and dict_ram[nna_ram]["gf_combine_default"] == "GF")
           or (prec_subdiv[12:] not in dict_ram[nna_ram]["gf_combine_exceptions"]
               and dict_ram[nna_ram]["gf_combine_default"] == "Sujet")
         ):
        new_f6XX = value[:value.find(f" $3 {nna_ram}")]
        new_f608 = f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
    # Cas 3 : le concept du milieu est GF
    # parce que le dernier concept est toujours précédé de GF 
    # ou que celui du milieu fait partie des exceptions du dernier concept
    # Et l'antépénultième est Sujet par le même mécanisme
    elif (
          (antepenultieme_subdiv[12:] in dict_ram[prec_subdiv[0:8]]["gf_combine_exceptions"])
           and dict_ram[prec_subdiv[0:8]]["gf_combine_default"] == "GF")
           or (antepenultieme_subdiv[12:]  not in dict_ram[prec_subdiv[0:8]]["gf_combine_exceptions"])
               and dict_ram[prec_subdiv[0:8]]["gf_combine_default"] == "Sujet"):
        new_f6XX = value[:value.find(f" $3 {prec_subdiv[0:8]}")]
        new_f608 = "¤".join([
                            f"$3 {prec_subdiv[0:8]} $a {prec_subdiv[12:]}",
                            f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
                            ])
    # Cas 4 : les 3 sont des GF
    else:
        new_f6XX = value[:value.find(f" $3 {antepenultieme_subdiv[0:8]}")]
        new_f608 = "¤".join([
                             f"$3 {antepenultieme_subdiv[0:8]} $a {antepenultieme_subdiv[12:]}",
                             f"$3 {prec_subdiv[0:8]} $a {prec_subdiv[12:]}",
                             f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
                            ])
    line = [ark_bib, nna_ram, field, end_value[1],
                 value, new_f6XX, new_f608, "3 genres-formes"]
    line2report(line, outputfile)


def deux_genres_formes(nna_ram, ark_bib, xml_record, field,
                       value, prec_subdiv, outputfile):
    end_value = value[value.find(f"$3 {nna_ram} ") + len(f"$3 {nna_ram} "):]
    new_f6XX = ""
    new_f608 = ""
    # Cas 1 : l'avant-dernier concept est sujet
    # parce que le dernier concept est toujours précédé de sujet 
    # ou que celui du milieu fait partie des exceptions du dernier concept
    if (
          (prec_subdiv[12:] in dict_ram[nna_ram]["gf_combine_exceptions"]
           and dict_ram[nna_ram]["gf_combine_default"] == "GF")
           or (prec_subdiv[12:] not in dict_ram[nna_ram]["gf_combine_exceptions"]
               and dict_ram[nna_ram]["gf_combine_default"] == "Sujet")
         ):
        new_f6XX = value[:value.find(f" $3 {nna_ram}")]
        new_f608 = f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
    # Cas 2 : l'avant-dernier concept est GF
    # parce que le dernier concept est toujours précédé de GF 
    # ou que l'avant-dernier fait partie des exceptions du dernier concept
    else :
        new_f6XX = value[:value.find(f" $3 {prec_subdiv[0:8]}")]
        new_f608 = "¤".join([
                            f"$3 {prec_subdiv[0:8]} $a {prec_subdiv[12:]}",
                            f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
                            ])
    line = [ark_bib, nna_ram, field, end_value[1],
                 value, new_f6XX, new_f608, "3 genres-formes"]
    line2report(line, outputfile)


def field606a(nna_ram, ark_bib, xml_record, field, value, outputfile):
    """
    Cas où la RAM genre-forme apparaît en 606$a
    """
    test_music = check_music(nna_ram, ark_bib, xml_record, field, value, outputfile)
    if test_music is False:
        if (dict_ram[nna_ram]["histoire_et_critique"]
            or dict_ram[nna_ram]["zone_202"] is False
            or dict_ram[nna_ram]["vedette_de_forme"] is True):
            new_f6XX = ""
            new_f608 = value
            line = [ark_bib, nna_ram, field, "a",
                    value, new_f6XX, new_f608]
            line2report(line, outputfile)
        elif(dict_ram[nna_ram]["sous_cette_vedette"] is True
            and dict_ram[nna_ram]["etudes_sur"] is False):
            new_f6XX = ""
            new_f608 = value
            line = [ark_bib, nna_ram, field, "a",
                    value, new_f6XX, new_f608]
            line2report(line, outputfile)


def check_music(nna_ram, ark_bib, xml_record, field, value, outputfile):
    test = False
    end_value = value[value.find(f"$3 {nna_ram} ") + len(f"$3 {nna_ram} "):]
    code = end_value[1]
    if ("ntm" in sru.record2fieldvalue(xml_record, "051$a")):
        test is True
        split_music_gf(nna_ram, ark_bib, xml_record, field, value, outputfile)    
    return test


def split_music_gf(nna_ram, ark_bib, xml_record, field, value, outputfile):
    """
    Le redécoupage des zones 606 pour les partitions notamment
    obéit à des règles différentes :
    si la dernière 606 $x = "Méthodes" (ou autres exceptions ?), seul Méthodes passe en 608
    Sinon, tout passe en 608
    """
    exceptions_split_music_gf = ["Méthodes"]
    if (dict_ram[nna_ram] in exceptions_split_music_gf):
        begin_value = value[:value.find(f"$3 {nna_ram} ")]
        new_f6XX = begin_value.strip()
        new_f608 = f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
        line = [ark_bib, nna_ram, field, end_value[1],
                value, new_f6XX, new_f608]
        line2report(line, outputfile)
    else:
        new_f6XX = ""
        new_f608 = value
        line = [ark_bib, nna_ram, field, code,
                    value, new_f6XX, new_f608, "musique"]


def field606x(nna_ram, ark_bib, xml_record, field, value, outputfile):
    """
    Cas où la RAM est la dernière $x de la zone 606
    """
    # tester si genre-forme simple ou combiné
    # en tout cas le dernier concept est du genre-forme
    type_doct = sru.record2fieldvalue(xml_record, "009").split("~")
    type_doct = [el[0] for el in type_doct]
    test_music = check_music(nna_ram, ark_bib, xml_record, field, value, outputfile)
    if (test_music is False):
        if (re.fullmatch(".+s'emploie[^\.]*en subdivision de forme.+",
            dict_ram[nna_ram]["zone_202"] is not None):
            print("gf")
        # subdivision de sujet ou de forme : cas par cas
        elif (re.fullmatch(".+s'emploie[^\.]*en subdivision de sujet.+ ou de forme.+",
            dict_ram[nna_ram]["zone_202"] is not None):
            test_gf = True
            if (nna_ram in dict_subdiv_sujets_formes):
                if (dict_subdiv_sujets_formes[nna_ram]["exceptions"]):
                    test_exceptions = False
                    for el in type_doct:
                        if (type_doct in dict_subdiv_sujets_formes[nna_ram]["exceptions"]):
                            test_exceptions = True
                    if (test_exceptions 
                        and dict_subdiv_sujets_formes[nna_ram]["default"] == "GF"):
                        test_gf = False
                    elif (test_exceptions is False
                        and dict_subdiv_sujets_formes[nna_ram]["default"] == "GF"):
                        test_gf = False
                elif (dict_subdiv_sujets_formes[nna_ram]["default"] == "GF"):
                    test_gf = False
            if test_gf:
                end_value = value[value.find(f"$3 {nna_ram} ") + len(f"$3 {nna_ram} "):]
                begin_value = value[:value.find(f"$3 {nna_ram} ")]
                if ("$x" not in begin_value):
                    new_f6XX = begin_value.strip()
                    new_f608 = f"$3 {nna_ram} {dict_ram[nna_ram]['libelle']}"
                    line = [ark_bib, nna_ram, field, end_value[1],
                            value, new_f6XX, new_f608]
                    line2report(line, outputfile)
                else:
                    prec_subdiv = begin_value.split(" $3 ")][-1].strip()
                    if (prec_subdiv[0:8] in ram_dict
                        and prec_subdiv[10] == "x"):
                        antepenultieme_subdiv = begin_value.split(" $3 ")][-2].strip()
                        if (antepenultieme_subdiv[0:8] in ram_dict
                            and antepenultieme_subdiv[10] == "x"):
                            trois_genres_formes(nna_ram, ark_bib, 
                                                xml_record, field,
                                                value, 
                                                prec_subdiv,
                                                antepenultieme_subdiv,
                                                outputfile)
                        else:
                            deux_genres_formes(nna_ram, ark_bib, 
                                            xml_record, field,
                                            value, 
                                            prec_subdiv,
                                            outputfile)

def EOT(ark_bib_traites, ram2metas, outputfile):
    """
    Fin des traitements, fermeture des fichiers, écriture des bilans
    """
    outputfile.close()
    ark_bib_traites_file.write("\n".join(list(ark_bib_traites)))
    ark_bib_traites_file.close
    for ark_ram in dict_ram:
        line = [dict_ram["ark_ram"]["zone_202"],
                dict_ram["ark_ram"]["histoire_et_critique"],
                dict_ram["ark_ram"]["vedette_de_forme"],
                dict_ram["ark_ram"]["sous_cette_vedette"],
                dict_ram["ark_ram"]["etudes_sur"],
                dict_ram["ark_ram"]["gf_combine_default"],
                dict_ram["ark_ram"]["gf_combine_exceptions"]]
        line2report(line, ram2metas)


def extract_subdiv_sujets_ou_formes(filename):
    with open(filename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for row in content:
            nna = row[0]
            default = row[1]
            type_doc_exceptions = row[2]
            dict_subdiv_sujets_formes[nna]["default"] = default
            dict_subdiv_sujets_formes[nna]["exceptions"] = type_doc_exceptions.split(",")


if __name__ == "__main__":
    input_filename = input("Nom du fichier contenant les NNA Rameau genre-forme : ")
    outputfile = input2outputfile(input_filename, "bib_liees")
    ark_bib_traites_file = input2outputfile(input_filename, "liste_NNB")
    ram_metas_file = input2outputfile(input_filename, "RAM_metas")
    
    line2report("NNB traités"], outputfile)
    line2report(["zone_202", "histoire_et_critique", "vedette_de_forme",
                 "sous_cette_vedette", "etudes_sur", "gf_combine_default",
                 "gf_combine_exceptions"], ram_metas_file)
    line2report(["ARK BIB", "NNA Rameau", "Zone", "Sous-zone",
                 "Valeur actuelle de la zone", "Nouvelle 6XX", "Nouvelle 608"], outputfile)
    nna_combines_dict = nnacombines2rules("nna_combines_regles.txt")
    extract_subdiv_sujets_ou_formes("subdiv_sujets_ou_forme.txt")
    file2ark(input_filename, nna_combines_dict, outputfile, ark_bib_traites_file)

    EOT(ark_bib_traites, ram2metas, outputfile)