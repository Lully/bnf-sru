# coding: utf-8

"""
Script pour passer les résultats de la command suggest en fichier en sortie
plutôt que dans le terminal

Source : https://groups.google.com/forum/#!topic/annif-users/fPM9vCmIfpU
"""

from pprint import pprint
import annif
import annif.project
from annif.suggestion import SuggestionResult, \
    LazySuggestionResult, ListSuggestionResult
from annif.corpus import SubjectIndex
import annif.backend

import csv

"""
text = "SOME TEXT HERE AND THERE YOU CAN TRY"

class Object(object):
    pass
project = Object()
project.language= 'en'
project.analyzer = annif.analyzer.get_analyzer('snowball(english)')
project.vocab='yso-en'
project.subjects = SubjectIndex.load('./data/vocabs/yso-en/subjects')

tfidf_type = annif.backend.get_backend("tfidf")
tfidf = tfidf_type(
    backend_id='tfidf-en',
    config_params={'limit': 10},
    datadir=str('./data/projects/tfidf-en')
)

results = tfidf.suggest(text, project)
print(len(results))

for result in results:
    print(result.label)
    pprint(result, indent=2)"""

def get_project(project_name):
    class Object(object):
        pass
    project = Object()
    project.id = project_name
    project.language= 'fr'
    project.analyzer = annif.analyzer.get_analyzer('snowball(french)')
    if "dewey" in project_name:
        project.vocab='dewey'
        project.subjects = SubjectIndex.load('.data\vocabs\dewey\subjects')
    else:
        project.vocab='rameau'
        project.subjects = SubjectIndex.load('.data\vocabs\rameau\subjects')
    return project


def construct_backend(backend_type_user, backend_id_user, params_user, datadir_user):
    print(datadir_user)
    tfidf_type = annif.backend.get_backend(backend_type_user)
    tfidf = tfidf_type(backend_id=backend_id_user,
                       config_params=params_user,
                       datadir=str(datadir_user)
                      )
    return tfidf
    
def file2results(inputfilename, project, backend_user):
    outputfilename = inputfilename[:-4] + "-results" + inputfilename[-4:]
    report = open(outputfilename, "w", encoding="utf-8")
    with open(inputfilename, encoding="utf-8") as file:
        content = csv.reader(file, delimiter="\t")
        for row in content:
            metas = row[0]
            results = text2results(metas, backend_user, project)
            line = [metas, str(len(results)), 
                    " ; ".join([r.label for r in results]),
                    " ".join([f"<{r.uri}>" for r in results])]
            line2report(line, report)



def line2report(line, report, i=0, display=True):
    """
    Envoie une line (liste) dans un fichier.
    Sauf demande contraire, affiche la ligne
    dans le terminal avec un compteur
    """
    if display:
        if i:
            print(i, line)
        else:
            print(line)
    try:
        report.write("\t".join(line) + "\n")
    except TypeError:
        report.write("\t".join([str(el) for el in line]) + "\n")
      

def text2results(text, backend_constructed, project):
    results = backend_constructed.suggest(text, project)
    return results


if __name__ == "__main__":
    project_name = input("Nom du projet : ")
    inputfilename = input("Nom du fichier en entrée : ")
    input_limit = input("Limit [default : 8] : ")
    if input_limit:
        input_limit = int(input_limit)
    else:
        input_limit = 8
    input_threshold = input("threshold [default : 0.6] : ")
    if (input_threshold):
        input_threshold = float(input_threshold)
    else:
        input_threshold = 0.6
    # seuil threshold non pris en compte : fichier suggestion.py, ligne 135
    project = get_project(project_name)
    backend_type_user = "tfidf"
    backend_id_user = "tfidf-fr"
    params_user = {"limit": input_limit, "threshold": input_threshold}
    datadir_user = f"./data/projects/{project_name}"
    backend_user = construct_backend(backend_type_user, backend_id_user, params_user, datadir_user)
    file2results(inputfilename, project, backend_user)