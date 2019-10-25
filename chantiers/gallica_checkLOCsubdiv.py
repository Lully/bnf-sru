# coding: utf-8

from stdf import *
from udecode import udecode

subdiv_lieu = file2list("subdiv_lieux.txt")
subdiv_lieu = [udecode(el.lower()) for el in subdiv_lieu]

def searchLOCinQuery(query_element):
    test = False
    split_criteres = [" -- ", "--", '"', " or ", " and ", " all ", " adj ", " any ",
                      " notice ", " dc.type "]
    for el in split_criteres:    
        query_element = query_element.replace(el, "¤")
    query_element = [el.strip() for el in query_element.split("¤") if el.strip()]
    for el in query_element:
        if el.lower in subdiv_lieu:
            test = True
    query_element = udecode(" ".join(query_element).lower())
    if test is False:
        for el in subdiv_lieu:
            if el in query_element:
                test = True
    return test