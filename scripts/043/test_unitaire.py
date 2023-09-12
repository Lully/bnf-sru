# coding: utf-8

import pandas as pd
from lxml import etree

from attrib043 import Record

import SRUextraction as sru

limit = 500

# Initialisation des données
df = pd.read_csv("tableau_cas_de_tests.csv", encoding="utf-8", sep="\t")
df = df.astype(str)
df = df.fillna("")

dataset = etree.parse("castest-aut.xml")

dict_records = {}
for record in dataset.xpath("//record"):
    ark = sru.clean_ark(sru.record2fieldvalue(record, "003"))
    dict_records[ark] = Record(ark, record)

def test_043():
    df043 = df[df["zone"] == "43"]
    df043o = df043[df043["sous-zone"] == "o"]
    j = 0
    for i, row in df043o.iterrows():
        if j < limit:
            ark = row["ARK"]
            if "43" in str(row["Déjà rempli"]):
                new043 = sru.record2fieldvalue(dict_records[ark].new_xml, "043")
            if ark and ark in dict_records and "43" not in str(row["Déjà rempli"]):
                new043 = sru.record2fieldvalue(dict_records[ark].new_xml, "043").strip()
                #new043 = dict_records[ark].new043
                # à restaurer quand j'aurai alimenté la nouvelle notice XML
                # assert f043 == row["valeur"] == new043o
                expected = f"${row['sous-zone']} {row['valeur']}"
                expected = expected.replace("$$", "$").strip()
                print(39, j, ark, f"'{expected}'", f"'{new043}'")
                assert expected in new043
        j += 1

def test_06X():
    # print(df["zone"])
    for tag in [int(el) for el in "060,061,062,063,064,065".split(",")]:
        sub_df = df[df["zone"] == tag]      # Sous-ensemble de données du dataframe
        if len(sub_df) == 0:
            sub_df = df[df["zone"] == str(tag)]
        # print(sub_df)
        j = 0
        for i, row in sub_df.iterrows():
            if j < limit:
                ark = row["ARK"]
                subf = row["sous-zone"]
                if ark in dict_records:
                    field_value = sru.record2fieldvalue(dict_records[ark].new_xml, f"0{str(tag)}")
                    new06X = dict_records[ark].new06X["value"]
                    # print(ark, tag, field_value, row["valeur"])
                    expected = f"${row['sous-zone']} {row['valeur']}"
                    expected = expected.replace("$$", "$")
                    # print(62, i, ark, expected, new06X)
                    print(62, i, ark, expected, " -- trouvé : ", field_value)
                    # assert expected in new06X
                    assert expected in field_value
        j += 1

if __name__ == "__main__":
    test_043()
    test_06X()