# coding: utf-8
 
"""
En entrée de la fonction : un dictionnaire avec des listes
(objectif : comparaison de noms de collections pour un même éditeur)
"""
from pprint import pprint
from distance import levenshtein
from collections import defaultdict

exemple = {"Elsevier": ["coll1", "collection2", "coll3", "collect4", "colle4"]}

def liste2clusters(liste, distance_max):
    libelle2clusters = defaultdict(list)  # Pour un libellé, liste des clusters temporaires
    clusters = defaultdict(set)
    i = 0
    cluster_no = 0
    for el in liste:
        libelle2libelles = defaultdict(list) 
        j = liste.index(el)
        # Comparaison avec les éléments suivants dans la liste
        if (j > 0):
            if (el not in libelle2clusters):
                libelle2clusters[el].append(cluster_no)
            for el2 in liste[:j]:
                dist = levenshtein(el, el2)
                if (dist < distance_max):
                    cluster_num_el2 = libelle2clusters[el2][0]
                    libelle2clusters[el].append(cluster_num_el2)
        if (j+1 != len(liste)):
            for el2 in liste[j+1:]:
                dist = levenshtein(el, el2)
                if dist < distance_max:
                    libelle2libelles[el].append(el2)
                    libelle2clusters[el].append(cluster_no)
        i += 1
        cluster_no += 1

    clusters_temps2id = defaultdict(list)
    for libelle in libelle2clusters:
        libelle2clusters[libelle] = list(set(libelle2clusters[libelle]))
        for cluster in libelle2clusters[libelle]:
            clusters_temps2id[cluster].extend(libelle2clusters[libelle])
    for cluster in clusters_temps2id:
        clusters_temps2id[cluster] = "-".join([str(el) for el in sorted(list(set(clusters_temps2id[cluster])))])

    clusterid = 0
    for libelle in libelle2clusters:
        for cluster_temp in libelle2clusters[libelle]:
            empreinte = clusters_temps2id[cluster_temp]
            clusters[empreinte].add(libelle)
    for cluster in clusters:
        clusters[cluster] = sorted(list(clusters[cluster]))

    return (clusters)

def group2cluster(group, distance_max):
    """Clusterisation des éléments
    pour un sous-ensemble (exemple : pour un éditeur)"""
    libelle2clusters = liste2clusters(group, distance_max)
    if __name__ == "__main__":
        pprint(libelle2clusters)
    return libelle2clusters

def clusterisation(dico, distance_max):
    """
    Traitement du dictionnaire global comprenant plusieurs
    sous-ensembles de listes
    """
    general_dic = defaultdict(dict)
    for group in dico:
            general_dic[group] = group2cluster(dico[group], distance_max)
    return general_dic

if __name__ == "__main__":
    clusters = clusterisation(exemple, 3)