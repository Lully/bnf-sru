# coding: utf-8

from stdf import create_file, line2report, file2list, sparql2dict
import csv

def file2analyse(liste_libelles, report):
    for libelle in liste_libelles:
        check_libelle(libelle, report)


def check_libelle(libelle, report):
    query = """
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    select * where {
    ?ark dcterms:isPartOf ?rameau; a skos:Concept;
    skos:prefLabel ?label.
    FILTER contains(?label, " -- """ + libelle + """\")
    }
    """
    results = sparql2dict("http://data.bnf.fr/sparql", query, ["ark", "label"])
    for result in results:
        line2report([result[result.find("ark"):], results[result]["label"][0]],
                    report)

if __name__ == "__main__":
    liste_libelles_filename = input("Nom du fichier contenant les libellés : ")
    liste_libelles = file2list(liste_libelles_filename)
    report = create_file("Controles subdiv gf.txt")
    file2analyse(liste_libelles, report)