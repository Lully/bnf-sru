# coding: utf-8

import pandas as pd
from lxml import etree

from attrib043 import Record

import SRUextraction as sru

# Initialisation des données
df = pd.read_csv("tableau_cas_de_tests.csv", encoding="utf-8", sep="\t")
df = df.astype(str)
df = df.fillna("")

dataset = etree.parse("castest-aut.xml")

dict_records = {}
for record in dataset.xpath("//record"):
    ark = sru.clean_ark(sru.record2fieldvalue(record, "003"))
    dict_records[ark] = Record(ark, record)

def test_043a():
    df043 = df[df["zone"] == "43"]
    df043o = df043[df043["sous-zone"] == "o"]
    for i, row in df043o.iterrows():
        ark = row["ARK"]
        if ark and ark in dict_records:
            f043o = sru.record2fieldvalue(dict_records[ark].new_xml, "043$o")
            new043o = dict_records[ark].new043o
            # à restaurer quand j'aurai alimenté la nouvelle notice XML
            # assert f043o == row["valeur"] == new043o
            assert row["valeur"] == new043o

"""def test_06X():
    # print(df["zone"])
    for tag in [int(el) for el in "060,061,062,063,064,065".split(",")]:
        sub_df = df[df["zone"] == tag]      # Sous-ensemble de données du dataframe
        if len(sub_df) == 0:
            sub_df = df[df["zone"] == str(tag)]
        print(sub_df)
        for i, row in sub_df.iterrows():
            ark = row["ARK"]
            subf = row["sous-zone"]
            field_value = sru.record2fieldvalue(dict_records[ark].new_xml, f"{tag}${subf}")
            # print(ark, tag, field_value, row["valeur"])
            assert field_value == row["valeur"]"""


if __name__ == "__main__":
    test_06X()