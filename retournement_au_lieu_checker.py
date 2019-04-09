# coding: utf-8
"""
tests sur le retournement au lieu pour les vedettes pré-construites

Specs :
N°
1. a x --> a y
2. a g x --> a y g
3. a o g x g --> a y o g g
4. a g g x g --> a y g g g
5. a x y --> a y y
6. a x g --> a y g
7. a x z --> a y z
8. a x1 x2 --> a y x
Si Forces armées ou colonies :
$a {Sujet 1} $y {Lieu} $x {Sujet 2}
Sinon
$a {Sujet 2} $y {Lieu} $x {Sujet 1}

9. a g x1 x2 --> a y g x1
10. a x1 x2 g --> a y x1 g
11. a o g g x g --> a y o g g g
12. a z g x --> a y z g
13. a g x g --> a y g g
14. a x g g --> a y g g 
15. a o g x --> a y o g
16. a g x z --> a y g z 
17. a g g x z --> a y g g z
18. a x z g --> a y z g
"""

from collections import Counter

import SRUextraction as sru
from stdf import *


liste_subdiv_lieu = [
                    "ark:/12148/cb119677659",
                    "ark:/12148/cb120423190",
                    "ark:/12148/cb12340540d",
                    "ark:/12148/cb131629886",
                    "ark:/12148/cb12008152w",
                    "ark:/12148/cb133253863",
                    "ark:/12148/cb133254224",
                    "ark:/12148/cb11943941g",
                    "ark:/12148/cb12347990r",
                    "ark:/12148/cb119595562",
                    "ark:/12148/cb11947941f",
                    "ark:/12148/cb120452121",
                    "ark:/12148/cb133183242",
                    "ark:/12148/cb11935764v",
                    "ark:/12148/cb12304351n",
                    "ark:/12148/cb13537886h",
                    "ark:/12148/cb11961551m",
                    "ark:/12148/cb11975864z",
                    "ark:/12148/cb120329888",
                    "ark:/12148/cb11952385d",
                    "ark:/12148/cb13514114k",
                    "ark:/12148/cb13514118z",
                    "ark:/12148/cb119540612",
                    "ark:/12148/cb11966521w",
                    "ark:/12148/cb12010935s",
                    "ark:/12148/cb124685460",
                    "ark:/12148/cb120109395",
                    "ark:/12148/cb12289358r",
                    "ark:/12148/cb13537890r",
                    "ark:/12148/cb119471746",
                    "ark:/12148/cb11959623c",
                    "ark:/12148/cb12247500p",
                    "ark:/12148/cb12264901t",
                    "ark:/12148/cb12421645d",
                    "ark:/12148/cb124216473",
                    "ark:/12148/cb124216500",
                    "ark:/12148/cb11973342s",
                    "ark:/12148/cb11958033s",
                    "ark:/12148/cb119733434",
                    "ark:/12148/cb167543946",
                    "ark:/12148/cb119759407",
                    "ark:/12148/cb12100436q",
                    "ark:/12148/cb120458418",
                    "ark:/12148/cb11967146c",
                    "ark:/12148/cb13319049t",
                    "ark:/12148/cb11952088m",
                    "ark:/12148/cb11941828h",
                    "ark:/12148/cb11976156n",
                    "ark:/12148/cb11978058j",
                    "ark:/12148/cb12042405k",
                    "ark:/12148/cb12042477f",
                    "ark:/12148/cb123606643",
                    "ark:/12148/cb11938223m",
                    "ark:/12148/cb11934135c",
                    "ark:/12148/cb11965815j",
                    "ark:/12148/cb11975851m",
                    "ark:/12148/cb137694876",
                    "ark:/12148/cb12042216p",
                    "ark:/12148/cb119711762",
                    "ark:/12148/cb12084609t",
                    "ark:/12148/cb12173351h",
                    "ark:/12148/cb124196543",
                    "ark:/12148/cb12499139g",
                    "ark:/12148/cb12530973m",
                    "ark:/12148/cb122557030",
                    "ark:/12148/cb11964915k",
                    "ark:/12148/cb12010947s",
                    "ark:/12148/cb13318988z",
                    "ark:/12148/cb135386626",
                    "ark:/12148/cb11957063g",
                    "ark:/12148/cb133183409",
                    "ark:/12148/cb12181820b",
                    "ark:/12148/cb12046316x",
                    "ark:/12148/cb11975674q",
                    "ark:/12148/cb11954089f",
                    "ark:/12148/cb12061783c",
                    "ark:/12148/cb13318797c",
                    "ark:/12148/cb11996017w",
                    "ark:/12148/cb119414121",
                    "ark:/12148/cb11952003d",
                    "ark:/12148/cb12069649v",
                    "ark:/12148/cb11954113g",
                    "ark:/12148/cb12049667c",
                    "ark:/12148/cb11934650n",
                    "ark:/12148/cb119562675",
                    "ark:/12148/cb13574198p",
                    "ark:/12148/cb11955444t",
                    "ark:/12148/cb11946058f",
                    "ark:/12148/cb11931529t",
                    "ark:/12148/cb11976799k",
                    "ark:/12148/cb119813504",
                    "ark:/12148/cb12009075h",
                    "ark:/12148/cb11947289h",
                    "ark:/12148/cb11954159s",
                    "ark:/12148/cb11961809n",
                    "ark:/12148/cb12198848m",
                    "ark:/12148/cb133187919",
                    "ark:/12148/cb11944175t",
                    "ark:/12148/cb12650437z",
                    "ark:/12148/cb119670285",
                    "ark:/12148/cb119765542",
                    "ark:/12148/cb124685329",
                    "ark:/12148/cb11974104x",
                    "ark:/12148/cb12045383t",
                    "ark:/12148/cb11976925k",
                    "ark:/12148/cb119591726",
                    "ark:/12148/cb12047252r",
                    "ark:/12148/cb12099992f",
                    "ark:/12148/cb12306118r",
                    "ark:/12148/cb12061769t",
                    "ark:/12148/cb11975938p",
                    "ark:/12148/cb119486515",
                    "ark:/12148/cb12547283w",
                    "ark:/12148/cb11932512b",
                    "ark:/12148/cb119757593",
                    "ark:/12148/cb15094378f",
                    "ark:/12148/cb135433464",
                    "ark:/12148/cb120705515",
                    "ark:/12148/cb119353920",
                    "ark:/12148/cb119758132",
                    "ark:/12148/cb11937374j",
                    "ark:/12148/cb119759120",
                    "ark:/12148/cb12042702c",
                    "ark:/12148/cb14552446h",
                    "ark:/12148/cb12047837h",
                    "ark:/12148/cb12223189s",
                    "ark:/12148/cb119510511",
                    "ark:/12148/cb119708951",
                    "ark:/12148/cb12030497c",
                    "ark:/12148/cb12036995h",
                    "ark:/12148/cb12033175z",
                    "ark:/12148/cb11935195g",
                    "ark:/12148/cb119563454",
                    "ark:/12148/cb11970927t",
                    "ark:/12148/cb119800026",
                    "ark:/12148/cb11932843f",
                    "ark:/12148/cb12168051p",
                    "ark:/12148/cb119756632",
                    "ark:/12148/cb13319040q",
                    "ark:/12148/cb119770062",
                    "ark:/12148/cb11948225h",
                    "ark:/12148/cb11938467s",
                    "ark:/12148/cb12093666m",
                    "ark:/12148/cb119773224",
                    "ark:/12148/cb119766681",
                    "ark:/12148/cb11976472q",
                    "ark:/12148/cb13535166g",
                    "ark:/12148/cb12012192w",
                    "ark:/12148/cb11977309x",
                    "ark:/12148/cb122454556",
                    "ark:/12148/cb12062276z",
                    "ark:/12148/cb120496692",
                    "ark:/12148/cb12083312n",
                    "ark:/12148/cb11948618b",
                    "ark:/12148/cb11963568t",
                    "ark:/12148/cb11948231f",
                    "ark:/12148/cb122147017",
                    "ark:/12148/cb13319359z",
                    "ark:/12148/cb125248764",
                    "ark:/12148/cb11947876t",
                    "ark:/12148/cb12015428b",
                    "ark:/12148/cb11971664f",
                    "ark:/12148/cb13753975x",
                    "ark:/12148/cb11979281v",
                    "ark:/12148/cb13318474w",
                    "ark:/12148/cb11933785b",
                    "ark:/12148/cb11961511c",
                    "ark:/12148/cb119338054",
                    "ark:/12148/cb135439939",
                    "ark:/12148/cb11953253r"]

class Label:
    """Classe définissant les propriétés d'une notice"""

    def record2label(record, field):
        label = sru.record2fieldvalue(record, field)
        label = label[label.find("$a"):]
        label_subfields = ""
        for field_occ in record.xpath(record, field):
            label_subfields = sru.field2listsubfields(field_occ)
        return label, label_subfields

    def __init__(self, ark, field):  # Notre méthode constructeur
        self.ark = ark
        self.record = sru.SRU_result(f'persistent.id any "{ark}"',
                                     parametres="{'recordSchema': 'intermarcxchange'}").dict_records[ark]
        self.label, self.label_subfields = record2label(record, field)
        

def analyse_ark(ark, report):
    label = Label(ark)
    count_subfields = Counter(label.label_subfields)
    label_returned = ""
    if (count_subfields["x"] == 2):
        label_returned = return2subfieldsX(ark, label, report)
    else:
        label_returned = return1subfieldX(ark, label, report)
    line = [ark, arn2nn(ark), label.label, label.subfields, label_returned]
    line2report(line, report)


def return2subfieldsX(ark, label, report):
    """
    Cas des points d'accès après plusieurs $x
    --> Déplacer le 2e $x en $a, sauf
    si $x = "Forces armées" ou "Colonies"
    """
    label_list = label.label.split("$")[1:]
    position_x1 = 0
    position_x2 = 0
    label_returned = []
    i = 0
    for subfield in label_list:
        if (subfield[0] == "x"):
            if (position_x1 == 0):
                position_x1 = i
            else:
                position_x2 = i
        i += 1
    if ("x Colonies" in label_list
        or "x Forces armées" in label_list):
        label_returned.append(label_list.pop(position_x1))
    else:
        label_returned.append(label_list.pop(position_x2))
    for el in label_list:
        label_returned.append(el)
    label_returned[0] = "a" + label_returned[0][1:]
    label_returned[1] = "y" + label_returned[1][1:]
    label_returned = "$" + "$".join(label_returned)
    return label_returned

def return1subfieldX(ark, label, report):
    """
    Cas des points d'accès avec 1 seul $x
    """
    label_list = label.label.split("$")[1:]
    label_returned = []
    for subfield in label_list:
        if (subfield[0] == "x"):
            label_returned.append(label_list.pop(x_position))
    for el in label_list:
        label_returned.append(el)
    label_returned[0] = "a" + label_returned[0][1:]
    label_returned[1] = "y" + label_returned[1][1:]
    label_returned = "$" + "$".join(label_returned)
    return label_returned

if __name__ == "__main__":
    input_filename = input("Nom du fichier contenant la liste des ARK des notices à retourner : ")
    liste_ark = file2list(input_filename)
    report = input2outputfile(input_filename, "retournement")
    for ark in liste_ark:
        analyse_ark(ark, report)