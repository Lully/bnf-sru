# coding: utf-8

explain = """Le groupe de suivi a grand besoin d'un fichier à trois onglets : 
    la totalité des 167 ;
    les 167 dont le $g est le nom d'un département français ;
    les 167 dont le $g est le nom d'un État américain, sachant que Rameau a choisi de les saisir en respectant les AACR2 de 1979. Je te joins le tableau des formes utilisées, qui sont très souvent des formes abrégées."""

from stdf import *
import SRUextraction as sru

from listes import *


def extract_concepts(tous_167, depts_fr_167, lieux_americains):
    for ark in arks167:
        record = sru.SRU_result(f"idPerenne any \"{ark}\"", "http://noticesservices.bnf.fr/SRU", 
                                {"recordSchema": "InterXmarc_Complet"}).firstRecord
        if record is not None:
            label = sru.record2fieldvalue(record, "167")
            node167 = [node for node in record.xpath("*[@tag='167']")][0]
            subfields = sru.field2listsubfields(node167)
            f167g = sru.record2fieldvalue(record, "167$g")
            others = []
            for field in "460,461,462,463,464,465,466,467,468".split(","):
                for occ_field in record.xpath(f"*[@tag='{field}']"):
                    value = f"{field} {sru.field2value(field)}"
                    others.append(value)
            others = "¤".join(others)
            line2report([ark, ark2nn(ark), label, subfields, others], tous_167)
            if f167g in depts_fr_167:
                line2report([ark, ark2nn(ark), label, f167g, subfields, others], depts_fr_167)
            if f167g in lieux_americains:
                line2report([ark, ark2nn(ark), label, f167g, subfields, others], lieux_americains)

if __name__ == "__main__":
    tous_167 = create_file("tous_167.txt", "ARK,NNA,Label,listes sous-zones,Formes rejetées".split(","))
    depts_fr_167 = create_file("depts_fr_167.txt", "ARK,NNA,Label,$g,listes sous-zones,Formes rejetées".split(","))
    lieux_americains = create_file("lieux_americains.txt", "ARK,NNA,Label,$g,listes sous-zones,Formes rejetées".split(","))
    extract_concepts(tous_167, depts_fr_167, lieux_americains)