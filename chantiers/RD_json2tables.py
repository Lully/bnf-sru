# coding: utf-8

explain = """Récupération des oeuvres RobotDonnées JSON
pour en faire une page HTML par run avec toutes les oeuvres 
produisant chacune un tableau"""

from urllib import URLopener
from json2html import json2html
import re
import zipfile

from stdf import *


def initiate_html_file(file, run):
    line2report(f"<html>\n <head><title>run {run}</title></head>", file)
    line2report(f"<style type=\"text/css\">", file)
    line2report(f"</style>", file)
    line2report(f"<body>", file)

def end_html_file(file):
    line2report(" </body></html>")

def enrich_html(html_content, json_filename, rd_instance):
    html_content = f"\n<h1><a href=\"{rd_instance}/work/{json_filename}\">{json_filename}</a></h1>\n" + html_content
    html_content = re.sub(r"ark([\w:/]+)", 
                          r"<a href=\"https://catalogue.bnf.fr/\1\">\1</a>",
                          html_content)
    return html_content

def run2html(run, rd_instance):
    report = create_file("{run}.html")
    initiate_html_file(report, run)
    run_zipfile = f"{rd_instance}/workszip/{run}"
    URLopener(run_zipfile)
    # Décompression du fichier ZIP et écriture dans un dossier

    for json_file in run_zipfile:
        content = json.load(json_file)
        html_content = json2html(content)
        html_content = enrich_html(html_content, json_file.name, rd_instance)
        report.write(html_content)
    end_html_file(html_content)


if __name__ = "__main__":
    runs = input("Numéro du ou des runs (sép. : point-virgule) : ")
    rd_instance = input2default(input("Instance RobotDonnées [défaut : pfv] : "), "pfv")
    if "pfv" in rd_instance:
        rd_instance = "https://pfvrobotdonnees.bnf.fr"
    else:
        rd_instance = "http://robotdonnees.bnf.fr"
    for run in runs.split(";"):
        run2html(run, rd_instance)