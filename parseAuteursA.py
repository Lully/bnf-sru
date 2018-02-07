# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 15:50:09 2018

@author: Lully
"""


from lxml.html import parse
from lxml import etree
from unidecode import unidecode

url = "http://catalogue.bnf.fr/resultats-auteur.do?nomAuteur=a&filtre=2&pageRech=rau"
firstpage = parse(url)
suffixe = "depart=-"

resultats = open("resultatsAuteursA.txt","w",encoding="utf-8")
i = 18

while (i < 350000):
    urlpage = url + suffixe + str(i)
    print(urlpage)
    page = parse(urlpage)
    for lien in page.xpath("//a"):
        u = lien.get("href")
        texte = lien.text
        
        if (u is not None and texte is not None and u.find("ark") > 0 and unidecode(texte[0].lower()) == "a"):
            resultats.write(u.replace("/ark","ark") + "\n")
            print(u, texte)
            
    i += 20
	