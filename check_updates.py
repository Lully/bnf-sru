# -*- coding: utf-8 -*-
"""
Created on Fri Nov  3 06:58:38 2017

@author: Lully
"""
import tkinter as tk
import re
import csv
from tkinter import filedialog
from lxml.html import parse
from lxml import etree
from unidecode import unidecode
from time import gmtime, strftime
import urllib.parse
from urllib import request
import pathlib
import webbrowser
import json
from collections import defaultdict

version = 2.0


url = "https://raw.githubusercontent.com/Lully/bnf-sru/master/last_compilations.csv"
response = urllib.request.urlopen(url)
cr = csv.reader(response, delimiter=':')
dic_compilations = defaultdict(int)
for row in cr:
    print(str(row))
    #dic_compilations[row[0]] = dic_compilations[row[1]]

print(dic_compilations)
"""
def check_updates():
    current_version = version
    url = "https://raw.githubusercontent.com/Lully/bnf-sru/master/last_compilations.py"
    response = urllib.request.urlopen(url)
    encoding = response.info().get_content_charset('utf8')
    data = json.loads(response.read().decode(encoding))
    print(data)
"""